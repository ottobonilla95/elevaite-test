import re
import sys
import time
import boto3
import logging
from typing import Optional, TextIO, Dict, Any
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.instrumentation.logging import LoggingInstrumentor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.semconv.resource import ResourceAttributes


def configure_tracer(
    service_name: str = "fastapi-service",
    otlp_endpoint: Optional[str] = None,
    add_console_exporter: bool = True,
    resource_attributes: Optional[Dict[str, Any]] = None,
) -> trace.TracerProvider:
    """
    Configure OpenTelemetry tracer with optional OTLP exporter.

    Args:
        service_name: Name of the service for telemetry data
        otlp_endpoint: Endpoint for OTLP exporter (e.g. 'http://localhost:4317')
        add_console_exporter: Whether to add a console exporter for traces
        resource_attributes: Additional resource attributes to add

    Returns:
        The configured TracerProvider
    """
    # Create resource with service info
    attributes = {
        ResourceAttributes.SERVICE_NAME: service_name,
    }

    # Add any additional attributes
    if resource_attributes:
        attributes.update(resource_attributes)

    resource = Resource.create(attributes)

    # Create and set tracer provider
    provider = TracerProvider(resource=resource)

    # Add console exporter if requested
    if add_console_exporter:
        console_processor = BatchSpanProcessor(ConsoleSpanExporter())
        provider.add_span_processor(console_processor)

    # Add OTLP exporter if endpoint provided
    if otlp_endpoint:
        otlp_exporter = OTLPSpanExporter(endpoint=otlp_endpoint)
        otlp_processor = BatchSpanProcessor(otlp_exporter)
        provider.add_span_processor(otlp_processor)

    return provider


# Default tracer provider for when developers don't configure their own
default_tracer_provider = TracerProvider()
trace.set_tracer_provider(default_tracer_provider)
tracer = trace.get_tracer(__name__)

default_span_processor = BatchSpanProcessor(ConsoleSpanExporter())
trace.get_tracer_provider().add_span_processor(default_span_processor)  # type: ignore -- Exists after set is called

LoggingInstrumentor().instrument(set_logging_format=True)


class FastAPILogger:
    def __init__(
        self,
        name: str = "fastapi_logger",
        level: int = logging.DEBUG,
        stream: TextIO = sys.stdout,
        cloudwatch_enabled: bool = False,
        log_group: Optional[str] = None,
        log_stream: Optional[str] = None,
        filter_fastapi: bool = False,
        service_name: str = "fastapi-service",
        otlp_endpoint: Optional[str] = None,
        configure_otel: bool = False,
        resource_attributes: Optional[Dict[str, str]] = None,
    ):
        """
        Initialize a FastAPI logger with optional CloudWatch and OpenTelemetry integration.

        Args:
            name: Name of the logger
            level: Logging level
            stream: Output stream for logs
            cloudwatch_enabled: Whether to send logs to CloudWatch
            log_group: CloudWatch log group name (required if cloudwatch_enabled is True)
            log_stream: CloudWatch log stream name (required if cloudwatch_enabled is True)
            filter_fastapi: Whether to filter out standard FastAPI logs when sending to CloudWatch
            service_name: Service name for OpenTelemetry (used if configure_otel is True)
            otlp_endpoint: OpenTelemetry collector endpoint (e.g. 'http://localhost:4317')
            configure_otel: Whether to configure OpenTelemetry with this logger instance
            resource_attributes: Additional resource attributes for OpenTelemetry
        """
        # Configure OpenTelemetry if requested
        self.tracer = tracer
        if configure_otel:
            provider = configure_tracer(
                service_name=service_name,
                otlp_endpoint=otlp_endpoint,
                resource_attributes=resource_attributes,
            )
            trace.set_tracer_provider(provider)
            self.tracer = trace.get_tracer(name)

        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)
        self.filter_fastapi = filter_fastapi
        self.cloudwatch_enabled = cloudwatch_enabled
        self.log_group = log_group
        self.log_stream = log_stream

        # Validate CloudWatch parameters if enabled
        if cloudwatch_enabled:
            if not log_group or not log_stream:
                raise ValueError(
                    "log_group and log_stream must be provided when cloudwatch_enabled is True"
                )
            # Initialize boto3 client
            self.cloudwatch_client = boto3.client("logs")

        # Prevent duplicate handlers if already configured
        if not self.logger.handlers:
            handler = logging.StreamHandler(stream)
            # Ensure that the formatter includes trace and span IDs (injected by OpenTelemetry)
            formatter = logging.Formatter(
                "[elevAIte Logger] %(asctime)s - %(name)s - %(levelname)s - %(message)s - "
                "trace_id=%(otelTraceID)s - span_id=%(otelSpanID)s"
            )
            handler.setFormatter(formatter)

            # Create a custom handler that also sends to CloudWatch if enabled
            if cloudwatch_enabled:
                self._setup_cloudwatch_handler(handler)

            self.logger.addHandler(handler)

    def _setup_cloudwatch_handler(self, handler: logging.Handler) -> None:
        """Set up the CloudWatch handler by extending the existing handler."""
        original_emit = handler.emit

        def new_emit(record):
            # Call the original emit function first
            original_emit(record)

            formatter = handler.formatter
            if formatter:
                # Extract the log message
                log_message = formatter.format(record)

                # Process the log message
                processed_log = self._process_log(log_message)

                # Only send to CloudWatch if the log wasn't filtered out
                if processed_log is not None:
                    # Wrap the CloudWatch send in a span to capture trace details
                    with self.tracer.start_as_current_span("cloudwatch_log_send"):
                        self._send_log_to_cloudwatch(processed_log)

        # Replace the emit function
        handler.emit = new_emit

    def _process_log(self, log: str) -> Optional[str]:
        """
        Processes a log string by:
          1. Removing the bracketed prefix.
          2. Optionally filtering out regular FastAPI logs (if filter_fastapi is True).

        Args:
            log (str): The log string to process.

        Returns:
            Optional[str]: The cleaned log string, or None if it was filtered out.
        """
        # Remove leading square-bracketed prefix
        cleaned = re.sub(r"^\[[^\]]*\]\s*", "", log)

        if self.filter_fastapi:
            # Check for standard HTTP methods at the start of the cleaned log message
            if re.match(r"^(GET|POST|PUT|DELETE|PATCH|OPTIONS|HEAD)\s", cleaned):
                # If it's a typical FastAPI log message, return None to indicate it's ignored
                return None

        return cleaned

    def _send_log_to_cloudwatch(self, log: str) -> None:
        """
        Sends a given log string to AWS CloudWatch Logs.

        Args:
            log (str): The log message to send.
        """
        # Skip if CloudWatch is not enabled
        if not self.cloudwatch_enabled:
            return

        try:
            # Retrieve the upload sequence token for the log stream
            response = self.cloudwatch_client.describe_log_streams(
                logGroupName=self.log_group, logStreamNamePrefix=self.log_stream
            )
            if response["logStreams"]:
                sequence_token = response["logStreams"][0].get("uploadSequenceToken")
            else:
                self.logger.error(
                    "Log stream not found. Please ensure the log stream exists."
                )
                return
        except Exception as e:
            self.logger.error(f"Error retrieving log stream information: {e}")
            return

        # Create a log event with the current timestamp (in milliseconds)
        timestamp = int(time.time() * 1000)
        log_event = {"timestamp": timestamp, "message": log}

        # Prepare the parameters for sending the log event
        params = {
            "logGroupName": self.log_group,
            "logStreamName": self.log_stream,
            "logEvents": [log_event],
        }
        if sequence_token:
            params["sequenceToken"] = sequence_token

        # Send the log event to CloudWatch
        try:
            self.cloudwatch_client.put_log_events(**params)
        except Exception as e:
            self.logger.error(f"Error sending log event to CloudWatch: {e}")

    def get_logger(self):
        """
        Get the configured logger instance.

        Returns:
            logging.Logger: The configured logger instance.
        """
        return self.logger

    @staticmethod
    def attach_to_uvicorn(
        cloudwatch_enabled: bool = False,
        log_group: Optional[str] = None,
        log_stream: Optional[str] = None,
        filter_fastapi: bool = False,
        service_name: str = "fastapi-service",
        otlp_endpoint: Optional[str] = None,
        configure_otel: bool = False,
        resource_attributes: Optional[Dict[str, str]] = None,
    ):
        """
        Attach this logger to Uvicorn and FastAPI logs with optional CloudWatch and OpenTelemetry integration.

        Args:
            cloudwatch_enabled: Whether to send logs to CloudWatch
            log_group: CloudWatch log group name (required if cloudwatch_enabled is True)
            log_stream: CloudWatch log stream name (required if cloudwatch_enabled is True)
            filter_fastapi: Whether to filter out standard FastAPI logs when sending to CloudWatch
            service_name: Service name for OpenTelemetry (used if configure_otel is True)
            otlp_endpoint: OpenTelemetry collector endpoint (e.g. 'http://localhost:4317')
            configure_otel: Whether to configure OpenTelemetry with this logger instance
            resource_attributes: Additional resource attributes for OpenTelemetry
        """
        custom_logger = FastAPILogger(
            cloudwatch_enabled=cloudwatch_enabled,
            log_group=log_group,
            log_stream=log_stream,
            filter_fastapi=filter_fastapi,
            service_name=service_name,
            otlp_endpoint=otlp_endpoint,
            configure_otel=configure_otel,
            resource_attributes=resource_attributes,
        ).get_logger()

        # Redirect Uvicorn logs
        for uvicorn_logger in ["uvicorn", "uvicorn.access", "uvicorn.error"]:
            logging.getLogger(uvicorn_logger).handlers = custom_logger.handlers
            logging.getLogger(uvicorn_logger).setLevel(logging.DEBUG)

        # Redirect FastAPI logs
        logging.getLogger("fastapi").handlers = custom_logger.handlers
        logging.getLogger("fastapi").setLevel(logging.DEBUG)

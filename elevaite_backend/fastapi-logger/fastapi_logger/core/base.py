"""Base logger implementation for the Elevaite Logger."""

import sys
import logging
from typing import Optional, TextIO, Dict, Any

import boto3
from opentelemetry import trace

from fastapi_logger.core.telemetry import configure_tracer, default_tracer
from fastapi_logger.core.cloudwatch import CloudWatchHandler


class BaseLogger:
    """Base logger that handles configuration and core functionality."""

    def __init__(
        self,
        name: str = "elevaite_logger",
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
        Initialize a base logger with optional CloudWatch and OpenTelemetry integration.

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
        self.tracer = default_tracer
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
        self.cloudwatch_client = None

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
            if cloudwatch_enabled and self.cloudwatch_client:
                cloudwatch_handler = CloudWatchHandler(
                    self.cloudwatch_client,
                    self.log_group or "",
                    self.log_stream or "",
                    self.filter_fastapi,
                    self.tracer,
                )
                cloudwatch_handler.setup_handler(handler)

            self.logger.addHandler(handler)

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
        custom_logger = BaseLogger(
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

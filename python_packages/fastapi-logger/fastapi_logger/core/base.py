"""Base logger implementation for the Elevaite Logger."""

import sys
import logging
from typing import Optional, TextIO, Dict, Any

import boto3
from opentelemetry import trace

from fastapi_logger.core.telemetry import configure_tracer, default_tracer
from fastapi_logger.core.cloudwatch import CloudWatchHandler

# Global flag to prevent multiple uvicorn attachments
_uvicorn_attached = False


class BaseLogger:
    def __init__(
        self,
        name: str = "elevaite_logger",
        level: int = logging.INFO,
        stream: TextIO = sys.stdout,
        cloudwatch_enabled: bool = False,
        log_group: Optional[str] = None,
        log_stream: Optional[str] = None,
        filter_fastapi: bool = False,
        service_name: str = "fastapi-service",
        otlp_endpoint: Optional[str] = None,
        configure_otel: bool = False,
        resource_attributes: Optional[Dict[str, str]] = None,
        otlp_insecure: bool = False,
        otlp_timeout: int = 5,
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
            otlp_insecure: Whether to use insecure connection for OTLP (default: False for security)
            otlp_timeout: Timeout in seconds for OTLP exporter (default: 5)
        """
        # Configure OpenTelemetry if requested
        self.tracer = default_tracer
        if configure_otel:
            try:
                provider = configure_tracer(
                    service_name=service_name,
                    otlp_endpoint=otlp_endpoint,
                    resource_attributes=resource_attributes,
                    otlp_insecure=otlp_insecure,
                    otlp_timeout=otlp_timeout,
                )
                trace.set_tracer_provider(provider)
                self.tracer = trace.get_tracer(name)
            except Exception as e:
                # If OpenTelemetry configuration fails, fall back to default tracer
                print(f"Warning: OpenTelemetry configuration failed: {e}")
                self.tracer = default_tracer

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
            # Initialize boto3 client with error handling
            try:
                self.cloudwatch_client = boto3.client("logs")
            except Exception as e:
                print(f"Warning: CloudWatch client initialization failed: {e}")
                self.cloudwatch_enabled = False
                self.cloudwatch_client = None

        # Prevent duplicate handlers if already configured
        # Also check if any handler has our marker to avoid duplicates
        ELEVAITE_HANDLER_MARKER = "_elevaite_handler"
        has_elevaite_handler = any(
            hasattr(h, ELEVAITE_HANDLER_MARKER) for h in self.logger.handlers
        )

        if not self.logger.handlers or not has_elevaite_handler:
            # Clear existing handlers to prevent accumulation
            if has_elevaite_handler:
                self.logger.handlers = [
                    h
                    for h in self.logger.handlers
                    if not hasattr(h, ELEVAITE_HANDLER_MARKER)
                ]

            handler = logging.StreamHandler(stream)
            # Mark our handler
            setattr(handler, ELEVAITE_HANDLER_MARKER, True)

            # Use a colorized formatter with date first
            from fastapi_logger.core.formatter import ColorizedFormatter

            formatter = ColorizedFormatter()
            handler.setFormatter(formatter)

            # Create a custom handler that also sends to CloudWatch if enabled
            # Only if CloudWatch is enabled and not in a recursive logging situation
            if (
                cloudwatch_enabled
                and self.cloudwatch_client
                and name != "cloudwatch_logger"
            ):
                try:
                    cloudwatch_handler = CloudWatchHandler(
                        self.cloudwatch_client,
                        self.log_group or "",
                        self.log_stream or "",
                        self.filter_fastapi,
                        self.tracer,
                    )
                    cloudwatch_handler.setup_handler(handler)
                except Exception as e:
                    print(f"Warning: CloudWatch handler setup failed: {e}")

            self.logger.addHandler(handler)
            # Prevent propagation to root logger to avoid duplicate messages
            self.logger.propagate = False

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
        otlp_insecure: bool = False,
        otlp_timeout: int = 5,
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
            otlp_insecure: Whether to use insecure connection for OTLP (default: False for security)
            otlp_timeout: Timeout in seconds for OTLP exporter (default: 5)
        """
        global _uvicorn_attached

        # Prevent multiple attachments
        if _uvicorn_attached:
            print(
                "Warning: Uvicorn logger already attached, skipping duplicate attachment"
            )
            return

        # Create a marker to identify our handlers
        ELEVAITE_HANDLER_MARKER = "_elevaite_handler"

        custom_logger = BaseLogger(
            name="elevaite_uvicorn_logger",
            level=logging.INFO,  # Use INFO level instead of DEBUG to reduce log volume
            cloudwatch_enabled=cloudwatch_enabled,
            log_group=log_group,
            log_stream=log_stream,
            filter_fastapi=filter_fastapi,
            service_name=service_name,
            otlp_endpoint=otlp_endpoint,
            configure_otel=configure_otel,
            resource_attributes=resource_attributes,
            otlp_insecure=otlp_insecure,
            otlp_timeout=otlp_timeout,
        ).get_logger()

        # Mark our handlers to avoid duplicates
        for handler in custom_logger.handlers:
            setattr(handler, ELEVAITE_HANDLER_MARKER, True)

        # Add our custom handler to existing loggers instead of replacing them
        # This prevents breaking uvicorn's internal logging mechanisms
        for uvicorn_logger_name in ["uvicorn", "uvicorn.access", "uvicorn.error"]:
            uvicorn_logger = logging.getLogger(uvicorn_logger_name)

            # Check if we already have our handler attached
            has_elevaite_handler = any(
                hasattr(h, ELEVAITE_HANDLER_MARKER) for h in uvicorn_logger.handlers
            )

            if not has_elevaite_handler:
                # Add only the first handler to avoid duplicates
                if custom_logger.handlers:
                    uvicorn_logger.addHandler(custom_logger.handlers[0])
                # Set appropriate log level
                uvicorn_logger.setLevel(logging.INFO)
            # Prevent propagation to avoid duplicate logs
            uvicorn_logger.propagate = False

        # Add our handler to FastAPI logger
        fastapi_logger = logging.getLogger("fastapi")
        has_elevaite_handler = any(
            hasattr(h, ELEVAITE_HANDLER_MARKER) for h in fastapi_logger.handlers
        )

        if not has_elevaite_handler:
            if custom_logger.handlers:
                fastapi_logger.addHandler(custom_logger.handlers[0])
            fastapi_logger.setLevel(logging.INFO)
        fastapi_logger.propagate = False

        # Mark that we've attached to uvicorn
        _uvicorn_attached = True

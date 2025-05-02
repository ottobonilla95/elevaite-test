import os
import time
from typing import Dict, Optional

from fastapi_logger import ElevaiteLogger

LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")

CLOUDWATCH_ENABLED = os.environ.get("CLOUDWATCH_ENABLED", "false").lower() == "true"
LOG_GROUP = os.environ.get("AWS_LOG_GROUP", "auth-api-logs")
LOG_STREAM = os.environ.get("AWS_LOG_STREAM", f"auth-api-{int(time.time())}")

OTEL_ENABLED = os.environ.get("OTEL_ENABLED", "false").lower() == "true"
SERVICE_NAME = os.environ.get("OTEL_SERVICE_NAME", "auth-api")
OTLP_ENDPOINT = os.environ.get("OTLP_ENDPOINT", "http://localhost:4317")


def setup_logger(
    name: str = "auth_api", resource_attributes: Optional[Dict[str, str]] = None
) -> ElevaiteLogger:
    """
    Set up and configure the ElevaiteLogger.

    Args:
        name: Logger name
        resource_attributes: Additional resource attributes for OpenTelemetry

    Returns:
        Configured ElevaiteLogger instance
    """
    logger = ElevaiteLogger(
        name=name,
        cloudwatch_enabled=CLOUDWATCH_ENABLED,
        log_group=LOG_GROUP,
        log_stream=LOG_STREAM,
        filter_fastapi=True,
        service_name=SERVICE_NAME,
        otlp_endpoint=OTLP_ENDPOINT if OTEL_ENABLED else None,
        configure_otel=OTEL_ENABLED,
        resource_attributes=resource_attributes,
    )

    return logger


# Create a default logger instance
logger = setup_logger().get_logger()


def attach_logger_to_app():
    """
    Attach the logger to FastAPI and Uvicorn.
    This redirects all FastAPI and Uvicorn logs through our logger.
    """
    ElevaiteLogger.attach_to_uvicorn(
        cloudwatch_enabled=CLOUDWATCH_ENABLED,
        log_group=LOG_GROUP,
        log_stream=LOG_STREAM,
        filter_fastapi=True,
        service_name=SERVICE_NAME,
        otlp_endpoint=OTLP_ENDPOINT if OTEL_ENABLED else None,
        configure_otel=OTEL_ENABLED,
        resource_attributes={
            "service.name": SERVICE_NAME,
            "deployment.environment": os.environ.get("ENVIRONMENT", "development"),
        },
    )

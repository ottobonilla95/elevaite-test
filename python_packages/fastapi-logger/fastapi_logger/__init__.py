from fastapi_logger.logger import ElevaiteLogger
from fastapi_logger.core.base import BaseLogger
from fastapi_logger.core.telemetry import configure_tracer

elevaite_logger = ElevaiteLogger()

__all__ = [
    "ElevaiteLogger",
    "BaseLogger",
    "configure_tracer",
    "elevaite_logger",
]

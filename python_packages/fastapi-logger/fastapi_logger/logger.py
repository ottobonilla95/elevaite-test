import sys
import logging
from typing import Optional, TextIO, Dict, Any, Callable

from fastapi_logger.core.base import BaseLogger
from fastapi_logger.decorators.trace import TraceManager


class ElevaiteLogger(BaseLogger):
    """
    Enhanced logger with annotation and tracing capabilities.

    This logger extends the base logger with decorators for code tracing,
    logging function inputs/outputs, and annotating code with logging
    instructions.
    """

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
        otlp_insecure: bool = False,
        otlp_timeout: int = 5,
    ):
        super().__init__(
            name=name,
            level=level,
            stream=stream,
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
        )

        # Initialize the trace manager
        self.trace_manager = TraceManager(self.logger, self.tracer)

    # Expose decorator methods from trace manager

    def capture(self, func: Callable) -> Callable:
        """
        Decorator to capture and log function inputs and outputs.

        Example:
        @elevaite_logger.capture
        def add(a, b):
            return a + b

        Will log: "Function add called with: a=5, b=10" and "Function add returned: 15"
        """
        return self.trace_manager.capture(func)

    def watch(self, value: Any) -> Any:
        """
        Decorator to watch and log a string expression.

        Example:
        @elevaite_logger.watch
        f"Starting process with {variable_name}"

        Will log: "Expression: Starting process with {actual_value}"
        """
        return self.trace_manager.watch(value)

    def snapshot(self, variable_name: str, value: Any) -> Any:
        """
        Take a variable snapshot and log its value.

        Example:
        # Use this function call:
        result = calculate_complex_value()
        elevaite_logger.snapshot("result", result)

        Will log: "Variable snapshot: result = {actual_value}"
        """
        return self.trace_manager.snapshot(variable_name, value)

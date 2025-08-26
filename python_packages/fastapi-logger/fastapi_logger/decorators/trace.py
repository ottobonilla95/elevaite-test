import inspect
import functools
import logging
from typing import Any, Callable, Dict, List, Tuple, Optional

from opentelemetry import trace

from fastapi_logger.decorators.annotations import LogAnnotation, parse_annotations


class TraceManager:
    """Manages function tracing and annotation processing."""

    def __init__(self, logger: logging.Logger, tracer: Optional[trace.Tracer] = None):
        """
        Initialize the trace manager.

        Args:
            logger: The logger to use for log output
            tracer: Optional OpenTelemetry tracer
        """
        self.logger = logger
        self.tracer = tracer or trace.get_tracer(__name__)

    def capture(self, func: Callable) -> Callable:
        """
        Decorator to capture and log function inputs and outputs.

        Example:
        @elevaite_logger.capture
        def add(a, b):
            return a + b

        Will log: "Function add called with: a=5, b=10" and "Function add returned: 15"
        """

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Get source code to find annotations
            try:
                source = inspect.getsource(func)
                annotations = parse_annotations(source)
            except (OSError, TypeError):
                # If we can't get the source, continue without annotations
                annotations = []

            # Prepare parameters for logging
            sig = inspect.signature(func)
            bound_args = sig.bind(*args, **kwargs)
            bound_args.apply_defaults()

            # Start function execution
            with self.tracer.start_as_current_span(func.__name__):
                # Process function-level logging
                arg_values = []
                for param_name, param_value in bound_args.arguments.items():
                    arg_values.append(f"{param_name}={param_value}")

                message_called = (
                    f"Function {func.__name__} called with: {', '.join(arg_values)}"
                )
                self.logger.info(message_called)
                # Also log to module-level 'logger' if present and different
                try:
                    module_logger = func.__globals__.get("logger")
                    if (
                        module_logger is not None
                        and hasattr(module_logger, "info")
                        and module_logger is not self.logger
                    ):
                        module_logger.info(message_called)
                except Exception:
                    pass

                # Execute function with annotations processing
                frame = inspect.currentframe()
                try:
                    # Execute function while capturing all variable values at each line
                    result = self._execute_with_annotations(
                        func, args, kwargs, annotations, frame
                    )

                    # Log the function result
                    message_returned = f"Function {func.__name__} returned: {result}"
                    self.logger.info(message_returned)
                    try:
                        module_logger = func.__globals__.get("logger")
                        if (
                            module_logger is not None
                            and hasattr(module_logger, "info")
                            and module_logger is not self.logger
                        ):
                            module_logger.info(message_returned)
                    except Exception:
                        pass
                    return result
                finally:
                    del frame  # Avoid reference cycles

        return wrapper

    def watch(self, value: Any) -> Any:
        """
        Log an expression or string.

        Example:
        # Instead of the annotation-style syntax:
        # @elevaite_logger.watch
        # f"Starting process with {variable_name}"

        # Use this function call:
        elevaite_logger.watch(f"Starting process with {variable_name}")

        Will log: "Expression: Starting process with {actual_value}"
        """
        # Log the expression directly when called as a function
        self.logger.info(f"Expression: {value}")
        return value

    def snapshot(self, variable_name: str, value: Any) -> Any:
        """
        Take a variable snapshot and log its value.

        Example:
        # Instead of the annotation-style syntax:
        # @elevaite_logger.snapshot
        # result = calculate_complex_value()

        # Use this function call:
        result = calculate_complex_value()
        elevaite_logger.snapshot("result", result)

        Will log: "Variable snapshot: result = {actual_value}"
        """
        # Log the variable directly when called as a function
        self.logger.info(f"Variable snapshot: {variable_name} = {value}")
        return value

    def _execute_with_annotations(
        self,
        func: Callable,
        args: Tuple[Any, ...],
        kwargs: Dict[str, Any],
        annotations: List[LogAnnotation],
        parent_frame,
    ) -> Any:
        """Execute a function while processing annotations."""
        # Execute the function
        result = func(*args, **kwargs)

        # Process any annotations that were inside the function
        for annotation in annotations:
            if annotation.kind == "watch":
                # For watch annotations, log the expression
                cleaned_expression = annotation.value.strip()
                self.logger.info(f"Expression: {cleaned_expression}")

            elif annotation.kind == "snapshot":
                # For snapshot annotations, extract the variable name and log it
                try:
                    var_expr = annotation.value.strip()
                    if "=" in var_expr:
                        var_name = var_expr.split("=")[0].strip()
                        self.logger.info(f"Variable snapshot: {var_name}")
                except Exception as e:
                    self.logger.debug(f"Error processing snapshot annotation: {e}")

        return result

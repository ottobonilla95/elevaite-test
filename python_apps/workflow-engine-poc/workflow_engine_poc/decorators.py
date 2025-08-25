from typing import Callable
from .monitoring import monitoring


def step_traced(step_type: str):
    """Decorator to ensure step execution is wrapped in a span consistently."""

    def decorator(func: Callable):
        async def async_wrapper(*args, **kwargs):
            execution_context = kwargs.get("execution_context")
            step_config = kwargs.get("step_config", {})
            step_id = step_config.get("step_id", "unknown")
            exec_id = getattr(execution_context, "execution_id", "unknown")
            with monitoring.trace_step_execution(
                step_id=step_id, step_type=step_type, execution_id=exec_id
            ):
                return await func(*args, **kwargs)

        def sync_wrapper(*args, **kwargs):
            execution_context = kwargs.get("execution_context")
            step_config = kwargs.get("step_config", {})
            step_id = step_config.get("step_id", "unknown")
            exec_id = getattr(execution_context, "execution_id", "unknown")
            with monitoring.trace_step_execution(
                step_id=step_id, step_type=step_type, execution_id=exec_id
            ):
                return func(*args, **kwargs)

        import asyncio

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator

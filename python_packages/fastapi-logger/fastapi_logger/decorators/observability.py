from __future__ import annotations

import time
import functools
from typing import Any, Callable, Dict, Optional

from opentelemetry import trace
import opentelemetry.metrics as otelmetrics

from fastapi_logger.observability_constants import (
    COMPONENT_AGENT_STUDIO,
    ATTR_COMPONENT,
    ATTR_STATUS,
    ATTR_TOOL_NAME,
    SPAN_TOOL_CALL,
    METRIC_TOOL_CALLS_TOTAL,
    METRIC_TOOL_CALL_DURATION,
)

# Optional LLM constants (kept minimal to avoid unnecessary deps)
LLM_SPAN_NAME = "llm_call"
METRIC_LLM_CALLS_TOTAL = "llm_calls_total"
METRIC_LLM_CALL_DURATION = "llm_call_duration_seconds"
ATTR_LLM_MODEL = "llm.model"
ATTR_LLM_PROVIDER = "llm.provider"


def _get_meter(scope_name: str = "fastapi-logger.observability"):
    try:
        return otelmetrics.get_meter(scope_name)
    except Exception:
        return None


def _get_tracer():
    t = trace.get_tracer("fastapi-logger.observability")
    return (
        t if getattr(t, "start_as_current_span", None) else trace.get_tracer(__name__)
    )


def instrument_tool(
    tool_name_arg: str | int | None = None, component: str = COMPONENT_AGENT_STUDIO
) -> Callable:
    """
    Decorator to instrument a tool function with OTEL span and metrics.

    Args:
        tool_name_arg: Name or index of arg to use as tool name; if None uses function.__name__
        component: Component label value to apply to metrics/spans
    """

    def decorator(func: Callable) -> Callable:
        meter = _get_meter()
        counter = histogram = None
        try:
            if meter:
                counter = meter.create_counter(METRIC_TOOL_CALLS_TOTAL)
                histogram = meter.create_histogram(METRIC_TOOL_CALL_DURATION)
        except Exception:
            pass

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            tracer = _get_tracer()
            # Resolve tool name
            tool_name = func.__name__
            if isinstance(tool_name_arg, str) and tool_name_arg in kwargs:
                tool_name = kwargs.get(tool_name_arg, tool_name)
            elif isinstance(tool_name_arg, int) and tool_name_arg < len(args):
                tool_name = args[tool_name_arg]

            start = time.time()
            with tracer.start_as_current_span(
                SPAN_TOOL_CALL,
                attributes={ATTR_TOOL_NAME: str(tool_name), ATTR_COMPONENT: component},
            ) as span:
                status = "completed"
                try:
                    result = func(*args, **kwargs)
                    span.set_status(trace.Status(trace.StatusCode.OK))
                    return result
                except Exception as e:
                    status = "failed"
                    span.record_exception(e)
                    span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
                    raise
                finally:
                    duration = time.time() - start
                    try:
                        if counter:
                            counter.add(
                                1,
                                {
                                    ATTR_TOOL_NAME: str(tool_name),
                                    ATTR_STATUS: status,
                                    ATTR_COMPONENT: component,
                                },
                            )
                        if histogram:
                            histogram.record(
                                duration,
                                {
                                    ATTR_TOOL_NAME: str(tool_name),
                                    ATTR_COMPONENT: component,
                                },
                            )
                    except Exception:
                        pass

        return wrapper

    return decorator


def instrument_llm(
    model: Optional[str] = None,
    provider: Optional[str] = None,
    component: str = COMPONENT_AGENT_STUDIO,
) -> Callable:
    """
    Decorator to instrument LLM calls (generic), emitting span + metrics.

    If the wrapped function returns a dict with token counts (prompt_tokens, completion_tokens),
    this decorator does not attempt to parse it—keeps minimal surface for now.
    """

    def decorator(func: Callable) -> Callable:
        meter = _get_meter()
        counter = histogram = None
        try:
            if meter:
                counter = meter.create_counter(METRIC_LLM_CALLS_TOTAL)
                histogram = meter.create_histogram(METRIC_LLM_CALL_DURATION)
        except Exception:
            pass

        pass

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            span_attrs: Dict[str, Any] = {ATTR_COMPONENT: component}
            if model:
                span_attrs[ATTR_LLM_MODEL] = model
            if provider:
                span_attrs[ATTR_LLM_PROVIDER] = provider

            start = time.time()
            tracer = _get_tracer()
            with tracer.start_as_current_span(
                LLM_SPAN_NAME, attributes=span_attrs
            ) as span:
                status = "completed"
                try:
                    result = func(*args, **kwargs)
                    span.set_status(trace.Status(trace.StatusCode.OK))
                    return result
                except Exception as e:
                    status = "failed"
                    span.record_exception(e)
                    span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
                    raise
                finally:
                    duration = time.time() - start
                    try:
                        if counter:
                            labels = {ATTR_STATUS: status, ATTR_COMPONENT: component}
                            if model:
                                labels[ATTR_LLM_MODEL] = model
                            if provider:
                                labels[ATTR_LLM_PROVIDER] = provider
                            counter.add(1, labels)
                        if histogram:
                            labels = {ATTR_COMPONENT: component}
                            if model:
                                labels[ATTR_LLM_MODEL] = model
                            if provider:
                                labels[ATTR_LLM_PROVIDER] = provider
                            histogram.record(duration, labels)
                    except Exception:
                        pass

        return wrapper

    return decorator

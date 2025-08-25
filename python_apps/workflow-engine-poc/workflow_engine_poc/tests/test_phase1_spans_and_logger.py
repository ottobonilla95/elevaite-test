from typing import Sequence
from opentelemetry import trace
from opentelemetry.sdk.trace import ReadableSpan, TracerProvider
from opentelemetry.sdk.trace.export import (
    SimpleSpanProcessor,
    SpanExporter,
    SpanExportResult,
)

from workflow_engine_poc.monitoring import monitoring
from workflow_engine_poc.decorators import step_traced


class ListExporter(SpanExporter):
    def __init__(self):
        self.spans = []

    def export(self, spans: Sequence[ReadableSpan]) -> "SpanExportResult":
        self.spans.extend(spans)
        return SpanExportResult.SUCCESS

    def shutdown(self):
        return None


def test_monitoring_step_span_records_error_status():
    # Attach an in-memory exporter to the already-configured provider in monitoring
    exporter = ListExporter()
    provider = trace.get_tracer_provider()
    if isinstance(provider, TracerProvider):
        provider.add_span_processor(SimpleSpanProcessor(exporter))

    try:
        with monitoring.trace_step_execution("s1", "unit_test", "exec-1"):
            raise ValueError("boom")
    except ValueError:
        pass

    spans = exporter.spans
    # Last span should be step_execution with error status
    step_spans = [s for s in spans if s.name == "step_execution"]
    assert step_spans, "No step_execution spans captured"
    assert any(
        s.status
        and hasattr(s.status, "status_code")
        and s.status.status_code.name == "ERROR"
        for s in step_spans
    )
    # Attribute coverage
    attrs = step_spans[-1].attributes
    assert attrs.get("step.id") == "s1"
    assert attrs.get("step.type") == "unit_test"
    assert attrs.get("execution.id") == "exec-1"


def test_step_traced_decorator_wraps_calls():
    calls = []

    @step_traced("unit_test")
    def run_step(step_config=None, execution_context=None):
        step_id = step_config["step_id"] if step_config else "unknown"
        exec_id = execution_context.execution_id if execution_context else "unknown"
        calls.append((step_id, exec_id))
        return {"ok": True}

    class Ctx:
        execution_id = "exec-2"

    out = run_step(step_config={"step_id": "s2"}, execution_context=Ctx())
    assert out == {"ok": True}
    assert calls == [("s2", "exec-2")]


def test_elevaite_logger_attach_metrics_no_crash():
    from fastapi_logger import ElevaiteLogger

    # ensure metrics init path executes without OTLP configured
    ElevaiteLogger.attach_to_uvicorn(
        service_name="workflow-engine",
        configure_otel=True,
        configure_metrics_provider=True,
    )

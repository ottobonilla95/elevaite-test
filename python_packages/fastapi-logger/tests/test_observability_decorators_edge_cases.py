import pytest
import opentelemetry.metrics as otelmetrics
from opentelemetry import trace
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import InMemoryMetricReader
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import (
    SimpleSpanProcessor,
    SpanExporter,
    SpanExportResult,
)

from fastapi_logger.decorators.observability import instrument_tool, instrument_llm


class _InMemorySpanExporter(SpanExporter):
    def __init__(self):
        self.spans = []

    def export(self, spans):
        self.spans.extend(spans)
        return SpanExportResult.SUCCESS

    def get_finished_spans(self):
        return list(self.spans)

    def shutdown(self):
        self.spans.clear()


@pytest.fixture()
def otel_env(monkeypatch):
    # Metrics
    reader = InMemoryMetricReader()
    mprovider = MeterProvider(metric_readers=[reader])

    monkeypatch.setattr(
        otelmetrics,
        "get_meter",
        lambda name="fastapi-logger.observability": mprovider.get_meter(name),
    )

    # Traces
    exporter = _InMemorySpanExporter()
    tprovider = TracerProvider()
    tprovider.add_span_processor(SimpleSpanProcessor(exporter))

    try:
        trace.set_tracer_provider(tprovider)
    except Exception:
        pass

    monkeypatch.setattr(
        trace,
        "get_tracer",
        lambda name, version=None, schema_url=None: tprovider.get_tracer(name),
    )

    yield reader, exporter

    tprovider.shutdown()


def find_metric(reader, name):
    md = reader.get_metrics_data()
    for rm in getattr(md, "resource_metrics", []) or []:
        for sm in rm.scope_metrics:
            for m in sm.metrics:
                if m.name == name:
                    return m
    return None


def datapoints(metric):
    return getattr(getattr(metric, "data", None), "data_points", [])


def test_instrument_tool_name_resolution_edge_cases(otel_env):
    reader, exporter = otel_env

    @instrument_tool(tool_name_arg="name", component="agent_studio")
    def tool_missing_kw(x):
        return x

    @instrument_tool(tool_name_arg=5, component="agent_studio")
    def tool_index_oob(x):
        return x

    assert tool_missing_kw(1) == 1
    assert tool_index_oob(2) == 2

    # No exceptions and spans should be recorded
    spans = exporter.get_finished_spans()
    assert any(s.name == "tool_call" for s in spans)


def test_instrument_llm_without_model_provider(otel_env):
    reader, exporter = otel_env

    @instrument_llm(component="agent_studio")
    def call_llm(x):
        return x

    assert call_llm("ok") == "ok"

    spans = exporter.get_finished_spans()
    assert any(s.name == "llm_call" for s in spans)


def test_metrics_provider_unavailable_graceful(monkeypatch, otel_env):
    reader, exporter = otel_env

    # Force meter retrieval to fail
    monkeypatch.setattr(
        otelmetrics,
        "get_meter",
        lambda *a, **k: (_ for _ in ()).throw(Exception("no meter")),
    )

    @instrument_tool(component="agent_studio")
    def tool(x):
        return x

    @instrument_llm(component="agent_studio")
    def llm(x):
        return x

    assert tool(1) == 1
    assert llm(2) == 2

    # Spans still emitted
    spans = [s.name for s in exporter.get_finished_spans()]
    assert "tool_call" in spans and "llm_call" in spans


def test_parent_child_span_relationship(otel_env):
    reader, exporter = otel_env

    tracer = trace.get_tracer("test")

    @instrument_tool(component="agent_studio")
    def tool(x):
        return x

    with tracer.start_as_current_span("parent") as parent:
        tool(3)

    spans = exporter.get_finished_spans()
    child = next(s for s in spans if s.name == "tool_call")
    p = next(s for s in spans if s.name == "parent")
    # Validate parent-child linkage by span context
    assert getattr(child, "parent", None) is not None
    assert child.parent.span_id == p.context.span_id

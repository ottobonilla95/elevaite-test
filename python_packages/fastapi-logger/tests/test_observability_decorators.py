import time
import pytest

from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import InMemoryMetricReader
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import (
    SimpleSpanProcessor,
    SpanExporter,
    SpanExportResult,
)
from opentelemetry import trace


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


class _ResettableMeterProvider(MeterProvider):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def install(self):
        # Avoid override errors by installing only when no provider is set
        try:
            from opentelemetry.metrics import set_meter_provider

            set_meter_provider(self)
        except Exception:
            # swallow to keep tests independent
            pass


from fastapi_logger.decorators.observability import instrument_tool, instrument_llm


@pytest.fixture()
def otel_env(monkeypatch):
    # Metrics
    mreader = InMemoryMetricReader()
    mprovider = _ResettableMeterProvider(metric_readers=[mreader])
    mprovider.install()
    # Ensure our decorators obtain meters from this provider
    import opentelemetry.metrics as otelmetrics

    monkeypatch.setattr(
        otelmetrics,
        "get_meter",
        lambda name="fastapi-logger.observability": mprovider.get_meter(name),
    )

    # Traces
    exporter = _InMemorySpanExporter()
    provider = TracerProvider()
    processor = SimpleSpanProcessor(exporter)
    provider.add_span_processor(processor)
    try:
        trace.set_tracer_provider(provider)
    except Exception:
        # If provider already set, attach our processor to it
        try:
            current_provider = trace.get_tracer_provider()
            current_provider.add_span_processor(processor)
        except Exception:
            pass

    # Ensure our decorators get tracers from this provider
    def _get_tracer(name, version=None, schema_url=None):
        return provider.get_tracer(name, version, schema_url)

    monkeypatch.setattr(trace, "get_tracer", _get_tracer)

    yield mreader, exporter, mprovider

    # Cleanup once for the module
    provider.shutdown()


def find_metric(reader, name):
    md = reader.get_metrics_data()
    for rm in md.resource_metrics:
        for sm in rm.scope_metrics:
            for m in sm.metrics:
                if m.name == name:
                    return m
    return None


def data_points(metric):
    return getattr(getattr(metric, "data", None), "data_points", [])


def test_instrument_tool_success_and_failure(otel_env):
    reader, exporter, provider = otel_env

    calls = {"n": 0}

    @instrument_tool(tool_name_arg=None, component="agent_studio")
    def sample_tool(x):
        calls["n"] += 1
        if calls["n"] == 2:
            raise RuntimeError("boom")
        return x * 2

    assert sample_tool(3) == 6
    with pytest.raises(RuntimeError):
        sample_tool(1)

    provider.force_flush()

    total = find_metric(reader, "tool_calls_total")
    dur = find_metric(reader, "tool_call_duration_seconds")
    assert total is not None and dur is not None

    dps = data_points(total)
    statuses = sorted([dp.attributes.get("status") for dp in dps])
    assert statuses == ["completed", "failed"]
    for dp in dps:
        assert dp.attributes.get("component") == "agent_studio"
        assert dp.attributes.get("tool.name") == "sample_tool"

    # Spans
    spans = exporter.get_finished_spans()
    names = [s.name for s in spans]
    assert names.count("tool_call") == 2


def test_instrument_llm_success_and_failure(otel_env):
    reader, exporter, provider = otel_env

    @instrument_llm(model="gpt-4o", provider="openai", component="agent_studio")
    def call_llm(prompt):
        if "fail" in prompt:
            raise ValueError("bad prompt")
        return prompt.upper()

    assert call_llm("hello") == "HELLO"
    with pytest.raises(ValueError):
        call_llm("fail please")

    provider.force_flush()

    total = find_metric(reader, "llm_calls_total")
    dur = find_metric(reader, "llm_call_duration_seconds")
    assert total is not None and dur is not None

    for dp in data_points(total):
        assert dp.attributes.get("status") in ("completed", "failed")
        assert dp.attributes.get("component") == "agent_studio"
        assert dp.attributes.get("llm.model") == "gpt-4o"
        assert dp.attributes.get("llm.provider") == "openai"

    spans = exporter.get_finished_spans()
    names = [s.name for s in spans]
    assert names.count("llm_call") == 2

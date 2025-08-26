from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import InMemoryMetricReader
from opentelemetry.metrics import set_meter_provider


def find_metric(reader, name):
    md = reader.get_metrics_data()
    for rm in md.resource_metrics:
        for sm in rm.scope_metrics:
            for m in sm.metrics:
                if m.name == name:
                    return m
    return None


def test_workflow_metrics_emitted_with_trace_context_manager(monkeypatch):
    from workflow_engine_poc.monitoring import monitoring

    reader = InMemoryMetricReader()
    provider = MeterProvider(metric_readers=[reader])
    set_meter_provider(provider)

    with monitoring.trace_workflow_execution("wf-x", "exec-x"):
        pass

    provider.force_flush()

    wf_total = find_metric(reader, "workflow_executions_total")
    wf_dur = find_metric(reader, "workflow_execution_duration_seconds")
    assert wf_total is not None and wf_dur is not None


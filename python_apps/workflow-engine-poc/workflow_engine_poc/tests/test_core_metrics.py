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


def count_points(metric):
    if metric is None:
        return 0
    return len(getattr(metric.data, "data_points", []))


def test_workflow_metrics_emitted_with_trace_context_manager_success_and_failure(
    monkeypatch,
):
    from workflow_engine_poc.monitoring import monitoring

    reader = InMemoryMetricReader()
    provider = MeterProvider(metric_readers=[reader])
    set_meter_provider(provider)

    # Success path
    with monitoring.trace_workflow_execution("wf-x", "exec-x"):
        pass

    # Failure path
    try:
        with monitoring.trace_workflow_execution("wf-y", "exec-y"):
            raise RuntimeError("boom")
    except RuntimeError:
        pass

    provider.force_flush()

    wf_total = find_metric(reader, "workflow_executions_total")
    wf_dur = find_metric(reader, "workflow_execution_duration_seconds")
    assert wf_total is not None and wf_dur is not None

    # Verify two increments (completed and failed)
    dps = getattr(wf_total.data, "data_points", [])
    statuses = sorted([dp.attributes.get("status") for dp in dps])
    assert statuses == ["completed", "failed"]
    # Labels include component
    for dp in dps:
        assert dp.attributes.get("component") == "workflow_engine"

    # Duration histogram has at least one datapoint and component label
    assert count_points(wf_dur) >= 1
    for dp in getattr(wf_dur.data, "data_points", []):
        assert dp.attributes.get("component") == "workflow_engine"

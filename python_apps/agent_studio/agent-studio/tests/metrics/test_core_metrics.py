from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import InMemoryMetricReader
from opentelemetry.metrics import get_meter, set_meter_provider


def collect_metrics():
    reader = InMemoryMetricReader()
    provider = MeterProvider(metric_readers=[reader])
    set_meter_provider(provider)
    meter = get_meter("agent-studio.analytics")
    return reader, provider, meter


def find_metric(reader, name):
    md = reader.get_metrics_data()
    for rm in md.resource_metrics:
        for sm in rm.scope_metrics:
            for m in sm.metrics:
                if m.name == name:
                    return m
    return None


def test_workflow_agent_tool_metrics_emitted_when_methods_called(monkeypatch):
    from services.analytics_service import analytics_service

    reader, provider, meter = collect_metrics()

    # Simulate workflow
    analytics_service.start_workflow(
        "wf-1", "unit", agents_involved=["a"], session_id=None, user_id=None
    )
    analytics_service.end_workflow("wf-1", status="success", db=None)

    # Simulate agent
    analytics_service.start_agent_execution("exec-1", agent_name="Agent", db=None)
    analytics_service.end_agent_execution("exec-1", status="success", db=None)

    # Simulate tool
    analytics_service.start_tool_usage("use-1", tool_name="tool", execution_id="exec-1")
    analytics_service.end_tool_usage("use-1", status="success", db=None)

    provider.force_flush()

    # Workflow metrics
    wf_total = find_metric(reader, "workflow_executions_total")
    wf_dur = find_metric(reader, "workflow_execution_duration_seconds")
    assert wf_total is not None and wf_dur is not None

    # Agent metrics
    agent_total = find_metric(reader, "agent_executions_total")
    agent_dur = find_metric(reader, "agent_execution_duration_seconds")
    assert agent_total is not None and agent_dur is not None

    # Tool metrics
    tool_total = find_metric(reader, "tool_calls_total")
    tool_dur = find_metric(reader, "tool_call_duration_seconds")
    assert tool_total is not None and tool_dur is not None

    # Verify component labels are present in all metrics
    for metric in [wf_total, agent_total, tool_total]:
        dps = getattr(metric.data, "data_points", [])
        for dp in dps:
            assert dp.attributes.get("component") == "agent_studio"

    # Verify duration histograms have component labels
    for metric in [wf_dur, agent_dur, tool_dur]:
        dps = getattr(metric.data, "data_points", [])
        for dp in dps:
            assert dp.attributes.get("component") == "agent_studio"

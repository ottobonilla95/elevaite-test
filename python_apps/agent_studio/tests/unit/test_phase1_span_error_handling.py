from fastapi_logger import ElevaiteLogger
from services.analytics_service import analytics_service


def test_logger_attach_with_metrics_flag_no_crash(monkeypatch):
    ElevaiteLogger.attach_to_uvicorn(
        service_name="agent-studio",
        configure_otel=True,
        configure_metrics_provider=True,
    )


def test_analytics_service_spans_record_exception(monkeypatch):
    try:
        with analytics_service.track_workflow(
            workflow_type="test", session_id="s", user_id="u"
        ):
            raise RuntimeError("wf failure")
    except RuntimeError:
        pass

    try:
        with analytics_service.track_agent_execution(
            agent_id="1", agent_name="Test", execution_id="exec-123"
        ):
            raise RuntimeError("agent failure")
    except RuntimeError:
        pass

    try:
        with analytics_service.track_tool_usage(
            tool_name="tool", execution_id="exec-123"
        ):
            raise RuntimeError("tool failure")
    except RuntimeError:
        pass

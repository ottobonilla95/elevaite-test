"""
Unit tests for AnalyticsService

Tests the business logic of analytics recording with mocked database.
"""

import uuid
from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest

from workflow_core_sdk.services.analytics_service import AnalyticsService


@pytest.fixture
def mock_session():
    """Mock SQLModel session"""
    session = MagicMock()
    session.add.return_value = None
    session.commit.return_value = None
    return session


@pytest.fixture
def analytics_service():
    """Create an instance of AnalyticsService"""
    return AnalyticsService()


@pytest.fixture
def sample_agent_output():
    """Sample agent output for testing"""
    return {
        "agent_name": "TestAgent",
        "agent_id": str(uuid.uuid4()),
        "query": "What is the weather?",
        "response": "The weather is sunny.",
        "usage": {
            "tokens_in": 10,
            "tokens_out": 20,
            "total_tokens": 30,
            "llm_calls": 1,
        },
        "model": {
            "provider": "openai",
            "name": "gpt-4",
        },
    }


class TestRecordAgentExecution:
    """Tests for recording agent execution metrics"""

    def test_record_agent_execution_success(self, analytics_service, mock_session, sample_agent_output):
        """Test recording agent execution with all fields"""
        execution_id = str(uuid.uuid4())
        step_execution_id = str(uuid.uuid4())
        started_at = datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
        completed_at = datetime(2024, 1, 1, 0, 0, 5, tzinfo=timezone.utc)

        # Mock refresh to set the ID
        metric_id = uuid.uuid4()

        def mock_refresh(obj):
            obj.id = metric_id

        mock_session.refresh.side_effect = mock_refresh

        result_id = analytics_service.record_agent_execution(
            mock_session,
            execution_id=execution_id,
            step_execution_id=step_execution_id,
            agent_output=sample_agent_output,
            status="completed",
            started_at=started_at,
            completed_at=completed_at,
        )

        assert result_id == metric_id
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()
        mock_session.refresh.assert_called_once()

        # Verify the metric object that was added
        added_metric = mock_session.add.call_args[0][0]
        assert str(added_metric.execution_id) == execution_id
        assert str(added_metric.step_execution_id) == step_execution_id
        assert added_metric.agent_name == "TestAgent"
        assert added_metric.status == "completed"
        assert added_metric.query == "What is the weather?"
        assert added_metric.response == "The weather is sunny."
        assert added_metric.tokens_in == 10
        assert added_metric.tokens_out == 20
        assert added_metric.total_tokens == 30
        assert added_metric.llm_calls == 1
        assert added_metric.model_provider == "openai"
        assert added_metric.model_name == "gpt-4"
        assert added_metric.duration_ms == 5000  # 5 seconds

    def test_record_agent_execution_without_step_id(self, analytics_service, mock_session, sample_agent_output):
        """Test recording agent execution without step_execution_id"""
        execution_id = str(uuid.uuid4())
        metric_id = uuid.uuid4()

        def mock_refresh(obj):
            obj.id = metric_id

        mock_session.refresh.side_effect = mock_refresh

        result_id = analytics_service.record_agent_execution(
            mock_session,
            execution_id=execution_id,
            step_execution_id=None,
            agent_output=sample_agent_output,
            status="completed",
        )

        assert result_id == metric_id
        added_metric = mock_session.add.call_args[0][0]
        assert added_metric.step_execution_id is None

    def test_record_agent_execution_with_error(self, analytics_service, mock_session, sample_agent_output):
        """Test recording agent execution with error"""
        execution_id = str(uuid.uuid4())
        metric_id = uuid.uuid4()

        def mock_refresh(obj):
            obj.id = metric_id

        mock_session.refresh.side_effect = mock_refresh

        result_id = analytics_service.record_agent_execution(
            mock_session,
            execution_id=execution_id,
            step_execution_id=None,
            agent_output=sample_agent_output,
            status="failed",
            error_message="Connection timeout",
        )

        assert result_id == metric_id
        added_metric = mock_session.add.call_args[0][0]
        assert added_metric.status == "failed"
        assert added_metric.error_message == "Connection timeout"

    def test_record_agent_execution_redact_response(self, analytics_service, mock_session, sample_agent_output):
        """Test recording agent execution with redacted response"""
        execution_id = str(uuid.uuid4())
        metric_id = uuid.uuid4()

        def mock_refresh(obj):
            obj.id = metric_id

        mock_session.refresh.side_effect = mock_refresh

        result_id = analytics_service.record_agent_execution(
            mock_session,
            execution_id=execution_id,
            step_execution_id=None,
            agent_output=sample_agent_output,
            status="completed",
            redact_response_in_analytics=True,
        )

        assert result_id == metric_id
        added_metric = mock_session.add.call_args[0][0]
        assert added_metric.response is None  # Response should be redacted
        assert added_metric.query == "What is the weather?"  # Query should still be present

    def test_record_agent_execution_missing_usage(self, analytics_service, mock_session):
        """Test recording agent execution with missing usage data"""
        execution_id = str(uuid.uuid4())
        metric_id = uuid.uuid4()

        def mock_refresh(obj):
            obj.id = metric_id

        mock_session.refresh.side_effect = mock_refresh

        agent_output = {
            "agent_name": "TestAgent",
            "query": "Test query",
            "response": "Test response",
        }

        result_id = analytics_service.record_agent_execution(
            mock_session,
            execution_id=execution_id,
            step_execution_id=None,
            agent_output=agent_output,
            status="completed",
        )

        assert result_id == metric_id
        added_metric = mock_session.add.call_args[0][0]
        assert added_metric.tokens_in is None
        assert added_metric.tokens_out is None
        assert added_metric.total_tokens is None
        assert added_metric.llm_calls is None

    def test_record_agent_execution_missing_model(self, analytics_service, mock_session):
        """Test recording agent execution with missing model data"""
        execution_id = str(uuid.uuid4())
        metric_id = uuid.uuid4()

        def mock_refresh(obj):
            obj.id = metric_id

        mock_session.refresh.side_effect = mock_refresh

        agent_output = {
            "agent_name": "TestAgent",
            "query": "Test query",
            "response": "Test response",
        }

        result_id = analytics_service.record_agent_execution(
            mock_session,
            execution_id=execution_id,
            step_execution_id=None,
            agent_output=agent_output,
            status="completed",
        )

        assert result_id == metric_id
        added_metric = mock_session.add.call_args[0][0]
        assert added_metric.model_provider is None
        assert added_metric.model_name is None

    def test_record_agent_execution_fallback_agent_name(self, analytics_service, mock_session):
        """Test recording agent execution with fallback agent name"""
        execution_id = str(uuid.uuid4())
        metric_id = uuid.uuid4()

        def mock_refresh(obj):
            obj.id = metric_id

        mock_session.refresh.side_effect = mock_refresh

        # Test with agentId instead of agent_name
        agent_output = {
            "agentId": "agent-123",
            "query": "Test query",
        }

        result_id = analytics_service.record_agent_execution(
            mock_session,
            execution_id=execution_id,
            step_execution_id=None,
            agent_output=agent_output,
            status="completed",
        )

        assert result_id == metric_id
        added_metric = mock_session.add.call_args[0][0]
        assert added_metric.agent_name == "agent-123"

    def test_record_agent_execution_default_agent_name(self, analytics_service, mock_session):
        """Test recording agent execution with default agent name"""
        execution_id = str(uuid.uuid4())
        metric_id = uuid.uuid4()

        def mock_refresh(obj):
            obj.id = metric_id

        mock_session.refresh.side_effect = mock_refresh

        # No agent_name or agentId
        agent_output = {"query": "Test query"}

        result_id = analytics_service.record_agent_execution(
            mock_session,
            execution_id=execution_id,
            step_execution_id=None,
            agent_output=agent_output,
            status="completed",
        )

        assert result_id == metric_id
        added_metric = mock_session.add.call_args[0][0]
        assert added_metric.agent_name == "Agent"  # Default fallback


class TestRecordWorkflowMetrics:
    """Tests for recording workflow metrics"""

    def test_record_workflow_metrics_success(self, analytics_service, mock_session):
        """Test recording workflow metrics with all fields"""
        execution_id = str(uuid.uuid4())
        workflow_id = str(uuid.uuid4())
        started_at = datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
        completed_at = datetime(2024, 1, 1, 0, 1, 0, tzinfo=timezone.utc)

        metric_id = uuid.uuid4()

        def mock_refresh(obj):
            obj.id = metric_id

        mock_session.refresh.side_effect = mock_refresh

        summary = {"total_steps": 5, "completed_steps": 5, "failed_steps": 0}
        totals = {"tokens_in": 100, "tokens_out": 200, "total_tokens": 300, "llm_calls": 5}

        result_id = analytics_service.record_workflow_metrics(
            mock_session,
            execution_id=execution_id,
            workflow_id=workflow_id,
            workflow_name="Test Workflow",
            summary=summary,
            totals=totals,
            status="completed",
            started_at=started_at,
            completed_at=completed_at,
        )

        assert result_id == metric_id
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()
        mock_session.refresh.assert_called_once()

        # Verify the metric object that was added
        added_metric = mock_session.add.call_args[0][0]
        assert str(added_metric.execution_id) == execution_id
        assert str(added_metric.workflow_id) == workflow_id
        assert added_metric.workflow_name == "Test Workflow"
        assert added_metric.status == "completed"
        assert added_metric.total_steps == 5
        assert added_metric.completed_steps == 5
        assert added_metric.failed_steps == 0
        assert added_metric.total_tokens_in == 100
        assert added_metric.total_tokens_out == 200
        assert added_metric.total_tokens == 300
        assert added_metric.total_llm_calls == 5
        assert added_metric.duration_ms == 60000  # 1 minute

    def test_record_workflow_metrics_without_timestamps(self, analytics_service, mock_session):
        """Test recording workflow metrics without timestamps"""
        execution_id = str(uuid.uuid4())
        workflow_id = str(uuid.uuid4())
        metric_id = uuid.uuid4()

        def mock_refresh(obj):
            obj.id = metric_id

        mock_session.refresh.side_effect = mock_refresh

        summary = {"total_steps": 3, "completed_steps": 2, "failed_steps": 1}
        totals = {"tokens_in": 50, "tokens_out": 100, "total_tokens": 150, "llm_calls": 3}

        result_id = analytics_service.record_workflow_metrics(
            mock_session,
            execution_id=execution_id,
            workflow_id=workflow_id,
            workflow_name="Test Workflow",
            summary=summary,
            totals=totals,
            status="failed",
            started_at=None,
            completed_at=None,
        )

        assert result_id == metric_id
        added_metric = mock_session.add.call_args[0][0]
        assert added_metric.start_time is None
        assert added_metric.end_time is None
        assert added_metric.duration_ms is None

    def test_record_workflow_metrics_partial_timestamps(self, analytics_service, mock_session):
        """Test recording workflow metrics with only started_at"""
        execution_id = str(uuid.uuid4())
        workflow_id = str(uuid.uuid4())
        metric_id = uuid.uuid4()
        started_at = datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc)

        def mock_refresh(obj):
            obj.id = metric_id

        mock_session.refresh.side_effect = mock_refresh

        summary = {"total_steps": 3, "completed_steps": 2, "failed_steps": 1}
        totals = {"tokens_in": 50, "tokens_out": 100, "total_tokens": 150, "llm_calls": 3}

        result_id = analytics_service.record_workflow_metrics(
            mock_session,
            execution_id=execution_id,
            workflow_id=workflow_id,
            workflow_name="Test Workflow",
            summary=summary,
            totals=totals,
            status="running",
            started_at=started_at,
            completed_at=None,
        )

        assert result_id == metric_id
        added_metric = mock_session.add.call_args[0][0]
        assert added_metric.start_time is not None
        assert added_metric.end_time is None
        assert added_metric.duration_ms is None

    def test_record_workflow_metrics_without_workflow_name(self, analytics_service, mock_session):
        """Test recording workflow metrics without workflow name"""
        execution_id = str(uuid.uuid4())
        workflow_id = str(uuid.uuid4())
        metric_id = uuid.uuid4()

        def mock_refresh(obj):
            obj.id = metric_id

        mock_session.refresh.side_effect = mock_refresh

        summary = {"total_steps": 1, "completed_steps": 1, "failed_steps": 0}
        totals = {"tokens_in": 10, "tokens_out": 20, "total_tokens": 30, "llm_calls": 1}

        result_id = analytics_service.record_workflow_metrics(
            mock_session,
            execution_id=execution_id,
            workflow_id=workflow_id,
            workflow_name=None,
            summary=summary,
            totals=totals,
            status="completed",
            started_at=None,
            completed_at=None,
        )

        assert result_id == metric_id
        added_metric = mock_session.add.call_args[0][0]
        assert added_metric.workflow_name is None

    def test_record_workflow_metrics_empty_summary(self, analytics_service, mock_session):
        """Test recording workflow metrics with empty summary"""
        execution_id = str(uuid.uuid4())
        workflow_id = str(uuid.uuid4())
        metric_id = uuid.uuid4()

        def mock_refresh(obj):
            obj.id = metric_id

        mock_session.refresh.side_effect = mock_refresh

        summary = {}
        totals = {}

        result_id = analytics_service.record_workflow_metrics(
            mock_session,
            execution_id=execution_id,
            workflow_id=workflow_id,
            workflow_name="Test Workflow",
            summary=summary,
            totals=totals,
            status="completed",
            started_at=None,
            completed_at=None,
        )

        assert result_id == metric_id
        added_metric = mock_session.add.call_args[0][0]
        assert added_metric.total_steps is None
        assert added_metric.completed_steps is None
        assert added_metric.failed_steps is None
        assert added_metric.total_tokens_in is None
        assert added_metric.total_tokens_out is None
        assert added_metric.total_tokens is None
        assert added_metric.total_llm_calls is None

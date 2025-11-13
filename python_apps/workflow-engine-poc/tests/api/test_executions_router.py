"""
Tests for Executions Router

Tests all execution status, results, and analytics endpoints.
"""

import pytest
import uuid
from datetime import datetime, timezone
from unittest.mock import patch, MagicMock, AsyncMock, ANY, Mock
from fastapi.testclient import TestClient

from workflow_engine_poc.main import app
from workflow_core_sdk.execution.context_impl import ExecutionContext, StepResult
from workflow_core_sdk.models import ExecutionStatus, StepStatus

client = TestClient(app)


# ========== Fixtures ==========


@pytest.fixture
def mock_workflow_engine():
    """Create a mock workflow engine for testing."""
    engine = AsyncMock()
    engine.get_execution_context = AsyncMock(return_value=None)
    engine.get_execution_analytics = AsyncMock(
        return_value={
            "total_executions": 0,
            "active_executions": 0,
            "completed_executions": 0,
            "failed_executions": 0,
            "executions": [],
        }
    )
    return engine


@pytest.fixture
def mock_execution_context():
    """Create a mock execution context for testing."""
    execution_id = str(uuid.uuid4())
    workflow_id = str(uuid.uuid4())

    # Create a mock execution context
    context = Mock(spec=ExecutionContext)
    context.execution_id = execution_id
    context.workflow_id = workflow_id
    context.status = ExecutionStatus.RUNNING
    context.steps_config = [{"step_id": "step1"}, {"step_id": "step2"}]
    context.completed_steps = ["step1"]
    context.failed_steps = []
    context.step_results = {}
    context.step_io_data = {}
    context.global_variables = {"test_var": "test_value"}

    # Mock the get_execution_summary method
    context.get_execution_summary.return_value = {
        "execution_id": execution_id,
        "workflow_id": workflow_id,
        "status": "running",
        "current_step": "step2",
        "completed_steps": ["step1"],
        "failed_steps": [],
        "pending_steps": ["step2"],
        "total_steps": 2,
        "started_at": datetime.now(timezone.utc).isoformat(),
        "completed_at": None,
    }

    return context


@pytest.fixture
def mock_app_state(mock_workflow_engine):
    """Mock the app.state to include workflow_engine."""
    with patch.object(app.state, "workflow_engine", mock_workflow_engine):
        yield mock_workflow_engine


# ========== Get Execution Status Tests ==========


@pytest.mark.api
class TestGetExecutionStatus:
    """Tests for GET /executions/{execution_id}"""

    @pytest.mark.api
    def test_get_execution_status_from_engine(self, test_client, auth_headers, mock_app_state, mock_execution_context):
        """Test getting execution status from in-memory engine context"""
        execution_id = mock_execution_context.execution_id

        # Configure mock to return execution context
        mock_app_state.get_execution_context.return_value = mock_execution_context

        response = test_client.get(f"/executions/{execution_id}", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["execution_id"] == execution_id
        assert data["workflow_id"] == mock_execution_context.workflow_id
        assert data["status"] == "running"
        assert data["total_steps"] == 2

    @pytest.mark.api
    def test_get_execution_status_from_db(self, test_client, auth_headers, mock_app_state, session):
        """Test getting execution status from database when not in memory"""
        from workflow_engine_poc.services.workflows_service import WorkflowsService

        execution_id = str(uuid.uuid4())
        workflow_id = str(uuid.uuid4())

        # Create execution in DB
        created_id = WorkflowsService.create_execution(
            session,
            {
                "workflow_id": workflow_id,
                "user_id": "test-user",
                "session_id": "test-session",
            },
        )

        # Engine returns None (not in memory)
        mock_app_state.get_execution_context.return_value = None

        response = test_client.get(f"/executions/{created_id}", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["execution_id"] == created_id
        assert data["workflow_id"] == workflow_id

    @pytest.mark.api
    def test_get_execution_status_not_found(self, test_client, auth_headers, mock_app_state):
        """Test getting status for non-existent execution"""
        execution_id = str(uuid.uuid4())

        # Engine returns None
        mock_app_state.get_execution_context.return_value = None

        response = test_client.get(f"/executions/{execution_id}", headers=auth_headers)

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


# ========== Get Execution Results Tests ==========


@pytest.mark.api
class TestGetExecutionResults:
    """Tests for GET /executions/{execution_id}/results"""

    @pytest.mark.api
    def test_get_execution_results_from_engine(self, test_client, auth_headers, mock_app_state, mock_execution_context):
        """Test getting execution results from in-memory engine context"""
        execution_id = mock_execution_context.execution_id

        # Add step results to context
        step_result = Mock(spec=StepResult)
        step_result.step_id = "step1"
        step_result.status = StepStatus.COMPLETED
        step_result.output_data = {"result": "success"}
        step_result.error_message = None
        step_result.execution_time_ms = 100

        mock_execution_context.step_results = {"step1": step_result}

        # Configure mock to return execution context
        mock_app_state.get_execution_context.return_value = mock_execution_context

        response = test_client.get(f"/executions/{execution_id}/results", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["execution_id"] == execution_id
        assert data["status"] == "running"
        assert "step_results" in data
        assert "step1" in data["step_results"]
        assert data["step_results"]["step1"]["output_data"] == {"result": "success"}

    @pytest.mark.api
    def test_get_execution_results_from_db(self, test_client, auth_headers, mock_app_state, session):
        """Test getting execution results from database when not in memory"""
        from workflow_engine_poc.services.workflows_service import WorkflowsService

        execution_id = str(uuid.uuid4())
        workflow_id = str(uuid.uuid4())

        # Create execution in DB
        created_id = WorkflowsService.create_execution(
            session,
            {
                "workflow_id": workflow_id,
                "user_id": "test-user",
                "session_id": "test-session",
            },
        )

        # Engine returns None (not in memory)
        mock_app_state.get_execution_context.return_value = None

        response = test_client.get(f"/executions/{created_id}/results", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["execution_id"] == created_id
        assert "step_results" in data
        assert "execution_summary" in data

    @pytest.mark.api
    def test_get_execution_results_not_found(self, test_client, auth_headers, mock_app_state):
        """Test getting results for non-existent execution"""
        execution_id = str(uuid.uuid4())

        # Engine returns None
        mock_app_state.get_execution_context.return_value = None

        response = test_client.get(f"/executions/{execution_id}/results", headers=auth_headers)

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


# ========== Get Execution Analytics Tests ==========


@pytest.mark.api
class TestGetExecutionAnalytics:
    """Tests for GET /executions/"""

    @pytest.mark.api
    def test_get_execution_analytics_success(self, test_client, auth_headers, mock_app_state, session):
        """Test getting execution analytics"""
        from workflow_engine_poc.services.workflows_service import WorkflowsService

        # Create some executions in DB
        for i in range(3):
            WorkflowsService.create_execution(
                session,
                {
                    "workflow_id": str(uuid.uuid4()),
                    "user_id": "test-user",
                    "session_id": "test-session",
                },
            )

        # Configure engine analytics
        mock_app_state.get_execution_analytics.return_value = {
            "total_executions": 5,
            "active_executions": 2,
            "completed_executions": 3,
            "failed_executions": 0,
            "executions": [],
        }

        response = test_client.get("/executions/", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert "total_executions" in data
        assert "db_executions" in data
        assert len(data["db_executions"]) == 3

    @pytest.mark.api
    def test_get_execution_analytics_with_filters(self, test_client, auth_headers, mock_app_state, session):
        """Test getting execution analytics with filters"""
        from workflow_engine_poc.services.workflows_service import WorkflowsService
        from workflow_core_sdk.db.service import DatabaseService

        workflow_id = str(uuid.uuid4())

        # Create executions with different statuses
        exec1_id = WorkflowsService.create_execution(
            session,
            {
                "workflow_id": workflow_id,
                "user_id": "test-user",
                "session_id": "test-session",
            },
        )
        exec2_id = WorkflowsService.create_execution(
            session,
            {
                "workflow_id": workflow_id,
                "user_id": "test-user",
                "session_id": "test-session",
            },
        )

        # Update one to completed status
        db = DatabaseService()
        db.update_execution(session, exec1_id, {"status": "completed"})

        response = test_client.get(f"/executions/?workflow_id={workflow_id}&status=completed", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert "db_executions" in data
        # Should only return completed executions
        assert len(data["db_executions"]) >= 1
        for exec in data["db_executions"]:
            assert exec["status"] == "completed"

    @pytest.mark.api
    def test_get_execution_analytics_exclude_db(self, test_client, auth_headers, mock_app_state):
        """Test getting execution analytics with exclude_db flag"""
        # Configure engine analytics
        mock_app_state.get_execution_analytics.return_value = {
            "total_executions": 5,
            "active_executions": 2,
            "completed_executions": 3,
            "failed_executions": 0,
            "executions": [],
        }

        response = test_client.get("/executions/?exclude_db=true", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert "total_executions" in data
        assert "db_executions" not in data  # Should be excluded


# ========== Stream Execution Updates Tests ==========


@pytest.mark.api
class TestStreamExecutionUpdates:
    """Tests for GET /executions/{execution_id}/stream"""

    @pytest.mark.api
    def test_stream_execution_updates_not_found(self, test_client, auth_headers, mock_app_state):
        """Test streaming for non-existent execution returns 404"""
        execution_id = str(uuid.uuid4())

        # Engine returns None (not in memory or DB)
        mock_app_state.get_execution_context.return_value = None

        response = test_client.get(f"/executions/{execution_id}/stream", headers=auth_headers)

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

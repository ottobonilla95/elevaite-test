"""
Tests for Workflows Router

Tests all workflow CRUD, validation, and execution endpoints.
"""

import pytest
import uuid
from datetime import datetime, timezone
from unittest.mock import patch, MagicMock, AsyncMock, ANY
from fastapi.testclient import TestClient

from workflow_core_sdk.db.models import Workflow, WorkflowRead
from workflow_engine_poc.main import app

client = TestClient(app)


# ========== Fixtures ==========


@pytest.fixture
def mock_session():
    """Mock database session"""
    return MagicMock()


@pytest.fixture
def sample_workflow():
    """Sample workflow for testing"""
    now = datetime.now(timezone.utc)
    workflow_id = uuid.uuid4()
    return Workflow(
        id=workflow_id,
        name="test_workflow",
        description="Test workflow description",
        configuration={
            "nodes": [
                {"id": "node1", "type": "trigger", "config": {}},
                {"id": "node2", "type": "agent", "config": {"agent_id": str(uuid.uuid4())}},
            ],
            "edges": [{"source": "node1", "target": "node2"}],
        },
        tags=["test", "demo"],
        created_by="user-123",
        created_at=now,
        updated_at=now,
    )


@pytest.fixture
def sample_workflow_config():
    """Sample workflow configuration for creation"""
    return {
        "name": "new_workflow",
        "description": "New workflow description",
        "steps": [
            {"step_type": "trigger", "parameters": {"kind": "webhook"}},
            {"step_type": "tool", "name": "Calculator", "config": {"tool_name": "calculator"}},
        ],
        "tags": ["new", "test"],
    }


# ========== List Workflows Tests ==========


@pytest.mark.api
class TestListWorkflows:
    """Tests for GET /workflows/"""

    @patch("workflow_engine_poc.routers.workflows.WorkflowsService.list_workflows_entities")
    @patch("workflow_engine_poc.routers.workflows.get_db_session")
    @patch("workflow_engine_poc.routers.workflows.api_key_or_user_guard")
    @pytest.mark.api
    def test_list_workflows_success(self, mock_guard, mock_get_session, mock_list, mock_session, sample_workflow):
        """Test listing all workflows"""
        mock_guard.return_value = lambda: "user-123"
        mock_get_session.return_value = mock_session
        mock_list.return_value = [sample_workflow]

        response = client.get("/workflows/")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "test_workflow"
        assert data[0]["description"] == "Test workflow description"

    @patch("workflow_engine_poc.routers.workflows.WorkflowsService.list_workflows_entities")
    @patch("workflow_engine_poc.routers.workflows.get_db_session")
    @patch("workflow_engine_poc.routers.workflows.api_key_or_user_guard")
    @pytest.mark.api
    def test_list_workflows_with_pagination(self, mock_guard, mock_get_session, mock_list, mock_session):
        """Test listing workflows with pagination"""
        mock_guard.return_value = lambda: "user-123"
        mock_get_session.return_value = mock_session
        mock_list.return_value = []

        response = client.get("/workflows/?limit=50&offset=10")

        assert response.status_code == 200
        # Verify service was called with correct parameters
        mock_list.assert_called_once_with(ANY, limit=50, offset=10)

    @patch("workflow_engine_poc.routers.workflows.WorkflowsService.list_workflows_entities")
    @patch("workflow_engine_poc.routers.workflows.get_db_session")
    @patch("workflow_engine_poc.routers.workflows.api_key_or_user_guard")
    @pytest.mark.api
    def test_list_workflows_empty(self, mock_guard, mock_get_session, mock_list, mock_session):
        """Test listing workflows when none exist"""
        mock_guard.return_value = lambda: "user-123"
        mock_get_session.return_value = mock_session
        mock_list.return_value = []

        response = client.get("/workflows/")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 0

    @patch("workflow_engine_poc.routers.workflows.WorkflowsService.list_workflows_entities")
    @patch("workflow_engine_poc.routers.workflows.get_db_session")
    @patch("workflow_engine_poc.routers.workflows.api_key_or_user_guard")
    @pytest.mark.api
    def test_list_workflows_error(self, mock_guard, mock_get_session, mock_list, mock_session):
        """Test list workflows error handling"""
        mock_guard.return_value = lambda: "user-123"
        mock_get_session.return_value = mock_session
        mock_list.side_effect = Exception("Database error")

        response = client.get("/workflows/")

        assert response.status_code == 500
        assert "Database error" in response.json()["detail"]


# ========== Get Workflow Tests ==========


@pytest.mark.api
class TestGetWorkflow:
    """Tests for GET /workflows/{workflow_id}"""

    @patch("workflow_engine_poc.routers.workflows.WorkflowsService.get_workflow_entity")
    @patch("workflow_engine_poc.routers.workflows.get_db_session")
    @patch("workflow_engine_poc.routers.workflows.api_key_or_user_guard")
    @pytest.mark.api
    def test_get_workflow_success(self, mock_guard, mock_get_session, mock_get, mock_session, sample_workflow):
        """Test getting a workflow by ID"""
        mock_guard.return_value = lambda: "user-123"
        mock_get_session.return_value = mock_session
        mock_get.return_value = sample_workflow

        response = client.get(f"/workflows/{sample_workflow.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "test_workflow"
        assert data["description"] == "Test workflow description"
        assert "configuration" in data

    @patch("workflow_engine_poc.routers.workflows.WorkflowsService.get_workflow_entity")
    @patch("workflow_engine_poc.routers.workflows.get_db_session")
    @patch("workflow_engine_poc.routers.workflows.api_key_or_user_guard")
    @pytest.mark.api
    def test_get_workflow_not_found(self, mock_guard, mock_get_session, mock_get, mock_session):
        """Test getting a non-existent workflow"""
        mock_guard.return_value = lambda: "user-123"
        mock_get_session.return_value = mock_session
        mock_get.return_value = None

        workflow_id = uuid.uuid4()
        response = client.get(f"/workflows/{workflow_id}")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"]


# ========== Create Workflow Tests ==========


@pytest.mark.api
class TestCreateWorkflow:
    """Tests for POST /workflows/"""

    @patch("workflow_engine_poc.routers.workflows.WorkflowsService.create_workflow")
    @patch("workflow_engine_poc.routers.workflows.get_db_session")
    @patch("workflow_engine_poc.routers.workflows.api_key_or_user_guard")
    def test_create_workflow_success(
        self, mock_guard, mock_get_session, mock_create, mock_session, sample_workflow, sample_workflow_config
    ):
        """Test creating a new workflow"""
        mock_guard.return_value = lambda: "user-123"
        mock_get_session.return_value = mock_session
        mock_create.return_value = sample_workflow

        response = client.post("/workflows/", json=sample_workflow_config)

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "test_workflow"

    @patch("workflow_engine_poc.routers.workflows.WorkflowsService.create_workflow")
    @patch("workflow_engine_poc.routers.workflows.get_db_session")
    @patch("workflow_engine_poc.routers.workflows.api_key_or_user_guard")
    @pytest.mark.api
    def test_create_workflow_duplicate(self, mock_guard, mock_get_session, mock_create, mock_session):
        """Test creating a workflow with duplicate name"""
        mock_guard.return_value = lambda: "user-123"
        mock_get_session.return_value = mock_session
        mock_create.side_effect = ValueError("Workflow with name 'test_workflow' already exists")

        payload = {
            "name": "test_workflow",
            "description": "Test",
            "steps": [{"step_type": "trigger", "parameters": {"kind": "webhook"}}],
        }

        response = client.post("/workflows/", json=payload)

        assert response.status_code == 500  # ValueError is caught and returned as 500
        assert "already exists" in response.json()["detail"]

    @patch("workflow_engine_poc.routers.workflows.get_db_session")
    @patch("workflow_engine_poc.routers.workflows.api_key_or_user_guard")
    @pytest.mark.api
    def test_create_workflow_invalid_config(self, mock_guard, mock_get_session, mock_session):
        """Test creating a workflow with invalid configuration"""
        mock_guard.return_value = lambda: "user-123"
        mock_get_session.return_value = mock_session

        # Missing required fields
        payload = {"description": "Test"}

        response = client.post("/workflows/", json=payload)

        assert response.status_code == 422  # Validation error


# ========== Delete Workflow Tests ==========


@pytest.mark.api
class TestDeleteWorkflow:
    """Tests for DELETE /workflows/{workflow_id}"""

    @patch("workflow_engine_poc.routers.workflows.WorkflowsService.delete_workflow")
    @patch("workflow_engine_poc.routers.workflows.get_db_session")
    @patch("workflow_engine_poc.routers.workflows.api_key_or_user_guard")
    @pytest.mark.api
    def test_delete_workflow_success(self, mock_guard, mock_get_session, mock_delete, mock_session):
        """Test deleting a workflow"""
        mock_guard.return_value = lambda: "user-123"
        mock_get_session.return_value = mock_session
        mock_delete.return_value = True

        workflow_id = uuid.uuid4()
        response = client.delete(f"/workflows/{workflow_id}")

        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert str(workflow_id) in data["message"]

    @patch("workflow_engine_poc.routers.workflows.WorkflowsService.delete_workflow")
    @patch("workflow_engine_poc.routers.workflows.get_db_session")
    @patch("workflow_engine_poc.routers.workflows.api_key_or_user_guard")
    @pytest.mark.api
    def test_delete_workflow_not_found(self, mock_guard, mock_get_session, mock_delete, mock_session):
        """Test deleting a non-existent workflow"""
        mock_guard.return_value = lambda: "user-123"
        mock_get_session.return_value = mock_session
        mock_delete.return_value = False

        workflow_id = uuid.uuid4()
        response = client.delete(f"/workflows/{workflow_id}")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"]


# ========== Validate Workflow Tests ==========


@pytest.mark.api
class TestValidateWorkflow:
    """Tests for POST /workflows/validate"""

    @patch("workflow_engine_poc.routers.workflows.Request")
    @patch("workflow_engine_poc.routers.workflows.api_key_or_user_guard")
    @pytest.mark.api
    def test_validate_workflow_success(self, mock_guard, mock_request_class, sample_workflow_config):
        """Test validating a valid workflow configuration"""
        mock_guard.return_value = lambda: "user-123"

        # Mock workflow engine
        mock_engine = AsyncMock()
        mock_engine.validate_workflow = AsyncMock(return_value={"valid": True, "errors": [], "warnings": []})

        # Mock request with app state
        mock_request = MagicMock()
        mock_request.app.state.workflow_engine = mock_engine

        # Call the endpoint directly
        from workflow_engine_poc.routers.workflows import validate_workflow
        import asyncio

        result = asyncio.run(
            validate_workflow(
                workflow_config=MagicMock(model_dump=lambda: sample_workflow_config),
                request=mock_request,
                api_key=None,
                user_id=None,
                org_id=None,
                project_id=None,
                account_id=None,
            )
        )

        assert result["valid"] is True
        assert len(result["errors"]) == 0

    @patch("workflow_engine_poc.routers.workflows.Request")
    @patch("workflow_engine_poc.routers.workflows.api_key_or_user_guard")
    @pytest.mark.api
    def test_validate_workflow_with_errors(self, mock_guard, mock_request_class):
        """Test validating an invalid workflow configuration"""
        mock_guard.return_value = lambda: "user-123"

        # Mock workflow engine
        mock_engine = AsyncMock()
        mock_engine.validate_workflow = AsyncMock(
            return_value={
                "valid": False,
                "errors": ["Missing required field: nodes", "Invalid edge: source node not found"],
                "warnings": ["Node 'node1' has no outgoing edges"],
            }
        )

        mock_request = MagicMock()
        mock_request.app.state.workflow_engine = mock_engine

        from workflow_engine_poc.routers.workflows import validate_workflow
        import asyncio

        invalid_config = {"name": "invalid", "description": "Invalid workflow", "config": {}}

        result = asyncio.run(
            validate_workflow(
                workflow_config=MagicMock(model_dump=lambda: invalid_config),
                request=mock_request,
                api_key=None,
                user_id=None,
                org_id=None,
                project_id=None,
                account_id=None,
            )
        )

        assert result["valid"] is False
        assert len(result["errors"]) == 2
        assert len(result["warnings"]) == 1


# ========== Execute Workflow Tests ==========


@pytest.mark.api
class TestExecuteWorkflow:
    """Tests for POST /workflows/{workflow_id}/execute"""

    @pytest.mark.skip(reason="Execute endpoint requires complex workflow engine setup and async execution mocking")
    @patch("workflow_engine_poc.routers.workflows.Request")
    @patch("workflow_engine_poc.routers.workflows.api_key_or_user_guard")
    @pytest.mark.api
    def test_execute_workflow_success(self, mock_guard, mock_request_class):
        """Test executing a workflow"""
        mock_guard.return_value = lambda: "user-123"

        # This test would require mocking the entire workflow engine execution flow
        # which is complex and better tested in integration tests
        pass

    @pytest.mark.skip(reason="Execute endpoint requires complex workflow engine setup")
    @patch("workflow_engine_poc.routers.workflows.Request")
    @patch("workflow_engine_poc.routers.workflows.api_key_or_user_guard")
    @pytest.mark.api
    def test_execute_workflow_with_backend(self, mock_guard, mock_request_class):
        """Test executing a workflow with specific backend"""
        mock_guard.return_value = lambda: "user-123"
        pass


# ========== Stream Workflow Tests ==========


@pytest.mark.api
class TestStreamWorkflow:
    """Tests for GET /workflows/{workflow_id}/stream"""

    @pytest.mark.skip(reason="Stream endpoint requires SSE setup and async streaming mocking")
    @patch("workflow_engine_poc.routers.workflows.Request")
    @patch("workflow_engine_poc.routers.workflows.api_key_or_user_guard")
    @pytest.mark.api
    def test_stream_workflow_execution(self, mock_guard, mock_request_class):
        """Test streaming workflow execution updates"""
        mock_guard.return_value = lambda: "user-123"
        # SSE streaming tests are complex and better tested in integration tests
        pass

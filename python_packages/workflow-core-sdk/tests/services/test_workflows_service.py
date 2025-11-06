"""
Unit tests for WorkflowsService

Tests the business logic of workflow and execution operations with mocked DatabaseService.
"""

import uuid
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

from workflow_core_sdk.db.models import Workflow
from workflow_core_sdk.db.models.executions import ExecutionStatus
from workflow_core_sdk.services.workflows_service import WorkflowsService


@pytest.fixture
def mock_session():
    """Mock SQLModel session"""
    return MagicMock()


@pytest.fixture
def sample_workflow():
    """Sample workflow entity for testing"""
    now = datetime.now(timezone.utc)
    workflow_id = uuid.uuid4()
    return Workflow(
        id=workflow_id,
        name="test_workflow",
        description="Test workflow description",
        configuration={
            "nodes": [{"id": "node1", "type": "trigger"}],
            "edges": [],
        },
        tags=["test", "demo"],
        created_by="user-123",
        created_at=now,
        updated_at=now,
    )


@pytest.fixture
def sample_workflow_data():
    """Sample workflow data for creation"""
    return {
        "name": "new_workflow",
        "description": "New workflow description",
        "steps": [
            {"step_type": "trigger", "parameters": {"kind": "webhook"}},
            {"step_type": "tool", "name": "Calculator"},
        ],
        "tags": ["new", "test"],
    }


@pytest.fixture
def sample_execution():
    """Sample execution data"""
    return {
        "id": str(uuid.uuid4()),
        "workflow_id": str(uuid.uuid4()),
        "status": "completed",
        "user_id": "user-123",
        "session_id": "session-123",
        "started_at": datetime.now(timezone.utc).isoformat(),
        "completed_at": datetime.now(timezone.utc).isoformat(),
        "step_io_data": {},
    }


class TestWorkflowEntities:
    """Tests for workflow entity operations"""

    @patch("workflow_core_sdk.services.workflows_service.DatabaseService")
    def test_list_workflows_entities(self, mock_db_class, mock_session, sample_workflow):
        """Test listing workflow entities"""
        mock_db = MagicMock()
        mock_db.list_workflow_entities.return_value = [sample_workflow]
        mock_db_class.return_value = mock_db

        workflows = WorkflowsService.list_workflows_entities(mock_session, limit=100, offset=0)

        assert len(workflows) == 1
        assert workflows[0].id == sample_workflow.id
        assert workflows[0].name == "test_workflow"
        mock_db.list_workflow_entities.assert_called_once_with(mock_session, limit=100, offset=0)

    @patch("workflow_core_sdk.services.workflows_service.DatabaseService")
    def test_list_workflows_entities_with_pagination(self, mock_db_class, mock_session):
        """Test listing workflows with pagination"""
        mock_db = MagicMock()
        mock_db.list_workflow_entities.return_value = []
        mock_db_class.return_value = mock_db

        workflows = WorkflowsService.list_workflows_entities(mock_session, limit=10, offset=20)

        assert len(workflows) == 0
        mock_db.list_workflow_entities.assert_called_once_with(mock_session, limit=10, offset=20)

    @patch("workflow_core_sdk.services.workflows_service.DatabaseService")
    def test_get_workflow_entity_success(self, mock_db_class, mock_session, sample_workflow):
        """Test getting a workflow entity by ID"""
        mock_db = MagicMock()
        mock_db.get_workflow_entity.return_value = sample_workflow
        mock_db_class.return_value = mock_db

        workflow = WorkflowsService.get_workflow_entity(mock_session, str(sample_workflow.id))

        assert workflow is not None
        assert workflow.id == sample_workflow.id
        assert workflow.name == "test_workflow"
        mock_db.get_workflow_entity.assert_called_once_with(mock_session, str(sample_workflow.id))

    @patch("workflow_core_sdk.services.workflows_service.DatabaseService")
    def test_get_workflow_entity_not_found(self, mock_db_class, mock_session):
        """Test getting a non-existent workflow entity"""
        mock_db = MagicMock()
        mock_db.get_workflow_entity.return_value = None
        mock_db_class.return_value = mock_db

        workflow_id = str(uuid.uuid4())
        workflow = WorkflowsService.get_workflow_entity(mock_session, workflow_id)

        assert workflow is None

    @patch("workflow_core_sdk.services.workflows_service.uuid_module")
    @patch("workflow_core_sdk.services.workflows_service.DatabaseService")
    def test_create_workflow_success(self, mock_db_class, mock_uuid, mock_session, sample_workflow_data, sample_workflow):
        """Test creating a new workflow"""
        workflow_id = str(uuid.uuid4())
        mock_uuid.uuid4.return_value = uuid.UUID(workflow_id)

        mock_db = MagicMock()
        mock_db.save_workflow.return_value = None
        mock_db.get_workflow_entity.return_value = sample_workflow
        mock_db_class.return_value = mock_db

        workflow = WorkflowsService.create_workflow(mock_session, sample_workflow_data)

        assert workflow is not None
        assert workflow.id == sample_workflow.id
        mock_db.save_workflow.assert_called_once_with(mock_session, workflow_id, sample_workflow_data)
        mock_db.get_workflow_entity.assert_called_once_with(mock_session, workflow_id)

    @patch("workflow_core_sdk.services.workflows_service.uuid_module")
    @patch("workflow_core_sdk.services.workflows_service.DatabaseService")
    def test_create_workflow_retrieval_failure(self, mock_db_class, mock_uuid, mock_session, sample_workflow_data):
        """Test creating a workflow but failing to retrieve it"""
        workflow_id = str(uuid.uuid4())
        mock_uuid.uuid4.return_value = uuid.UUID(workflow_id)

        mock_db = MagicMock()
        mock_db.save_workflow.return_value = None
        mock_db.get_workflow_entity.return_value = None  # Retrieval fails
        mock_db_class.return_value = mock_db

        with pytest.raises(RuntimeError, match="Failed to retrieve saved workflow entity"):
            WorkflowsService.create_workflow(mock_session, sample_workflow_data)

    @patch("workflow_core_sdk.services.workflows_service.DatabaseService")
    def test_delete_workflow_success(self, mock_db_class, mock_session):
        """Test deleting a workflow successfully"""
        mock_db = MagicMock()
        mock_db.delete_workflow.return_value = True
        mock_db_class.return_value = mock_db

        workflow_id = str(uuid.uuid4())
        result = WorkflowsService.delete_workflow(mock_session, workflow_id)

        assert result is True
        mock_db.delete_workflow.assert_called_once_with(mock_session, workflow_id)

    @patch("workflow_core_sdk.services.workflows_service.DatabaseService")
    def test_delete_workflow_not_found(self, mock_db_class, mock_session):
        """Test deleting a non-existent workflow"""
        mock_db = MagicMock()
        mock_db.delete_workflow.return_value = False
        mock_db_class.return_value = mock_db

        workflow_id = str(uuid.uuid4())
        result = WorkflowsService.delete_workflow(mock_session, workflow_id)

        assert result is False


class TestWorkflowConfiguration:
    """Tests for workflow configuration operations"""

    @patch("workflow_core_sdk.services.workflows_service.DatabaseService")
    def test_get_workflow_config_success(self, mock_db_class, mock_session):
        """Test getting workflow configuration"""
        workflow_config = {
            "workflow_id": str(uuid.uuid4()),
            "name": "test_workflow",
            "steps": [],
        }

        mock_db = MagicMock()
        mock_db.get_workflow.return_value = workflow_config
        mock_db_class.return_value = mock_db

        config = WorkflowsService.get_workflow_config(mock_session, workflow_config["workflow_id"])

        assert config is not None
        assert config["name"] == "test_workflow"
        mock_db.get_workflow.assert_called_once_with(mock_session, workflow_config["workflow_id"])

    @patch("workflow_core_sdk.services.workflows_service.DatabaseService")
    def test_get_workflow_config_not_found(self, mock_db_class, mock_session):
        """Test getting configuration for non-existent workflow"""
        mock_db = MagicMock()
        mock_db.get_workflow.return_value = None
        mock_db_class.return_value = mock_db

        workflow_id = str(uuid.uuid4())
        config = WorkflowsService.get_workflow_config(mock_session, workflow_id)

        assert config is None


class TestExecutions:
    """Tests for execution operations"""

    @patch("workflow_core_sdk.services.workflows_service.DatabaseService")
    def test_create_execution(self, mock_db_class, mock_session):
        """Test creating a new execution"""
        execution_id = str(uuid.uuid4())
        execution_data = {
            "workflow_id": str(uuid.uuid4()),
            "user_id": "user-123",
            "status": "pending",
        }

        mock_db = MagicMock()
        mock_db.create_execution.return_value = execution_id
        mock_db_class.return_value = mock_db

        result_id = WorkflowsService.create_execution(mock_session, execution_data)

        assert result_id == execution_id
        mock_db.create_execution.assert_called_once_with(mock_session, execution_data)

    @patch("workflow_core_sdk.services.workflows_service.DatabaseService")
    def test_get_execution_success(self, mock_db_class, mock_session, sample_execution):
        """Test getting an execution by ID"""
        mock_db = MagicMock()
        mock_db.get_execution.return_value = sample_execution
        mock_db_class.return_value = mock_db

        execution = WorkflowsService.get_execution(mock_session, sample_execution["id"])

        assert execution is not None
        assert execution["id"] == sample_execution["id"]
        assert execution["status"] == "completed"
        mock_db.get_execution.assert_called_once_with(mock_session, sample_execution["id"])

    @patch("workflow_core_sdk.services.workflows_service.DatabaseService")
    def test_get_execution_not_found(self, mock_db_class, mock_session):
        """Test getting a non-existent execution"""
        mock_db = MagicMock()
        mock_db.get_execution.return_value = None
        mock_db_class.return_value = mock_db

        execution_id = str(uuid.uuid4())
        execution = WorkflowsService.get_execution(mock_session, execution_id)

        assert execution is None

    @patch("workflow_core_sdk.services.workflows_service.DatabaseService")
    def test_list_executions_no_filters(self, mock_db_class, mock_session, sample_execution):
        """Test listing executions without filters"""
        mock_db = MagicMock()
        mock_db.list_executions.return_value = [sample_execution]
        mock_db_class.return_value = mock_db

        executions = WorkflowsService.list_executions(mock_session, limit=100, offset=0)

        assert len(executions) == 1
        assert executions[0]["id"] == sample_execution["id"]
        mock_db.list_executions.assert_called_once_with(mock_session, workflow_id=None, status=None, limit=100, offset=0)

    @patch("workflow_core_sdk.services.workflows_service.DatabaseService")
    def test_list_executions_with_workflow_filter(self, mock_db_class, mock_session, sample_execution):
        """Test listing executions filtered by workflow ID"""
        mock_db = MagicMock()
        mock_db.list_executions.return_value = [sample_execution]
        mock_db_class.return_value = mock_db

        workflow_id = sample_execution["workflow_id"]
        executions = WorkflowsService.list_executions(mock_session, workflow_id=workflow_id)

        assert len(executions) == 1
        mock_db.list_executions.assert_called_once_with(mock_session, workflow_id=workflow_id, status=None, limit=100, offset=0)

    @patch("workflow_core_sdk.services.workflows_service.DatabaseService")
    def test_list_executions_with_status_filter(self, mock_db_class, mock_session, sample_execution):
        """Test listing executions filtered by status"""
        mock_db = MagicMock()
        mock_db.list_executions.return_value = [sample_execution]
        mock_db_class.return_value = mock_db

        executions = WorkflowsService.list_executions(mock_session, status="completed")

        assert len(executions) == 1
        assert executions[0]["status"] == "completed"
        mock_db.list_executions.assert_called_once_with(mock_session, workflow_id=None, status="completed", limit=100, offset=0)

    @patch("workflow_core_sdk.services.workflows_service.DatabaseService")
    def test_list_executions_with_pagination(self, mock_db_class, mock_session):
        """Test listing executions with pagination"""
        mock_db = MagicMock()
        mock_db.list_executions.return_value = []
        mock_db_class.return_value = mock_db

        executions = WorkflowsService.list_executions(mock_session, limit=10, offset=20)

        assert len(executions) == 0
        mock_db.list_executions.assert_called_once_with(mock_session, workflow_id=None, status=None, limit=10, offset=20)

    @patch("workflow_core_sdk.services.workflows_service.DatabaseService")
    def test_update_execution_status_success(self, mock_db_class, mock_session):
        """Test updating execution status"""
        mock_db = MagicMock()
        mock_db.update_execution.return_value = True
        mock_db_class.return_value = mock_db

        execution_id = str(uuid.uuid4())
        result = WorkflowsService.update_execution_status(mock_session, execution_id, "running")

        assert result is True
        # Verify the status was converted to enum
        call_args = mock_db.update_execution.call_args
        assert call_args[0][0] == mock_session
        assert call_args[0][1] == execution_id
        assert call_args[0][2]["status"] == ExecutionStatus.RUNNING

    @patch("workflow_core_sdk.services.workflows_service.DatabaseService")
    def test_update_execution_status_invalid_status(self, mock_db_class, mock_session):
        """Test updating execution with invalid status (should not raise)"""
        mock_db = MagicMock()
        mock_db.update_execution.return_value = False
        mock_db_class.return_value = mock_db

        execution_id = str(uuid.uuid4())
        # Should not raise, just pass through to DB layer
        result = WorkflowsService.update_execution_status(mock_session, execution_id, "invalid_status")

        assert result is False
        mock_db.update_execution.assert_called_once()


class TestAgentMessages:
    """Tests for agent message operations"""

    @patch("workflow_core_sdk.services.workflows_service.DatabaseService")
    def test_create_agent_message(self, mock_db_class, mock_session):
        """Test creating an agent message"""
        message_id = str(uuid.uuid4())
        mock_db = MagicMock()
        mock_db.create_agent_message.return_value = message_id
        mock_db_class.return_value = mock_db

        execution_id = str(uuid.uuid4())
        step_id = "agent_step_1"
        result_id = WorkflowsService.create_agent_message(
            mock_session,
            execution_id=execution_id,
            step_id=step_id,
            role="assistant",
            content="Hello, how can I help?",
            metadata={"model": "gpt-4o"},
            user_id="user-123",
            session_id="session-123",
        )

        assert result_id == message_id
        mock_db.create_agent_message.assert_called_once_with(
            mock_session,
            execution_id=execution_id,
            step_id=step_id,
            role="assistant",
            content="Hello, how can I help?",
            metadata={"model": "gpt-4o"},
            user_id="user-123",
            session_id="session-123",
        )

    @patch("workflow_core_sdk.services.workflows_service.DatabaseService")
    def test_create_agent_message_minimal(self, mock_db_class, mock_session):
        """Test creating an agent message with minimal parameters"""
        message_id = str(uuid.uuid4())
        mock_db = MagicMock()
        mock_db.create_agent_message.return_value = message_id
        mock_db_class.return_value = mock_db

        execution_id = str(uuid.uuid4())
        result_id = WorkflowsService.create_agent_message(
            mock_session,
            execution_id=execution_id,
            step_id="step1",
            role="user",
            content="Test message",
        )

        assert result_id == message_id

    @patch("workflow_core_sdk.services.workflows_service.DatabaseService")
    def test_list_agent_messages_no_filters(self, mock_db_class, mock_session):
        """Test listing agent messages without filters"""
        messages = [
            {"id": str(uuid.uuid4()), "role": "user", "content": "Hello"},
            {"id": str(uuid.uuid4()), "role": "assistant", "content": "Hi there"},
        ]

        mock_db = MagicMock()
        mock_db.list_agent_messages.return_value = messages
        mock_db_class.return_value = mock_db

        execution_id = str(uuid.uuid4())
        result = WorkflowsService.list_agent_messages(mock_session, execution_id=execution_id)

        assert len(result) == 2
        assert result[0]["role"] == "user"
        assert result[1]["role"] == "assistant"
        mock_db.list_agent_messages.assert_called_once_with(
            mock_session, execution_id=execution_id, step_id=None, limit=100, offset=0
        )

    @patch("workflow_core_sdk.services.workflows_service.DatabaseService")
    def test_list_agent_messages_with_step_filter(self, mock_db_class, mock_session):
        """Test listing agent messages filtered by step ID"""
        messages = [{"id": str(uuid.uuid4()), "role": "user", "content": "Hello"}]

        mock_db = MagicMock()
        mock_db.list_agent_messages.return_value = messages
        mock_db_class.return_value = mock_db

        execution_id = str(uuid.uuid4())
        step_id = "agent_step_1"
        result = WorkflowsService.list_agent_messages(mock_session, execution_id=execution_id, step_id=step_id)

        assert len(result) == 1
        mock_db.list_agent_messages.assert_called_once_with(
            mock_session, execution_id=execution_id, step_id=step_id, limit=100, offset=0
        )

    @patch("workflow_core_sdk.services.workflows_service.DatabaseService")
    def test_list_agent_messages_with_pagination(self, mock_db_class, mock_session):
        """Test listing agent messages with pagination"""
        mock_db = MagicMock()
        mock_db.list_agent_messages.return_value = []
        mock_db_class.return_value = mock_db

        execution_id = str(uuid.uuid4())
        result = WorkflowsService.list_agent_messages(mock_session, execution_id=execution_id, limit=10, offset=20)

        assert len(result) == 0
        mock_db.list_agent_messages.assert_called_once_with(
            mock_session, execution_id=execution_id, step_id=None, limit=10, offset=20
        )

    @patch("workflow_core_sdk.services.workflows_service.DatabaseService")
    def test_list_agent_messages_empty_result(self, mock_db_class, mock_session):
        """Test listing agent messages when no messages exist"""
        mock_db = MagicMock()
        mock_db.list_agent_messages.return_value = []
        mock_db_class.return_value = mock_db

        execution_id = str(uuid.uuid4())
        result = WorkflowsService.list_agent_messages(mock_session, execution_id=execution_id)

        assert len(result) == 0

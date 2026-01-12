"""
Tests for Messages Router

Tests all interactive message endpoints:
- GET /executions/{execution_id}/steps/{step_id}/messages - List messages for a step
- POST /executions/{execution_id}/steps/{step_id}/messages - Create/send message to step
"""

import pytest
import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient


@pytest.fixture
def sample_execution_id():
    """Sample execution ID for testing"""
    return str(uuid.uuid4())


@pytest.fixture
def sample_step_id():
    """Sample step ID for testing"""
    return "agent_step_1"


@pytest.fixture
def sample_messages():
    """Sample agent messages for testing"""
    execution_id = str(uuid.uuid4())
    step_id = "agent_step_1"

    return [
        {
            "id": str(uuid.uuid4()),
            "execution_id": execution_id,
            "step_id": step_id,
            "role": "user",
            "content": "Hello, can you help me?",
            "metadata": {"source": "web"},
            "user_id": "user-123",
            "session_id": "session-456",
            "created_at": datetime.now(timezone.utc).isoformat(),
        },
        {
            "id": str(uuid.uuid4()),
            "execution_id": execution_id,
            "step_id": step_id,
            "role": "assistant",
            "content": "Of course! How can I assist you?",
            "metadata": {"model": "gpt-4"},
            "user_id": None,
            "session_id": "session-456",
            "created_at": datetime.now(timezone.utc).isoformat(),
        },
        {
            "id": str(uuid.uuid4()),
            "execution_id": execution_id,
            "step_id": step_id,
            "role": "user",
            "content": "I need help with my workflow",
            "metadata": None,
            "user_id": "user-123",
            "session_id": "session-456",
            "created_at": datetime.now(timezone.utc).isoformat(),
        },
    ]


@pytest.fixture
def mock_execution_context():
    """Mock execution context"""
    ctx = MagicMock()
    ctx.execution_id = str(uuid.uuid4())
    ctx.workflow_id = str(uuid.uuid4())
    return ctx


@pytest.mark.api
class TestListStepMessages:
    """Tests for GET /executions/{execution_id}/steps/{step_id}/messages endpoint"""

    def test_list_messages_success(
        self, authenticated_client: TestClient, sample_execution_id, sample_step_id, sample_messages, mock_execution_context
    ):
        """Test successfully listing messages for a step"""
        with (
            patch.object(
                authenticated_client.app.state.workflow_engine, "get_execution_context", new_callable=AsyncMock
            ) as mock_get_ctx,
            patch("workflow_core_sdk.services.workflows_service.WorkflowsService.list_agent_messages") as mock_list,
        ):
            mock_get_ctx.return_value = mock_execution_context
            mock_list.return_value = sample_messages

            response = authenticated_client.get(f"/executions/{sample_execution_id}/steps/{sample_step_id}/messages")

            assert response.status_code == 200
            data = response.json()
            assert len(data) == 3
            assert data[0]["role"] == "user"
            assert data[1]["role"] == "assistant"
            assert data[2]["content"] == "I need help with my workflow"
            mock_list.assert_called_once()

    def test_list_messages_with_pagination(
        self, authenticated_client: TestClient, sample_execution_id, sample_step_id, sample_messages, mock_execution_context
    ):
        """Test listing messages with pagination parameters"""
        with (
            patch.object(
                authenticated_client.app.state.workflow_engine, "get_execution_context", new_callable=AsyncMock
            ) as mock_get_ctx,
            patch("workflow_core_sdk.services.workflows_service.WorkflowsService.list_agent_messages") as mock_list,
        ):
            mock_get_ctx.return_value = mock_execution_context
            mock_list.return_value = sample_messages[:2]

            response = authenticated_client.get(
                f"/executions/{sample_execution_id}/steps/{sample_step_id}/messages?limit=2&offset=0"
            )

            assert response.status_code == 200
            data = response.json()
            assert len(data) == 2
            mock_list.assert_called_once()
            call_kwargs = mock_list.call_args[1]
            assert call_kwargs["limit"] == 2
            assert call_kwargs["offset"] == 0

    @pytest.mark.api
    def test_list_messages_execution_not_found(self, authenticated_client: TestClient, sample_execution_id, sample_step_id):
        """Test listing messages when execution doesn't exist"""
        with (
            patch.object(
                authenticated_client.app.state.workflow_engine, "get_execution_context", new_callable=AsyncMock
            ) as mock_get_ctx,
            patch("workflow_core_sdk.services.executions_service.ExecutionsService.get_execution") as mock_get_exec,
        ):
            mock_get_ctx.return_value = None
            mock_get_exec.return_value = None

            response = authenticated_client.get(f"/executions/{sample_execution_id}/steps/{sample_step_id}/messages")

            assert response.status_code == 404
            assert "not found" in response.json()["detail"].lower()

    def test_list_messages_empty_result(
        self, authenticated_client: TestClient, sample_execution_id, sample_step_id, mock_execution_context
    ):
        """Test listing messages when no messages exist"""
        with (
            patch.object(
                authenticated_client.app.state.workflow_engine, "get_execution_context", new_callable=AsyncMock
            ) as mock_get_ctx,
            patch("workflow_core_sdk.services.workflows_service.WorkflowsService.list_agent_messages") as mock_list,
        ):
            mock_get_ctx.return_value = mock_execution_context
            mock_list.return_value = []

            response = authenticated_client.get(f"/executions/{sample_execution_id}/steps/{sample_step_id}/messages")

            assert response.status_code == 200
            assert response.json() == []

    def test_list_messages_from_db_when_no_context(
        self, authenticated_client: TestClient, sample_execution_id, sample_step_id, sample_messages
    ):
        """Test listing messages from DB when execution context not in memory"""
        mock_execution_details = {
            "id": sample_execution_id,
            "workflow_id": str(uuid.uuid4()),
            "status": "completed",
        }

        with (
            patch.object(
                authenticated_client.app.state.workflow_engine, "get_execution_context", new_callable=AsyncMock
            ) as mock_get_ctx,
            patch("workflow_core_sdk.services.executions_service.ExecutionsService.get_execution") as mock_get_exec,
            patch("workflow_core_sdk.services.workflows_service.WorkflowsService.list_agent_messages") as mock_list,
        ):
            mock_get_ctx.return_value = None
            mock_get_exec.return_value = mock_execution_details
            mock_list.return_value = sample_messages

            response = authenticated_client.get(f"/executions/{sample_execution_id}/steps/{sample_step_id}/messages")

            assert response.status_code == 200
            data = response.json()
            assert len(data) == 3


@pytest.mark.api
class TestCreateStepMessage:
    """Tests for POST /executions/{execution_id}/steps/{step_id}/messages endpoint"""

    def test_create_message_success_local_backend(
        self, authenticated_client: TestClient, sample_execution_id, sample_step_id, mock_execution_context
    ):
        """Test successfully creating a message with local backend"""
        message_body = {
            "role": "user",
            "content": "This is a test message",
            "metadata": {"source": "test"},
            "user_id": "user-123",
            "session_id": "session-456",
        }

        created_message = {
            "id": str(uuid.uuid4()),
            "execution_id": sample_execution_id,
            "step_id": sample_step_id,
            **message_body,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

        mock_execution_details = {
            "id": sample_execution_id,
            "metadata": {"backend": "local"},
        }

        with (
            patch.object(
                authenticated_client.app.state.workflow_engine, "get_execution_context", new_callable=AsyncMock
            ) as mock_get_ctx,
            patch.object(
                authenticated_client.app.state.workflow_engine, "resume_execution", new_callable=AsyncMock
            ) as mock_resume,
            patch("workflow_core_sdk.services.workflows_service.WorkflowsService.create_agent_message") as mock_create,
            patch("workflow_core_sdk.services.workflows_service.WorkflowsService.list_agent_messages") as mock_list,
            patch(
                "workflow_core_sdk.services.workflows_service.WorkflowsService.update_execution_status"
            ) as mock_update_status,
            patch("workflow_core_sdk.services.executions_service.ExecutionsService.get_execution") as mock_get_exec,
            patch("workflow_core_sdk.streaming.stream_manager") as mock_stream,
        ):
            mock_get_ctx.return_value = mock_execution_context
            mock_create.return_value = created_message["id"]
            mock_list.return_value = [created_message]
            mock_get_exec.return_value = mock_execution_details
            mock_stream.emit_execution_event = AsyncMock()

            response = authenticated_client.post(
                f"/executions/{sample_execution_id}/steps/{sample_step_id}/messages",
                json=message_body,
            )

            assert response.status_code == 200
            data = response.json()
            assert data["role"] == "user"
            assert data["content"] == "This is a test message"
            assert data["execution_id"] == sample_execution_id
            assert data["step_id"] == sample_step_id

            # Verify workflow engine was resumed
            mock_resume.assert_called_once()
            resume_call = mock_resume.call_args
            assert resume_call[1]["execution_id"] == sample_execution_id
            assert resume_call[1]["step_id"] == sample_step_id

    @pytest.mark.api
    def test_create_message_execution_not_found(self, authenticated_client: TestClient, sample_execution_id, sample_step_id):
        """Test creating message when execution doesn't exist"""
        message_body = {
            "role": "user",
            "content": "Test message",
        }

        with (
            patch.object(
                authenticated_client.app.state.workflow_engine, "get_execution_context", new_callable=AsyncMock
            ) as mock_get_ctx,
            patch("workflow_core_sdk.services.executions_service.ExecutionsService.get_execution") as mock_get_exec,
        ):
            mock_get_ctx.return_value = None
            mock_get_exec.return_value = None

            response = authenticated_client.post(
                f"/executions/{sample_execution_id}/steps/{sample_step_id}/messages",
                json=message_body,
            )

            assert response.status_code == 404
            assert "not found" in response.json()["detail"].lower()

    def test_create_message_with_final_turn(
        self, authenticated_client: TestClient, sample_execution_id, sample_step_id, mock_execution_context
    ):
        """Test creating message with final_turn metadata"""
        message_body = {
            "role": "user",
            "content": "Final message",
            "metadata": {"final_turn": True},
        }

        created_message = {
            "id": str(uuid.uuid4()),
            "execution_id": sample_execution_id,
            "step_id": sample_step_id,
            **message_body,
            "user_id": None,
            "session_id": None,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

        mock_execution_details = {"id": sample_execution_id, "metadata": {"backend": "local"}}

        with (
            patch.object(
                authenticated_client.app.state.workflow_engine, "get_execution_context", new_callable=AsyncMock
            ) as mock_get_ctx,
            patch.object(
                authenticated_client.app.state.workflow_engine, "resume_execution", new_callable=AsyncMock
            ) as mock_resume,
            patch("workflow_core_sdk.services.workflows_service.WorkflowsService.create_agent_message") as mock_create,
            patch("workflow_core_sdk.services.workflows_service.WorkflowsService.list_agent_messages") as mock_list,
            patch("workflow_core_sdk.services.workflows_service.WorkflowsService.update_execution_status"),
            patch("workflow_core_sdk.services.executions_service.ExecutionsService.get_execution") as mock_get_exec,
            patch("workflow_core_sdk.streaming.stream_manager") as mock_stream,
        ):
            mock_get_ctx.return_value = mock_execution_context
            mock_create.return_value = created_message["id"]
            mock_list.return_value = [created_message]
            mock_get_exec.return_value = mock_execution_details
            mock_stream.emit_execution_event = AsyncMock()

            response = authenticated_client.post(
                f"/executions/{sample_execution_id}/steps/{sample_step_id}/messages",
                json=message_body,
            )

            assert response.status_code == 200

            # Verify final_turn was passed to resume_execution
            mock_resume.assert_called_once()
            decision_output = mock_resume.call_args[1]["decision_output"]
            assert decision_output["final_turn"] is True

"""
Integration tests for Workflows API endpoints.

Tests all CRUD operations and execution for workflows including:
- Create workflow
- List workflows with filters
- Get workflow by ID
- Update workflow
- Delete workflow
- Execute workflow (sync and async)
- Stream workflow execution
- Error cases and validation
"""

import pytest
import uuid
from fastapi.testclient import TestClient


class TestWorkflowsAPI:
    """Test suite for Workflows API endpoints."""

    def test_create_workflow_success(self, test_client: TestClient):
        """Test creating a workflow with all fields."""
        workflow_data = {
            "name": f"Test Workflow {uuid.uuid4().hex[:8]}",
            "description": "A test workflow for integration testing",
            "version": "1.0.0",
            "tags": ["test", "integration"],
            "configuration": {
                "steps": [
                    {
                        "step_id": "step1",
                        "step_type": "data_processing",
                        "name": "Process Data",
                        "config": {"processing_type": "passthrough"},
                        "dependencies": [],
                    }
                ]
            },
            "created_by": "test_user",
            "is_active": True,
        }

        response = test_client.post("/api/workflows/", json=workflow_data)

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == workflow_data["name"]
        assert data["description"] == workflow_data["description"]
        assert "workflow_id" in data  # UUID
        assert "configuration" in data

    def test_create_workflow_minimal_fields(self, test_client: TestClient):
        """Test creating a workflow with only required fields."""
        workflow_data = {
            "name": f"Minimal Workflow {uuid.uuid4().hex[:8]}",
            "configuration": {"steps": []},
        }

        response = test_client.post("/api/workflows/", json=workflow_data)

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == workflow_data["name"]
        assert "is_active" in data  # Check field exists

    def test_list_workflows_empty(self, test_client: TestClient):
        """Test listing workflows when none exist."""
        response = test_client.get("/api/workflows/")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_list_workflows_with_pagination(self, test_client: TestClient):
        """Test listing workflows with pagination."""
        # Create multiple workflows
        created_ids = []
        for i in range(3):
            workflow_data = {
                "name": f"Workflow {i} {uuid.uuid4().hex[:8]}",
                "configuration": {"steps": []},
            }
            response = test_client.post("/api/workflows/", json=workflow_data)
            assert response.status_code == 200
            created_ids.append(response.json()["workflow_id"])

        # Test pagination
        response = test_client.get("/api/workflows/?skip=0&limit=2")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 2  # At least our 2 workflows

        # Cleanup
        for workflow_id in created_ids:
            test_client.delete(f"/api/workflows/{workflow_id}")

    def test_get_workflow_by_id_success(self, test_client: TestClient):
        """Test getting a specific workflow by ID."""
        # Create a workflow
        workflow_data = {
            "name": f"Get Test Workflow {uuid.uuid4().hex[:8]}",
            "configuration": {"steps": []},
        }
        create_response = test_client.post("/api/workflows/", json=workflow_data)
        assert create_response.status_code == 200
        workflow_id = create_response.json()["workflow_id"]

        # Get the workflow
        response = test_client.get(f"/api/workflows/{workflow_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == workflow_data["name"]
        assert str(data["workflow_id"]) == str(workflow_id)

        # Cleanup
        test_client.delete(f"/api/workflows/{workflow_id}")

    def test_get_workflow_not_found(self, test_client: TestClient):
        """Test getting a non-existent workflow."""
        fake_id = str(uuid.uuid4())
        response = test_client.get(f"/api/workflows/{fake_id}")

        assert response.status_code == 404

    def test_update_workflow_success(self, test_client: TestClient):
        """Test updating a workflow."""
        # Create a workflow
        workflow_data = {
            "name": f"Original Workflow {uuid.uuid4().hex[:8]}",
            "configuration": {"steps": []},
        }
        create_response = test_client.post("/api/workflows/", json=workflow_data)
        assert create_response.status_code == 200
        workflow_id = create_response.json()["workflow_id"]

        # Update the workflow
        update_data = {
            "name": "Updated Workflow",
            "description": "Updated description",
            "is_active": False,
        }
        response = test_client.put(f"/api/workflows/{workflow_id}", json=update_data)

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == update_data["name"]
        assert data["description"] == update_data["description"]
        assert data["is_active"] == update_data["is_active"]

        # Cleanup
        test_client.delete(f"/api/workflows/{workflow_id}")

    def test_update_workflow_not_found(self, test_client: TestClient):
        """Test updating a non-existent workflow."""
        fake_id = str(uuid.uuid4())
        update_data = {"name": "Updated"}

        response = test_client.put(f"/api/workflows/{fake_id}", json=update_data)

        assert response.status_code == 404

    def test_delete_workflow_success(self, test_client: TestClient):
        """Test deleting a workflow."""
        # Create a workflow
        workflow_data = {
            "name": f"Delete Test Workflow {uuid.uuid4().hex[:8]}",
            "configuration": {"steps": []},
        }
        create_response = test_client.post("/api/workflows/", json=workflow_data)
        assert create_response.status_code == 200
        workflow_id = create_response.json()["workflow_id"]

        # Delete the workflow
        response = test_client.delete(f"/api/workflows/{workflow_id}")

        assert response.status_code == 200

        # Verify it's deleted
        get_response = test_client.get(f"/api/workflows/{workflow_id}")
        assert get_response.status_code == 404

    def test_delete_workflow_not_found(self, test_client: TestClient):
        """Test deleting a non-existent workflow."""
        fake_id = str(uuid.uuid4())
        response = test_client.delete(f"/api/workflows/{fake_id}")

        assert response.status_code == 404

    def test_workflow_with_multiple_steps(self, test_client: TestClient):
        """Test creating a workflow with multiple steps and dependencies."""
        workflow_data = {
            "name": f"Multi-Step Workflow {uuid.uuid4().hex[:8]}",
            "configuration": {
                "steps": [
                    {
                        "step_id": "step1",
                        "step_type": "data_processing",
                        "name": "First Step",
                        "config": {"processing_type": "passthrough"},
                        "dependencies": [],
                    },
                    {
                        "step_id": "step2",
                        "step_type": "data_processing",
                        "name": "Second Step",
                        "config": {"processing_type": "passthrough"},
                        "dependencies": ["step1"],
                    },
                ]
            },
        }

        response = test_client.post("/api/workflows/", json=workflow_data)

        assert response.status_code == 200
        data = response.json()
        assert len(data["configuration"]["steps"]) == 2
        assert data["configuration"]["steps"][1]["dependencies"] == ["step1"]

        # Cleanup
        test_client.delete(f"/api/workflows/{data['workflow_id']}")

    def test_workflow_with_tags(self, test_client: TestClient):
        """Test creating workflows with different tags."""
        tags_list = [["production"], ["test", "staging"], ["development", "experimental"]]

        created_ids = []
        for tags in tags_list:
            workflow_data = {
                "name": f"Tagged Workflow {uuid.uuid4().hex[:8]}",
                "tags": tags,
                "configuration": {"steps": []},
            }
            response = test_client.post("/api/workflows/", json=workflow_data)
            assert response.status_code == 200
            data = response.json()
            assert set(data["tags"]) == set(tags)
            created_ids.append(data["workflow_id"])

        # Cleanup
        for workflow_id in created_ids:
            test_client.delete(f"/api/workflows/{workflow_id}")

    def test_workflow_lifecycle(self, test_client: TestClient):
        """Test complete workflow lifecycle: create -> read -> update -> delete."""
        # Create
        workflow_data = {
            "name": f"Lifecycle Workflow {uuid.uuid4().hex[:8]}",
            "configuration": {"steps": []},
        }
        create_response = test_client.post("/api/workflows/", json=workflow_data)
        assert create_response.status_code == 200
        workflow_id = create_response.json()["workflow_id"]

        # Read
        get_response = test_client.get(f"/api/workflows/{workflow_id}")
        assert get_response.status_code == 200
        assert get_response.json()["name"] == workflow_data["name"]

        # Update
        update_data = {"name": "Updated Lifecycle Workflow"}
        update_response = test_client.put(f"/api/workflows/{workflow_id}", json=update_data)
        assert update_response.status_code == 200
        assert update_response.json()["name"] == update_data["name"]

        # Delete
        delete_response = test_client.delete(f"/api/workflows/{workflow_id}")
        assert delete_response.status_code == 200

        # Verify deleted
        final_get = test_client.get(f"/api/workflows/{workflow_id}")
        assert final_get.status_code == 404


class TestWorkflowExecutionAPI:
    """Test suite for Workflow Execution API endpoints."""

    @pytest.fixture
    def mock_workflow_engine(self, test_client: TestClient):
        """Mock the workflow engine in app state for execution tests."""
        from unittest.mock import AsyncMock, MagicMock

        # Create a mock workflow engine
        mock_engine = MagicMock()
        mock_engine.execute_workflow = AsyncMock(return_value=None)

        # Set the engine on the app state
        test_client.app.state.workflow_engine = mock_engine

        yield mock_engine

        # Cleanup - remove the mock engine
        if hasattr(test_client.app.state, "workflow_engine"):
            delattr(test_client.app.state, "workflow_engine")

    @pytest.fixture
    def workflow_with_trigger_and_agent(self, test_client: TestClient):
        """Create a workflow with trigger and agent step for execution testing."""
        workflow_data = {
            "name": f"Execution Test Workflow {uuid.uuid4().hex[:8]}",
            "description": "Workflow for testing execution endpoints",
            "version": "1.0.0",
            "configuration": {
                "steps": [
                    {
                        "step_id": "trigger",
                        "step_type": "trigger",
                        "name": "Chat Trigger",
                        "config": {
                            "kind": "chat",
                            "need_history": False,
                            "allowed_modalities": ["text"],
                        },
                        "dependencies": [],
                    },
                    {
                        "step_id": "agent_1",
                        "step_type": "agent_execution",
                        "name": "Test Agent",
                        "dependencies": ["trigger"],
                        "config": {
                            "agent_name": "Test Agent",
                            "system_prompt": "You are a test agent. Respond briefly.",
                            "query": "{current_message}",
                            "interactive": True,
                            "multi_turn": False,
                        },
                    },
                ],
            },
            "created_by": "test_user",
            "is_active": True,
        }

        response = test_client.post("/api/workflows/", json=workflow_data)
        assert response.status_code == 200
        workflow = response.json()

        yield workflow

        # Cleanup
        test_client.delete(f"/api/workflows/{workflow['workflow_id']}")

    def test_execute_async_with_query(self, test_client: TestClient, mock_workflow_engine, workflow_with_trigger_and_agent):
        """Test that /execute/async endpoint properly handles query parameter.

        This test verifies the fix for the issue where workflows with interactive
        agents would get stuck in 'waiting' status when a query was provided.
        The trigger data (current_message, messages, chat_history) must be
        populated for the agent step to proceed without waiting for user input.
        """
        workflow_id = workflow_with_trigger_and_agent["workflow_id"]

        execution_request = {
            "query": "Hello, this is a test message",
            "chat_history": [],
            "runtime_overrides": {},
            "session_id": f"test_session_{uuid.uuid4().hex[:8]}",
            "user_id": "test_user",
        }

        response = test_client.post(f"/api/workflows/{workflow_id}/execute/async", json=execution_request)

        # 202 Accepted is the correct status for async execution
        assert response.status_code == 202
        data = response.json()
        assert "execution_id" in data
        assert data["status"] in ["queued", "running", "completed", "error"]
        # The key assertion: status should NOT be "waiting" when a query is provided
        # If the fix is not in place, an interactive agent would return "waiting"
        # because it wouldn't receive the user message
        assert data["status"] != "waiting", (
            "Execution should not be 'waiting' when query is provided. "
            "This indicates the trigger data is not being populated correctly."
        )

        # Verify that the engine was called with proper execution context
        mock_workflow_engine.execute_workflow.assert_called_once()

    def test_execute_async_with_chat_history(
        self, test_client: TestClient, mock_workflow_engine, workflow_with_trigger_and_agent
    ):
        """Test that /execute/async properly handles chat_history in various formats."""
        workflow_id = workflow_with_trigger_and_agent["workflow_id"]

        # Test with role/content format
        execution_request = {
            "query": "Follow-up question",
            "chat_history": [
                {"role": "user", "content": "Previous question"},
                {"role": "assistant", "content": "Previous answer"},
            ],
            "runtime_overrides": {},
            "session_id": f"test_session_{uuid.uuid4().hex[:8]}",
            "user_id": "test_user",
        }

        response = test_client.post(f"/api/workflows/{workflow_id}/execute/async", json=execution_request)

        # 202 Accepted is the correct status for async execution
        assert response.status_code == 202
        data = response.json()
        assert "execution_id" in data
        assert data["status"] != "waiting"

    def test_execute_async_returns_execution_id(
        self, test_client: TestClient, mock_workflow_engine, workflow_with_trigger_and_agent
    ):
        """Test that /execute/async returns a valid execution_id for polling."""
        workflow_id = workflow_with_trigger_and_agent["workflow_id"]

        execution_request = {
            "query": "Test query for execution ID check",
            "chat_history": [],
        }

        response = test_client.post(f"/api/workflows/{workflow_id}/execute/async", json=execution_request)

        # 202 Accepted is the correct status for async execution
        assert response.status_code == 202
        data = response.json()

        # Verify execution_id is a valid UUID
        assert "execution_id" in data
        execution_id = data["execution_id"]
        try:
            uuid.UUID(execution_id)
        except ValueError:
            pytest.fail(f"execution_id '{execution_id}' is not a valid UUID")

    def test_execute_async_workflow_not_found(self, test_client: TestClient, mock_workflow_engine):
        """Test that /execute/async returns 404 for non-existent workflow."""
        fake_id = str(uuid.uuid4())

        execution_request = {
            "query": "Test query",
            "chat_history": [],
        }

        response = test_client.post(f"/api/workflows/{fake_id}/execute/async", json=execution_request)

        assert response.status_code == 404

    def test_execute_async_populates_trigger_data(
        self, test_client: TestClient, mock_workflow_engine, workflow_with_trigger_and_agent
    ):
        """Test that /execute/async populates trigger data correctly in execution context.

        This is a regression test for the bug where the async endpoint did not populate
        step_io_data["trigger"], causing interactive agent steps to wait for user input
        even when a query was provided.
        """
        workflow_id = workflow_with_trigger_and_agent["workflow_id"]
        test_query = "Test message for trigger data verification"
        test_history = [
            {"role": "user", "content": "Previous question"},
            {"role": "assistant", "content": "Previous answer"},
        ]

        execution_request = {
            "query": test_query,
            "chat_history": test_history,
            "session_id": f"test_session_{uuid.uuid4().hex[:8]}",
            "user_id": "test_user",
        }

        response = test_client.post(f"/api/workflows/{workflow_id}/execute/async", json=execution_request)

        assert response.status_code == 202

        # Verify the mock engine was called
        mock_workflow_engine.execute_workflow.assert_called_once()

        # Get the execution context that was passed to the engine
        call_args = mock_workflow_engine.execute_workflow.call_args
        execution_context = call_args[0][0]  # First positional argument

        # Verify trigger data was populated correctly
        assert "trigger" in execution_context.step_io_data, "Trigger data should be populated in step_io_data"

        trigger_data = execution_context.step_io_data["trigger"]
        assert trigger_data.get("current_message") == test_query, (
            f"current_message should be '{test_query}', got: {trigger_data.get('current_message')}"
        )
        assert "messages" in trigger_data, "messages should be in trigger data"
        assert len(trigger_data["messages"]) == 3, "messages should contain chat history + current query (3 total)"
        # The last message should be the current query
        assert trigger_data["messages"][-1]["content"] == test_query
        assert trigger_data["messages"][-1]["role"] == "user"


class TestWorkflowSyncExecutionAPI:
    """Test suite for synchronous Workflow Execution API endpoint (/execute)."""

    @pytest.fixture
    def mock_workflow_engine(self, test_client: TestClient):
        """Mock the workflow engine in app state for execution tests."""
        from unittest.mock import AsyncMock, MagicMock

        # Create a mock workflow engine
        mock_engine = MagicMock()
        mock_engine.execute_workflow = AsyncMock(return_value=None)

        # Set the engine on the app state
        test_client.app.state.workflow_engine = mock_engine

        yield mock_engine

        # Cleanup - remove the mock engine
        if hasattr(test_client.app.state, "workflow_engine"):
            delattr(test_client.app.state, "workflow_engine")

    @pytest.fixture
    def workflow_with_trigger_and_agent(self, test_client: TestClient):
        """Create a workflow with trigger and agent step for execution testing."""
        workflow_data = {
            "name": f"Sync Execution Test Workflow {uuid.uuid4().hex[:8]}",
            "description": "Workflow for testing sync execution endpoint",
            "version": "1.0.0",
            "configuration": {
                "steps": [
                    {
                        "step_id": "trigger",
                        "step_type": "trigger",
                        "name": "Chat Trigger",
                        "config": {
                            "kind": "chat",
                            "need_history": False,
                            "allowed_modalities": ["text"],
                        },
                        "dependencies": [],
                    },
                    {
                        "step_id": "agent_1",
                        "step_type": "agent_execution",
                        "name": "Test Agent",
                        "dependencies": ["trigger"],
                        "config": {
                            "agent_name": "Test Agent",
                            "system_prompt": "You are a test agent. Respond briefly.",
                            "query": "{current_message}",
                            "interactive": True,
                            "multi_turn": False,
                        },
                    },
                ],
            },
            "created_by": "test_user",
            "is_active": True,
        }

        response = test_client.post("/api/workflows/", json=workflow_data)
        assert response.status_code == 200
        workflow = response.json()

        yield workflow

        # Cleanup
        test_client.delete(f"/api/workflows/{workflow['workflow_id']}")

    def test_execute_sync_with_query(self, test_client: TestClient, mock_workflow_engine, workflow_with_trigger_and_agent):
        """Test that /execute endpoint properly handles query parameter."""
        workflow_id = workflow_with_trigger_and_agent["workflow_id"]

        execution_request = {
            "query": "Hello, this is a sync test message",
            "chat_history": [],
            "runtime_overrides": {},
            "session_id": f"test_session_{uuid.uuid4().hex[:8]}",
            "user_id": "test_user",
        }

        response = test_client.post(f"/api/workflows/{workflow_id}/execute", json=execution_request)

        # 200 OK for sync execution
        assert response.status_code == 200
        data = response.json()
        assert "execution_id" in data
        # Verify the engine was called
        mock_workflow_engine.execute_workflow.assert_called_once()

    def test_execute_sync_with_chat_history(
        self, test_client: TestClient, mock_workflow_engine, workflow_with_trigger_and_agent
    ):
        """Test that /execute properly handles chat_history."""
        workflow_id = workflow_with_trigger_and_agent["workflow_id"]

        execution_request = {
            "query": "Follow-up question",
            "chat_history": [
                {"role": "user", "content": "Previous question"},
                {"role": "assistant", "content": "Previous answer"},
            ],
            "session_id": f"test_session_{uuid.uuid4().hex[:8]}",
            "user_id": "test_user",
        }

        response = test_client.post(f"/api/workflows/{workflow_id}/execute", json=execution_request)

        assert response.status_code == 200
        data = response.json()
        assert "execution_id" in data

    def test_execute_sync_workflow_not_found(self, test_client: TestClient, mock_workflow_engine):
        """Test that /execute returns 404 for non-existent workflow."""
        fake_id = str(uuid.uuid4())

        execution_request = {
            "query": "Test query",
            "chat_history": [],
        }

        response = test_client.post(f"/api/workflows/{fake_id}/execute", json=execution_request)

        assert response.status_code == 404

    def test_execute_sync_populates_trigger_data(
        self, test_client: TestClient, mock_workflow_engine, workflow_with_trigger_and_agent
    ):
        """Test that /execute populates trigger data correctly in execution context.

        This is a regression test for the bug where agent steps would wait for
        user input even when a query was provided.
        """
        workflow_id = workflow_with_trigger_and_agent["workflow_id"]
        test_query = "Test message for sync trigger data verification"
        test_history = [
            {"role": "user", "content": "Previous question"},
            {"role": "assistant", "content": "Previous answer"},
        ]

        execution_request = {
            "query": test_query,
            "chat_history": test_history,
            "session_id": f"test_session_{uuid.uuid4().hex[:8]}",
            "user_id": "test_user",
        }

        response = test_client.post(f"/api/workflows/{workflow_id}/execute", json=execution_request)

        assert response.status_code == 200

        # Verify the mock engine was called
        mock_workflow_engine.execute_workflow.assert_called_once()

        # Get the execution context that was passed to the engine
        call_args = mock_workflow_engine.execute_workflow.call_args
        execution_context = call_args[0][0]  # First positional argument

        # Verify trigger data was populated correctly
        assert "trigger" in execution_context.step_io_data, "Trigger data should be populated in step_io_data"

        trigger_data = execution_context.step_io_data["trigger"]
        assert trigger_data.get("current_message") == test_query, (
            f"current_message should be '{test_query}', got: {trigger_data.get('current_message')}"
        )
        assert "messages" in trigger_data, "messages should be in trigger data"
        assert len(trigger_data["messages"]) == 3, "messages should contain chat history + current query (3 total)"
        # The last message should be the current query
        assert trigger_data["messages"][-1]["content"] == test_query
        assert trigger_data["messages"][-1]["role"] == "user"

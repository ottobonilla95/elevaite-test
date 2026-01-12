"""
Tests for Agents Router

Tests all agent CRUD endpoints, tool binding operations, and agent execution.
"""

import pytest
import uuid
from datetime import datetime, timezone
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi.testclient import TestClient

from workflow_engine_poc.main import app
from workflow_core_sdk.db.models import Agent, AgentRead, AgentToolBinding, Prompt

client = TestClient(app)


@pytest.fixture
def mock_session():
    """Mock database session"""
    return MagicMock()


@pytest.fixture
def sample_agent(session):
    """Sample agent for testing - persisted to database"""
    now = datetime.now(timezone.utc)
    prompt_id = uuid.uuid4()

    # Create and persist the prompt first
    from workflow_core_sdk.db.models import Prompt

    prompt = Prompt(
        id=prompt_id,
        prompt_label="test_prompt",
        prompt="You are a helpful assistant.",
        unique_label="test_prompt_unique",
        app_name="test_app",
        ai_model_provider="openai",
        ai_model_name="gpt-4",
        organization_id="org-123",
        created_by="user-123",
    )
    session.add(prompt)
    session.commit()

    # Create and persist the agent
    agent = Agent(
        id=uuid.uuid4(),
        name="test_agent",
        description="Test agent description",
        system_prompt_id=prompt_id,
        provider_type="openai_textgen",
        provider_config={"model_name": "gpt-4", "temperature": 0.7},
        tags=["test", "demo"],
        status="active",
        organization_id="org-123",
        created_by="user-123",
        created_at=now,
        updated_at=now,
    )
    session.add(agent)
    session.commit()
    session.refresh(agent)
    return agent


@pytest.fixture
def sample_tool_binding():
    """Sample agent tool binding for testing"""
    now = datetime.now(timezone.utc)
    return AgentToolBinding(
        id=uuid.uuid4(),
        agent_id=uuid.uuid4(),
        tool_id=uuid.uuid4(),
        override_parameters={"param1": "value1"},
        is_active=True,
        organization_id="org-123",
        created_by="user-123",
        created_at=now,
        updated_at=now,
    )


@pytest.fixture
def sample_prompt():
    """Sample prompt for testing"""
    now = datetime.now(timezone.utc)
    return Prompt(
        id=uuid.uuid4(),
        name="test_prompt",
        prompt="You are a helpful assistant.",
        description="Test prompt",
        tags=["test"],
        organization_id="org-123",
        created_by="user-123",
        created_at=now,
        updated_at=now,
    )


# ========== Agent CRUD Tests ==========


@pytest.mark.api
class TestCreateAgent:
    """Tests for POST /agents/"""

    @patch("workflow_engine_poc.routers.agents.AgentsService.create_agent")
    @patch("workflow_engine_poc.routers.agents.get_db_session")
    @patch("workflow_engine_poc.routers.agents.api_key_or_user_guard")
    @pytest.mark.api
    def test_create_agent_success(self, mock_guard, mock_get_session, mock_create, mock_session, sample_agent):
        """Test creating an agent successfully"""
        mock_guard.return_value = lambda: "user-123"
        mock_get_session.return_value = mock_session
        mock_create.return_value = sample_agent

        payload = {
            "name": "test_agent",
            "description": "Test agent description",
            "system_prompt_id": str(sample_agent.system_prompt_id),
            "provider_type": "openai_textgen",
            "provider_config": {"model_name": "gpt-4", "temperature": 0.7},
            "tags": ["test", "demo"],
            "status": "active",
            "organization_id": "org-123",
            "created_by": "user-123",
        }

        response = client.post("/agents/", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "test_agent"
        assert data["provider_type"] == "openai_textgen"
        assert mock_create.call_count == 1

    @patch("workflow_engine_poc.routers.agents.AgentsService.create_agent")
    @patch("workflow_engine_poc.routers.agents.get_db_session")
    @patch("workflow_engine_poc.routers.agents.api_key_or_user_guard")
    @pytest.mark.api
    def test_create_agent_duplicate(self, mock_guard, mock_get_session, mock_create, mock_session):
        """Test creating a duplicate agent"""
        mock_guard.return_value = lambda: "user-123"
        mock_get_session.return_value = mock_session
        mock_create.side_effect = ValueError("Agent with this name already exists")

        payload = {
            "name": "duplicate_agent",
            "description": "Duplicate agent",
            "system_prompt_id": str(uuid.uuid4()),
            "provider_type": "openai_textgen",
            "provider_config": {},
        }

        response = client.post("/agents/", json=payload)

        assert response.status_code == 409
        assert "already exists" in response.json()["detail"]

    @patch("workflow_engine_poc.routers.agents.get_db_session")
    @patch("workflow_engine_poc.routers.agents.api_key_or_user_guard")
    @pytest.mark.api
    def test_create_agent_invalid_provider_config(self, mock_guard, mock_get_session, mock_session):
        """Test creating an agent with invalid provider config"""
        mock_guard.return_value = lambda: "user-123"
        mock_get_session.return_value = mock_session

        payload = {
            "name": "test_agent",
            "description": "Test agent",
            "system_prompt_id": str(uuid.uuid4()),
            "provider_type": "invalid_provider",
            "provider_config": {},
        }

        response = client.post("/agents/", json=payload)

        assert response.status_code == 400
        assert "Unknown provider_type" in response.json()["detail"]


@pytest.mark.api
class TestListAgents:
    """Tests for GET /agents/"""

    @patch("workflow_engine_poc.routers.agents.AgentsService.list_agents")
    @patch("workflow_engine_poc.routers.agents.get_db_session")
    @patch("workflow_engine_poc.routers.agents.api_key_or_user_guard")
    @pytest.mark.api
    def test_list_agents_success(self, mock_guard, mock_get_session, mock_list, mock_session, sample_agent):
        """Test listing agents"""
        mock_guard.return_value = lambda: "user-123"
        mock_get_session.return_value = mock_session
        mock_list.return_value = [sample_agent]

        response = client.get("/agents/")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "test_agent"

    @patch("workflow_engine_poc.routers.agents.AgentsService.list_agents")
    @patch("workflow_engine_poc.routers.agents.get_db_session")
    @patch("workflow_engine_poc.routers.agents.api_key_or_user_guard")
    @pytest.mark.api
    def test_list_agents_with_filters(self, mock_guard, mock_get_session, mock_list, mock_session, sample_agent):
        """Test listing agents with query filters"""
        mock_guard.return_value = lambda: "user-123"
        mock_get_session.return_value = mock_session
        mock_list.return_value = [sample_agent]

        response = client.get("/agents/?organization_id=org-123&status=active&q=test")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        # Verify the service was called with correct parameters
        assert mock_list.call_count == 1
        call_args = mock_list.call_args[0][1]
        assert call_args.organization_id == "org-123"
        assert call_args.status == "active"
        assert call_args.q == "test"

    @patch("workflow_engine_poc.routers.agents.AgentsService.list_agents")
    @patch("workflow_engine_poc.routers.agents.get_db_session")
    @patch("workflow_engine_poc.routers.agents.api_key_or_user_guard")
    @pytest.mark.api
    def test_list_agents_with_tag_filter(self, mock_guard, mock_get_session, mock_list, mock_session, sample_agent):
        """Test listing agents with tag filter"""
        mock_guard.return_value = lambda: "user-123"
        mock_get_session.return_value = mock_session
        # Create two agents, one with matching tag
        agent_with_tag = sample_agent
        agent_without_tag = Agent(
            id=uuid.uuid4(),
            name="other_agent",
            description="Other agent",
            system_prompt_id=uuid.uuid4(),
            provider_type="openai_textgen",
            provider_config={},
            tags=["other"],
            status="active",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        mock_list.return_value = [agent_with_tag, agent_without_tag]

        response = client.get("/agents/?tag=test")

        assert response.status_code == 200
        data = response.json()
        # Should only return the agent with the "test" tag
        assert len(data) == 1
        assert data[0]["name"] == "test_agent"

    @patch("workflow_engine_poc.routers.agents.AgentsService.list_agents")
    @patch("workflow_engine_poc.routers.agents.get_db_session")
    @patch("workflow_engine_poc.routers.agents.api_key_or_user_guard")
    @pytest.mark.api
    def test_list_agents_pagination(self, mock_guard, mock_get_session, mock_list, mock_session, sample_agent):
        """Test listing agents with pagination"""
        mock_guard.return_value = lambda: "user-123"
        mock_get_session.return_value = mock_session
        mock_list.return_value = [sample_agent]

        response = client.get("/agents/?limit=10&offset=5")

        assert response.status_code == 200
        # Verify pagination parameters were passed
        call_args = mock_list.call_args[0][1]
        assert call_args.limit == 10
        assert call_args.offset == 5


@pytest.mark.api
class TestGetAgent:
    """Tests for GET /agents/{agent_id}"""

    @patch("workflow_engine_poc.routers.agents.AgentsService.get_agent")
    @patch("workflow_engine_poc.routers.agents.get_db_session")
    @patch("workflow_engine_poc.routers.agents.api_key_or_user_guard")
    @pytest.mark.api
    def test_get_agent_success(self, mock_guard, mock_get_session, mock_get, mock_session, sample_agent):
        """Test getting an agent by ID"""
        mock_guard.return_value = lambda: "user-123"
        mock_get_session.return_value = mock_session
        mock_get.return_value = sample_agent

        response = client.get(f"/agents/{sample_agent.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "test_agent"
        assert data["id"] == str(sample_agent.id)

    @patch("workflow_engine_poc.routers.agents.AgentsService.get_agent")
    @patch("workflow_engine_poc.routers.agents.get_db_session")
    @patch("workflow_engine_poc.routers.agents.api_key_or_user_guard")
    @pytest.mark.api
    def test_get_agent_not_found(self, mock_guard, mock_get_session, mock_get, mock_session):
        """Test getting a non-existent agent"""
        mock_guard.return_value = lambda: "user-123"
        mock_get_session.return_value = mock_session
        mock_get.return_value = None

        agent_id = uuid.uuid4()
        response = client.get(f"/agents/{agent_id}")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"]


@pytest.mark.api
class TestUpdateAgent:
    """Tests for PATCH /agents/{agent_id}"""

    @patch("workflow_engine_poc.routers.agents.AgentsService.update_agent")
    @patch("workflow_engine_poc.routers.agents.get_db_session")
    @patch("workflow_engine_poc.routers.agents.api_key_or_user_guard")
    @pytest.mark.api
    def test_update_agent_success(self, mock_guard, mock_get_session, mock_update, mock_session, sample_agent):
        """Test updating an agent"""
        mock_guard.return_value = lambda: "user-123"
        mock_get_session.return_value = mock_session
        updated_agent = sample_agent
        updated_agent.name = "updated_agent"
        mock_update.return_value = updated_agent

        payload = {"name": "updated_agent", "description": "Updated description"}

        response = client.patch(f"/agents/{sample_agent.id}", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "updated_agent"

    @patch("workflow_engine_poc.routers.agents.AgentsService.update_agent")
    @patch("workflow_engine_poc.routers.agents.get_db_session")
    @patch("workflow_engine_poc.routers.agents.api_key_or_user_guard")
    @pytest.mark.api
    def test_update_agent_not_found(self, mock_guard, mock_get_session, mock_update, mock_session):
        """Test updating a non-existent agent"""
        mock_guard.return_value = lambda: "user-123"
        mock_get_session.return_value = mock_session
        mock_update.side_effect = ValueError("Agent not found")

        agent_id = uuid.uuid4()
        payload = {"name": "updated_agent"}

        response = client.patch(f"/agents/{agent_id}", json=payload)

        assert response.status_code == 404
        assert "not found" in response.json()["detail"]


@pytest.mark.api
class TestDeleteAgent:
    """Tests for DELETE /agents/{agent_id}"""

    @patch("workflow_engine_poc.routers.agents.AgentsService.delete_agent")
    @patch("workflow_engine_poc.routers.agents.get_db_session")
    @patch("workflow_engine_poc.routers.agents.api_key_or_user_guard")
    @pytest.mark.api
    def test_delete_agent_success(self, mock_guard, mock_get_session, mock_delete, mock_session, sample_agent):
        """Test deleting an agent"""
        mock_guard.return_value = lambda: "user-123"
        mock_get_session.return_value = mock_session
        mock_delete.return_value = True

        response = client.delete(f"/agents/{sample_agent.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["deleted"] is True

    @patch("workflow_engine_poc.routers.agents.AgentsService.delete_agent")
    @patch("workflow_engine_poc.routers.agents.get_db_session")
    @patch("workflow_engine_poc.routers.agents.api_key_or_user_guard")
    @pytest.mark.api
    def test_delete_agent_not_found(self, mock_guard, mock_get_session, mock_delete, mock_session):
        """Test deleting a non-existent agent"""
        mock_guard.return_value = lambda: "user-123"
        mock_get_session.return_value = mock_session
        mock_delete.return_value = False

        agent_id = uuid.uuid4()
        response = client.delete(f"/agents/{agent_id}")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"]


# ========== Agent Tool Binding Tests ==========


@pytest.mark.api
class TestListAgentTools:
    """Tests for GET /agents/{agent_id}/tools"""

    @patch("workflow_engine_poc.routers.agents.AgentsService.list_agent_tools")
    @patch("workflow_engine_poc.routers.agents.get_db_session")
    @patch("workflow_engine_poc.routers.agents.api_key_or_user_guard")
    @pytest.mark.api
    def test_list_agent_tools_success(self, mock_guard, mock_get_session, mock_list, mock_session, sample_tool_binding):
        """Test listing tools for an agent"""
        mock_guard.return_value = lambda: "user-123"
        mock_get_session.return_value = mock_session
        mock_list.return_value = [sample_tool_binding]

        agent_id = uuid.uuid4()
        response = client.get(f"/agents/{agent_id}/tools")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["is_active"] is True

    @patch("workflow_engine_poc.routers.agents.AgentsService.list_agent_tools")
    @patch("workflow_engine_poc.routers.agents.get_db_session")
    @patch("workflow_engine_poc.routers.agents.api_key_or_user_guard")
    @pytest.mark.api
    def test_list_agent_tools_empty(self, mock_guard, mock_get_session, mock_list, mock_session):
        """Test listing tools for an agent with no tools"""
        mock_guard.return_value = lambda: "user-123"
        mock_get_session.return_value = mock_session
        mock_list.return_value = []

        agent_id = uuid.uuid4()
        response = client.get(f"/agents/{agent_id}/tools")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 0


@pytest.mark.api
class TestAttachToolToAgent:
    """Tests for POST /agents/{agent_id}/tools"""

    @patch("workflow_engine_poc.routers.agents.AgentsService.attach_tool_to_agent")
    @patch("workflow_engine_poc.routers.agents.get_db_session")
    @patch("workflow_engine_poc.routers.agents.api_key_or_user_guard")
    @pytest.mark.api
    def test_attach_tool_success(self, mock_guard, mock_get_session, mock_attach, mock_session, sample_tool_binding):
        """Test attaching a tool to an agent"""
        mock_guard.return_value = lambda: "user-123"
        mock_get_session.return_value = mock_session
        mock_attach.return_value = sample_tool_binding

        agent_id = uuid.uuid4()
        payload = {
            "tool_id": str(uuid.uuid4()),
            "override_parameters": {"param1": "value1"},
            "is_active": True,
        }

        response = client.post(f"/agents/{agent_id}/tools", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["is_active"] is True

    @patch("workflow_engine_poc.routers.agents.AgentsService.attach_tool_to_agent")
    @patch("workflow_engine_poc.routers.agents.get_db_session")
    @patch("workflow_engine_poc.routers.agents.api_key_or_user_guard")
    @pytest.mark.api
    def test_attach_tool_agent_not_found(self, mock_guard, mock_get_session, mock_attach, mock_session):
        """Test attaching a tool to a non-existent agent"""
        mock_guard.return_value = lambda: "user-123"
        mock_get_session.return_value = mock_session
        mock_attach.side_effect = ValueError("Agent not found")

        agent_id = uuid.uuid4()
        payload = {"tool_id": str(uuid.uuid4())}

        response = client.post(f"/agents/{agent_id}/tools", json=payload)

        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    @patch("workflow_engine_poc.routers.agents.AgentsService.attach_tool_to_agent")
    @patch("workflow_engine_poc.routers.agents.get_db_session")
    @patch("workflow_engine_poc.routers.agents.api_key_or_user_guard")
    @pytest.mark.api
    def test_attach_tool_missing_identifier(self, mock_guard, mock_get_session, mock_attach, mock_session):
        """Test attaching a tool without tool_id or local_tool_name"""
        mock_guard.return_value = lambda: "user-123"
        mock_get_session.return_value = mock_session
        mock_attach.side_effect = ValueError("Provide tool_id or local_tool_name")

        agent_id = uuid.uuid4()
        payload = {"override_parameters": {}}

        response = client.post(f"/agents/{agent_id}/tools", json=payload)

        assert response.status_code == 400
        assert "Provide tool_id or local_tool_name" in response.json()["detail"]


@pytest.mark.api
class TestUpdateAgentToolBinding:
    """Tests for PATCH /agents/{agent_id}/tools/{binding_id}"""

    @patch("workflow_engine_poc.routers.agents.AgentsService.update_agent_tool_binding")
    @patch("workflow_engine_poc.routers.agents.get_db_session")
    @patch("workflow_engine_poc.routers.agents.api_key_or_user_guard")
    @pytest.mark.api
    def test_update_binding_success(self, mock_guard, mock_get_session, mock_update, mock_session, sample_tool_binding):
        """Test updating a tool binding"""
        mock_guard.return_value = lambda: "user-123"
        mock_get_session.return_value = mock_session
        updated_binding = sample_tool_binding
        updated_binding.is_active = False
        mock_update.return_value = updated_binding

        agent_id = uuid.uuid4()
        binding_id = uuid.uuid4()
        payload = {"is_active": False, "override_parameters": {"param2": "value2"}}

        response = client.patch(f"/agents/{agent_id}/tools/{binding_id}", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["is_active"] is False

    @patch("workflow_engine_poc.routers.agents.AgentsService.update_agent_tool_binding")
    @patch("workflow_engine_poc.routers.agents.get_db_session")
    @patch("workflow_engine_poc.routers.agents.api_key_or_user_guard")
    @pytest.mark.api
    def test_update_binding_not_found(self, mock_guard, mock_get_session, mock_update, mock_session):
        """Test updating a non-existent binding"""
        mock_guard.return_value = lambda: "user-123"
        mock_get_session.return_value = mock_session
        mock_update.side_effect = ValueError("Binding not found")

        agent_id = uuid.uuid4()
        binding_id = uuid.uuid4()
        payload = {"is_active": False}

        response = client.patch(f"/agents/{agent_id}/tools/{binding_id}", json=payload)

        assert response.status_code == 404
        assert "not found" in response.json()["detail"]


@pytest.mark.api
class TestDetachToolFromAgent:
    """Tests for DELETE /agents/{agent_id}/tools/{binding_id}"""

    @patch("workflow_engine_poc.routers.agents.AgentsService.detach_tool_from_agent")
    @patch("workflow_engine_poc.routers.agents.get_db_session")
    @patch("workflow_engine_poc.routers.agents.api_key_or_user_guard")
    @pytest.mark.api
    def test_detach_tool_success(self, mock_guard, mock_get_session, mock_detach, mock_session):
        """Test detaching a tool from an agent"""
        mock_guard.return_value = lambda: "user-123"
        mock_get_session.return_value = mock_session
        mock_detach.return_value = True

        agent_id = uuid.uuid4()
        binding_id = uuid.uuid4()

        response = client.delete(f"/agents/{agent_id}/tools/{binding_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["deleted"] is True

    @patch("workflow_engine_poc.routers.agents.AgentsService.detach_tool_from_agent")
    @patch("workflow_engine_poc.routers.agents.get_db_session")
    @patch("workflow_engine_poc.routers.agents.api_key_or_user_guard")
    @pytest.mark.api
    def test_detach_tool_not_found(self, mock_guard, mock_get_session, mock_detach, mock_session):
        """Test detaching a non-existent binding"""
        mock_guard.return_value = lambda: "user-123"
        mock_get_session.return_value = mock_session
        mock_detach.return_value = False

        agent_id = uuid.uuid4()
        binding_id = uuid.uuid4()

        response = client.delete(f"/agents/{agent_id}/tools/{binding_id}")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"]


# ========== Agent Execution Tests ==========


@pytest.mark.api
class TestExecuteAgent:
    """Tests for POST /agents/{agent_id}/execute"""

    @patch("workflow_core_sdk.steps.ai_steps.AgentStep")
    @pytest.mark.api
    def test_execute_agent_success(self, mock_agent_step_class, test_client, session, sample_agent, sample_prompt):
        """Test executing an agent with a query"""
        import json

        # Mock AgentStep instance
        mock_agent_instance = AsyncMock()
        mock_agent_instance.execute = AsyncMock(return_value={"response": "Test response", "status": "success"})
        mock_agent_step_class.return_value = mock_agent_instance

        # Prepare multipart form data
        payload_data = {"query": "What is the weather?", "context": {"location": "NYC"}}

        response = test_client.post(
            f"/agents/{sample_agent.id}/execute",
            data={"payload": json.dumps(payload_data)},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["response"] == "Test response"
        assert data["status"] == "success"

        # Verify AgentStep was called correctly
        mock_agent_step_class.assert_called_once()
        mock_agent_instance.execute.assert_called_once_with("What is the weather?", {"location": "NYC"})

    @pytest.mark.api
    def test_execute_agent_not_found(self, test_client):
        """Test executing a non-existent agent"""
        import json

        agent_id = uuid.uuid4()
        payload_data = {"query": "Test query"}

        response = test_client.post(
            f"/agents/{agent_id}/execute",
            data={"payload": json.dumps(payload_data)},
        )

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    @pytest.mark.api
    def test_execute_agent_missing_query(self, test_client, session, sample_agent, sample_prompt):
        """Test executing an agent without a query"""
        import json

        payload_data = {"context": {"key": "value"}}  # Missing query

        response = test_client.post(
            f"/agents/{sample_agent.id}/execute",
            data={"payload": json.dumps(payload_data)},
        )

        assert response.status_code == 400
        assert "query" in response.json()["detail"].lower()

    @pytest.mark.api
    def test_execute_agent_missing_payload(self, test_client, session, sample_agent):
        """Test executing an agent without payload"""
        response = test_client.post(f"/agents/{sample_agent.id}/execute")

        assert response.status_code == 400
        assert "payload" in response.json()["detail"].lower()

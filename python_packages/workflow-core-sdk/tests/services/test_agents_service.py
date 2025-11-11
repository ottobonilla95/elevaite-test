"""
Unit tests for AgentsService

Tests the business logic of agent and agent tool binding operations with mocked database.
"""

import uuid
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

from workflow_core_sdk.db.models import Agent, AgentUpdate, AgentToolBinding
from workflow_core_sdk.services.agents_service import AgentsService, AgentsListQuery


@pytest.fixture
def mock_session():
    """Mock SQLModel session"""
    return MagicMock()


@pytest.fixture
def sample_agent():
    """Sample agent for testing"""
    now = datetime.now(timezone.utc)
    agent_id = uuid.uuid4()
    return Agent(
        id=agent_id,
        name="test_agent",
        description="Test agent description",
        agent_type="conversational",
        status="active",
        configuration={
            "model": "gpt-4o",
            "temperature": 0.7,
        },
        organization_id="org-123",
        created_by="user-123",
        created_at=now,
        updated_at=now,
    )


@pytest.fixture
def sample_agent_data():
    """Sample agent data for creation"""
    return {
        "name": "new_agent",
        "description": "New agent description",
        "agent_type": "conversational",
        "status": "active",
        "configuration": {"model": "gpt-4o"},
        "organization_id": "org-123",
        "created_by": "user-123",
    }


@pytest.fixture
def sample_tool_binding():
    """Sample agent tool binding"""
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


class TestAgentsCRUD:
    """Tests for agent CRUD operations"""

    def test_create_agent_success(self, mock_session, sample_agent_data, sample_agent):
        """Test creating a new agent"""
        # Mock the uniqueness check
        mock_result = MagicMock()
        mock_result.first.return_value = None  # No existing agent
        mock_session.exec.return_value = mock_result

        # Mock add/commit/refresh
        mock_session.add.return_value = None
        mock_session.commit.return_value = None
        mock_session.refresh.side_effect = lambda obj: setattr(obj, "id", sample_agent.id)

        agent = AgentsService.create_agent(mock_session, sample_agent_data)

        assert agent is not None
        assert agent.name == "new_agent"
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()

    def test_create_agent_duplicate_name_with_org(self, mock_session, sample_agent_data, sample_agent):
        """Test creating an agent with duplicate name in same organization"""
        # Mock the uniqueness check to return existing agent
        mock_result = MagicMock()
        mock_result.first.return_value = sample_agent
        mock_session.exec.return_value = mock_result

        with pytest.raises(ValueError, match="Agent with this name already exists"):
            AgentsService.create_agent(mock_session, sample_agent_data)

    def test_create_agent_duplicate_name_without_org(self, mock_session, sample_agent):
        """Test creating an agent with duplicate name without organization"""
        agent_data = {
            "name": "test_agent",
            "description": "Test",
            "agent_type": "conversational",
        }

        # Mock the uniqueness check to return existing agent
        mock_result = MagicMock()
        mock_result.first.return_value = sample_agent
        mock_session.exec.return_value = mock_result

        with pytest.raises(ValueError, match="Agent with this name already exists"):
            AgentsService.create_agent(mock_session, agent_data)

    def test_list_agents_no_filters(self, mock_session, sample_agent):
        """Test listing agents without filters"""
        mock_result = MagicMock()
        mock_result.all.return_value = [sample_agent]
        mock_session.exec.return_value = mock_result

        params = AgentsListQuery(limit=100, offset=0)
        agents = AgentsService.list_agents(mock_session, params)

        assert len(agents) == 1
        assert agents[0].name == "test_agent"

    def test_list_agents_with_organization_filter(self, mock_session, sample_agent):
        """Test listing agents filtered by organization"""
        mock_result = MagicMock()
        mock_result.all.return_value = [sample_agent]
        mock_session.exec.return_value = mock_result

        params = AgentsListQuery(organization_id="org-123", limit=100, offset=0)
        agents = AgentsService.list_agents(mock_session, params)

        assert len(agents) == 1
        assert agents[0].organization_id == "org-123"

    def test_list_agents_with_status_filter(self, mock_session, sample_agent):
        """Test listing agents filtered by status"""
        mock_result = MagicMock()
        mock_result.all.return_value = [sample_agent]
        mock_session.exec.return_value = mock_result

        params = AgentsListQuery(status="active", limit=100, offset=0)
        agents = AgentsService.list_agents(mock_session, params)

        assert len(agents) == 1
        assert agents[0].status == "active"

    def test_list_agents_with_search_query(self, mock_session, sample_agent):
        """Test listing agents with text search"""
        mock_result = MagicMock()
        mock_result.all.return_value = [sample_agent]
        mock_session.exec.return_value = mock_result

        params = AgentsListQuery(q="test", limit=100, offset=0)
        agents = AgentsService.list_agents(mock_session, params)

        assert len(agents) == 1
        assert "test" in agents[0].name.lower()

    def test_list_agents_search_no_match(self, mock_session, sample_agent):
        """Test listing agents with search query that doesn't match"""
        mock_result = MagicMock()
        mock_result.all.return_value = [sample_agent]
        mock_session.exec.return_value = mock_result

        params = AgentsListQuery(q="nomatch", limit=100, offset=0)
        agents = AgentsService.list_agents(mock_session, params)

        assert len(agents) == 0

    def test_list_agents_with_pagination(self, mock_session):
        """Test listing agents with pagination"""
        mock_result = MagicMock()
        mock_result.all.return_value = []
        mock_session.exec.return_value = mock_result

        params = AgentsListQuery(limit=10, offset=20)
        agents = AgentsService.list_agents(mock_session, params)

        assert len(agents) == 0

    def test_get_agent_success(self, mock_session, sample_agent):
        """Test getting an agent by ID"""
        mock_result = MagicMock()
        mock_result.first.return_value = sample_agent
        mock_session.exec.return_value = mock_result

        agent = AgentsService.get_agent(mock_session, str(sample_agent.id))

        assert agent is not None
        assert agent.id == sample_agent.id
        assert agent.name == "test_agent"

    def test_get_agent_not_found(self, mock_session):
        """Test getting a non-existent agent"""
        mock_result = MagicMock()
        mock_result.first.return_value = None
        mock_session.exec.return_value = mock_result

        agent_id = str(uuid.uuid4())
        agent = AgentsService.get_agent(mock_session, agent_id)

        assert agent is None

    def test_update_agent_success(self, mock_session, sample_agent):
        """Test updating an agent"""
        mock_result = MagicMock()
        mock_result.first.return_value = sample_agent
        mock_session.exec.return_value = mock_result

        payload = AgentUpdate(description="Updated description", status="inactive")
        agent = AgentsService.update_agent(mock_session, str(sample_agent.id), payload)

        assert agent is not None
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()

    def test_update_agent_not_found(self, mock_session):
        """Test updating a non-existent agent"""
        mock_result = MagicMock()
        mock_result.first.return_value = None
        mock_session.exec.return_value = mock_result

        agent_id = str(uuid.uuid4())
        payload = AgentUpdate(description="Updated")

        with pytest.raises(ValueError, match="Agent not found"):
            AgentsService.update_agent(mock_session, agent_id, payload)

    def test_delete_agent_success(self, mock_session, sample_agent):
        """Test deleting an agent"""
        mock_result = MagicMock()
        mock_result.first.return_value = sample_agent
        mock_session.exec.return_value = mock_result

        result = AgentsService.delete_agent(mock_session, str(sample_agent.id))

        assert result is True
        mock_session.delete.assert_called_once_with(sample_agent)
        mock_session.commit.assert_called_once()

    def test_delete_agent_not_found(self, mock_session):
        """Test deleting a non-existent agent"""
        mock_result = MagicMock()
        mock_result.first.return_value = None
        mock_session.exec.return_value = mock_result

        agent_id = str(uuid.uuid4())
        result = AgentsService.delete_agent(mock_session, agent_id)

        assert result is False
        mock_session.delete.assert_not_called()


class TestAgentToolBindings:
    """Tests for agent tool binding operations"""

    def test_list_agent_tools(self, mock_session, sample_tool_binding):
        """Test listing tools bound to an agent"""
        mock_result = MagicMock()
        mock_result.all.return_value = [sample_tool_binding]
        mock_session.exec.return_value = mock_result

        agent_id = str(uuid.uuid4())
        bindings = AgentsService.list_agent_tools(mock_session, agent_id)

        assert len(bindings) == 1
        assert bindings[0].id == sample_tool_binding.id

    def test_attach_tool_to_agent_with_tool_id(self, mock_session, sample_agent):
        """Test attaching a tool to an agent using tool_id"""
        # Mock agent lookup
        mock_result = MagicMock()
        mock_result.first.return_value = sample_agent
        mock_session.exec.return_value = mock_result

        # Mock add/commit/refresh
        mock_session.add.return_value = None
        mock_session.commit.return_value = None
        mock_session.refresh.return_value = None

        tool_id = str(uuid.uuid4())
        binding = AgentsService.attach_tool_to_agent(
            mock_session,
            str(sample_agent.id),
            tool_id=tool_id,
            override_parameters={"param1": "value1"},
            is_active=True,
        )

        assert binding is not None
        assert binding.agent_id == sample_agent.id
        assert str(binding.tool_id) == tool_id
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()

    @patch("workflow_core_sdk.services.agents_service.tool_registry")
    def test_attach_tool_to_agent_with_local_tool_name(self, mock_registry, mock_session, sample_agent):
        """Test attaching a tool to an agent using local_tool_name"""
        # Mock agent lookup
        mock_result = MagicMock()
        mock_result.first.return_value = sample_agent
        mock_session.exec.return_value = mock_result

        # Mock tool registry
        tool_id = uuid.uuid4()
        mock_registry.sync_local_tool_by_name.return_value = tool_id

        # Mock add/commit/refresh
        mock_session.add.return_value = None
        mock_session.commit.return_value = None
        mock_session.refresh.return_value = None

        binding = AgentsService.attach_tool_to_agent(
            mock_session,
            str(sample_agent.id),
            local_tool_name="calculator",
            is_active=True,
        )

        assert binding is not None
        assert binding.agent_id == sample_agent.id
        assert binding.tool_id == tool_id
        mock_registry.sync_local_tool_by_name.assert_called_once_with(mock_session, "calculator")

    @patch("workflow_core_sdk.services.agents_service.tool_registry")
    def test_attach_tool_to_agent_local_tool_not_found(self, mock_registry, mock_session, sample_agent):
        """Test attaching a tool with local_tool_name that doesn't exist"""
        # Mock agent lookup
        mock_result = MagicMock()
        mock_result.first.return_value = sample_agent
        mock_session.exec.return_value = mock_result

        # Mock tool registry returning None
        mock_registry.sync_local_tool_by_name.return_value = None

        with pytest.raises(ValueError, match="Local tool not found in registry"):
            AgentsService.attach_tool_to_agent(
                mock_session,
                str(sample_agent.id),
                local_tool_name="nonexistent_tool",
            )

    def test_attach_tool_to_agent_no_tool_specified(self, mock_session, sample_agent):
        """Test attaching a tool without providing tool_id or local_tool_name"""
        # Mock agent lookup
        mock_result = MagicMock()
        mock_result.first.return_value = sample_agent
        mock_session.exec.return_value = mock_result

        with pytest.raises(ValueError, match="Provide tool_id or local_tool_name"):
            AgentsService.attach_tool_to_agent(mock_session, str(sample_agent.id))

    def test_attach_tool_to_agent_agent_not_found(self, mock_session):
        """Test attaching a tool to a non-existent agent"""
        # Mock agent lookup returning None
        mock_result = MagicMock()
        mock_result.first.return_value = None
        mock_session.exec.return_value = mock_result

        agent_id = str(uuid.uuid4())
        tool_id = str(uuid.uuid4())

        with pytest.raises(ValueError, match="Agent not found"):
            AgentsService.attach_tool_to_agent(mock_session, agent_id, tool_id=tool_id)

    def test_update_agent_tool_binding_success(self, mock_session, sample_tool_binding):
        """Test updating an agent tool binding"""
        # Mock binding lookup
        mock_session.get.return_value = sample_tool_binding

        # Mock add/commit/refresh
        mock_session.add.return_value = None
        mock_session.commit.return_value = None
        mock_session.refresh.return_value = None

        updates = {"override_parameters": {"new_param": "new_value"}, "is_active": False}
        binding = AgentsService.update_agent_tool_binding(
            mock_session,
            str(sample_tool_binding.agent_id),
            str(sample_tool_binding.id),
            updates,
        )

        assert binding is not None
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()

    def test_update_agent_tool_binding_not_found(self, mock_session):
        """Test updating a non-existent binding"""
        # Mock binding lookup returning None
        mock_session.get.return_value = None

        agent_id = str(uuid.uuid4())
        binding_id = str(uuid.uuid4())
        updates = {"is_active": False}

        with pytest.raises(ValueError, match="Binding not found"):
            AgentsService.update_agent_tool_binding(mock_session, agent_id, binding_id, updates)

    def test_update_agent_tool_binding_agent_mismatch(self, mock_session, sample_tool_binding):
        """Test updating a binding with mismatched agent_id"""
        # Mock binding lookup
        mock_session.get.return_value = sample_tool_binding

        wrong_agent_id = str(uuid.uuid4())
        updates = {"is_active": False}

        with pytest.raises(ValueError, match="Agent/binding mismatch"):
            AgentsService.update_agent_tool_binding(
                mock_session,
                wrong_agent_id,
                str(sample_tool_binding.id),
                updates,
            )

    def test_detach_tool_from_agent_success(self, mock_session, sample_tool_binding):
        """Test detaching a tool from an agent"""
        # Mock binding lookup
        mock_session.get.return_value = sample_tool_binding

        result = AgentsService.detach_tool_from_agent(
            mock_session,
            str(sample_tool_binding.agent_id),
            str(sample_tool_binding.id),
        )

        assert result is True
        mock_session.delete.assert_called_once_with(sample_tool_binding)
        mock_session.commit.assert_called_once()

    def test_detach_tool_from_agent_not_found(self, mock_session):
        """Test detaching a non-existent binding"""
        # Mock binding lookup returning None
        mock_session.get.return_value = None

        agent_id = str(uuid.uuid4())
        binding_id = str(uuid.uuid4())

        result = AgentsService.detach_tool_from_agent(mock_session, agent_id, binding_id)

        assert result is False
        mock_session.delete.assert_not_called()

    def test_detach_tool_from_agent_agent_mismatch(self, mock_session, sample_tool_binding):
        """Test detaching a binding with mismatched agent_id"""
        # Mock binding lookup
        mock_session.get.return_value = sample_tool_binding

        wrong_agent_id = str(uuid.uuid4())

        with pytest.raises(ValueError, match="Agent/binding mismatch"):
            AgentsService.detach_tool_from_agent(
                mock_session,
                wrong_agent_id,
                str(sample_tool_binding.id),
            )

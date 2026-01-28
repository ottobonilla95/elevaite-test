"""
Unit tests for A2AAgentsService

Tests the business logic of A2A agent operations with mocked database.
"""

import uuid
from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock

import pytest

from workflow_core_sdk.db.models import A2AAgent, A2AAgentCreate, A2AAgentUpdate
from workflow_core_sdk.services.a2a_agents_service import (
    A2AAgentsService,
    A2AAgentsListQuery,
)


@pytest.fixture
def mock_session():
    """Mock SQLModel session"""
    return MagicMock()


@pytest.fixture
def sample_a2a_agent():
    """Sample A2A agent for testing"""
    now = datetime.now(timezone.utc)
    agent_id = uuid.uuid4()
    return A2AAgent(
        id=agent_id,
        name="test_a2a_agent",
        description="Test A2A agent description",
        base_url="https://agent.example.com",
        agent_card_url="/.well-known/agent.json",
        auth_type="bearer",
        auth_config={"token": "test-token"},
        status="active",
        organization_id="org-123",
        created_by="user-123",
        registered_at=now,
        updated_at=now,
        tags=["test", "external"],
    )


@pytest.fixture
def sample_a2a_agent_create():
    """Sample A2A agent creation data"""
    return A2AAgentCreate(
        name="new_a2a_agent",
        description="New A2A agent",
        base_url="https://new-agent.example.com",
        auth_type="api_key",
        auth_config={"key": "test-key"},
        organization_id="org-123",
        tags=["new"],
    )


class TestA2AAgentsCRUD:
    """Tests for A2A agent CRUD operations"""

    def test_create_agent_success(
        self, mock_session, sample_a2a_agent_create, sample_a2a_agent
    ):
        """Test creating a new A2A agent"""
        mock_result = MagicMock()
        mock_result.first.return_value = None  # No existing agent
        mock_session.exec.return_value = mock_result

        mock_session.add.return_value = None
        mock_session.commit.return_value = None
        mock_session.refresh.side_effect = lambda obj: setattr(
            obj, "id", sample_a2a_agent.id
        )

        agent = A2AAgentsService.create_agent(
            mock_session, sample_a2a_agent_create, created_by="user-123"
        )

        assert agent is not None
        assert agent.name == "new_a2a_agent"
        assert agent.base_url == "https://new-agent.example.com"
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()

    def test_create_agent_duplicate_base_url(
        self, mock_session, sample_a2a_agent_create, sample_a2a_agent
    ):
        """Test creating an agent with duplicate base_url fails"""
        mock_result = MagicMock()
        mock_result.first.return_value = sample_a2a_agent  # Existing agent
        mock_session.exec.return_value = mock_result

        with pytest.raises(ValueError, match="already exists"):
            A2AAgentsService.create_agent(mock_session, sample_a2a_agent_create)

    def test_list_agents_no_filters(self, mock_session, sample_a2a_agent):
        """Test listing agents without filters"""
        mock_result = MagicMock()
        mock_result.all.return_value = [sample_a2a_agent]
        mock_session.exec.return_value = mock_result

        params = A2AAgentsListQuery(limit=100, offset=0)
        agents = A2AAgentsService.list_agents(mock_session, params)

        assert len(agents) == 1
        assert agents[0].name == "test_a2a_agent"

    def test_list_agents_with_org_filter(self, mock_session, sample_a2a_agent):
        """Test listing agents filtered by organization"""
        mock_result = MagicMock()
        mock_result.all.return_value = [sample_a2a_agent]
        mock_session.exec.return_value = mock_result

        params = A2AAgentsListQuery(organization_id="org-123")
        agents = A2AAgentsService.list_agents(mock_session, params)

        assert len(agents) == 1
        assert agents[0].organization_id == "org-123"

    def test_list_agents_with_search(self, mock_session, sample_a2a_agent):
        """Test listing agents with text search"""
        mock_result = MagicMock()
        mock_result.all.return_value = [sample_a2a_agent]
        mock_session.exec.return_value = mock_result

        params = A2AAgentsListQuery(q="test")
        agents = A2AAgentsService.list_agents(mock_session, params)

        assert len(agents) == 1
        assert "test" in agents[0].name.lower()

    def test_list_agents_search_no_match(self, mock_session, sample_a2a_agent):
        """Test listing agents with search query that doesn't match"""
        mock_result = MagicMock()
        mock_result.all.return_value = [sample_a2a_agent]
        mock_session.exec.return_value = mock_result

        params = A2AAgentsListQuery(q="nomatch")
        agents = A2AAgentsService.list_agents(mock_session, params)

        assert len(agents) == 0

    def test_list_agents_with_tags_filter(self, mock_session, sample_a2a_agent):
        """Test listing agents filtered by tags"""
        mock_result = MagicMock()
        mock_result.all.return_value = [sample_a2a_agent]
        mock_session.exec.return_value = mock_result

        params = A2AAgentsListQuery(tags=["external"])
        agents = A2AAgentsService.list_agents(mock_session, params)

        assert len(agents) == 1
        assert "external" in agents[0].tags

    def test_get_agent_success(self, mock_session, sample_a2a_agent):
        """Test getting an agent by ID"""
        mock_result = MagicMock()
        mock_result.first.return_value = sample_a2a_agent
        mock_session.exec.return_value = mock_result

        agent = A2AAgentsService.get_agent(mock_session, str(sample_a2a_agent.id))

        assert agent is not None
        assert agent.id == sample_a2a_agent.id

    def test_get_agent_not_found(self, mock_session):
        """Test getting a non-existent agent"""
        mock_result = MagicMock()
        mock_result.first.return_value = None
        mock_session.exec.return_value = mock_result

        agent = A2AAgentsService.get_agent(mock_session, str(uuid.uuid4()))
        assert agent is None

    def test_get_agent_by_base_url(self, mock_session, sample_a2a_agent):
        """Test getting an agent by base URL"""
        mock_result = MagicMock()
        mock_result.first.return_value = sample_a2a_agent
        mock_session.exec.return_value = mock_result

        agent = A2AAgentsService.get_agent_by_base_url(
            mock_session, "https://agent.example.com"
        )

        assert agent is not None
        assert agent.base_url == "https://agent.example.com"

    def test_update_agent_success(self, mock_session, sample_a2a_agent):
        """Test updating an agent"""
        mock_result = MagicMock()
        mock_result.first.return_value = sample_a2a_agent
        mock_session.exec.return_value = mock_result

        payload = A2AAgentUpdate(description="Updated description", status="inactive")
        agent = A2AAgentsService.update_agent(
            mock_session, str(sample_a2a_agent.id), payload
        )

        assert agent is not None
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()

    def test_update_agent_not_found(self, mock_session):
        """Test updating a non-existent agent"""
        mock_result = MagicMock()
        mock_result.first.return_value = None
        mock_session.exec.return_value = mock_result

        payload = A2AAgentUpdate(description="Updated")

        with pytest.raises(ValueError, match="not found"):
            A2AAgentsService.update_agent(mock_session, str(uuid.uuid4()), payload)

    def test_delete_agent_success(self, mock_session, sample_a2a_agent):
        """Test deleting an agent"""
        mock_result = MagicMock()
        mock_result.first.return_value = sample_a2a_agent
        mock_session.exec.return_value = mock_result

        result = A2AAgentsService.delete_agent(mock_session, str(sample_a2a_agent.id))

        assert result is True
        mock_session.delete.assert_called_once_with(sample_a2a_agent)
        mock_session.commit.assert_called_once()

    def test_delete_agent_not_found(self, mock_session):
        """Test deleting a non-existent agent"""
        mock_result = MagicMock()
        mock_result.first.return_value = None
        mock_session.exec.return_value = mock_result

        result = A2AAgentsService.delete_agent(mock_session, str(uuid.uuid4()))

        assert result is False
        mock_session.delete.assert_not_called()


class TestA2AAgentCardManagement:
    """Tests for Agent Card management operations"""

    def test_update_agent_card_success(self, mock_session, sample_a2a_agent):
        """Test updating cached Agent Card data"""
        mock_result = MagicMock()
        mock_result.first.return_value = sample_a2a_agent
        mock_session.exec.return_value = mock_result

        agent_card = {
            "name": "Test Agent",
            "protocolVersion": "1.0",
            "skills": [{"id": "skill-1", "name": "Test Skill"}],
            "capabilities": {
                "inputModes": ["text"],
                "outputModes": ["text", "file"],
            },
        }

        agent = A2AAgentsService.update_agent_card(
            mock_session, str(sample_a2a_agent.id), agent_card
        )

        assert agent is not None
        assert agent.agent_card == agent_card
        assert agent.protocol_version == "1.0"
        assert agent.skills == [{"id": "skill-1", "name": "Test Skill"}]
        assert agent.supported_input_modes == ["text"]
        assert agent.supported_output_modes == ["text", "file"]
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()

    def test_update_agent_card_not_found(self, mock_session):
        """Test updating Agent Card for non-existent agent"""
        mock_result = MagicMock()
        mock_result.first.return_value = None
        mock_session.exec.return_value = mock_result

        with pytest.raises(ValueError, match="not found"):
            A2AAgentsService.update_agent_card(mock_session, str(uuid.uuid4()), {})


class TestA2AHealthCheckManagement:
    """Tests for health check management operations"""

    def test_update_health_status_healthy(self, mock_session, sample_a2a_agent):
        """Test updating health status when agent is healthy"""
        sample_a2a_agent.consecutive_failures = 2
        sample_a2a_agent.status = "error"

        mock_result = MagicMock()
        mock_result.first.return_value = sample_a2a_agent
        mock_session.exec.return_value = mock_result

        agent = A2AAgentsService.update_health_status(
            mock_session, str(sample_a2a_agent.id), is_healthy=True
        )

        assert agent.status == "active"
        assert agent.consecutive_failures == 0
        assert agent.last_health_check is not None
        assert agent.last_seen is not None

    def test_update_health_status_unhealthy_first_failure(
        self, mock_session, sample_a2a_agent
    ):
        """Test updating health status on first failure"""
        sample_a2a_agent.consecutive_failures = 0
        sample_a2a_agent.status = "active"

        mock_result = MagicMock()
        mock_result.first.return_value = sample_a2a_agent
        mock_session.exec.return_value = mock_result

        agent = A2AAgentsService.update_health_status(
            mock_session, str(sample_a2a_agent.id), is_healthy=False
        )

        assert agent.status == "error"
        assert agent.consecutive_failures == 1

    def test_update_health_status_unhealthy_becomes_unreachable(
        self, mock_session, sample_a2a_agent
    ):
        """Test agent becomes unreachable after 3 consecutive failures"""
        sample_a2a_agent.consecutive_failures = 2
        sample_a2a_agent.status = "error"

        mock_result = MagicMock()
        mock_result.first.return_value = sample_a2a_agent
        mock_session.exec.return_value = mock_result

        agent = A2AAgentsService.update_health_status(
            mock_session, str(sample_a2a_agent.id), is_healthy=False
        )

        assert agent.status == "unreachable"
        assert agent.consecutive_failures == 3

    def test_get_agents_needing_health_check_never_checked(
        self, mock_session, sample_a2a_agent
    ):
        """Test getting agents that have never been health checked"""
        sample_a2a_agent.last_health_check = None

        mock_result = MagicMock()
        mock_result.all.return_value = [sample_a2a_agent]
        mock_session.exec.return_value = mock_result

        agents = A2AAgentsService.get_agents_needing_health_check(mock_session)

        assert len(agents) == 1
        assert agents[0].id == sample_a2a_agent.id

    def test_get_agents_needing_health_check_overdue(
        self, mock_session, sample_a2a_agent
    ):
        """Test getting agents that are overdue for health check"""
        sample_a2a_agent.health_check_interval = 300  # 5 minutes
        sample_a2a_agent.last_health_check = datetime.now(timezone.utc) - timedelta(
            minutes=10
        )

        mock_result = MagicMock()
        mock_result.all.return_value = [sample_a2a_agent]
        mock_session.exec.return_value = mock_result

        agents = A2AAgentsService.get_agents_needing_health_check(mock_session)

        assert len(agents) == 1

    def test_get_agents_needing_health_check_recently_checked(
        self, mock_session, sample_a2a_agent
    ):
        """Test agents recently checked are not included"""
        sample_a2a_agent.health_check_interval = 300  # 5 minutes
        sample_a2a_agent.last_health_check = datetime.now(timezone.utc) - timedelta(
            minutes=1
        )

        mock_result = MagicMock()
        mock_result.all.return_value = [sample_a2a_agent]
        mock_session.exec.return_value = mock_result

        agents = A2AAgentsService.get_agents_needing_health_check(mock_session)

        assert len(agents) == 0

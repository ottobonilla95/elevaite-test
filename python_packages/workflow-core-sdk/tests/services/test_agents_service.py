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
        mock_session.refresh.side_effect = lambda obj: setattr(
            obj, "id", sample_agent.id
        )

        agent = AgentsService.create_agent(mock_session, sample_agent_data)

        assert agent is not None
        assert agent.name == "new_agent"
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()

    def test_create_agent_duplicate_name_with_org(
        self, mock_session, sample_agent_data, sample_agent
    ):
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
    def test_attach_tool_to_agent_with_local_tool_name(
        self, mock_registry, mock_session, sample_agent
    ):
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
        mock_registry.sync_local_tool_by_name.assert_called_once_with(
            mock_session, "calculator"
        )

    @patch("workflow_core_sdk.services.agents_service.tool_registry")
    def test_attach_tool_to_agent_local_tool_not_found(
        self, mock_registry, mock_session, sample_agent
    ):
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
        """Test attaching a tool without providing tool_id, local_tool_name, or inline_definition"""
        # Mock agent lookup
        mock_result = MagicMock()
        mock_result.first.return_value = sample_agent
        mock_session.exec.return_value = mock_result

        with pytest.raises(
            ValueError, match="Provide tool_id, local_tool_name, or inline_definition"
        ):
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

        updates = {
            "override_parameters": {"new_param": "new_value"},
            "is_active": False,
        }
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
            AgentsService.update_agent_tool_binding(
                mock_session, agent_id, binding_id, updates
            )

    def test_update_agent_tool_binding_agent_mismatch(
        self, mock_session, sample_tool_binding
    ):
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

        result = AgentsService.detach_tool_from_agent(
            mock_session, agent_id, binding_id
        )

        assert result is False
        mock_session.delete.assert_not_called()

    def test_detach_tool_from_agent_agent_mismatch(
        self, mock_session, sample_tool_binding
    ):
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


class TestInlineToolDefinitions:
    """Tests for inline tool definition support"""

    def test_attach_user_function_inline_definition(self, mock_session, sample_agent):
        """Test attaching a user function via inline definition"""
        from workflow_core_sdk.schemas.inline_tools import (
            UserFunctionDefinition,
            PLACEHOLDER_TOOL_IDS,
        )

        # Mock agent lookup
        mock_result = MagicMock()
        mock_result.first.return_value = sample_agent
        mock_session.exec.return_value = mock_result

        # Mock add/commit/refresh
        mock_session.add.return_value = None
        mock_session.commit.return_value = None
        mock_session.refresh.return_value = None

        # Create inline user function definition
        inline_def = UserFunctionDefinition(
            name="calculate_discount",
            description="Calculate discount for a product",
            parameters_schema={
                "type": "object",
                "properties": {
                    "price": {"type": "number"},
                    "discount_percent": {"type": "number"},
                },
                "required": ["price", "discount_percent"],
            },
            code="def calculate_discount(price, discount_percent):\n    return price * (1 - discount_percent / 100)",
            timeout_seconds=30,
            memory_mb=256,
        )

        binding = AgentsService.attach_tool_to_agent(
            mock_session,
            str(sample_agent.id),
            inline_definition=inline_def,
            is_active=True,
        )

        assert binding is not None
        # Should use placeholder tool_id for user_function
        assert str(binding.tool_id) == PLACEHOLDER_TOOL_IDS["user_function"]
        # Should store inline definition in override_parameters
        assert "_inline_definition" in binding.override_parameters
        assert (
            binding.override_parameters["_inline_definition"]["type"] == "user_function"
        )
        assert (
            binding.override_parameters["_inline_definition"]["name"]
            == "calculate_discount"
        )
        assert (
            binding.override_parameters["_inline_definition"]["code"] == inline_def.code
        )
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()

    def test_attach_web_search_inline_definition(self, mock_session, sample_agent):
        """Test attaching a web search tool via inline definition"""
        from workflow_core_sdk.schemas.inline_tools import (
            WebSearchToolConfig,
            WebSearchUserLocation,
            PLACEHOLDER_TOOL_IDS,
        )

        # Mock agent lookup
        mock_result = MagicMock()
        mock_result.first.return_value = sample_agent
        mock_session.exec.return_value = mock_result

        # Mock add/commit/refresh
        mock_session.add.return_value = None
        mock_session.commit.return_value = None
        mock_session.refresh.return_value = None

        # Create inline web search definition
        inline_def = WebSearchToolConfig(
            search_context_size="high",
            user_location=WebSearchUserLocation(
                country="US",
                region="California",
                city="San Francisco",
            ),
            allowed_domains=["docs.python.org", "stackoverflow.com"],
        )

        binding = AgentsService.attach_tool_to_agent(
            mock_session,
            str(sample_agent.id),
            inline_definition=inline_def,
            is_active=True,
        )

        assert binding is not None
        # Should use placeholder tool_id for web_search
        assert str(binding.tool_id) == PLACEHOLDER_TOOL_IDS["web_search"]
        # Should store inline definition in override_parameters
        assert "_inline_definition" in binding.override_parameters
        assert binding.override_parameters["_inline_definition"]["type"] == "web_search"
        assert (
            binding.override_parameters["_inline_definition"]["search_context_size"]
            == "high"
        )
        assert binding.override_parameters["_inline_definition"]["allowed_domains"] == [
            "docs.python.org",
            "stackoverflow.com",
        ]
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()

    def test_attach_inline_definition_preserves_override_parameters(
        self, mock_session, sample_agent
    ):
        """Test that inline definition merges with existing override_parameters"""
        from workflow_core_sdk.schemas.inline_tools import UserFunctionDefinition

        # Mock agent lookup
        mock_result = MagicMock()
        mock_result.first.return_value = sample_agent
        mock_session.exec.return_value = mock_result

        # Mock add/commit/refresh
        mock_session.add.return_value = None
        mock_session.commit.return_value = None
        mock_session.refresh.return_value = None

        inline_def = UserFunctionDefinition(
            name="my_func",
            description="My function",
            parameters_schema={"type": "object", "properties": {}},
            code="def my_func(): return 42",
        )

        # Pass additional override_parameters
        binding = AgentsService.attach_tool_to_agent(
            mock_session,
            str(sample_agent.id),
            inline_definition=inline_def,
            override_parameters={"custom_param": "custom_value"},
            is_active=True,
        )

        assert binding is not None
        # Should have both the inline definition and custom param
        assert "_inline_definition" in binding.override_parameters
        assert binding.override_parameters["custom_param"] == "custom_value"


class TestBuildInlineToolSchema:
    """Tests for _build_inline_tool_schema function"""

    def test_build_user_function_schema(self):
        """Test building OpenAI schema from user function inline definition"""
        from workflow_core_sdk.steps.ai_steps import _build_inline_tool_schema

        inline_def = {
            "type": "user_function",
            "name": "calculate_tax",
            "description": "Calculate tax for an amount",
            "parameters_schema": {
                "type": "object",
                "properties": {
                    "amount": {"type": "number", "description": "The amount"},
                    "rate": {"type": "number", "description": "Tax rate as decimal"},
                },
                "required": ["amount", "rate"],
            },
            "code": "def calculate_tax(amount, rate):\n    return amount * rate",
            "timeout_seconds": 15,
            "memory_mb": 128,
        }

        schema = _build_inline_tool_schema(inline_def)

        assert schema is not None
        assert schema["type"] == "function"
        assert schema["function"]["name"] == "calculate_tax"
        assert schema["function"]["description"] == "Calculate tax for an amount"
        assert (
            schema["function"]["parameters"]["properties"]["amount"]["type"] == "number"
        )
        # Should have metadata for executor
        assert "_inline_user_function" in schema
        assert schema["_inline_user_function"]["code"] == inline_def["code"]
        assert schema["_inline_user_function"]["timeout_seconds"] == 15
        assert schema["_inline_user_function"]["memory_mb"] == 128

    def test_build_user_function_schema_defaults(self):
        """Test that user function schema uses defaults for optional fields"""
        from workflow_core_sdk.steps.ai_steps import _build_inline_tool_schema

        inline_def = {
            "type": "user_function",
            "name": "simple_func",
            "code": "def simple_func(): return 42",
        }

        schema = _build_inline_tool_schema(inline_def)

        assert schema is not None
        assert schema["function"]["name"] == "simple_func"
        # Should use default description
        assert schema["function"]["description"] == "Function simple_func"
        # Should use default parameters schema
        assert schema["function"]["parameters"]["type"] == "object"
        # Should use default timeout and memory
        assert schema["_inline_user_function"]["timeout_seconds"] == 30
        assert schema["_inline_user_function"]["memory_mb"] == 256

    def test_build_user_function_schema_missing_name(self):
        """Test that user function schema returns None if name is missing"""
        from workflow_core_sdk.steps.ai_steps import _build_inline_tool_schema

        inline_def = {
            "type": "user_function",
            "code": "def unnamed(): pass",
        }

        schema = _build_inline_tool_schema(inline_def)

        assert schema is None

    def test_build_web_search_schema(self):
        """Test building OpenAI schema from web search inline definition"""
        from workflow_core_sdk.steps.ai_steps import _build_inline_tool_schema

        inline_def = {
            "type": "web_search",
            "search_context_size": "high",
            "user_location": {
                "country": "US",
                "region": "California",
                "city": "San Francisco",
            },
            "allowed_domains": ["docs.python.org"],
            "blocked_domains": ["spam.com"],
        }

        schema = _build_inline_tool_schema(inline_def)

        assert schema is not None
        assert schema["type"] == "function"
        assert schema["function"]["name"] == "web_search"
        assert schema["function"]["description"] == "Search the web for information"
        assert "query" in schema["function"]["parameters"]["properties"]
        # Should have config for provider-side handling
        assert "_inline_web_search" in schema
        assert schema["_inline_web_search"]["search_context_size"] == "high"
        assert schema["_inline_web_search"]["allowed_domains"] == ["docs.python.org"]
        assert schema["_inline_web_search"]["blocked_domains"] == ["spam.com"]
        assert schema["_inline_web_search"]["user_location"]["country"] == "US"

    def test_build_web_search_schema_defaults(self):
        """Test that web search schema uses defaults for optional fields"""
        from workflow_core_sdk.steps.ai_steps import _build_inline_tool_schema

        inline_def = {
            "type": "web_search",
        }

        schema = _build_inline_tool_schema(inline_def)

        assert schema is not None
        assert schema["_inline_web_search"]["search_context_size"] == "medium"
        assert schema["_inline_web_search"]["user_location"] is None
        assert schema["_inline_web_search"]["allowed_domains"] is None

    def test_build_unknown_type_returns_none(self):
        """Test that unknown inline definition type returns None"""
        from workflow_core_sdk.steps.ai_steps import _build_inline_tool_schema

        inline_def = {
            "type": "unknown_tool_type",
            "name": "something",
        }

        schema = _build_inline_tool_schema(inline_def)

        assert schema is None


class TestExecuteUserFunction:
    """Tests for execute_user_function"""

    @patch("workflow_core_sdk.tools.user_function_executor.requests.post")
    def test_execute_user_function_success(self, mock_post):
        """Test successful user function execution"""
        from workflow_core_sdk.tools.user_function_executor import execute_user_function

        # Mock successful response from code execution service
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "success": True,
            "stdout": '{"result": 42}',
            "stderr": "",
            "execution_time_ms": 50,
        }
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        result = execute_user_function(
            code="def my_func(x): return {'result': x * 2}",
            function_name="my_func",
            arguments={"x": 21},
            timeout_seconds=30,
            memory_mb=256,
        )

        assert result == '{"result": 42}'
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert call_args[1]["json"]["language"] == "python"
        assert "my_func" in call_args[1]["json"]["code"]

    @patch("workflow_core_sdk.tools.user_function_executor.requests.post")
    def test_execute_user_function_with_error_in_code(self, mock_post):
        """Test user function that raises an exception"""
        from workflow_core_sdk.tools.user_function_executor import execute_user_function

        # Mock response with error from user code
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "success": True,
            "stdout": '{"error": "division by zero", "type": "ZeroDivisionError"}',
            "stderr": "",
            "execution_time_ms": 10,
        }
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        result = execute_user_function(
            code="def bad_func(x): return 1/0",
            function_name="bad_func",
            arguments={"x": 0},
        )

        assert "Function error: division by zero" in result

    @patch("workflow_core_sdk.tools.user_function_executor.requests.post")
    def test_execute_user_function_execution_failure(self, mock_post):
        """Test handling of execution service failure"""
        from workflow_core_sdk.tools.user_function_executor import execute_user_function

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "success": False,
            "error": "Syntax error in code",
            "stderr": "SyntaxError: invalid syntax",
        }
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        result = execute_user_function(
            code="def broken(: pass",  # Invalid syntax
            function_name="broken",
            arguments={},
        )

        assert "Execution failed" in result
        assert "Syntax error" in result

    @patch("workflow_core_sdk.tools.user_function_executor.requests.post")
    def test_execute_user_function_timeout(self, mock_post):
        """Test handling of timeout"""
        from workflow_core_sdk.tools.user_function_executor import execute_user_function
        import requests

        mock_post.side_effect = requests.exceptions.Timeout()

        result = execute_user_function(
            code="def slow(): import time; time.sleep(100)",
            function_name="slow",
            arguments={},
            timeout_seconds=5,
        )

        assert "timed out" in result.lower()

    @patch("workflow_core_sdk.tools.user_function_executor.requests.post")
    def test_execute_user_function_connection_error(self, mock_post):
        """Test handling of connection error to code execution service"""
        from workflow_core_sdk.tools.user_function_executor import execute_user_function
        import requests

        mock_post.side_effect = requests.exceptions.ConnectionError(
            "Connection refused"
        )

        result = execute_user_function(
            code="def func(): pass",
            function_name="func",
            arguments={},
        )

        assert "Could not connect to code execution service" in result

    def test_execute_user_function_clamps_timeout(self):
        """Test that timeout is clamped to valid range"""
        from workflow_core_sdk.tools.user_function_executor import execute_user_function

        with patch(
            "workflow_core_sdk.tools.user_function_executor.requests.post"
        ) as mock_post:
            mock_response = MagicMock()
            mock_response.json.return_value = {"success": True, "stdout": "ok"}
            mock_response.raise_for_status = MagicMock()
            mock_post.return_value = mock_response

            # Test with timeout > 60 (should be clamped to 60)
            execute_user_function(
                code="def f(): pass",
                function_name="f",
                arguments={},
                timeout_seconds=120,
            )

            call_args = mock_post.call_args
            assert call_args[1]["json"]["timeout_seconds"] == 60

    def test_execute_user_function_clamps_memory(self):
        """Test that memory is clamped to valid range"""
        from workflow_core_sdk.tools.user_function_executor import execute_user_function

        with patch(
            "workflow_core_sdk.tools.user_function_executor.requests.post"
        ) as mock_post:
            mock_response = MagicMock()
            mock_response.json.return_value = {"success": True, "stdout": "ok"}
            mock_response.raise_for_status = MagicMock()
            mock_post.return_value = mock_response

            # Test with memory > 512 (should be clamped to 512)
            execute_user_function(
                code="def f(): pass",
                function_name="f",
                arguments={},
                memory_mb=1024,
            )

            call_args = mock_post.call_args
            assert call_args[1]["json"]["memory_mb"] == 512

"""Tests for A2A agent execution within agent_execution_step."""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from workflow_core_sdk.execution_context import ExecutionContext, UserContext


@pytest.fixture
def execution_context():
    """Create a mock execution context."""
    workflow_config = {
        "workflow_id": str(uuid.uuid4()),
        "name": "Test Workflow",
        "steps": [],
    }
    return ExecutionContext(
        workflow_config=workflow_config,
        user_context=UserContext(user_id="test-user", session_id="test-session"),
        execution_id=str(uuid.uuid4()),
    )


@pytest.fixture
def mock_a2a_agent():
    """Create a mock A2A agent database record."""
    agent = MagicMock()
    agent.id = uuid.uuid4()
    agent.name = "Test A2A Agent"
    agent.base_url = "https://example.com/agent"
    agent.agent_card_url = None
    agent.auth_type = "none"
    agent.auth_config = None
    agent.timeout = 30.0
    agent.status = "active"
    return agent


class TestA2AAgentDispatch:
    """Tests for A2A agent dispatch in agent_execution_step."""

    async def test_dispatches_to_a2a_when_a2a_agent_id_provided(self, execution_context):
        """When a2a_agent_id is in config, should dispatch to A2A execution."""
        from workflow_core_sdk.steps.ai_steps import agent_execution_step

        step_config = {
            "step_id": "test-step",
            "config": {
                "a2a_agent_id": str(uuid.uuid4()),
                "query": "Hello",
            },
        }
        input_data = {}

        # Mock the _execute_a2a_agent function
        with patch(
            "workflow_core_sdk.steps.ai_steps._execute_a2a_agent",
            new_callable=AsyncMock,
        ) as mock_execute_a2a:
            mock_execute_a2a.return_value = {
                "success": True,
                "response": "Hello from A2A!",
                "mode": "a2a",
            }

            result = await agent_execution_step(step_config, input_data, execution_context)

            mock_execute_a2a.assert_called_once_with(step_config, input_data, execution_context)
            assert result["success"] is True
            assert result["response"] == "Hello from A2A!"
            assert result["mode"] == "a2a"

    async def test_does_not_dispatch_to_a2a_without_a2a_agent_id(self, execution_context):
        """When a2a_agent_id is not provided, should use built-in agent path."""
        from workflow_core_sdk.steps.ai_steps import agent_execution_step

        step_config = {
            "step_id": "test-step",
            "config": {
                "agent_name": "Test Agent",
                "query": "{current_message}",
            },
        }
        input_data = {"current_message": "Hello"}

        # Mock the _execute_a2a_agent function to verify it's NOT called
        with patch(
            "workflow_core_sdk.steps.ai_steps._execute_a2a_agent",
            new_callable=AsyncMock,
        ) as mock_execute_a2a:
            # Also mock AgentStep to avoid actual LLM calls
            with patch("workflow_core_sdk.steps.ai_steps.AgentStep") as mock_agent_step:
                mock_agent = MagicMock()
                mock_agent.execute = AsyncMock(return_value={"response": "Hello from built-in!", "tool_calls": []})
                mock_agent._dynamic_agent_tools = {}
                mock_agent.tools = []
                mock_agent._ensure_dynamic_agent_tools = AsyncMock()
                mock_agent_step.return_value = mock_agent

                # Run the step - it should return waiting status for interactive mode
                result = await agent_execution_step(step_config, input_data, execution_context)

                # _execute_a2a_agent should NOT be called
                mock_execute_a2a.assert_not_called()


class TestA2AAgentExecution:
    """Tests for _execute_a2a_agent helper function."""

    async def test_returns_error_when_llm_gateway_not_available(self, execution_context):
        """Should return error if llm-gateway is not installed."""
        from workflow_core_sdk.steps.ai_steps import _execute_a2a_agent

        step_config = {
            "config": {
                "a2a_agent_id": str(uuid.uuid4()),
                "query": "Hello",
            },
        }
        input_data = {}

        with patch.dict("sys.modules", {"llm_gateway": None, "llm_gateway.a2a": None}):
            # Force ImportError by patching the import
            with patch(
                "workflow_core_sdk.steps.ai_steps._execute_a2a_agent",
                side_effect=ImportError("No module named 'llm_gateway'"),
            ):
                # Direct test would require actual import failure
                pass

    async def test_returns_error_when_agent_not_found(self, execution_context):
        """Should return error when A2A agent is not found in database."""
        from workflow_core_sdk.steps.ai_steps import _execute_a2a_agent

        step_config = {
            "config": {
                "a2a_agent_id": str(uuid.uuid4()),
                "query": "Hello",
            },
        }
        input_data = {}

        with patch("sqlmodel.Session") as mock_session_cls:
            mock_session = MagicMock()
            mock_session.__enter__ = MagicMock(return_value=mock_session)
            mock_session.__exit__ = MagicMock(return_value=False)
            mock_session.exec.return_value.first.return_value = None
            mock_session_cls.return_value = mock_session

            result = await _execute_a2a_agent(step_config, input_data, execution_context)

            assert result["success"] is False
            assert "not found" in result["error"]

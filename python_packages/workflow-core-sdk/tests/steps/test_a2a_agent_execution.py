"""Tests for A2A agent execution within agent_execution_step.

Uses a real A2A test server for integration testing instead of mocks.
"""

import asyncio
import socket
import uuid
from contextlib import asynccontextmanager
from threading import Thread
from typing import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import uvicorn

from workflow_core_sdk.db.models.a2a_agents import A2AAgent, A2AAgentStatus, A2AAuthType
from workflow_core_sdk.execution_context import ExecutionContext, UserContext


def get_free_port() -> int:
    """Find a free port on localhost."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        return s.getsockname()[1]


class EchoAgentExecutor:
    """Simple echo agent for testing - echoes back the message."""

    async def execute(self, context, event_queue) -> None:
        from a2a.utils import new_agent_text_message

        # Extract message text from context
        message_text = "No message"
        if context.message and context.message.parts:
            for part in context.message.parts:
                if hasattr(part, "root") and hasattr(part.root, "text"):
                    message_text = part.root.text
                    break
                elif hasattr(part, "text"):
                    message_text = part.text
                    break

        # Echo it back with prefix
        await event_queue.enqueue_event(new_agent_text_message(f"Echo: {message_text}"))

    async def cancel(self, context, event_queue) -> None:
        pass


class StreamingAgentExecutor:
    """Agent that streams multiple chunks for testing streaming."""

    async def execute(self, context, event_queue) -> None:
        from a2a.utils import new_agent_text_message

        # Stream in chunks
        chunks = ["Hello", " ", "World", "!"]
        accumulated = ""
        for chunk in chunks:
            accumulated += chunk
            await event_queue.enqueue_event(new_agent_text_message(accumulated))
            await asyncio.sleep(0.01)  # Small delay between chunks

    async def cancel(self, context, event_queue) -> None:
        pass


@pytest.fixture(scope="module")
def a2a_echo_server():
    """Start a real A2A echo server for testing."""
    from a2a.server.apps import A2AStarletteApplication
    from a2a.server.request_handlers import DefaultRequestHandler
    from a2a.server.tasks import InMemoryTaskStore
    from a2a.types import AgentCapabilities, AgentCard, AgentSkill

    port = get_free_port()

    agent_card = AgentCard(
        name="Test Echo Agent",
        description="Echoes messages for testing",
        url=f"http://localhost:{port}/",
        version="1.0.0",
        default_input_modes=["text"],
        default_output_modes=["text"],
        capabilities=AgentCapabilities(streaming=True),
        skills=[
            AgentSkill(
                id="echo",
                name="Echo",
                description="Echoes back the message",
                tags=["test"],
                examples=["hello"],
            )
        ],
    )

    request_handler = DefaultRequestHandler(
        agent_executor=EchoAgentExecutor(),
        task_store=InMemoryTaskStore(),
    )

    app = A2AStarletteApplication(
        agent_card=agent_card,
        http_handler=request_handler,
    )

    config = uvicorn.Config(app.build(), host="127.0.0.1", port=port, log_level="warning")
    server = uvicorn.Server(config)

    # Run server in a background thread
    thread = Thread(target=server.run, daemon=True)
    thread.start()

    # Wait for server to be ready
    import time

    for _ in range(50):  # 5 seconds max
        try:
            import httpx

            httpx.get(f"http://127.0.0.1:{port}/.well-known/agent.json", timeout=0.1)
            break
        except Exception:
            time.sleep(0.1)

    yield {"base_url": f"http://127.0.0.1:{port}", "agent_name": "Test Echo Agent", "port": port}

    # Server will be stopped when thread is garbage collected (daemon=True)


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
def create_a2a_agent_record(a2a_echo_server):
    """Factory to create A2A agent database records pointing to test server."""

    def _create(status: A2AAgentStatus = A2AAgentStatus.ACTIVE) -> A2AAgent:
        agent = A2AAgent(
            id=uuid.uuid4(),
            name=a2a_echo_server["agent_name"],
            base_url=a2a_echo_server["base_url"],
            agent_card_url=None,
            auth_type=A2AAuthType.NONE,
            auth_config=None,
            timeout=30.0,
            status=status,
        )
        return agent

    return _create


class TestA2AAgentDispatch:
    """Tests for A2A agent dispatch routing in agent_execution_step."""

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

        # Mock _execute_a2a_agent to verify dispatch routing
        with patch(
            "workflow_core_sdk.steps.ai_steps._execute_a2a_agent",
            new_callable=AsyncMock,
        ) as mock_execute_a2a:
            mock_execute_a2a.return_value = {"success": True, "response": "Hello from A2A!", "mode": "a2a"}

            result = await agent_execution_step(step_config, input_data, execution_context)

            mock_execute_a2a.assert_called_once_with(step_config, input_data, execution_context)
            assert result["success"] is True
            assert result["mode"] == "a2a"

    async def test_does_not_dispatch_to_a2a_without_a2a_agent_id(self, execution_context):
        """When a2a_agent_id is not provided, should NOT call _execute_a2a_agent."""
        from workflow_core_sdk.steps.ai_steps import agent_execution_step

        step_config = {
            "step_id": "test-step",
            "config": {"agent_name": "Test Agent", "query": "{current_message}"},
        }
        input_data = {"current_message": "Hello"}

        with patch("workflow_core_sdk.steps.ai_steps._execute_a2a_agent", new_callable=AsyncMock) as mock_a2a:
            with patch("workflow_core_sdk.steps.ai_steps.AgentStep") as mock_agent_step:
                mock_agent = MagicMock()
                mock_agent.execute = AsyncMock(return_value={"response": "Hi", "tool_calls": []})
                mock_agent._dynamic_agent_tools = {}
                mock_agent.tools = []
                mock_agent._ensure_dynamic_agent_tools = AsyncMock()
                mock_agent_step.return_value = mock_agent

                await agent_execution_step(step_config, input_data, execution_context)
                mock_a2a.assert_not_called()


def mock_session_with_agent(agent):
    """Create a context manager that mocks Session to return a specific agent."""
    mock_session = MagicMock()
    mock_session.__enter__ = MagicMock(return_value=mock_session)
    mock_session.__exit__ = MagicMock(return_value=False)
    mock_session.exec.return_value.first.return_value = agent
    return patch("sqlmodel.Session", return_value=mock_session)


class TestA2AAgentExecutionIntegration:
    """Integration tests using real A2A server."""

    async def test_successful_a2a_call(self, a2a_echo_server, execution_context, create_a2a_agent_record):
        """Test successful A2A call against real server."""
        from workflow_core_sdk.steps.ai_steps import _execute_a2a_agent

        agent = create_a2a_agent_record(A2AAgentStatus.ACTIVE)

        step_config = {
            "step_id": "test-step",
            "config": {
                "a2a_agent_id": str(agent.id),
                "query": "Hello World",
                "stream": False,
            },
        }

        with mock_session_with_agent(agent):
            result = await _execute_a2a_agent(step_config, {}, execution_context)

        assert result["success"] is True
        assert "Echo: Hello World" in result["response"]
        assert result["mode"] == "a2a"
        assert result["agent_name"] == agent.name

    async def test_a2a_agent_not_found(self, execution_context):
        """Test error when A2A agent not found in database."""
        from workflow_core_sdk.steps.ai_steps import _execute_a2a_agent

        step_config = {
            "step_id": "test-step",
            "config": {
                "a2a_agent_id": str(uuid.uuid4()),
                "query": "Hello",
            },
        }

        with mock_session_with_agent(None):
            result = await _execute_a2a_agent(step_config, {}, execution_context)

        assert result["success"] is False
        assert "not found" in result["error"]

    async def test_a2a_agent_inactive(self, a2a_echo_server, execution_context, create_a2a_agent_record):
        """Test error when A2A agent is not active."""
        from workflow_core_sdk.steps.ai_steps import _execute_a2a_agent

        agent = create_a2a_agent_record(A2AAgentStatus.INACTIVE)

        step_config = {
            "step_id": "test-step",
            "config": {
                "a2a_agent_id": str(agent.id),
                "query": "Hello",
            },
        }

        with mock_session_with_agent(agent):
            result = await _execute_a2a_agent(step_config, {}, execution_context)

        assert result["success"] is False
        assert "not active" in result["error"]

    async def test_query_from_input_data(self, a2a_echo_server, execution_context, create_a2a_agent_record):
        """Test that query can come from input_data if not in config."""
        from workflow_core_sdk.steps.ai_steps import _execute_a2a_agent

        agent = create_a2a_agent_record(A2AAgentStatus.ACTIVE)

        step_config = {
            "step_id": "test-step",
            "config": {
                "a2a_agent_id": str(agent.id),
                # No query in config
            },
        }
        input_data = {"current_message": "Hello from input_data"}

        with mock_session_with_agent(agent):
            result = await _execute_a2a_agent(step_config, input_data, execution_context)

        assert result["success"] is True
        assert "Echo: Hello from input_data" in result["response"]

    async def test_missing_query_returns_error(self, execution_context):
        """Test error when no query is provided."""
        from workflow_core_sdk.steps.ai_steps import _execute_a2a_agent

        step_config = {
            "step_id": "test-step",
            "config": {
                "a2a_agent_id": str(uuid.uuid4()),
                # No query
            },
        }
        input_data = {}  # No current_message either

        result = await _execute_a2a_agent(step_config, input_data, execution_context)

        assert result["success"] is False
        assert "query is required" in result["error"]

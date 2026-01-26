"""
Tests for MCP tool execution in tool_execution_step.

Tests the integration of MCP client with tool execution step.
"""

import pytest
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

from workflow_core_sdk.steps.tool_steps import tool_execution_step
from workflow_core_sdk.execution_context import ExecutionContext
from workflow_core_sdk.db.models import Tool as DBTool, MCPServer


@pytest.fixture
def execution_context():
    """Create a mock execution context."""
    context = ExecutionContext(
        workflow_config={"workflow_id": str(uuid.uuid4())},
        user_context={"user_id": "test-user"},
        execution_id=str(uuid.uuid4()),
    )
    context.workflow_id = str(uuid.uuid4())
    return context


@pytest.fixture
def mcp_tool_record():
    """Create a mock MCP tool database record."""
    tool = MagicMock(spec=DBTool)
    tool.id = uuid.uuid4()
    tool.name = "test_mcp_tool"
    tool.description = "A test MCP tool"
    tool.tool_type = "mcp"
    tool.execution_type = "api"
    tool.mcp_server_id = uuid.uuid4()
    tool.remote_name = "remote_test_tool"
    tool.parameters_schema = {
        "type": "object",
        "properties": {
            "input": {"type": "string"},
            "count": {"type": "integer"},
        },
    }
    tool.return_schema = None
    tool.version = "1.0.0"
    return tool


@pytest.fixture
def mcp_server():
    """Create a mock MCP server database record."""
    server = MagicMock(spec=MCPServer)
    server.id = uuid.uuid4()
    server.name = "test-mcp-server"
    server.host = "localhost"
    server.port = 8080
    server.protocol = "http"
    server.endpoint = "/api"
    server.auth_type = None
    server.auth_config = None
    return server


class TestMCPToolExecution:
    """Test MCP tool execution functionality."""

    @pytest.mark.asyncio
    @patch("workflow_core_sdk.steps.tool_steps.Session")
    @patch("workflow_core_sdk.steps.tool_steps.mcp_client")
    @patch("workflow_core_sdk.steps.tool_steps.stream_manager")
    async def test_execute_mcp_tool_success(
        self,
        mock_stream,
        mock_mcp_client,
        mock_session_class,
        mcp_tool_record,
        mcp_server,
        execution_context,
    ):
        """Test successful MCP tool execution."""
        mock_stream.emit_execution_event = AsyncMock()
        mock_stream.emit_workflow_event = AsyncMock()

        # Mock database session
        mock_session = MagicMock()
        mock_session_class.return_value.__enter__.return_value = mock_session
        mock_session_class.return_value.__exit__.return_value = None

        # Mock database queries
        mock_session.exec.return_value.first.side_effect = [mcp_tool_record, mcp_server]

        # Mock MCP client execution
        mock_mcp_client.execute_tool = AsyncMock(
            return_value={
                "status": "success",
                "result": "Tool executed successfully",
                "execution_time": 150,
            }
        )

        # Execute tool
        step_config = {
            "step_id": "test-step-1",
            "config": {
                "tool_id": str(mcp_tool_record.id),
                "static_params": {"input": "test input", "count": 5},
            },
        }

        result = await tool_execution_step(step_config, {}, execution_context)

        # Verify result
        assert result["success"] is True
        assert result["tool"]["name"] == "test_mcp_tool"
        assert result["tool"]["type"] == "mcp"
        assert result["tool"]["remote_name"] == "remote_test_tool"
        assert result["tool"]["server"] == "test-mcp-server"
        assert "result" in result
        assert result["params"]["input"] == "test input"
        assert result["params"]["count"] == 5

        # Verify MCP client was called correctly
        mock_mcp_client.execute_tool.assert_called_once()
        call_args = mock_mcp_client.execute_tool.call_args
        assert call_args[1]["tool_name"] == "remote_test_tool"
        assert call_args[1]["parameters"]["input"] == "test input"
        assert call_args[1]["parameters"]["count"] == 5

    @pytest.mark.asyncio
    @patch("workflow_core_sdk.steps.tool_steps.Session")
    @patch("workflow_core_sdk.steps.tool_steps.mcp_client")
    @patch("workflow_core_sdk.steps.tool_steps.stream_manager")
    async def test_execute_mcp_tool_with_param_mapping(
        self,
        mock_stream,
        mock_mcp_client,
        mock_session_class,
        mcp_tool_record,
        mcp_server,
        execution_context,
    ):
        """Test MCP tool execution with parameter mapping."""
        mock_stream.emit_execution_event = AsyncMock()
        mock_stream.emit_workflow_event = AsyncMock()

        # Mock database session
        mock_session = MagicMock()
        mock_session_class.return_value.__enter__.return_value = mock_session
        mock_session_class.return_value.__exit__.return_value = None

        # Mock database queries
        mock_session.exec.return_value.first.side_effect = [mcp_tool_record, mcp_server]

        # Mock MCP client execution
        mock_mcp_client.execute_tool = AsyncMock(
            return_value={"status": "success", "result": "Mapped execution"}
        )

        # Execute tool with parameter mapping
        step_config = {
            "step_id": "test-step-2",
            "config": {
                "tool_id": str(mcp_tool_record.id),
                "param_mapping": {"input": "user_input", "count": "iteration_count"},
                "static_params": {"count": 10},  # Will be overridden by mapping
            },
        }

        input_data = {"user_input": "mapped input", "iteration_count": 3}

        result = await tool_execution_step(step_config, input_data, execution_context)

        # Verify result
        assert result["success"] is True
        assert result["params"]["input"] == "mapped input"
        assert result["params"]["count"] == 3  # Mapped value overrides static

    @pytest.mark.asyncio
    @patch("workflow_core_sdk.steps.tool_steps.Session")
    @patch("workflow_core_sdk.steps.tool_steps.mcp_client")
    @patch("workflow_core_sdk.steps.tool_steps.stream_manager")
    async def test_execute_mcp_tool_server_not_found(
        self,
        mock_stream,
        mock_mcp_client,
        mock_session_class,
        mcp_tool_record,
        execution_context,
    ):
        """Test MCP tool execution when server is not found."""
        mock_stream.emit_execution_event = AsyncMock()
        mock_stream.emit_workflow_event = AsyncMock()

        # Mock database session
        mock_session = MagicMock()
        mock_session_class.return_value.__enter__.return_value = mock_session
        mock_session_class.return_value.__exit__.return_value = None

        # Mock database queries - tool found, server not found
        mock_session.exec.return_value.first.side_effect = [mcp_tool_record, None]

        # Execute tool
        step_config = {
            "step_id": "test-step-3",
            "config": {
                "tool_id": str(mcp_tool_record.id),
                "static_params": {"input": "test"},
            },
        }

        result = await tool_execution_step(step_config, {}, execution_context)

        # Verify error result
        assert result["success"] is False
        assert "MCP server not found" in result["error"]
        assert result["tool"]["name"] == "test_mcp_tool"

    @pytest.mark.asyncio
    @patch("workflow_core_sdk.steps.tool_steps.Session")
    @patch("workflow_core_sdk.steps.tool_steps.mcp_client")
    @patch("workflow_core_sdk.steps.tool_steps.stream_manager")
    async def test_execute_mcp_tool_execution_error(
        self,
        mock_stream,
        mock_mcp_client,
        mock_session_class,
        mcp_tool_record,
        mcp_server,
        execution_context,
    ):
        """Test MCP tool execution when tool execution fails."""
        from workflow_core_sdk.clients.mcp_client import MCPToolExecutionError

        mock_stream.emit_execution_event = AsyncMock()
        mock_stream.emit_workflow_event = AsyncMock()

        # Mock database session
        mock_session = MagicMock()
        mock_session_class.return_value.__enter__.return_value = mock_session
        mock_session_class.return_value.__exit__.return_value = None

        # Mock database queries
        mock_session.exec.return_value.first.side_effect = [mcp_tool_record, mcp_server]

        # Mock MCP client execution failure
        mock_mcp_client.execute_tool = AsyncMock(
            side_effect=MCPToolExecutionError("Tool execution failed")
        )

        # Execute tool
        step_config = {
            "step_id": "test-step-4",
            "config": {
                "tool_id": str(mcp_tool_record.id),
                "static_params": {"input": "test"},
            },
        }

        result = await tool_execution_step(step_config, {}, execution_context)

        # Verify error result
        assert result["success"] is False
        assert "MCP tool execution failed" in result["error"]
        assert result["tool"]["type"] == "mcp"

    @pytest.mark.asyncio
    @patch("workflow_core_sdk.steps.tool_steps.Session")
    @patch("workflow_core_sdk.steps.tool_steps.mcp_client")
    @patch("workflow_core_sdk.steps.tool_steps.stream_manager")
    async def test_execute_mcp_tool_server_unavailable(
        self,
        mock_stream,
        mock_mcp_client,
        mock_session_class,
        mcp_tool_record,
        mcp_server,
        execution_context,
    ):
        """Test MCP tool execution when server is unavailable."""
        from workflow_core_sdk.clients.mcp_client import MCPServerUnavailableError

        mock_stream.emit_execution_event = AsyncMock()
        mock_stream.emit_workflow_event = AsyncMock()

        # Mock database session
        mock_session = MagicMock()
        mock_session_class.return_value.__enter__.return_value = mock_session
        mock_session_class.return_value.__exit__.return_value = None

        # Mock database queries
        mock_session.exec.return_value.first.side_effect = [mcp_tool_record, mcp_server]

        # Mock MCP client server unavailable
        mock_mcp_client.execute_tool = AsyncMock(
            side_effect=MCPServerUnavailableError("Server unavailable")
        )

        # Execute tool
        step_config = {
            "step_id": "test-step-5",
            "config": {
                "tool_id": str(mcp_tool_record.id),
                "static_params": {"input": "test"},
            },
        }

        result = await tool_execution_step(step_config, {}, execution_context)

        # Verify error result
        assert result["success"] is False
        assert "MCP server unavailable" in result["error"]

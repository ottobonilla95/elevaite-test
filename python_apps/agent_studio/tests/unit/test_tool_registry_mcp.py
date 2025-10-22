"""
Unit tests for Tool Registry MCP functionality.

Tests the enhanced tool registry with MCP tool execution capabilities.
"""

import pytest
import uuid
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from services.tool_registry import ToolRegistry
from db import models, schemas


@pytest.fixture
def mock_db_session():
    """Create a mock database session."""
    return MagicMock()


@pytest.fixture
def mock_mcp_tool():
    """Create a mock MCP tool model."""
    tool = MagicMock(spec=models.Tool)
    tool.tool_id = uuid.uuid4()
    tool.name = "test_mcp_tool"
    tool.tool_type = "mcp"
    tool.remote_name = "remote_test_tool"
    tool.mcp_server_id = uuid.uuid4()
    tool.is_active = True
    tool.is_available = True
    return tool


@pytest.fixture
def mock_local_tool():
    """Create a mock local tool model."""
    tool = MagicMock(spec=models.Tool)
    tool.tool_id = uuid.uuid4()
    tool.name = "test_local_tool"
    tool.tool_type = "local"
    tool.remote_name = None
    tool.mcp_server_id = None
    tool.is_active = True
    tool.is_available = True
    return tool


@pytest.fixture
def mock_mcp_server():
    """Create a mock MCP server model."""
    server = MagicMock(spec=models.MCPServer)
    server.server_id = uuid.uuid4()
    server.name = "test-server"
    server.status = "active"
    return server


@pytest.fixture
def tool_registry():
    """Create a tool registry instance."""
    return ToolRegistry()


class TestToolRegistryMCP:
    """Test tool registry MCP functionality."""

    @pytest.mark.asyncio
    async def test_execute_local_tool(self, tool_registry, mock_local_tool, mock_db_session):
        """Test executing a local tool."""

        # Mock the local tool function
        def mock_function(param1, param2):
            return f"Result: {param1} + {param2}"

        tool_registry._local_tools[mock_local_tool.name] = mock_function
        tool_registry._tool_cache[mock_local_tool.name] = mock_local_tool

        with patch("services.tool_registry.crud") as mock_crud:
            # Mock the get_tool method to return our mock tool
            with patch.object(tool_registry, "get_tool", return_value=mock_local_tool):
                mock_crud.update_tool_usage_stats.return_value = None

                result = await tool_registry.execute_tool(
                    tool_name=mock_local_tool.name, parameters={"param1": "hello", "param2": "world"}, db=mock_db_session
                )

                assert result["status"] == "success"
                assert result["result"] == "Result: hello + world"
                assert "execution_time_ms" in result
                assert "tool_id" in result

    @pytest.mark.asyncio
    async def test_execute_mcp_tool_success(self, tool_registry, mock_mcp_tool, mock_mcp_server, mock_db_session):
        """Test successful MCP tool execution."""
        tool_registry._tool_cache[mock_mcp_tool.name] = mock_mcp_tool

        with patch("services.tool_registry.crud") as mock_crud:
            # Mock the get_tool method to return our mock tool
            with patch.object(tool_registry, "get_tool", return_value=mock_mcp_tool):
                mock_crud.get_mcp_server.return_value = mock_mcp_server
                mock_crud.update_tool_usage_stats.return_value = None

                with patch("services.mcp_client.mcp_client") as mock_mcp_client:
                    # Mock the async execute_tool method
                    mock_mcp_client.execute_tool = AsyncMock(
                        return_value={
                            "status": "success",
                            "result": {"output": "MCP tool executed"},
                            "execution_time": 200,
                        }
                    )

                    result = await tool_registry.execute_tool(
                        tool_name=mock_mcp_tool.name, parameters={"input": "test"}, db=mock_db_session
                    )

                    assert result["status"] == "success"
                    assert result["result"]["status"] == "success"
                    mock_mcp_client.execute_tool.assert_called_once_with(
                        server=mock_mcp_server, tool_name=mock_mcp_tool.remote_name, parameters={"input": "test"}
                    )

    @pytest.mark.asyncio
    async def test_execute_mcp_tool_no_server(self, tool_registry, mock_mcp_tool, mock_db_session):
        """Test MCP tool execution with no associated server."""
        mock_mcp_tool.mcp_server_id = None
        tool_registry._tool_cache[mock_mcp_tool.name] = mock_mcp_tool

        with patch("services.tool_registry.crud") as mock_crud:
            # Mock the get_tool method to return our mock tool
            with patch.object(tool_registry, "get_tool", return_value=mock_mcp_tool):
                mock_crud.update_tool_usage_stats.return_value = None

                result = await tool_registry.execute_tool(
                    tool_name=mock_mcp_tool.name, parameters={"input": "test"}, db=mock_db_session
                )

                assert result["status"] == "error"
                assert "no associated server" in result["error_message"]

    @pytest.mark.asyncio
    async def test_execute_mcp_tool_server_not_found(self, tool_registry, mock_mcp_tool, mock_db_session):
        """Test MCP tool execution with server not found in database."""
        tool_registry._tool_cache[mock_mcp_tool.name] = mock_mcp_tool

        with patch("services.tool_registry.crud") as mock_crud:
            mock_crud.get_mcp_server.return_value = None
            mock_crud.update_tool_usage_stats.return_value = None

            result = await tool_registry.execute_tool(
                tool_name=mock_mcp_tool.name, parameters={"input": "test"}, db=mock_db_session
            )

            assert result["status"] == "error"
            assert "MCP server not found" in result["error_message"]

    @pytest.mark.asyncio
    async def test_execute_mcp_tool_server_inactive(self, tool_registry, mock_mcp_tool, mock_mcp_server, mock_db_session):
        """Test MCP tool execution with inactive server."""
        mock_mcp_server.status = "inactive"
        tool_registry._tool_cache[mock_mcp_tool.name] = mock_mcp_tool

        with patch("services.tool_registry.crud") as mock_crud:
            mock_crud.get_mcp_server.return_value = mock_mcp_server
            mock_crud.update_tool_usage_stats.return_value = None

            result = await tool_registry.execute_tool(
                tool_name=mock_mcp_tool.name, parameters={"input": "test"}, db=mock_db_session
            )

            assert result["status"] == "error"
            assert "is not active" in result["error_message"]

    @pytest.mark.asyncio
    async def test_execute_mcp_tool_server_unavailable(self, tool_registry, mock_mcp_tool, mock_mcp_server, mock_db_session):
        """Test MCP tool execution with server unavailable."""
        tool_registry._tool_cache[mock_mcp_tool.name] = mock_mcp_tool

        with patch("services.tool_registry.crud") as mock_crud:
            mock_crud.get_mcp_server.return_value = mock_mcp_server
            mock_crud.update_tool_usage_stats.return_value = None
            mock_crud.update_mcp_server_health.return_value = None

            with patch("services.mcp_client.mcp_client") as mock_mcp_client:
                from services.mcp_client import MCPServerUnavailableError

                mock_mcp_client.execute_tool.side_effect = MCPServerUnavailableError("Server down")

                result = await tool_registry.execute_tool(
                    tool_name=mock_mcp_tool.name, parameters={"input": "test"}, db=mock_db_session
                )

                assert result["status"] == "error"
                assert "is unavailable" in result["error_message"]
                # Verify server health was updated
                mock_crud.update_mcp_server_health.assert_called_once_with(mock_db_session, mock_mcp_server.server_id, False)

    @pytest.mark.asyncio
    async def test_execute_mcp_tool_execution_error(self, tool_registry, mock_mcp_tool, mock_mcp_server, mock_db_session):
        """Test MCP tool execution with tool execution error."""
        tool_registry._tool_cache[mock_mcp_tool.name] = mock_mcp_tool

        with patch("services.tool_registry.crud") as mock_crud:
            mock_crud.get_mcp_server.return_value = mock_mcp_server
            mock_crud.update_tool_usage_stats.return_value = None

            with patch("services.mcp_client.mcp_client") as mock_mcp_client:
                from services.mcp_client import MCPToolExecutionError

                mock_mcp_client.execute_tool.side_effect = MCPToolExecutionError("Tool failed")

                result = await tool_registry.execute_tool(
                    tool_name=mock_mcp_tool.name, parameters={"input": "test"}, db=mock_db_session
                )

                assert result["status"] == "error"
                assert "Tool execution failed on MCP server" in result["error_message"]

    @pytest.mark.asyncio
    async def test_execute_tool_not_found(self, tool_registry, mock_db_session):
        """Test executing a tool that doesn't exist."""
        with pytest.raises(ValueError, match="Tool 'nonexistent_tool' not found"):
            await tool_registry.execute_tool(tool_name="nonexistent_tool", parameters={}, db=mock_db_session)

    @pytest.mark.asyncio
    async def test_execute_tool_inactive(self, tool_registry, mock_local_tool, mock_db_session):
        """Test executing an inactive tool."""
        mock_local_tool.is_active = False
        tool_registry._tool_cache[mock_local_tool.name] = mock_local_tool

        with pytest.raises(ValueError, match="is not available"):
            await tool_registry.execute_tool(tool_name=mock_local_tool.name, parameters={}, db=mock_db_session)

    @pytest.mark.asyncio
    async def test_execute_tool_unavailable(self, tool_registry, mock_local_tool, mock_db_session):
        """Test executing an unavailable tool."""
        mock_local_tool.is_available = False
        tool_registry._tool_cache[mock_local_tool.name] = mock_local_tool

        with pytest.raises(ValueError, match="is not available"):
            await tool_registry.execute_tool(tool_name=mock_local_tool.name, parameters={}, db=mock_db_session)

    def test_execute_local_tool_function_not_loaded(self, tool_registry, mock_local_tool):
        """Test executing a local tool with function not loaded."""
        # Ensure the function is not in _local_tools
        if mock_local_tool.name in tool_registry._local_tools:
            del tool_registry._local_tools[mock_local_tool.name]

        with pytest.raises(ValueError, match="Local tool function not loaded"):
            tool_registry._execute_local_tool(mock_local_tool, {})

    def test_register_mcp_server(self, tool_registry, mock_db_session):
        """Test registering an MCP server."""
        registration = schemas.MCPServerRegistration(
            name="test-server",
            description="Test MCP server",
            host="localhost",
            port=8080,
            protocol="http",
            capabilities=["tool_execution"],
        )

        mock_server = MagicMock(spec=models.MCPServer)
        mock_server.name = "test-server"

        with patch("services.tool_registry.crud") as mock_crud:
            mock_crud.get_mcp_server_by_name.return_value = None
            mock_crud.create_mcp_server.return_value = mock_server

            result = tool_registry.register_mcp_server(registration, mock_db_session)

            assert result == mock_server
            assert "test-server" in tool_registry._mcp_servers
            mock_crud.create_mcp_server.assert_called_once()

    def test_register_mcp_server_existing(self, tool_registry, mock_db_session):
        """Test registering an existing MCP server (update)."""
        registration = schemas.MCPServerRegistration(
            name="existing-server", description="Updated description", host="localhost", port=8080
        )

        existing_server = MagicMock(spec=models.MCPServer)
        existing_server.server_id = uuid.uuid4()
        existing_server.name = "existing-server"

        updated_server = MagicMock(spec=models.MCPServer)
        updated_server.name = "existing-server"

        with patch("services.tool_registry.crud") as mock_crud:
            mock_crud.get_mcp_server_by_name.return_value = existing_server
            mock_crud.update_mcp_server.return_value = updated_server

            result = tool_registry.register_mcp_server(registration, mock_db_session)

            assert result == updated_server
            mock_crud.update_mcp_server.assert_called_once()
            mock_crud.create_mcp_server.assert_not_called()

"""
Unit tests for MCP Client functionality.

Tests the HTTP client for communicating with MCP servers,
including tool discovery, execution, and health checks.
"""

import pytest
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

from services.mcp_client import MCPClient, MCPServerUnavailableError, MCPToolExecutionError
from db import models


@pytest.fixture
def mock_mcp_server():
    """Create a mock MCP server model."""
    server = MagicMock(spec=models.MCPServer)
    server.server_id = uuid.uuid4()
    server.name = "test-mcp-server"
    server.host = "localhost"
    server.port = 8080
    server.protocol = "http"
    server.endpoint = "/api"
    server.auth_type = None
    server.auth_config = None
    return server


@pytest.fixture
def mcp_client():
    """Create an MCP client instance."""
    return MCPClient(timeout=10, max_retries=2)


class TestMCPClient:
    """Test MCP client functionality."""

    @pytest.mark.asyncio
    async def test_health_check_success(self, mcp_client, mock_mcp_server):
        """Test successful health check."""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client

            # Mock successful health check response
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_client.get.return_value = mock_response

            result = await mcp_client.health_check(mock_mcp_server)

            assert result is True
            mock_client.get.assert_called_with("/health")

    @pytest.mark.asyncio
    async def test_health_check_fallback_to_tools(self, mcp_client, mock_mcp_server):
        """Test health check fallback to tools endpoint."""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client

            # Mock health endpoint failure, tools endpoint success
            import httpx

            health_error = httpx.RequestError("Health endpoint not found")
            tools_response = MagicMock()
            tools_response.status_code = 200

            mock_client.get.side_effect = [
                health_error,  # First call fails with RequestError
                tools_response,  # Second call succeeds
            ]

            result = await mcp_client.health_check(mock_mcp_server)

            assert result is True
            assert mock_client.get.call_count == 2

    @pytest.mark.asyncio
    async def test_health_check_failure(self, mcp_client, mock_mcp_server):
        """Test health check failure."""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client

            # Mock both endpoints failing
            mock_client.get.side_effect = Exception("Connection failed")

            result = await mcp_client.health_check(mock_mcp_server)

            assert result is False

    @pytest.mark.asyncio
    async def test_discover_tools_success(self, mcp_client, mock_mcp_server):
        """Test successful tool discovery."""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client

            # Mock successful tools response
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = [
                {"name": "test_tool", "description": "A test tool", "parameters_schema": {"type": "object"}}
            ]
            mock_client.get.return_value = mock_response

            tools = await mcp_client.discover_tools(mock_mcp_server)

            assert len(tools) == 1
            assert tools[0]["name"] == "test_tool"
            mock_client.get.assert_called_with("/tools")

    @pytest.mark.asyncio
    async def test_discover_tools_wrapped_response(self, mcp_client, mock_mcp_server):
        """Test tool discovery with wrapped response format."""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client

            # Mock wrapped tools response
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "tools": [{"name": "tool1", "description": "Tool 1"}, {"name": "tool2", "description": "Tool 2"}]
            }
            mock_client.get.return_value = mock_response

            tools = await mcp_client.discover_tools(mock_mcp_server)

            assert len(tools) == 2
            assert tools[0]["name"] == "tool1"
            assert tools[1]["name"] == "tool2"

    @pytest.mark.asyncio
    async def test_discover_tools_server_unavailable(self, mcp_client, mock_mcp_server):
        """Test tool discovery with server unavailable."""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client

            # Mock connection error
            import httpx

            mock_client.get.side_effect = httpx.RequestError("Connection failed")

            with pytest.raises(MCPServerUnavailableError):
                await mcp_client.discover_tools(mock_mcp_server)

    @pytest.mark.asyncio
    async def test_execute_tool_success(self, mcp_client, mock_mcp_server):
        """Test successful tool execution."""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client

            # Mock successful execution response
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "status": "success",
                "result": {"output": "Tool executed successfully"},
                "execution_time": 150,
            }
            mock_client.post.return_value = mock_response

            result = await mcp_client.execute_tool(server=mock_mcp_server, tool_name="test_tool", parameters={"input": "test"})

            assert result["status"] == "success"
            assert result["result"]["output"] == "Tool executed successfully"

            # Verify the request was made correctly
            mock_client.post.assert_called_once()
            call_args = mock_client.post.call_args
            assert call_args[0][0] == "/execute"
            request_data = call_args[1]["json"]
            assert request_data["tool"] == "test_tool"
            assert request_data["parameters"] == {"input": "test"}

    @pytest.mark.asyncio
    async def test_execute_tool_not_found(self, mcp_client, mock_mcp_server):
        """Test tool execution with tool not found."""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client

            # Mock 404 response
            mock_response = MagicMock()
            mock_response.status_code = 404
            mock_client.post.return_value = mock_response

            with pytest.raises(MCPToolExecutionError, match="Tool 'nonexistent_tool' not found"):
                await mcp_client.execute_tool(server=mock_mcp_server, tool_name="nonexistent_tool", parameters={})

    @pytest.mark.asyncio
    async def test_execute_tool_bad_request(self, mcp_client, mock_mcp_server):
        """Test tool execution with bad request."""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client

            # Mock 400 response
            mock_response = MagicMock()
            mock_response.status_code = 400
            mock_response.headers = {"content-type": "application/json"}
            mock_response.json.return_value = {"error": "Invalid parameters"}
            mock_client.post.return_value = mock_response

            with pytest.raises(MCPToolExecutionError, match="Tool execution failed"):
                await mcp_client.execute_tool(server=mock_mcp_server, tool_name="test_tool", parameters={"invalid": "params"})

    @pytest.mark.asyncio
    async def test_execute_tool_server_unavailable(self, mcp_client, mock_mcp_server):
        """Test tool execution with server unavailable."""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client

            # Mock connection error
            import httpx

            mock_client.post.side_effect = httpx.RequestError("Connection failed")

            with pytest.raises(MCPServerUnavailableError):
                await mcp_client.execute_tool(server=mock_mcp_server, tool_name="test_tool", parameters={})

    @pytest.mark.asyncio
    async def test_get_tool_schema_success(self, mcp_client, mock_mcp_server):
        """Test successful tool schema retrieval."""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client

            # Mock successful schema response
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"type": "object", "properties": {"input": {"type": "string"}}}
            mock_client.get.return_value = mock_response

            schema = await mcp_client.get_tool_schema(mock_mcp_server, "test_tool")

            assert schema is not None
            assert schema["type"] == "object"
            mock_client.get.assert_called_with("/tools/test_tool/schema")

    @pytest.mark.asyncio
    async def test_get_tool_schema_not_found(self, mcp_client, mock_mcp_server):
        """Test tool schema retrieval with tool not found."""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client

            # Mock 404 response
            mock_response = MagicMock()
            mock_response.status_code = 404
            mock_client.get.return_value = mock_response

            schema = await mcp_client.get_tool_schema(mock_mcp_server, "nonexistent_tool")

            assert schema is None

    @pytest.mark.asyncio
    async def test_client_caching(self, mcp_client, mock_mcp_server):
        """Test that HTTP clients are cached properly."""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client

            # Make multiple calls
            await mcp_client._get_client(mock_mcp_server)
            await mcp_client._get_client(mock_mcp_server)

            # Should only create one client instance
            assert mock_client_class.call_count == 1

    @pytest.mark.asyncio
    async def test_close_clients(self, mcp_client, mock_mcp_server):
        """Test closing all HTTP clients."""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client

            # Create a client
            await mcp_client._get_client(mock_mcp_server)

            # Close all clients
            await mcp_client.close()

            # Verify client was closed
            mock_client.aclose.assert_called_once()
            assert len(mcp_client._client_cache) == 0

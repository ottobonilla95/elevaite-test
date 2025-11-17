"""
End-to-End Integration Tests for MCP Tool Execution

Tests MCP tool execution with real MCP servers:
1. FastMCP test server (scripts/mcp_test_server.py on port 8765)
2. Local MCP server (running on port 3000)

Prerequisites:
- FastMCP test server running: python scripts/mcp_test_server.py
- Local MCP server running on port 3000 (optional)
"""

import asyncio
import httpx
import pytest
from uuid import uuid4

from workflow_core_sdk.db.models import MCPServer, Tool as DBTool
from workflow_core_sdk.clients.mcp_client import MCPClient
from workflow_core_sdk.steps.tool_steps import tool_execution_step
from workflow_core_sdk.execution.context import ExecutionContext


class TestMCPEndToEnd:
    """End-to-end tests for MCP tool execution."""

    @pytest.fixture
    async def mcp_client(self):
        """Create a fresh MCP client for each test."""
        client = MCPClient()
        yield client
        await client.close()

    @pytest.fixture
    async def check_fastmcp_server(self, fastmcp_server_config, mcp_client):
        """Check if FastMCP test server is running on port 8765."""
        try:
            # Use MCP client's health check which supports both transports
            is_healthy = await mcp_client.health_check(fastmcp_server_config)
            if is_healthy:
                return True
        except Exception:
            pass
        pytest.skip("FastMCP test server not running on port 8765. Start with: python scripts/mcp_test_server.py")

    @pytest.fixture
    async def check_local_mcp_server(self):
        """Check if local MCP server is running on port 3000."""
        try:
            async with httpx.AsyncClient() as client:
                # Try common health check endpoints
                for endpoint in ["/health", "/tools", "/"]:
                    try:
                        response = await client.get(f"http://localhost:3000{endpoint}", timeout=2.0)
                        if response.status_code in [200, 404]:  # 404 is ok, means server is up
                            return True
                    except Exception:
                        continue
        except Exception:
            pass
        pytest.skip("Local MCP server not running on port 3000")

    @pytest.fixture
    def fastmcp_server_config(self):
        """Configuration for FastMCP test server."""
        return {
            "host": "localhost",
            "port": 8765,
            "protocol": "http",
            "endpoint": "/mcp",  # FastMCP uses /mcp path
            "auth_type": None,
            "auth_config": None,
        }

    @pytest.fixture
    def local_mcp_server_config(self):
        """Configuration for local MCP server on port 3000."""
        return {
            "host": "localhost",
            "port": 3000,
            "protocol": "http",
            "endpoint": "",
            "auth_type": None,
            "auth_config": None,
        }

    @pytest.mark.asyncio
    async def test_fastmcp_health_check(self, check_fastmcp_server, fastmcp_server_config, mcp_client):
        """Test health check for FastMCP test server."""
        result = await mcp_client.health_check(fastmcp_server_config)
        assert result is True

    @pytest.mark.asyncio
    async def test_fastmcp_discover_tools(self, check_fastmcp_server, fastmcp_server_config, mcp_client):
        """Test tool discovery from FastMCP test server."""
        tools = await mcp_client.discover_tools(fastmcp_server_config)

        assert isinstance(tools, list)
        assert len(tools) > 0

        # Check for expected tools
        tool_names = [t["name"] for t in tools]
        assert "add" in tool_names
        assert "multiply" in tool_names
        assert "echo" in tool_names
        assert "get_current_time" in tool_names

        # Verify tool structure (MCP uses 'inputSchema' not 'parameters')
        add_tool = next(t for t in tools if t["name"] == "add")
        assert "description" in add_tool
        assert "inputSchema" in add_tool
        assert add_tool["inputSchema"]["type"] == "object"
        assert "a" in add_tool["inputSchema"]["properties"]
        assert "b" in add_tool["inputSchema"]["properties"]

    @pytest.mark.asyncio
    async def test_fastmcp_execute_add_tool(self, check_fastmcp_server, fastmcp_server_config, mcp_client):
        """Test executing the 'add' tool on FastMCP test server."""
        result = await mcp_client.execute_tool(
            server_config=fastmcp_server_config,
            tool_name="add",
            parameters={"a": 5, "b": 3},
            execution_id=str(uuid4()),
        )

        assert result is not None
        # FastMCP returns structured content with the result
        # Format: {'content': [...], 'isError': False, 'structuredContent': {'result': 8}}
        assert isinstance(result, dict)
        assert result.get("isError") is False

        # Check structured content
        structured = result.get("structuredContent", {})
        assert structured.get("result") == 8

    @pytest.mark.asyncio
    async def test_fastmcp_execute_echo_tool(self, check_fastmcp_server, fastmcp_server_config, mcp_client):
        """Test executing the 'echo' tool on FastMCP test server."""
        test_message = "Hello from MCP test!"
        result = await mcp_client.execute_tool(
            server_config=fastmcp_server_config,
            tool_name="echo",
            parameters={"message": test_message},
            execution_id=str(uuid4()),
        )

        assert result is not None
        assert isinstance(result, dict)
        assert result.get("isError") is False

        # Check structured content
        structured = result.get("structuredContent", {})
        assert structured.get("result") == test_message

    @pytest.mark.asyncio
    async def test_fastmcp_execute_greet_tool(self, check_fastmcp_server, fastmcp_server_config, mcp_client):
        """Test executing the 'greet' tool with default and custom greeting."""
        # Test with default greeting
        result = await mcp_client.execute_tool(
            server_config=fastmcp_server_config,
            tool_name="greet",
            parameters={"name": "World"},
            execution_id=str(uuid4()),
        )

        assert result is not None
        if isinstance(result, dict):
            greeting = result.get("result") or result.get("content")
        else:
            greeting = result
        assert "World" in str(greeting)

        # Test with custom greeting
        result = await mcp_client.execute_tool(
            server_config=fastmcp_server_config,
            tool_name="greet",
            parameters={"name": "Alice", "greeting": "Hi"},
            execution_id=str(uuid4()),
        )

        assert result is not None
        if isinstance(result, dict):
            greeting = result.get("result") or result.get("content")
        else:
            greeting = result
        assert "Hi" in str(greeting)
        assert "Alice" in str(greeting)

    @pytest.mark.asyncio
    async def test_local_mcp_health_check(self, mcp_client, check_local_mcp_server, local_mcp_server_config):
        """Test health check for local MCP server on port 3000."""
        result = await mcp_client.health_check(local_mcp_server_config)
        assert result is True

    @pytest.mark.asyncio
    async def test_local_mcp_discover_tools(self, mcp_client, check_local_mcp_server, local_mcp_server_config):
        """Test tool discovery from local MCP server on port 3000."""
        tools = await mcp_client.discover_tools(local_mcp_server_config)

        assert isinstance(tools, list)
        # Just verify we can discover tools, don't assert specific tools
        # since we don't know what's on the local server
        print(f"\n📋 Discovered {len(tools)} tools from local MCP server:")
        for tool in tools:
            print(f"   - {tool.get('name')}: {tool.get('description', 'No description')}")

    @pytest.mark.skip(reason="Requires database fixtures - to be implemented")
    @pytest.mark.asyncio
    async def test_workflow_with_fastmcp_tool(
        self,
        check_fastmcp_server,
        fastmcp_server_config,
        db_session,
        execution_context,
    ):
        """Test executing a workflow step with an MCP tool from FastMCP server."""
        # Create MCP server in database
        mcp_server = MCPServer(
            id=uuid4(),
            name="FastMCP Test Server",
            host=fastmcp_server_config["host"],
            port=fastmcp_server_config["port"],
            protocol=fastmcp_server_config["protocol"],
            endpoint=fastmcp_server_config["endpoint"],
            auth_type=fastmcp_server_config["auth_type"],
            auth_config=fastmcp_server_config["auth_config"],
            status="active",
        )
        db_session.add(mcp_server)
        db_session.commit()
        db_session.refresh(mcp_server)

        # Create MCP tool in database
        mcp_tool = DBTool(
            id=uuid4(),
            name="test_add",
            description="Add two numbers via MCP",
            tool_type="mcp",
            execution_type="api",
            mcp_server_id=mcp_server.id,
            remote_name="add",
            parameters_schema={
                "type": "object",
                "properties": {
                    "a": {"type": "integer", "description": "First number"},
                    "b": {"type": "integer", "description": "Second number"},
                },
                "required": ["a", "b"],
            },
        )
        db_session.add(mcp_tool)
        db_session.commit()
        db_session.refresh(mcp_tool)

        # Create step configuration
        step_config = {
            "step_id": "test_mcp_step",
            "step_type": "tool",
            "tool_name": "test_add",
            "param_mapping": {},
            "static_params": {"a": 10, "b": 20},
        }

        # Execute the step
        result = await tool_execution_step(
            step_config=step_config,
            input_data={},
            execution_context=execution_context,
        )

        # Verify result
        assert result["success"] is True
        assert result["tool"]["name"] == "test_add"
        assert result["tool"]["type"] == "mcp"
        # The actual result might be in different fields depending on MCP server response
        assert "result" in result or "output" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

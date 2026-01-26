"""
Integration tests for MCP functionality.

Tests the complete MCP workflow including server registration,
tool discovery, and execution through the API.
"""

import pytest
import uuid
from unittest.mock import patch
from fastapi.testclient import TestClient

from main import app
from db import models


@pytest.fixture
def test_client():
    """Create a test client."""
    return TestClient(app)


@pytest.fixture
def mock_mcp_server_registration():
    """Create a mock MCP server registration."""
    return {
        "name": "integration-test-server",
        "description": "Integration test MCP server",
        "host": "localhost",
        "port": 9090,
        "protocol": "http",
        "endpoint": "/api",
        "version": "1.0.0",
        "capabilities": ["tool_execution", "tool_discovery"],
        "tools": [
            {
                "name": "test_calculator",
                "description": "A simple calculator tool",
                "parameters_schema": {
                    "type": "object",
                    "properties": {
                        "operation": {"type": "string", "enum": ["add", "subtract", "multiply", "divide"]},
                        "a": {"type": "number"},
                        "b": {"type": "number"}
                    },
                    "required": ["operation", "a", "b"]
                },
                "version": "1.0.0"
            }
        ]
    }


class TestMCPIntegration:
    """Test complete MCP integration workflow."""

    def test_mcp_server_registration_workflow(self, test_client, mock_mcp_server_registration):
        """Test the complete MCP server registration workflow."""
        with patch('services.mcp_client.mcp_client') as mock_mcp_client:
            # Mock tool registration
            mock_tool = models.Tool(
                tool_id=uuid.uuid4(),
                name="test_calculator",
                description="A simple calculator tool",
                tool_type="mcp",
                parameters_schema={"type": "object"},
                is_active=True,
                is_available=True
            )
            mock_mcp_client.register_tools_from_server.return_value = [mock_tool]
            
            # Register the MCP server
            response = test_client.post(
                "/api/tools/mcp-servers/register",
                json=mock_mcp_server_registration
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["name"] == "integration-test-server"
            assert data["host"] == "localhost"
            assert data["port"] == 9090
            assert data["status"] == "active"

    def test_mcp_server_health_monitoring(self, test_client):
        """Test MCP server health monitoring."""
        # First create a server
        server_data = {
            "name": "health-test-server",
            "description": "Server for health testing",
            "host": "localhost",
            "port": 8081,
            "protocol": "http"
        }
        
        response = test_client.post("/api/tools/mcp-servers", json=server_data)
        assert response.status_code == 200
        server_id = response.json()["server_id"]
        
        # Update health status
        response = test_client.post(f"/api/tools/mcp-servers/{server_id}/health?is_healthy=true")
        assert response.status_code == 200
        assert response.json()["status"] == "active"
        
        # Update to unhealthy
        response = test_client.post(f"/api/tools/mcp-servers/{server_id}/health?is_healthy=false")
        assert response.status_code == 200
        assert response.json()["status"] == "unhealthy"

    def test_mcp_tool_execution_workflow(self, test_client):
        """Test the complete MCP tool execution workflow."""
        # Create a category first
        category_data = {
            "name": "MCP Tools",
            "description": "Tools from MCP servers",
            "icon": "🔧",
            "color": "#4CAF50"
        }
        category_response = test_client.post("/api/tools/categories", json=category_data)
        assert category_response.status_code == 200
        category_id = category_response.json()["category_id"]
        
        # Create an MCP server
        server_data = {
            "name": "execution-test-server",
            "description": "Server for execution testing",
            "host": "localhost",
            "port": 8082,
            "protocol": "http"
        }
        server_response = test_client.post("/api/tools/mcp-servers", json=server_data)
        assert server_response.status_code == 200
        server_id = server_response.json()["server_id"]
        
        # Create an MCP tool
        tool_data = {
            "name": "mcp_test_tool",
            "description": "Test tool for MCP execution",
            "tool_type": "mcp",
            "execution_type": "api",
            "parameters_schema": {
                "type": "object",
                "properties": {
                    "input": {"type": "string"}
                }
            },
            "remote_name": "test_tool",
            "category_id": category_id,
            "mcp_server_id": server_id
        }
        tool_response = test_client.post("/api/tools/", json=tool_data)
        assert tool_response.status_code == 200
        tool_id = tool_response.json()["tool_id"]
        
        # Mock the MCP client for tool execution
        with patch('services.mcp_client.mcp_client') as mock_mcp_client:
            mock_mcp_client.execute_tool.return_value = {
                "status": "success",
                "result": {"output": "Tool executed successfully"},
                "execution_time": 150
            }
            
            # Execute the tool
            execution_data = {
                "parameters": {"input": "test input"}
            }
            execution_response = test_client.post(
                f"/api/tools/{tool_id}/execute",
                json=execution_data
            )
            
            assert execution_response.status_code == 200
            result = execution_response.json()
            assert result["status"] == "success"
            assert "result" in result
            assert "execution_time_ms" in result

    def test_mcp_tool_execution_error_handling(self, test_client):
        """Test error handling in MCP tool execution."""
        # Create necessary resources
        category_response = test_client.post("/api/tools/categories", json={
            "name": "Error Test Category",
            "description": "Category for error testing"
        })
        category_id = category_response.json()["category_id"]
        
        server_response = test_client.post("/api/tools/mcp-servers", json={
            "name": "error-test-server",
            "host": "localhost",
            "port": 8083
        })
        server_id = server_response.json()["server_id"]
        
        tool_response = test_client.post("/api/tools/", json={
            "name": "error_test_tool",
            "description": "Tool for error testing",
            "tool_type": "mcp",
            "parameters_schema": {"type": "object"},
            "category_id": category_id,
            "mcp_server_id": server_id
        })
        tool_id = tool_response.json()["tool_id"]
        
        # Mock MCP client to raise an error
        with patch('services.mcp_client.mcp_client') as mock_mcp_client:
            from services.mcp_client import MCPServerUnavailableError
            mock_mcp_client.execute_tool.side_effect = MCPServerUnavailableError("Server is down")
            
            # Execute the tool (should handle error gracefully)
            execution_response = test_client.post(
                f"/api/tools/{tool_id}/execute",
                json={"parameters": {}}
            )
            
            assert execution_response.status_code == 200
            result = execution_response.json()
            assert result["status"] == "error"
            assert "error" in result["result"]

    def test_mcp_server_crud_operations(self, test_client):
        """Test CRUD operations for MCP servers."""
        # Create
        server_data = {
            "name": "crud-test-server",
            "description": "Server for CRUD testing",
            "host": "localhost",
            "port": 8084,
            "protocol": "http",
            "capabilities": ["tool_execution"]
        }
        create_response = test_client.post("/api/tools/mcp-servers", json=server_data)
        assert create_response.status_code == 200
        server_id = create_response.json()["server_id"]
        
        # Read
        get_response = test_client.get(f"/api/tools/mcp-servers/{server_id}")
        assert get_response.status_code == 200
        assert get_response.json()["name"] == "crud-test-server"
        
        # Update
        update_data = {
            "description": "Updated description",
            "port": 8085
        }
        update_response = test_client.put(f"/api/tools/mcp-servers/{server_id}", json=update_data)
        assert update_response.status_code == 200
        assert update_response.json()["description"] == "Updated description"
        assert update_response.json()["port"] == 8085
        
        # List
        list_response = test_client.get("/api/tools/mcp-servers")
        assert list_response.status_code == 200
        servers = list_response.json()
        assert any(server["server_id"] == server_id for server in servers)
        
        # Delete
        delete_response = test_client.delete(f"/api/tools/mcp-servers/{server_id}")
        assert delete_response.status_code == 200
        
        # Verify deletion
        get_response = test_client.get(f"/api/tools/mcp-servers/{server_id}")
        assert get_response.status_code == 404

    def test_mcp_tool_discovery_integration(self, test_client):
        """Test tool discovery integration with MCP servers."""
        # Create an MCP server
        server_data = {
            "name": "discovery-test-server",
            "description": "Server for tool discovery testing",
            "host": "localhost",
            "port": 8086,
            "protocol": "http"
        }
        server_response = test_client.post("/api/tools/mcp-servers", json=server_data)
        assert server_response.status_code == 200
        server_id = server_response.json()["server_id"]
        
        # Mock tool discovery
        with patch('services.mcp_client.mcp_client') as mock_mcp_client:
            mock_tools = [
                {
                    "name": "discovered_tool_1",
                    "description": "First discovered tool",
                    "parameters_schema": {"type": "object"}
                },
                {
                    "name": "discovered_tool_2",
                    "description": "Second discovered tool",
                    "parameters_schema": {"type": "object"}
                }
            ]
            mock_mcp_client.discover_tools.return_value = mock_tools
            
            # Register server with tools
            registration_data = {
                "name": "discovery-test-server",
                "host": "localhost",
                "port": 8086,
                "tools": mock_tools
            }
            
            registration_response = test_client.post(
                "/api/tools/mcp-servers/register",
                json=registration_data
            )
            assert registration_response.status_code == 200
            
            # Verify tools were registered (this would require checking the database)
            # For now, we just verify the server registration succeeded
            assert registration_response.json()["name"] == "discovery-test-server"

    def test_get_active_mcp_servers(self, test_client):
        """Test getting active MCP servers."""
        # Create an active server
        server_data = {
            "name": "active-server",
            "host": "localhost",
            "port": 8087,
            "status": "active"
        }
        test_client.post("/api/tools/mcp-servers", json=server_data)
        
        # Get active servers
        response = test_client.get("/api/tools/mcp-servers/active")
        assert response.status_code == 200
        active_servers = response.json()
        assert len(active_servers) >= 1
        assert any(server["name"] == "active-server" for server in active_servers)

    def test_mcp_server_filtering(self, test_client):
        """Test filtering MCP servers by status."""
        # Create servers with different statuses
        test_client.post("/api/tools/mcp-servers", json={
            "name": "active-filter-server",
            "host": "localhost",
            "port": 8088
        })
        
        # Get servers with status filter
        response = test_client.get("/api/tools/mcp-servers?status=active")
        assert response.status_code == 200
        servers = response.json()
        # All returned servers should have active status
        for server in servers:
            assert server["status"] == "active"

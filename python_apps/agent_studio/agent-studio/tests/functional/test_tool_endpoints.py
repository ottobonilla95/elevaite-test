"""
Functional tests for tool management API endpoints.

Tests the complete API functionality for tools, categories, and MCP servers.
"""

import pytest
import uuid
from fastapi.testclient import TestClient


class TestToolCategoryEndpoints:
    """Test tool category API endpoints."""

    def test_create_tool_category(self, test_client: TestClient):
        """Test creating a tool category via API."""
        category_data = {
            "name": "API Test Category",
            "description": "Category created via API test",
            "icon": "🧪",
            "color": "#FF0000"
        }
        
        response = test_client.post("/api/tools/categories", json=category_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "API Test Category"
        assert data["description"] == "Category created via API test"
        assert data["icon"] == "🧪"
        assert data["color"] == "#FF0000"
        assert "category_id" in data
        assert "created_at" in data

    def test_create_duplicate_category_name(self, test_client: TestClient):
        """Test creating a category with duplicate name fails."""
        category_data = {
            "name": "Duplicate Category",
            "description": "First category"
        }
        
        # Create first category
        response1 = test_client.post("/api/tools/categories", json=category_data)
        assert response1.status_code == 200
        
        # Try to create duplicate
        response2 = test_client.post("/api/tools/categories", json=category_data)
        assert response2.status_code == 400
        assert "already exists" in response2.json()["detail"]

    def test_get_tool_categories(self, test_client: TestClient):
        """Test retrieving all tool categories."""
        # Create test categories
        for i in range(3):
            category_data = {
                "name": f"Category {i}",
                "description": f"Test category {i}"
            }
            test_client.post("/api/tools/categories", json=category_data)
        
        # Get all categories
        response = test_client.get("/api/tools/categories")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 3
        assert all("category_id" in cat for cat in data)

    def test_get_tool_category_by_id(self, test_client: TestClient):
        """Test retrieving a specific tool category."""
        # Create category
        category_data = {
            "name": "Specific Category",
            "description": "Category for specific retrieval"
        }
        create_response = test_client.post("/api/tools/categories", json=category_data)
        created_category = create_response.json()
        
        # Get specific category
        response = test_client.get(f"/api/tools/categories/{created_category['category_id']}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Specific Category"
        assert data["category_id"] == created_category["category_id"]

    def test_update_tool_category(self, test_client: TestClient):
        """Test updating a tool category."""
        # Create category
        category_data = {
            "name": "Original Category",
            "description": "Original description"
        }
        create_response = test_client.post("/api/tools/categories", json=category_data)
        created_category = create_response.json()
        
        # Update category
        update_data = {
            "name": "Updated Category",
            "description": "Updated description",
            "color": "#00FF00"
        }
        response = test_client.put(
            f"/api/tools/categories/{created_category['category_id']}", 
            json=update_data
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Category"
        assert data["description"] == "Updated description"
        assert data["color"] == "#00FF00"

    def test_delete_tool_category(self, test_client: TestClient):
        """Test deleting a tool category."""
        # Create category
        category_data = {
            "name": "Category to Delete",
            "description": "This will be deleted"
        }
        create_response = test_client.post("/api/tools/categories", json=category_data)
        created_category = create_response.json()
        
        # Delete category
        response = test_client.delete(f"/api/tools/categories/{created_category['category_id']}")
        
        assert response.status_code == 200
        assert "deleted successfully" in response.json()["message"]
        
        # Verify deletion
        get_response = test_client.get(f"/api/tools/categories/{created_category['category_id']}")
        assert get_response.status_code == 404


class TestMCPServerEndpoints:
    """Test MCP server API endpoints."""

    def test_create_mcp_server(self, test_client: TestClient):
        """Test creating an MCP server via API."""
        server_data = {
            "name": "API Test MCP Server",
            "description": "MCP server created via API test",
            "host": "localhost",
            "port": 8080,
            "protocol": "http",
            "capabilities": ["tool_execution", "health_check"]
        }
        
        response = test_client.post("/api/tools/mcp-servers", json=server_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "API Test MCP Server"
        assert data["host"] == "localhost"
        assert data["port"] == 8080
        assert data["capabilities"] == ["tool_execution", "health_check"]
        assert data["status"] == "active"

    def test_get_mcp_servers(self, test_client: TestClient):
        """Test retrieving MCP servers."""
        # Create test servers
        for i in range(2):
            server_data = {
                "name": f"Test Server {i}",
                "host": "localhost",
                "port": 8080 + i
            }
            test_client.post("/api/tools/mcp-servers", json=server_data)
        
        # Get all servers
        response = test_client.get("/api/tools/mcp-servers")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 2

    def test_get_active_mcp_servers(self, test_client: TestClient):
        """Test retrieving only active MCP servers."""
        # Create active server
        active_server_data = {
            "name": "Active Server",
            "host": "localhost",
            "port": 8080
        }
        active_response = test_client.post("/api/tools/mcp-servers", json=active_server_data)
        active_server = active_response.json()
        
        # Create and deactivate another server
        inactive_server_data = {
            "name": "Inactive Server",
            "host": "localhost",
            "port": 8081
        }
        inactive_response = test_client.post("/api/tools/mcp-servers", json=inactive_server_data)
        inactive_server = inactive_response.json()
        
        # Deactivate server
        test_client.put(
            f"/api/tools/mcp-servers/{inactive_server['server_id']}", 
            json={"status": "inactive"}
        )
        
        # Get active servers
        response = test_client.get("/api/tools/mcp-servers/active")
        
        assert response.status_code == 200
        data = response.json()
        active_server_ids = [server["server_id"] for server in data]
        assert active_server["server_id"] in active_server_ids

    def test_mcp_server_self_registration(self, test_client: TestClient):
        """Test MCP server self-registration endpoint."""
        registration_data = {
            "name": "Self Registered Server",
            "description": "Server that registered itself",
            "host": "192.168.1.100",
            "port": 9000,
            "version": "1.0.0",
            "capabilities": ["tool_execution"],
            "tools": [
                {
                    "name": "remote_tool",
                    "description": "A tool from the remote server"
                }
            ]
        }
        
        response = test_client.post("/api/tools/mcp-servers/register", json=registration_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Self Registered Server"
        assert data["host"] == "192.168.1.100"
        assert data["port"] == 9000
        assert data["status"] == "active"

    def test_update_mcp_server_health(self, test_client: TestClient):
        """Test updating MCP server health status."""
        # Create server
        server_data = {
            "name": "Health Test Server",
            "host": "localhost",
            "port": 8080
        }
        create_response = test_client.post("/api/tools/mcp-servers", json=server_data)
        server = create_response.json()
        
        # Update health status
        response = test_client.post(
            f"/api/tools/mcp-servers/{server['server_id']}/health?is_healthy=false"
        )
        
        assert response.status_code == 200
        assert "Health status updated" in response.json()["message"]


class TestToolEndpoints:
    """Test tool API endpoints."""

    def test_create_local_tool(self, test_client: TestClient):
        """Test creating a local tool via API."""
        tool_data = {
            "name": "api_test_tool",
            "description": "Tool created via API test",
            "tool_type": "local",
            "parameters_schema": {
                "type": "object",
                "properties": {
                    "input": {"type": "string"}
                }
            },
            "module_path": "builtins",
            "function_name": "len"
        }
        
        response = test_client.post("/api/tools/", json=tool_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "api_test_tool"
        assert data["tool_type"] == "local"
        assert data["module_path"] == "builtins"
        assert data["function_name"] == "len"
        assert data["is_active"] is True

    def test_create_tool_with_category(self, test_client: TestClient):
        """Test creating a tool with a category."""
        # Create category first
        category_data = {
            "name": "Tool Category",
            "description": "Category for tools"
        }
        cat_response = test_client.post("/api/tools/categories", json=category_data)
        category = cat_response.json()
        
        # Create tool with category
        tool_data = {
            "name": "categorized_tool",
            "description": "Tool with category",
            "tool_type": "local",
            "parameters_schema": {"type": "object"},
            "category_id": category["category_id"]
        }
        
        response = test_client.post("/api/tools/", json=tool_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["category_id"] == category["category_id"]

    def test_get_tools(self, test_client: TestClient):
        """Test retrieving tools with filtering."""
        # Create test tools
        for i in range(3):
            tool_data = {
                "name": f"test_tool_{i}",
                "description": f"Test tool {i}",
                "tool_type": "local",
                "parameters_schema": {"type": "object"}
            }
            test_client.post("/api/tools/", json=tool_data)
        
        # Get all tools
        response = test_client.get("/api/tools/")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 3

    def test_get_available_tools(self, test_client: TestClient):
        """Test retrieving only available tools."""
        # Create active tool
        active_tool_data = {
            "name": "active_tool",
            "description": "Active tool",
            "tool_type": "local",
            "parameters_schema": {"type": "object"}
        }
        active_response = test_client.post("/api/tools/", json=active_tool_data)
        active_tool = active_response.json()
        
        # Create and deactivate another tool
        inactive_tool_data = {
            "name": "inactive_tool",
            "description": "Inactive tool",
            "tool_type": "local",
            "parameters_schema": {"type": "object"}
        }
        inactive_response = test_client.post("/api/tools/", json=inactive_tool_data)
        inactive_tool = inactive_response.json()
        
        # Deactivate tool
        test_client.put(
            f"/api/tools/{inactive_tool['tool_id']}", 
            json={"is_active": False}
        )
        
        # Get available tools
        response = test_client.get("/api/tools/available")
        
        assert response.status_code == 200
        data = response.json()
        tool_ids = [tool["tool_id"] for tool in data]
        assert active_tool["tool_id"] in tool_ids

    def test_update_tool(self, test_client: TestClient):
        """Test updating a tool."""
        # Create tool
        tool_data = {
            "name": "tool_to_update",
            "description": "Original description",
            "tool_type": "local",
            "parameters_schema": {"type": "object"}
        }
        create_response = test_client.post("/api/tools/", json=tool_data)
        tool = create_response.json()
        
        # Update tool
        update_data = {
            "description": "Updated description",
            "timeout_seconds": 60
        }
        response = test_client.put(f"/api/tools/{tool['tool_id']}", json=update_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["description"] == "Updated description"
        assert data["timeout_seconds"] == 60

    def test_delete_tool(self, test_client: TestClient):
        """Test deleting a tool."""
        # Create tool
        tool_data = {
            "name": "tool_to_delete",
            "description": "This will be deleted",
            "tool_type": "local",
            "parameters_schema": {"type": "object"}
        }
        create_response = test_client.post("/api/tools/", json=tool_data)
        tool = create_response.json()
        
        # Delete tool
        response = test_client.delete(f"/api/tools/{tool['tool_id']}")
        
        assert response.status_code == 200
        assert "deleted successfully" in response.json()["message"]
        
        # Verify deletion
        get_response = test_client.get(f"/api/tools/{tool['tool_id']}")
        assert get_response.status_code == 404

    def test_tool_execution_placeholder(self, test_client: TestClient):
        """Test tool execution endpoint (Phase 1 placeholder)."""
        # Create tool
        tool_data = {
            "name": "execution_test_tool",
            "description": "Tool for execution testing",
            "tool_type": "local",
            "parameters_schema": {"type": "object"}
        }
        create_response = test_client.post("/api/tools/", json=tool_data)
        tool = create_response.json()
        
        # Execute tool
        execution_data = {
            "tool_id": tool["tool_id"],
            "parameters": {"test": "value"}
        }
        response = test_client.post(f"/api/tools/{tool['tool_id']}/execute", json=execution_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "execution_time_ms" in data
        assert "timestamp" in data

    def test_tool_validation_errors(self, test_client: TestClient):
        """Test tool creation validation errors."""
        # Missing required fields
        invalid_tool_data = {
            "name": "invalid_tool"
            # Missing description, tool_type, parameters_schema
        }
        
        response = test_client.post("/api/tools/", json=invalid_tool_data)
        assert response.status_code == 422  # Validation error

    def test_tool_filtering_by_type(self, test_client: TestClient):
        """Test filtering tools by type."""
        # Create local tool
        local_tool_data = {
            "name": "local_filter_tool",
            "description": "Local tool for filtering",
            "tool_type": "local",
            "parameters_schema": {"type": "object"}
        }
        test_client.post("/api/tools/", json=local_tool_data)
        
        # Filter by tool type
        response = test_client.get("/api/tools/?tool_type=local")
        
        assert response.status_code == 200
        data = response.json()
        assert all(tool["tool_type"] == "local" for tool in data)

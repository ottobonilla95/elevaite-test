"""
Unit tests for tool storage functionality.

Tests the core tool storage models, CRUD operations, and schemas.
"""

import pytest
import uuid
from datetime import datetime
from sqlalchemy.orm import Session

from db import crud, schemas, models


class TestToolCategoryModel:
    """Test tool category model and operations."""

    def test_create_tool_category(self, test_db_session: Session):
        """Test creating a tool category."""
        category_data = schemas.ToolCategoryCreate(
            name="Test Category",
            description="A test category",
            icon="🧪",
            color="#FF0000"
        )
        
        category = crud.create_tool_category(test_db_session, category_data)
        
        assert category.name == "Test Category"
        assert category.description == "A test category"
        assert category.icon == "🧪"
        assert category.color == "#FF0000"
        assert category.category_id is not None
        assert isinstance(category.created_at, datetime)

    def test_get_tool_category_by_name(self, test_db_session: Session):
        """Test retrieving a tool category by name."""
        # Create category
        category_data = schemas.ToolCategoryCreate(name="Unique Category")
        created_category = crud.create_tool_category(test_db_session, category_data)
        
        # Retrieve by name
        retrieved_category = crud.get_tool_category_by_name(test_db_session, "Unique Category")
        
        assert retrieved_category is not None
        assert retrieved_category.category_id == created_category.category_id
        assert retrieved_category.name == "Unique Category"

    def test_update_tool_category(self, test_db_session: Session):
        """Test updating a tool category."""
        # Create category
        category_data = schemas.ToolCategoryCreate(name="Original Name")
        category = crud.create_tool_category(test_db_session, category_data)
        
        # Update category
        update_data = schemas.ToolCategoryUpdate(
            name="Updated Name",
            description="Updated description"
        )
        updated_category = crud.update_tool_category(test_db_session, category.category_id, update_data)
        
        assert updated_category is not None
        assert updated_category.name == "Updated Name"
        assert updated_category.description == "Updated description"

    def test_delete_tool_category(self, test_db_session: Session):
        """Test deleting a tool category."""
        # Create category
        category_data = schemas.ToolCategoryCreate(name="To Delete")
        category = crud.create_tool_category(test_db_session, category_data)
        
        # Delete category
        success = crud.delete_tool_category(test_db_session, category.category_id)
        
        assert success is True
        
        # Verify deletion
        deleted_category = crud.get_tool_category(test_db_session, category.category_id)
        assert deleted_category is None


class TestMCPServerModel:
    """Test MCP server model and operations."""

    def test_create_mcp_server(self, test_db_session: Session):
        """Test creating an MCP server."""
        server_data = schemas.MCPServerCreate(
            name="Test MCP Server",
            description="A test MCP server",
            host="localhost",
            port=8080,
            protocol="http",
            capabilities=["tool_execution", "health_check"]
        )
        
        server = crud.create_mcp_server(test_db_session, server_data)
        
        assert server.name == "Test MCP Server"
        assert server.host == "localhost"
        assert server.port == 8080
        assert server.protocol == "http"
        assert server.capabilities == ["tool_execution", "health_check"]
        assert server.status == "active"
        assert server.server_id is not None

    def test_update_mcp_server_health(self, test_db_session: Session):
        """Test updating MCP server health status."""
        # Create server
        server_data = schemas.MCPServerCreate(
            name="Health Test Server",
            host="localhost",
            port=8080
        )
        server = crud.create_mcp_server(test_db_session, server_data)
        
        # Update health - healthy
        updated_server = crud.update_mcp_server_health(test_db_session, server.server_id, True)
        
        assert updated_server is not None
        assert updated_server.consecutive_failures == 0
        assert updated_server.last_health_check is not None
        assert updated_server.status == "active"
        
        # Update health - unhealthy multiple times
        for _ in range(3):
            updated_server = crud.update_mcp_server_health(test_db_session, server.server_id, False)
        
        assert updated_server.consecutive_failures == 3
        assert updated_server.status == "error"

    def test_get_active_mcp_servers(self, test_db_session: Session):
        """Test retrieving only active MCP servers."""
        # Create active server
        active_server_data = schemas.MCPServerCreate(
            name="Active Server",
            host="localhost",
            port=8080
        )
        active_server = crud.create_mcp_server(test_db_session, active_server_data)
        
        # Create inactive server
        inactive_server_data = schemas.MCPServerCreate(
            name="Inactive Server",
            host="localhost",
            port=8081
        )
        inactive_server = crud.create_mcp_server(test_db_session, inactive_server_data)
        
        # Mark one as inactive
        crud.update_mcp_server(
            test_db_session,
            inactive_server.server_id,
            schemas.MCPServerUpdate(status="inactive")
        )
        
        # Get active servers
        active_servers = crud.get_active_mcp_servers(test_db_session)
        
        assert len(active_servers) == 1
        assert active_servers[0].server_id == active_server.server_id


class TestToolModel:
    """Test tool model and operations."""

    def test_create_local_tool(self, test_db_session: Session):
        """Test creating a local tool."""
        tool_data = schemas.ToolCreate(
            name="test_tool",
            description="A test tool",
            tool_type="local",
            parameters_schema={
                "type": "object",
                "properties": {
                    "param1": {"type": "string"}
                }
            },
            module_path="test.module",
            function_name="test_function"
        )
        
        tool = crud.create_tool(test_db_session, tool_data)
        
        assert tool.name == "test_tool"
        assert tool.tool_type == "local"
        assert tool.module_path == "test.module"
        assert tool.function_name == "test_function"
        assert tool.is_active is True
        assert tool.is_available is True
        assert tool.usage_count == 0

    def test_create_mcp_tool(self, test_db_session: Session):
        """Test creating an MCP tool."""
        # First create an MCP server
        server_data = schemas.MCPServerCreate(
            name="Tool Server",
            host="localhost",
            port=8080
        )
        server = crud.create_mcp_server(test_db_session, server_data)
        
        # Create MCP tool
        tool_data = schemas.ToolCreate(
            name="mcp_tool",
            description="An MCP tool",
            tool_type="mcp",
            parameters_schema={"type": "object"},
            mcp_server_id=server.server_id,
            remote_name="remote_tool_name"
        )
        
        tool = crud.create_tool(test_db_session, tool_data)
        
        assert tool.name == "mcp_tool"
        assert tool.tool_type == "mcp"
        assert tool.mcp_server_id == server.server_id
        assert tool.remote_name == "remote_tool_name"

    def test_update_tool_usage_stats(self, test_db_session: Session):
        """Test updating tool usage statistics."""
        # Create tool
        tool_data = schemas.ToolCreate(
            name="stats_tool",
            description="Tool for stats testing",
            tool_type="local",
            parameters_schema={"type": "object"}
        )
        tool = crud.create_tool(test_db_session, tool_data)
        
        # Update stats - successful execution
        updated_tool = crud.update_tool_usage_stats(
            test_db_session, tool.tool_id, 150, True
        )
        
        assert updated_tool.usage_count == 1
        assert updated_tool.success_count == 1
        assert updated_tool.error_count == 0
        assert updated_tool.average_execution_time_ms == 150.0
        assert updated_tool.last_used is not None
        
        # Update stats - failed execution
        updated_tool = crud.update_tool_usage_stats(
            test_db_session, tool.tool_id, 200, False
        )
        
        assert updated_tool.usage_count == 2
        assert updated_tool.success_count == 1
        assert updated_tool.error_count == 1
        # Average should be weighted: 150 * 0.8 + 200 * 0.2 = 160
        assert abs(updated_tool.average_execution_time_ms - 160.0) < 0.1

    def test_get_tools_by_category(self, test_db_session: Session):
        """Test filtering tools by category."""
        # Create category
        category_data = schemas.ToolCategoryCreate(name="Filter Category")
        category = crud.create_tool_category(test_db_session, category_data)
        
        # Create tools with and without category
        tool_with_category = schemas.ToolCreate(
            name="categorized_tool",
            description="Tool with category",
            tool_type="local",
            parameters_schema={"type": "object"},
            category_id=category.category_id
        )
        tool_without_category = schemas.ToolCreate(
            name="uncategorized_tool",
            description="Tool without category",
            tool_type="local",
            parameters_schema={"type": "object"}
        )
        
        crud.create_tool(test_db_session, tool_with_category)
        crud.create_tool(test_db_session, tool_without_category)
        
        # Filter by category
        categorized_tools = crud.get_tools(
            test_db_session, category_id=category.category_id
        )
        
        assert len(categorized_tools) == 1
        assert categorized_tools[0].name == "categorized_tool"

    def test_get_available_tools(self, test_db_session: Session):
        """Test getting only available tools."""
        # Create active tool
        active_tool_data = schemas.ToolCreate(
            name="active_tool",
            description="Active tool",
            tool_type="local",
            parameters_schema={"type": "object"}
        )
        active_tool = crud.create_tool(test_db_session, active_tool_data)
        
        # Create inactive tool
        inactive_tool_data = schemas.ToolCreate(
            name="inactive_tool",
            description="Inactive tool",
            tool_type="local",
            parameters_schema={"type": "object"}
        )
        inactive_tool = crud.create_tool(test_db_session, inactive_tool_data)
        
        # Mark one as inactive
        crud.update_tool(
            test_db_session,
            inactive_tool.tool_id,
            schemas.ToolUpdate(is_active=False)
        )
        
        # Get available tools
        available_tools = crud.get_available_tools(test_db_session)
        
        assert len(available_tools) == 1
        assert available_tools[0].tool_id == active_tool.tool_id


class TestToolSchemas:
    """Test tool-related Pydantic schemas."""

    def test_tool_create_schema_validation(self):
        """Test tool creation schema validation."""
        # Valid schema
        valid_data = {
            "name": "valid_tool",
            "description": "A valid tool",
            "tool_type": "local",
            "parameters_schema": {"type": "object"}
        }
        
        schema = schemas.ToolCreate(**valid_data)
        assert schema.name == "valid_tool"
        assert schema.tool_type == "local"
        assert schema.version == "1.0.0"  # Default value
        assert schema.timeout_seconds == 30  # Default value

    def test_tool_update_schema_partial(self):
        """Test tool update schema allows partial updates."""
        update_data = {
            "description": "Updated description",
            "is_active": False
        }
        
        schema = schemas.ToolUpdate(**update_data)
        assert schema.description == "Updated description"
        assert schema.is_active is False
        assert schema.name is None  # Not provided, should be None

    def test_mcp_server_registration_schema(self):
        """Test MCP server registration schema."""
        registration_data = {
            "name": "Test Server",
            "host": "localhost",
            "port": 8080,
            "tools": [
                {
                    "name": "remote_tool",
                    "description": "A remote tool"
                }
            ]
        }
        
        schema = schemas.MCPServerRegistration(**registration_data)
        assert schema.name == "Test Server"
        assert schema.protocol == "http"  # Default value
        assert len(schema.tools) == 1

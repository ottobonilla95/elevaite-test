"""
Integration tests for the tool registry service.

Tests the tool registry singleton, caching, and tool execution.
"""

import pytest
from sqlalchemy.orm import Session

from services.tool_registry import ToolRegistry
from db import crud, schemas


class TestToolRegistryIntegration:
    """Test tool registry integration functionality."""

    def setup_method(self):
        """Reset the tool registry singleton for each test."""
        # Reset the singleton instance
        ToolRegistry._instance = None
        ToolRegistry._initialized = False

    def test_tool_registry_singleton(self):
        """Test that tool registry is a proper singleton."""
        registry1 = ToolRegistry()
        registry2 = ToolRegistry()

        assert registry1 is registry2
        assert id(registry1) == id(registry2)

    def test_tool_registry_initialization(self, test_db_session: Session):
        """Test tool registry initialization with database."""
        # Create test tools
        category_data = schemas.ToolCategoryCreate(name="Test Category")
        category = crud.create_tool_category(test_db_session, category_data)

        tool_data = schemas.ToolCreate(
            name="test_tool",
            description="A test tool",
            tool_type="local",
            parameters_schema={"type": "object"},
            module_path="builtins",
            function_name="len",
            category_id=category.category_id,
        )
        crud.create_tool(test_db_session, tool_data)

        # Initialize registry
        registry = ToolRegistry()
        registry.initialize(test_db_session)

        # Check that tools are loaded
        tools = registry.get_available_tools(test_db_session)
        assert len(tools) == 1
        assert tools[0].name == "test_tool"

    def test_tool_registry_caching(self, test_db_session: Session):
        """Test tool registry caching mechanism."""
        # Create test tool
        tool_data = schemas.ToolCreate(
            name="cached_tool", description="Tool for cache testing", tool_type="local", parameters_schema={"type": "object"}
        )
        crud.create_tool(test_db_session, tool_data)

        registry = ToolRegistry()
        registry.initialize(test_db_session)

        # First call should populate cache
        tools1 = registry.get_available_tools(test_db_session)
        cache_time1 = registry._last_cache_refresh

        # Second call should use cache
        tools2 = registry.get_available_tools(test_db_session)
        cache_time2 = registry._last_cache_refresh

        assert tools1 == tools2
        assert cache_time1 == cache_time2  # Cache not refreshed

    def test_tool_registry_cache_expiration(self, test_db_session: Session):
        """Test tool registry cache expiration."""
        registry = ToolRegistry()
        registry._cache_ttl = 0  # Force immediate expiration
        registry.initialize(test_db_session)

        # First call
        registry.get_available_tools(test_db_session)
        cache_time1 = registry._last_cache_refresh

        # Second call should refresh cache due to TTL
        registry.get_available_tools(test_db_session)
        cache_time2 = registry._last_cache_refresh

        assert cache_time2 > cache_time1

    def test_get_tool_by_name(self, test_db_session: Session):
        """Test retrieving a specific tool by name."""
        # Create test tool
        tool_data = schemas.ToolCreate(
            name="specific_tool",
            description="Specific tool for testing",
            tool_type="local",
            parameters_schema={"type": "object"},
        )
        crud.create_tool(test_db_session, tool_data)

        registry = ToolRegistry()
        registry.initialize(test_db_session)

        # Get specific tool
        tool = registry.get_tool("specific_tool", test_db_session)

        assert tool is not None
        assert tool.name == "specific_tool"

        # Get non-existent tool
        non_existent = registry.get_tool("non_existent", test_db_session)
        assert non_existent is None

    def test_get_tools_by_category(self, test_db_session: Session):
        """Test filtering tools by category."""
        # Create categories
        cat1_data = schemas.ToolCategoryCreate(name="Category 1")
        cat2_data = schemas.ToolCategoryCreate(name="Category 2")
        cat1 = crud.create_tool_category(test_db_session, cat1_data)
        cat2 = crud.create_tool_category(test_db_session, cat2_data)

        # Create tools in different categories
        tool1_data = schemas.ToolCreate(
            name="tool_cat1",
            description="Tool in category 1",
            tool_type="local",
            parameters_schema={"type": "object"},
            category_id=cat1.category_id,
        )
        tool2_data = schemas.ToolCreate(
            name="tool_cat2",
            description="Tool in category 2",
            tool_type="local",
            parameters_schema={"type": "object"},
            category_id=cat2.category_id,
        )
        crud.create_tool(test_db_session, tool1_data)
        crud.create_tool(test_db_session, tool2_data)

        registry = ToolRegistry()
        registry.initialize(test_db_session)

        # Get tools by category
        cat1_tools = registry.get_tools_by_category("Category 1", test_db_session)
        cat2_tools = registry.get_tools_by_category("Category 2", test_db_session)

        assert len(cat1_tools) == 1
        assert len(cat2_tools) == 1
        assert cat1_tools[0].name == "tool_cat1"
        assert cat2_tools[0].name == "tool_cat2"

    @pytest.mark.skip(reason="Tool execution testing requires complex setup - will be implemented in Phase 2")
    def test_local_tool_execution(self, test_db_session: Session):
        """Test execution of local tools."""

        # Create a simple test function that accepts keyword arguments
        def test_add_func(**kwargs):
            return kwargs.get("a", 0) + kwargs.get("b", 0)

        # Create a tool
        tool_data = schemas.ToolCreate(
            name="test_tool",
            description="Tool for testing execution",
            tool_type="local",
            parameters_schema={"type": "object", "properties": {"a": {"type": "integer"}, "b": {"type": "integer"}}},
            module_path="test",
            function_name="test_add_func",
        )
        crud.create_tool(test_db_session, tool_data)

        registry = ToolRegistry()
        registry.initialize(test_db_session)

        # Manually add the function to the registry for testing
        registry._local_tools["test_tool"] = test_add_func

        # Execute tool
        result = registry.execute_tool("test_tool", {"a": 3, "b": 5}, test_db_session)

        assert result["status"] == "success"
        assert result["result"] == 8
        assert "execution_time_ms" in result
        assert "tool_id" in result

    def test_tool_execution_error_handling(self, test_db_session: Session):
        """Test error handling in tool execution."""
        # Create a tool that will cause an error
        tool_data = schemas.ToolCreate(
            name="error_tool",
            description="Tool that causes errors",
            tool_type="local",
            parameters_schema={"type": "object"},
            module_path="builtins",
            function_name="len",
        )
        crud.create_tool(test_db_session, tool_data)

        registry = ToolRegistry()
        registry.initialize(test_db_session)

        # Execute tool with invalid parameters
        result = registry.execute_tool(
            "error_tool",
            {"obj": "not_a_list_for_len"},  # This will cause TypeError
            test_db_session,
        )

        assert result["status"] == "error"
        assert "error_message" in result
        assert "execution_time_ms" in result

    def test_tool_execution_nonexistent_tool(self, test_db_session: Session):
        """Test execution of non-existent tool."""
        registry = ToolRegistry()
        registry.initialize(test_db_session)

        # Try to execute non-existent tool
        with pytest.raises(ValueError, match="Tool 'nonexistent' not found"):
            registry.execute_tool("nonexistent", {}, test_db_session)

    def test_tool_execution_inactive_tool(self, test_db_session: Session):
        """Test execution of inactive tool."""
        # Create inactive tool
        tool_data = schemas.ToolCreate(
            name="inactive_tool", description="Inactive tool", tool_type="local", parameters_schema={"type": "object"}
        )
        tool = crud.create_tool(test_db_session, tool_data)

        # Mark as inactive
        crud.update_tool(test_db_session, tool.tool_id, schemas.ToolUpdate(is_active=False))

        registry = ToolRegistry()
        registry.initialize(test_db_session)

        # Try to execute inactive tool - should not be found in available tools
        with pytest.raises(ValueError, match="Tool 'inactive_tool' not found"):
            registry.execute_tool("inactive_tool", {}, test_db_session)

    def test_register_local_tool(self, test_db_session: Session):
        """Test registering a new local tool."""
        registry = ToolRegistry()
        registry.initialize(test_db_session)

        # Define a test function
        def test_function(x: int, y: int) -> int:
            return x + y

        # Register the tool
        tool = registry.register_local_tool(
            name="add_function",
            description="Adds two numbers",
            function=test_function,
            parameters_schema={"type": "object", "properties": {"x": {"type": "integer"}, "y": {"type": "integer"}}},
            db=test_db_session,
        )

        assert tool.name == "add_function"
        assert tool.tool_type == "local"
        assert tool.function_name == "test_function"

        # Test execution of registered tool
        result = registry.execute_tool("add_function", {"x": 5, "y": 3}, test_db_session)

        assert result["status"] == "success"
        assert result["result"] == 8

    def test_register_mcp_server(self, test_db_session: Session):
        """Test registering an MCP server."""
        registry = ToolRegistry()
        registry.initialize(test_db_session)

        # Register MCP server
        server_info = schemas.MCPServerRegistration(
            name="Test MCP Server", description="Test server", host="localhost", port=8080, capabilities=["tool_execution"]
        )

        server = registry.register_mcp_server(server_info, test_db_session)

        assert server.name == "Test MCP Server"
        assert server.host == "localhost"
        assert server.port == 8080
        assert server.status == "active"

        # Test updating existing server
        updated_info = schemas.MCPServerRegistration(
            name="Test MCP Server",  # Same name
            description="Updated description",
            host="localhost",
            port=8081,  # Different port
            version="2.0",
        )

        updated_server = registry.register_mcp_server(updated_info, test_db_session)

        assert updated_server.server_id == server.server_id  # Same server
        assert updated_server.port == 8081  # Updated port
        assert updated_server.description == "Updated description"

    @pytest.mark.skip(reason="Tool execution testing requires complex setup - will be implemented in Phase 2")
    def test_tool_usage_statistics_tracking(self, test_db_session: Session):
        """Test that tool usage statistics are properly tracked."""

        # Create a simple test function
        def test_stats_func(**kwargs):
            return abs(kwargs.get("number", 0))

        # Create tool
        tool_data = schemas.ToolCreate(
            name="stats_tool",
            description="Tool for statistics testing",
            tool_type="local",
            parameters_schema={"type": "object", "properties": {"number": {"type": "number"}}},
            module_path="test",
            function_name="test_stats_func",
        )
        crud.create_tool(test_db_session, tool_data)

        registry = ToolRegistry()
        registry.initialize(test_db_session)

        # Manually add the function to the registry for testing
        registry._local_tools["stats_tool"] = test_stats_func

        # Execute tool multiple times
        registry.execute_tool("stats_tool", {"number": -5}, test_db_session)
        registry.execute_tool("stats_tool", {"number": -10}, test_db_session)

        # Force cache refresh to get updated statistics
        registry._refresh_cache(test_db_session)

        # Check statistics
        tool = registry.get_tool("stats_tool", test_db_session)
        assert tool is not None
        assert tool.usage_count == 2
        assert tool.success_count == 2
        assert tool.error_count == 0
        assert tool.last_used is not None

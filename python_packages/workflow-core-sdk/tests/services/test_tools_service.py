"""
Unit tests for ToolsService

Tests the business logic of tools, categories, and MCP server operations with mocked database.
"""

import uuid
from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest

from workflow_core_sdk.db.models import (
    Tool,
    ToolCreate,
    ToolUpdate,
    ToolCategory,
    ToolCategoryCreate,
    ToolCategoryUpdate,
    MCPServer,
    MCPServerCreate,
    MCPServerUpdate,
)
from workflow_core_sdk.services.tools_service import ToolsService


@pytest.fixture
def mock_session():
    """Mock SQLModel session"""
    return MagicMock()


@pytest.fixture
def sample_tool():
    """Sample tool for testing"""
    now = datetime.now(timezone.utc)
    tool_id = uuid.uuid4()
    return Tool(
        id=tool_id,
        name="calculator",
        version="1.0.0",
        description="A calculator tool",
        category_id=uuid.uuid4(),
        schema_={
            "type": "function",
            "function": {
                "name": "calculator",
                "parameters": {"type": "object", "properties": {}},
            },
        },
        is_local=True,
        organization_id="org-123",
        created_by="user-123",
        created_at=now,
        updated_at=now,
    )


@pytest.fixture
def sample_category():
    """Sample tool category for testing"""
    now = datetime.now(timezone.utc)
    category_id = uuid.uuid4()
    return ToolCategory(
        id=category_id,
        name="Math",
        description="Mathematical tools",
        icon="calculator",
        organization_id="org-123",
        created_by="user-123",
        created_at=now,
        updated_at=now,
    )


@pytest.fixture
def sample_mcp_server():
    """Sample MCP server for testing"""
    now = datetime.now(timezone.utc)
    server_id = uuid.uuid4()
    return MCPServer(
        id=server_id,
        name="remote_tools",
        description="Remote tool server",
        base_url="http://localhost:8080",
        is_active=True,
        organization_id="org-123",
        created_by="user-123",
        created_at=now,
        updated_at=now,
    )


class TestToolOperations:
    """Tests for tool CRUD operations"""

    def test_get_db_tool_by_id_success(self, mock_session, sample_tool):
        """Test getting a tool by ID"""
        mock_result = MagicMock()
        mock_result.first.return_value = sample_tool
        mock_session.exec.return_value = mock_result

        tool = ToolsService.get_db_tool_by_id(mock_session, str(sample_tool.id))

        assert tool is not None
        assert tool.id == sample_tool.id
        assert tool.name == "calculator"

    def test_get_db_tool_by_id_not_found(self, mock_session):
        """Test getting a non-existent tool by ID"""
        mock_result = MagicMock()
        mock_result.first.return_value = None
        mock_session.exec.return_value = mock_result

        tool_id = str(uuid.uuid4())
        tool = ToolsService.get_db_tool_by_id(mock_session, tool_id)

        assert tool is None

    def test_get_db_tool_by_name_success(self, mock_session, sample_tool):
        """Test getting a tool by name"""
        mock_result = MagicMock()
        mock_result.first.return_value = sample_tool
        mock_session.exec.return_value = mock_result

        tool = ToolsService.get_db_tool_by_name(mock_session, "calculator")

        assert tool is not None
        assert tool.name == "calculator"

    def test_get_db_tool_by_name_not_found(self, mock_session):
        """Test getting a non-existent tool by name"""
        mock_result = MagicMock()
        mock_result.first.return_value = None
        mock_session.exec.return_value = mock_result

        tool = ToolsService.get_db_tool_by_name(mock_session, "nonexistent")

        assert tool is None

    def test_create_tool_success(self, mock_session, sample_tool):
        """Test creating a new tool"""
        # Mock uniqueness check
        mock_result = MagicMock()
        mock_result.first.return_value = None
        mock_session.exec.return_value = mock_result

        # Mock add/commit/refresh
        mock_session.add.return_value = None
        mock_session.commit.return_value = None
        mock_session.refresh.side_effect = lambda obj: setattr(obj, "id", sample_tool.id)

        payload = ToolCreate(
            name="calculator",
            version="1.0.0",
            description="A calculator tool",
            tool_type="local",
            parameters_schema={"type": "object", "properties": {}},
        )

        tool = ToolsService.create_tool(mock_session, payload)

        assert tool is not None
        assert tool.name == "calculator"
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()

    def test_create_tool_duplicate(self, mock_session, sample_tool):
        """Test creating a tool with duplicate name and version"""
        # Mock uniqueness check returning existing tool
        mock_result = MagicMock()
        mock_result.first.return_value = sample_tool
        mock_session.exec.return_value = mock_result

        payload = ToolCreate(
            name="calculator",
            version="1.0.0",
            description="A calculator tool",
            tool_type="local",
            parameters_schema={"type": "object", "properties": {}},
        )

        with pytest.raises(ValueError, match="Tool with this name and version already exists"):
            ToolsService.create_tool(mock_session, payload)

    def test_list_db_tools_no_filters(self, mock_session, sample_tool):
        """Test listing tools without filters"""
        mock_result = MagicMock()
        mock_result.all.return_value = [sample_tool]
        mock_session.exec.return_value = mock_result

        tools = ToolsService.list_db_tools(mock_session, limit=100, offset=0)

        assert len(tools) == 1
        assert tools[0].name == "calculator"

    def test_list_db_tools_with_search(self, mock_session, sample_tool):
        """Test listing tools with search query"""
        mock_result = MagicMock()
        mock_result.all.return_value = [sample_tool]
        mock_session.exec.return_value = mock_result

        tools = ToolsService.list_db_tools(mock_session, q="calc", limit=100, offset=0)

        assert len(tools) == 1
        assert "calc" in tools[0].name.lower()

    def test_list_db_tools_search_no_match(self, mock_session, sample_tool):
        """Test listing tools with search query that doesn't match"""
        mock_result = MagicMock()
        mock_result.all.return_value = [sample_tool]
        mock_session.exec.return_value = mock_result

        tools = ToolsService.list_db_tools(mock_session, q="nomatch", limit=100, offset=0)

        assert len(tools) == 0

    def test_list_db_tools_with_pagination(self, mock_session):
        """Test listing tools with pagination"""
        mock_result = MagicMock()
        mock_result.all.return_value = []
        mock_session.exec.return_value = mock_result

        tools = ToolsService.list_db_tools(mock_session, limit=10, offset=20)

        assert len(tools) == 0

    def test_update_db_tool_success(self, mock_session, sample_tool):
        """Test updating a tool"""
        mock_result = MagicMock()
        mock_result.first.return_value = sample_tool
        mock_session.exec.return_value = mock_result

        payload = ToolUpdate(description="Updated description")
        tool = ToolsService.update_db_tool(mock_session, str(sample_tool.id), payload)

        assert tool is not None
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()

    def test_update_db_tool_not_found(self, mock_session):
        """Test updating a non-existent tool"""
        mock_result = MagicMock()
        mock_result.first.return_value = None
        mock_session.exec.return_value = mock_result

        tool_id = str(uuid.uuid4())
        payload = ToolUpdate(description="Updated")

        with pytest.raises(LookupError, match="Tool not found"):
            ToolsService.update_db_tool(mock_session, tool_id, payload)

    def test_delete_db_tool_success(self, mock_session, sample_tool):
        """Test deleting a tool"""
        mock_result = MagicMock()
        mock_result.first.return_value = sample_tool
        mock_session.exec.return_value = mock_result

        result = ToolsService.delete_db_tool(mock_session, str(sample_tool.id))

        assert result is True
        mock_session.delete.assert_called_once_with(sample_tool)
        mock_session.commit.assert_called_once()

    def test_delete_db_tool_not_found(self, mock_session):
        """Test deleting a non-existent tool"""
        mock_result = MagicMock()
        mock_result.first.return_value = None
        mock_session.exec.return_value = mock_result

        tool_id = str(uuid.uuid4())
        result = ToolsService.delete_db_tool(mock_session, tool_id)

        assert result is False
        mock_session.delete.assert_not_called()


class TestCategoryOperations:
    """Tests for tool category CRUD operations"""

    def test_create_category_success(self, mock_session, sample_category):
        """Test creating a new category"""
        # Mock uniqueness check
        mock_result = MagicMock()
        mock_result.first.return_value = None
        mock_session.exec.return_value = mock_result

        # Mock add/commit/refresh
        mock_session.add.return_value = None
        mock_session.commit.return_value = None
        mock_session.refresh.side_effect = lambda obj: setattr(obj, "id", sample_category.id)

        payload = ToolCategoryCreate(name="Math", description="Mathematical tools", icon="calculator")

        category = ToolsService.create_category(mock_session, payload)

        assert category is not None
        assert category.name == "Math"
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()

    def test_create_category_duplicate(self, mock_session, sample_category):
        """Test creating a category with duplicate name"""
        # Mock uniqueness check returning existing category
        mock_result = MagicMock()
        mock_result.first.return_value = sample_category
        mock_session.exec.return_value = mock_result

        payload = ToolCategoryCreate(name="Math", description="Mathematical tools")

        with pytest.raises(ValueError, match="Category with this name already exists"):
            ToolsService.create_category(mock_session, payload)

    def test_list_categories(self, mock_session, sample_category):
        """Test listing all categories"""
        mock_result = MagicMock()
        mock_result.all.return_value = [sample_category]
        mock_session.exec.return_value = mock_result

        categories = ToolsService.list_categories(mock_session)

        assert len(categories) == 1
        assert categories[0].name == "Math"

    def test_list_categories_empty(self, mock_session):
        """Test listing categories when none exist"""
        mock_result = MagicMock()
        mock_result.all.return_value = []
        mock_session.exec.return_value = mock_result

        categories = ToolsService.list_categories(mock_session)

        assert len(categories) == 0

    def test_get_category_success(self, mock_session, sample_category):
        """Test getting a category by ID"""
        mock_result = MagicMock()
        mock_result.first.return_value = sample_category
        mock_session.exec.return_value = mock_result

        category = ToolsService.get_category(mock_session, str(sample_category.id))

        assert category is not None
        assert category.id == sample_category.id
        assert category.name == "Math"

    def test_get_category_not_found(self, mock_session):
        """Test getting a non-existent category"""
        mock_result = MagicMock()
        mock_result.first.return_value = None
        mock_session.exec.return_value = mock_result

        category_id = str(uuid.uuid4())
        category = ToolsService.get_category(mock_session, category_id)

        assert category is None

    def test_update_category_success(self, mock_session, sample_category):
        """Test updating a category"""
        mock_result = MagicMock()
        mock_result.first.return_value = sample_category
        mock_session.exec.return_value = mock_result

        payload = ToolCategoryUpdate(description="Updated description")
        category = ToolsService.update_category(mock_session, str(sample_category.id), payload)

        assert category is not None
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()

    def test_update_category_not_found(self, mock_session):
        """Test updating a non-existent category"""
        mock_result = MagicMock()
        mock_result.first.return_value = None
        mock_session.exec.return_value = mock_result

        category_id = str(uuid.uuid4())
        payload = ToolCategoryUpdate(description="Updated")

        with pytest.raises(LookupError, match="Category not found"):
            ToolsService.update_category(mock_session, category_id, payload)

    def test_delete_category_success(self, mock_session, sample_category):
        """Test deleting a category"""
        mock_result = MagicMock()
        mock_result.first.return_value = sample_category
        mock_session.exec.return_value = mock_result

        result = ToolsService.delete_category(mock_session, str(sample_category.id))

        assert result is True
        mock_session.delete.assert_called_once_with(sample_category)
        mock_session.commit.assert_called_once()

    def test_delete_category_not_found(self, mock_session):
        """Test deleting a non-existent category"""
        mock_result = MagicMock()
        mock_result.first.return_value = None
        mock_session.exec.return_value = mock_result

        category_id = str(uuid.uuid4())
        result = ToolsService.delete_category(mock_session, category_id)

        assert result is False
        mock_session.delete.assert_not_called()


class TestMCPServerOperations:
    """Tests for MCP server CRUD operations"""

    def test_create_mcp_server_success(self, mock_session, sample_mcp_server):
        """Test creating a new MCP server"""
        # Mock uniqueness check
        mock_result = MagicMock()
        mock_result.first.return_value = None
        mock_session.exec.return_value = mock_result

        # Mock add/commit/refresh
        mock_session.add.return_value = None
        mock_session.commit.return_value = None
        mock_session.refresh.side_effect = lambda obj: setattr(obj, "id", sample_mcp_server.id)

        payload = MCPServerCreate(
            name="remote_tools",
            description="Remote tool server",
            host="localhost",
            port=8080,
            protocol="http",
        )

        server = ToolsService.create_mcp_server(mock_session, payload)

        assert server is not None
        assert server.name == "remote_tools"
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()

    def test_create_mcp_server_duplicate(self, mock_session, sample_mcp_server):
        """Test creating an MCP server with duplicate name"""
        # Mock uniqueness check returning existing server
        mock_result = MagicMock()
        mock_result.first.return_value = sample_mcp_server
        mock_session.exec.return_value = mock_result

        payload = MCPServerCreate(
            name="remote_tools",
            description="Remote tool server",
            host="localhost",
            port=8080,
            protocol="http",
        )

        with pytest.raises(ValueError, match="MCP server with this name already exists"):
            ToolsService.create_mcp_server(mock_session, payload)

    def test_list_mcp_servers(self, mock_session, sample_mcp_server):
        """Test listing all MCP servers"""
        mock_result = MagicMock()
        mock_result.all.return_value = [sample_mcp_server]
        mock_session.exec.return_value = mock_result

        servers = ToolsService.list_mcp_servers(mock_session)

        assert len(servers) == 1
        assert servers[0].name == "remote_tools"

    def test_list_mcp_servers_empty(self, mock_session):
        """Test listing MCP servers when none exist"""
        mock_result = MagicMock()
        mock_result.all.return_value = []
        mock_session.exec.return_value = mock_result

        servers = ToolsService.list_mcp_servers(mock_session)

        assert len(servers) == 0

    def test_get_mcp_server_success(self, mock_session, sample_mcp_server):
        """Test getting an MCP server by ID"""
        mock_result = MagicMock()
        mock_result.first.return_value = sample_mcp_server
        mock_session.exec.return_value = mock_result

        server = ToolsService.get_mcp_server(mock_session, str(sample_mcp_server.id))

        assert server is not None
        assert server.id == sample_mcp_server.id
        assert server.name == "remote_tools"

    def test_get_mcp_server_not_found(self, mock_session):
        """Test getting a non-existent MCP server"""
        mock_result = MagicMock()
        mock_result.first.return_value = None
        mock_session.exec.return_value = mock_result

        server_id = str(uuid.uuid4())
        server = ToolsService.get_mcp_server(mock_session, server_id)

        assert server is None

    def test_update_mcp_server_success(self, mock_session, sample_mcp_server):
        """Test updating an MCP server"""
        mock_result = MagicMock()
        mock_result.first.return_value = sample_mcp_server
        mock_session.exec.return_value = mock_result

        payload = MCPServerUpdate(description="Updated description", is_active=False)
        server = ToolsService.update_mcp_server(mock_session, str(sample_mcp_server.id), payload)

        assert server is not None
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()

    def test_update_mcp_server_not_found(self, mock_session):
        """Test updating a non-existent MCP server"""
        mock_result = MagicMock()
        mock_result.first.return_value = None
        mock_session.exec.return_value = mock_result

        server_id = str(uuid.uuid4())
        payload = MCPServerUpdate(description="Updated")

        with pytest.raises(LookupError, match="MCP server not found"):
            ToolsService.update_mcp_server(mock_session, server_id, payload)

    def test_delete_mcp_server_success(self, mock_session, sample_mcp_server):
        """Test deleting an MCP server"""
        mock_result = MagicMock()
        mock_result.first.return_value = sample_mcp_server
        mock_session.exec.return_value = mock_result

        result = ToolsService.delete_mcp_server(mock_session, str(sample_mcp_server.id))

        assert result is True
        mock_session.delete.assert_called_once_with(sample_mcp_server)
        mock_session.commit.assert_called_once()

    def test_delete_mcp_server_not_found(self, mock_session):
        """Test deleting a non-existent MCP server"""
        mock_result = MagicMock()
        mock_result.first.return_value = None
        mock_session.exec.return_value = mock_result

        server_id = str(uuid.uuid4())
        result = ToolsService.delete_mcp_server(mock_session, server_id)

        assert result is False
        mock_session.delete.assert_not_called()

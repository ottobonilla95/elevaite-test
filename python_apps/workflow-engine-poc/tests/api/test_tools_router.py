"""
Comprehensive tests for Tools Router

Tests all endpoints for tools, categories, and MCP servers:
- List tools (unified from DB + local registry)
- Get tool (DB preference, local fallback)
- DB Tool CRUD (create, list, get, update, delete)
- Category CRUD (create, list, get, update, delete)
- MCP Server CRUD (create, list, get, update, delete)
- Sync tools endpoint
"""

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from workflow_engine_poc.main import app
from workflow_core_sdk.db.models import (
    Tool,
    ToolCreate,
    ToolRead,
    ToolUpdate,
    ToolCategory,
    ToolCategoryCreate,
    ToolCategoryRead,
    ToolCategoryUpdate,
    MCPServer,
    MCPServerCreate,
    MCPServerRead,
    MCPServerUpdate,
)

client = TestClient(app)


@pytest.fixture
def mock_session():
    """Mock database session"""
    return MagicMock()


@pytest.fixture
def sample_tool():
    """Sample tool for testing"""
    now = datetime.now(timezone.utc)
    return Tool(
        id=uuid.uuid4(),
        name="test_tool",
        display_name="Test Tool",
        description="A test tool",
        version="1.0.0",
        tool_type="local",
        execution_type="function",
        parameters_schema={"type": "object", "properties": {"param1": {"type": "string"}}},
        return_schema=None,
        module_path="test.module",
        function_name="test_function",
        mcp_server_id=None,
        remote_name=None,
        api_endpoint=None,
        http_method=None,
        headers=None,
        auth_required=False,
        category_id=None,
        tags=["test"],
        documentation="Test documentation",
        examples=None,
        is_active=True,
        is_available=True,
        last_used=None,
        usage_count=0,
        created_at=now,
        updated_at=now,  # Required field, not Optional
    )


@pytest.fixture
def sample_category():
    """Sample tool category for testing"""
    now = datetime.now(timezone.utc)
    return ToolCategory(
        id=uuid.uuid4(),
        name="test_category",
        description="A test category",
        icon=None,
        color=None,
        tags=[],
        created_at=now,
        updated_at=None,  # This one is Optional
    )


@pytest.fixture
def sample_mcp_server():
    """Sample MCP server for testing"""
    now = datetime.now(timezone.utc)
    return MCPServer(
        id=uuid.uuid4(),
        name="test_mcp_server",
        description="A test MCP server",
        host="localhost",
        port=8080,
        protocol="http",
        endpoint=None,
        auth_type=None,
        auth_config=None,
        health_check_interval=300,
        version=None,
        capabilities=None,
        tags=None,
        status="active",
        last_health_check=None,
        consecutive_failures=0,
        registered_at=now,
        last_seen=None,
        updated_at=now,  # Required field
    )


@pytest.mark.api
class TestListTools:
    """Tests for GET /tools/"""

    @patch("workflow_engine_poc.routers.tools.tool_registry.get_unified_tools")
    @patch("workflow_engine_poc.routers.tools.ToolsService.get_db_tool_by_id")
    @patch("workflow_engine_poc.routers.tools.get_db_session")
    @patch("workflow_engine_poc.routers.tools.api_key_or_user_guard")
    @pytest.mark.api
    def test_list_tools_from_db(self, mock_guard, mock_get_session, mock_get_db_tool, mock_unified, mock_session, sample_tool):
        """Test listing tools from database"""
        mock_guard.return_value = lambda: "user-123"
        mock_get_session.return_value = mock_session

        # Mock unified tools returning DB tool
        unified_tool = MagicMock()
        unified_tool.source = "db"
        unified_tool.db_id = sample_tool.id
        unified_tool.name = sample_tool.name
        unified_tool.description = sample_tool.description
        unified_tool.parameters_schema = sample_tool.parameters_schema
        mock_unified.return_value = [unified_tool]

        mock_get_db_tool.return_value = sample_tool

        response = client.get("/tools/")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "test_tool"
        assert data[0]["source"] == "db"
        assert "db://" in data[0]["uri"]

    @patch("workflow_engine_poc.routers.tools.tool_registry.get_unified_tools")
    @patch("workflow_engine_poc.routers.tools.get_db_session")
    @patch("workflow_engine_poc.routers.tools.api_key_or_user_guard")
    @pytest.mark.api
    def test_list_tools_from_local(self, mock_guard, mock_get_session, mock_unified, mock_session):
        """Test listing tools from local registry"""
        mock_guard.return_value = lambda: "user-123"
        mock_get_session.return_value = mock_session

        # Mock unified tools returning local tool
        unified_tool = MagicMock()
        unified_tool.source = "local"
        unified_tool.db_id = None
        unified_tool.name = "local_tool"
        unified_tool.description = "A local tool"
        unified_tool.parameters_schema = {"type": "object"}
        mock_unified.return_value = [unified_tool]

        response = client.get("/tools/")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "local_tool"
        assert data[0]["source"] == "local"
        assert "local://" in data[0]["uri"]

    @patch("workflow_engine_poc.routers.tools.tool_registry.get_unified_tools")
    @patch("workflow_engine_poc.routers.tools.get_db_session")
    @patch("workflow_engine_poc.routers.tools.api_key_or_user_guard")
    @pytest.mark.api
    def test_list_tools_with_query_filter(self, mock_guard, mock_get_session, mock_unified, mock_session):
        """Test listing tools with query filter"""
        mock_guard.return_value = lambda: "user-123"
        mock_get_session.return_value = mock_session

        # Mock two local tools
        tool1 = MagicMock()
        tool1.source = "local"
        tool1.db_id = None
        tool1.name = "search_tool"
        tool1.description = "Search tool"
        tool1.parameters_schema = {}

        tool2 = MagicMock()
        tool2.source = "local"
        tool2.db_id = None
        tool2.name = "calculator"
        tool2.description = "Calculator tool"
        tool2.parameters_schema = {}

        mock_unified.return_value = [tool1, tool2]

        response = client.get("/tools/", params={"q": "search"})

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "search_tool"

    @patch("workflow_engine_poc.routers.tools.tool_registry.get_unified_tools")
    @patch("workflow_engine_poc.routers.tools.get_db_session")
    @patch("workflow_engine_poc.routers.tools.api_key_or_user_guard")
    @pytest.mark.api
    def test_list_tools_pagination(self, mock_guard, mock_get_session, mock_unified, mock_session):
        """Test pagination parameters"""
        mock_guard.return_value = lambda: "user-123"
        mock_get_session.return_value = mock_session

        # Mock 5 tools
        tools = []
        for i in range(5):
            tool = MagicMock()
            tool.source = "local"
            tool.db_id = None
            tool.name = f"tool_{i}"
            tool.description = f"Tool {i}"
            tool.parameters_schema = {}
            tools.append(tool)

        mock_unified.return_value = tools

        response = client.get("/tools/", params={"limit": 2, "offset": 1})

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        # Tools are sorted by name, so tool_1 and tool_2
        assert data[0]["name"] == "tool_1"
        assert data[1]["name"] == "tool_2"


@pytest.mark.api
class TestGetTool:
    """Tests for GET /tools/{tool_name}"""

    @patch("workflow_engine_poc.routers.tools.ToolsService.get_db_tool_by_name")
    @patch("workflow_engine_poc.routers.tools.get_db_session")
    @patch("workflow_engine_poc.routers.tools.api_key_or_user_guard")
    @pytest.mark.api
    def test_get_tool_from_db(self, mock_guard, mock_get_session, mock_get_db, mock_session, sample_tool):
        """Test getting tool from database (preferred)"""
        mock_guard.return_value = lambda: "user-123"
        mock_get_session.return_value = mock_session
        mock_get_db.return_value = sample_tool

        response = client.get("/tools/test_tool")

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "test_tool"
        assert data["source"] == "db"
        # Check call was made with correct tool name (session object may differ)
        assert mock_get_db.call_count == 1
        assert mock_get_db.call_args[0][1] == "test_tool"

    @patch("workflow_engine_poc.routers.tools.tool_registry.get_tool_by_name")
    @patch("workflow_engine_poc.routers.tools.ToolsService.get_db_tool_by_name")
    @patch("workflow_engine_poc.routers.tools.get_db_session")
    @patch("workflow_engine_poc.routers.tools.api_key_or_user_guard")
    @pytest.mark.api
    def test_get_tool_from_local_fallback(self, mock_guard, mock_get_session, mock_get_db, mock_get_local, mock_session):
        """Test getting tool from local registry when not in DB"""
        mock_guard.return_value = lambda: "user-123"
        mock_get_session.return_value = mock_session
        mock_get_db.return_value = None  # Not in DB

        # Mock local tool
        local_tool = MagicMock()
        local_tool.source = "local"
        local_tool.name = "local_tool"
        local_tool.description = "A local tool"
        local_tool.version = "1.0.0"
        local_tool.execution_type = "function"
        local_tool.parameters_schema = {"type": "object"}
        local_tool.return_schema = None
        local_tool.uri = "local://local_tool"
        mock_get_local.return_value = local_tool

        response = client.get("/tools/local_tool")

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "local_tool"
        assert data["source"] == "local"

    @patch("workflow_engine_poc.routers.tools.tool_registry.get_tool_by_name")
    @patch("workflow_engine_poc.routers.tools.ToolsService.get_db_tool_by_name")
    @patch("workflow_engine_poc.routers.tools.get_db_session")
    @patch("workflow_engine_poc.routers.tools.api_key_or_user_guard")
    @pytest.mark.api
    def test_get_tool_not_found(self, mock_guard, mock_get_session, mock_get_db, mock_get_local, mock_session):
        """Test getting non-existent tool returns 404"""
        mock_guard.return_value = lambda: "user-123"
        mock_get_session.return_value = mock_session
        mock_get_db.return_value = None
        mock_get_local.return_value = None

        response = client.get("/tools/nonexistent")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


@pytest.mark.api
class TestDBToolCRUD:
    """Tests for DB Tool CRUD endpoints"""

    @patch("workflow_engine_poc.routers.tools.ToolsService.create_tool")
    @patch("workflow_engine_poc.routers.tools.get_db_session")
    @patch("workflow_engine_poc.routers.tools.api_key_or_user_guard")
    @pytest.mark.api
    def test_create_db_tool_success(self, mock_guard, mock_get_session, mock_create, mock_session, sample_tool):
        """Test creating a DB tool"""
        mock_guard.return_value = lambda: "user-123"
        mock_get_session.return_value = mock_session
        # Service returns Tool, FastAPI converts to ToolRead
        mock_create.return_value = sample_tool

        payload = {
            "name": "test_tool",
            "description": "A test tool",
            "tool_type": "local",
            "execution_type": "function",
            "parameters_schema": {"type": "object"},
        }

        response = client.post("/tools/db", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "test_tool"
        mock_create.assert_called_once()

    @patch("workflow_engine_poc.routers.tools.ToolsService.create_tool")
    @patch("workflow_engine_poc.routers.tools.get_db_session")
    @patch("workflow_engine_poc.routers.tools.api_key_or_user_guard")
    @pytest.mark.api
    def test_create_db_tool_duplicate(self, mock_guard, mock_get_session, mock_create, mock_session):
        """Test creating duplicate tool raises 409"""
        mock_guard.return_value = lambda: "user-123"
        mock_get_session.return_value = mock_session
        mock_create.side_effect = ValueError("Tool with this name already exists")

        payload = {
            "name": "existing_tool",
            "description": "Test",
            "tool_type": "local",
            "execution_type": "function",
            "parameters_schema": {"type": "object", "properties": {}},
        }

        response = client.post("/tools/db", json=payload)

        assert response.status_code == 409

    @patch("workflow_engine_poc.routers.tools.ToolsService.list_db_tools")
    @patch("workflow_engine_poc.routers.tools.get_db_session")
    @patch("workflow_engine_poc.routers.tools.api_key_or_user_guard")
    @pytest.mark.api
    def test_list_db_tools(self, mock_guard, mock_get_session, mock_list, mock_session, sample_tool):
        """Test listing DB tools"""
        mock_guard.return_value = lambda: "user-123"
        mock_get_session.return_value = mock_session
        mock_list.return_value = [sample_tool]

        response = client.get("/tools/db")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "test_tool"

    @patch("workflow_engine_poc.routers.tools.ToolsService.get_db_tool_by_id")
    @patch("workflow_engine_poc.routers.tools.get_db_session")
    @patch("workflow_engine_poc.routers.tools.api_key_or_user_guard")
    @pytest.mark.api
    def test_get_db_tool_success(self, mock_guard, mock_get_session, mock_get, mock_session, sample_tool):
        """Test getting a DB tool by ID"""
        mock_guard.return_value = lambda: "user-123"
        mock_get_session.return_value = mock_session
        mock_get.return_value = sample_tool

        tool_id = str(sample_tool.id)
        response = client.get(f"/tools/db/{tool_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "test_tool"

    @patch("workflow_engine_poc.routers.tools.ToolsService.get_db_tool_by_id")
    @patch("workflow_engine_poc.routers.tools.get_db_session")
    @patch("workflow_engine_poc.routers.tools.api_key_or_user_guard")
    @pytest.mark.api
    def test_get_db_tool_not_found(self, mock_guard, mock_get_session, mock_get, mock_session):
        """Test getting non-existent DB tool returns 404"""
        mock_guard.return_value = lambda: "user-123"
        mock_get_session.return_value = mock_session
        mock_get.return_value = None

        tool_id = str(uuid.uuid4())
        response = client.get(f"/tools/db/{tool_id}")

        assert response.status_code == 404

    @patch("workflow_engine_poc.routers.tools.get_db_tool")
    @patch("workflow_engine_poc.routers.tools.ToolsService.update_db_tool")
    @patch("workflow_engine_poc.routers.tools.get_db_session")
    @patch("workflow_engine_poc.routers.tools.api_key_or_user_guard")
    @pytest.mark.api
    def test_update_db_tool_success(self, mock_guard, mock_get_session, mock_update, mock_get, mock_session, sample_tool):
        """Test updating a DB tool"""
        mock_guard.return_value = lambda: "user-123"
        mock_get_session.return_value = mock_session
        mock_update.return_value = sample_tool

        # Mock the get_db_tool function that's called after update
        async def mock_get_db_tool_func(tool_id, session):
            return sample_tool

        mock_get.side_effect = mock_get_db_tool_func

        tool_id = str(sample_tool.id)
        payload = {"description": "Updated description"}
        response = client.patch(f"/tools/db/{tool_id}", json=payload)

        assert response.status_code == 200
        mock_update.assert_called_once()

    @patch("workflow_engine_poc.routers.tools.ToolsService.update_db_tool")
    @patch("workflow_engine_poc.routers.tools.get_db_session")
    @patch("workflow_engine_poc.routers.tools.api_key_or_user_guard")
    @pytest.mark.api
    def test_update_db_tool_not_found(self, mock_guard, mock_get_session, mock_update, mock_session):
        """Test updating non-existent DB tool returns 404"""
        mock_guard.return_value = lambda: "user-123"
        mock_get_session.return_value = mock_session
        mock_update.side_effect = LookupError("Tool not found")

        tool_id = str(uuid.uuid4())
        payload = {"description": "Updated"}
        response = client.patch(f"/tools/db/{tool_id}", json=payload)

        assert response.status_code == 404

    @patch("workflow_engine_poc.routers.tools.ToolsService.delete_db_tool")
    @patch("workflow_engine_poc.routers.tools.get_db_session")
    @patch("workflow_engine_poc.routers.tools.api_key_or_user_guard")
    @pytest.mark.api
    def test_delete_db_tool_success(self, mock_guard, mock_get_session, mock_delete, mock_session):
        """Test deleting a DB tool"""
        mock_guard.return_value = lambda: "user-123"
        mock_get_session.return_value = mock_session
        mock_delete.return_value = True

        tool_id = str(uuid.uuid4())
        response = client.delete(f"/tools/db/{tool_id}")

        assert response.status_code == 200
        assert response.json()["deleted"] is True

    @patch("workflow_engine_poc.routers.tools.ToolsService.delete_db_tool")
    @patch("workflow_engine_poc.routers.tools.get_db_session")
    @patch("workflow_engine_poc.routers.tools.api_key_or_user_guard")
    @pytest.mark.api
    def test_delete_db_tool_not_found(self, mock_guard, mock_get_session, mock_delete, mock_session):
        """Test deleting non-existent DB tool returns 404"""
        mock_guard.return_value = lambda: "user-123"
        mock_get_session.return_value = mock_session
        mock_delete.return_value = False

        tool_id = str(uuid.uuid4())
        response = client.delete(f"/tools/db/{tool_id}")

        assert response.status_code == 404


@pytest.mark.api
class TestCategoryCRUD:
    """Tests for Tool Category CRUD endpoints"""

    @patch("workflow_engine_poc.routers.tools.ToolsService.create_category")
    @patch("workflow_engine_poc.routers.tools.get_db_session")
    @patch("workflow_engine_poc.routers.tools.api_key_or_user_guard")
    @pytest.mark.api
    def test_create_category_success(self, mock_guard, mock_get_session, mock_create, mock_session, sample_category):
        """Test creating a category"""
        mock_guard.return_value = lambda: "user-123"
        mock_get_session.return_value = mock_session
        mock_create.return_value = sample_category

        payload = {"name": "test_category", "display_name": "Test Category"}

        response = client.post("/tools/categories", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "test_category"

    @patch("workflow_engine_poc.routers.tools.ToolsService.create_category")
    @patch("workflow_engine_poc.routers.tools.get_db_session")
    @patch("workflow_engine_poc.routers.tools.api_key_or_user_guard")
    @pytest.mark.api
    def test_create_category_duplicate(self, mock_guard, mock_get_session, mock_create, mock_session):
        """Test creating duplicate category raises 409"""
        mock_guard.return_value = lambda: "user-123"
        mock_get_session.return_value = mock_session
        mock_create.side_effect = ValueError("Category already exists")

        payload = {"name": "existing_category"}

        response = client.post("/tools/categories", json=payload)

        assert response.status_code == 409

    @patch("workflow_engine_poc.routers.tools.ToolsService.list_categories")
    @patch("workflow_engine_poc.routers.tools.get_db_session")
    @patch("workflow_engine_poc.routers.tools.api_key_or_user_guard")
    @pytest.mark.api
    def test_list_categories(self, mock_guard, mock_get_session, mock_list, mock_session, sample_category):
        """Test listing categories"""
        mock_guard.return_value = lambda: "user-123"
        mock_get_session.return_value = mock_session
        mock_list.return_value = [sample_category]

        response = client.get("/tools/categories")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "test_category"

    @patch("workflow_engine_poc.routers.tools.ToolsService.get_category")
    @patch("workflow_engine_poc.routers.tools.get_db_session")
    @patch("workflow_engine_poc.routers.tools.api_key_or_user_guard")
    @pytest.mark.api
    def test_get_category_success(self, mock_guard, mock_get_session, mock_get, mock_session, sample_category):
        """Test getting a category by ID"""
        mock_guard.return_value = lambda: "user-123"
        mock_get_session.return_value = mock_session
        mock_get.return_value = sample_category

        category_id = str(sample_category.id)
        response = client.get(f"/tools/categories/{category_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "test_category"

    @patch("workflow_engine_poc.routers.tools.ToolsService.get_category")
    @patch("workflow_engine_poc.routers.tools.get_db_session")
    @patch("workflow_engine_poc.routers.tools.api_key_or_user_guard")
    @pytest.mark.api
    def test_get_category_not_found(self, mock_guard, mock_get_session, mock_get, mock_session):
        """Test getting non-existent category returns 404"""
        mock_guard.return_value = lambda: "user-123"
        mock_get_session.return_value = mock_session
        mock_get.return_value = None

        category_id = str(uuid.uuid4())
        response = client.get(f"/tools/categories/{category_id}")

        assert response.status_code == 404

    @patch("workflow_engine_poc.routers.tools.get_category")
    @patch("workflow_engine_poc.routers.tools.ToolsService.update_category")
    @patch("workflow_engine_poc.routers.tools.get_db_session")
    @patch("workflow_engine_poc.routers.tools.api_key_or_user_guard")
    @pytest.mark.api
    def test_update_category_success(self, mock_guard, mock_get_session, mock_update, mock_get, mock_session, sample_category):
        """Test updating a category"""
        mock_guard.return_value = lambda: "user-123"
        mock_get_session.return_value = mock_session
        mock_update.return_value = sample_category

        async def mock_get_category_func(category_id, session):
            return sample_category

        mock_get.side_effect = mock_get_category_func

        category_id = str(sample_category.id)
        payload = {"display_name": "Updated Category"}
        response = client.patch(f"/tools/categories/{category_id}", json=payload)

        assert response.status_code == 200
        mock_update.assert_called_once()

    @patch("workflow_engine_poc.routers.tools.ToolsService.delete_category")
    @patch("workflow_engine_poc.routers.tools.get_db_session")
    @patch("workflow_engine_poc.routers.tools.api_key_or_user_guard")
    @pytest.mark.api
    def test_delete_category_success(self, mock_guard, mock_get_session, mock_delete, mock_session):
        """Test deleting a category"""
        mock_guard.return_value = lambda: "user-123"
        mock_get_session.return_value = mock_session
        mock_delete.return_value = True

        category_id = str(uuid.uuid4())
        response = client.delete(f"/tools/categories/{category_id}")

        assert response.status_code == 200
        assert response.json()["deleted"] is True


@pytest.mark.api
class TestMCPServerCRUD:
    """Tests for MCP Server CRUD endpoints"""

    @patch("workflow_engine_poc.routers.tools.ToolsService.create_mcp_server")
    @patch("workflow_engine_poc.routers.tools.get_db_session")
    @patch("workflow_engine_poc.routers.tools.api_key_or_user_guard")
    @pytest.mark.api
    def test_create_mcp_server_success(self, mock_guard, mock_get_session, mock_create, mock_session, sample_mcp_server):
        """Test creating an MCP server"""
        mock_guard.return_value = lambda: "user-123"
        mock_get_session.return_value = mock_session
        mock_create.return_value = sample_mcp_server

        payload = {
            "name": "test_mcp_server",
            "host": "localhost",
            "port": 8080,
        }

        response = client.post("/tools/mcp-servers", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "test_mcp_server"

    @patch("workflow_engine_poc.routers.tools.ToolsService.list_mcp_servers")
    @patch("workflow_engine_poc.routers.tools.get_db_session")
    @patch("workflow_engine_poc.routers.tools.api_key_or_user_guard")
    @pytest.mark.api
    def test_list_mcp_servers(self, mock_guard, mock_get_session, mock_list, mock_session, sample_mcp_server):
        """Test listing MCP servers"""
        mock_guard.return_value = lambda: "user-123"
        mock_get_session.return_value = mock_session
        mock_list.return_value = [sample_mcp_server]

        response = client.get("/tools/mcp-servers")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "test_mcp_server"

    @patch("workflow_engine_poc.routers.tools.ToolsService.get_mcp_server")
    @patch("workflow_engine_poc.routers.tools.get_db_session")
    @patch("workflow_engine_poc.routers.tools.api_key_or_user_guard")
    @pytest.mark.api
    def test_get_mcp_server_success(self, mock_guard, mock_get_session, mock_get, mock_session, sample_mcp_server):
        """Test getting an MCP server by ID"""
        mock_guard.return_value = lambda: "user-123"
        mock_get_session.return_value = mock_session
        mock_get.return_value = sample_mcp_server

        server_id = str(sample_mcp_server.id)
        response = client.get(f"/tools/mcp-servers/{server_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "test_mcp_server"

    @patch("workflow_engine_poc.routers.tools.ToolsService.delete_mcp_server")
    @patch("workflow_engine_poc.routers.tools.get_db_session")
    @patch("workflow_engine_poc.routers.tools.api_key_or_user_guard")
    @pytest.mark.api
    def test_delete_mcp_server_success(self, mock_guard, mock_get_session, mock_delete, mock_session):
        """Test deleting an MCP server"""
        mock_guard.return_value = lambda: "user-123"
        mock_get_session.return_value = mock_session
        mock_delete.return_value = True

        server_id = str(uuid.uuid4())
        response = client.delete(f"/tools/mcp-servers/{server_id}")

        assert response.status_code == 200
        assert response.json()["deleted"] is True


@pytest.mark.api
class TestSyncTools:
    """Tests for POST /tools/sync endpoint"""

    @patch("workflow_engine_poc.routers.tools.tool_registry.sync_local_to_db")
    @patch("workflow_engine_poc.routers.tools.get_db_session")
    @patch("workflow_engine_poc.routers.tools.api_key_or_user_guard")
    @pytest.mark.api
    def test_sync_tools_local(self, mock_guard, mock_get_session, mock_sync, mock_session):
        """Test syncing local tools to database"""
        mock_guard.return_value = lambda: "user-123"
        mock_get_session.return_value = mock_session
        mock_sync.return_value = {"created": 5, "updated": 2, "skipped": 1}

        response = client.post("/tools/sync", params={"source": "local"})

        assert response.status_code == 200
        data = response.json()
        assert data["source"] == "local"
        assert data["created"] == 5
        assert data["updated"] == 2
        assert data["skipped"] == 1

    @patch("workflow_engine_poc.routers.tools.get_db_session")
    @patch("workflow_engine_poc.routers.tools.api_key_or_user_guard")
    @pytest.mark.api
    def test_sync_tools_unsupported_source(self, mock_guard, mock_get_session, mock_session):
        """Test syncing with unsupported source returns 400"""
        mock_guard.return_value = lambda: "user-123"
        mock_get_session.return_value = mock_session

        response = client.post("/tools/sync", params={"source": "remote"})

        assert response.status_code == 400
        assert "only source=local" in response.json()["detail"].lower()

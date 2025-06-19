"""
Tool Registry Service for Agent Studio

This service provides a hybrid singleton registry + MCP architecture for tool management.
It serves as the central point for tool discovery, loading, and execution.

Phase 1: Basic database-backed tool registry with in-memory caching
Phase 2: Full MCP integration with remote tool execution
"""

import uuid
import importlib
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
from sqlalchemy.orm import Session

from db import crud, models, schemas
from db.database import get_db


class ToolRegistry:
    """
    Singleton tool registry that manages both local and remote tools.

    This registry provides:
    - Database-backed tool persistence
    - In-memory caching for performance
    - Tool discovery and loading
    - Execution routing (local vs remote)
    - Health monitoring for remote tools
    """

    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ToolRegistry, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not self._initialized:
            self._local_tools: Dict[str, Callable] = {}
            self._tool_cache: Dict[str, models.Tool] = {}
            self._mcp_servers: Dict[str, models.MCPServer] = {}
            self._last_cache_refresh = None
            self._cache_ttl = 300  # 5 minutes
            ToolRegistry._initialized = True

    def initialize(self, db: Session):
        """Initialize the registry by loading tools from database."""
        self._refresh_cache(db)
        self._load_local_tools(db)

    def _refresh_cache(self, db: Session):
        """Refresh the in-memory cache from database."""
        # Load all active tools
        tools = crud.get_available_tools(db)
        self._tool_cache = {tool.name: tool for tool in tools}

        # Load all active MCP servers
        servers = crud.get_active_mcp_servers(db)
        self._mcp_servers = {server.name: server for server in servers}

        self._last_cache_refresh = datetime.now()

    def _is_cache_stale(self) -> bool:
        """Check if cache needs refreshing."""
        if self._last_cache_refresh is None:
            return True

        elapsed = (datetime.now() - self._last_cache_refresh).total_seconds()
        return elapsed > self._cache_ttl

    def _load_local_tools(self, db: Session):
        """Load local tools from their module paths."""
        local_tools = crud.get_tools(db, tool_type="local", is_active=True, is_available=True)

        for tool in local_tools:
            try:
                if tool.module_path and tool.function_name:
                    module = importlib.import_module(tool.module_path)
                    func = getattr(module, tool.function_name)
                    self._local_tools[tool.name] = func
                    print(f"Loaded local tool: {tool.name}")
            except Exception as e:
                print(f"Failed to load local tool {tool.name}: {e}")
                # Mark tool as unavailable
                crud.update_tool(db, tool.tool_id, schemas.ToolUpdate(is_available=False))

    def get_tool(self, tool_name: str, db: Session) -> Optional[models.Tool]:
        """Get tool metadata by name."""
        if self._is_cache_stale():
            self._refresh_cache(db)

        return self._tool_cache.get(tool_name)

    def get_available_tools(self, db: Session) -> List[models.Tool]:
        """Get all available tools."""
        if self._is_cache_stale():
            self._refresh_cache(db)

        return list(self._tool_cache.values())

    def get_tools_by_category(self, category_name: str, db: Session) -> List[models.Tool]:
        """Get tools by category name."""
        if self._is_cache_stale():
            self._refresh_cache(db)

        category = crud.get_tool_category_by_name(db, category_name)
        if not category:
            return []

        return [tool for tool in self._tool_cache.values() if tool.category_id == category.category_id]

    async def execute_tool(
        self, tool_name: str, parameters: Dict[str, Any], db: Session, timeout_override: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Execute a tool with given parameters.

        Phase 1: Only local tool execution
        Phase 2: Will add remote MCP tool execution
        """
        tool = self.get_tool(tool_name, db)
        if not tool:
            raise ValueError(f"Tool '{tool_name}' not found")

        if not tool.is_active or not tool.is_available:
            raise ValueError(f"Tool '{tool_name}' is not available")

        start_time = datetime.now()

        try:
            if tool.tool_type == "local":
                result = self._execute_local_tool(tool, parameters)
            elif tool.tool_type == "mcp":
                result = await self._execute_mcp_tool(tool, parameters, db)
            else:
                raise ValueError(f"Unsupported tool type: {tool.tool_type}")

            # Update usage statistics
            execution_time = int((datetime.now() - start_time).total_seconds() * 1000)
            crud.update_tool_usage_stats(db, tool.tool_id, execution_time, True)

            return {
                "status": "success",
                "result": result,
                "execution_time_ms": execution_time,
                "tool_id": str(tool.tool_id),
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            # Update error statistics
            execution_time = int((datetime.now() - start_time).total_seconds() * 1000)
            crud.update_tool_usage_stats(db, tool.tool_id, execution_time, False)

            return {
                "status": "error",
                "error_message": str(e),
                "execution_time_ms": execution_time,
                "tool_id": str(tool.tool_id),
                "timestamp": datetime.now().isoformat(),
            }

    def _execute_local_tool(self, tool: models.Tool, parameters: Dict[str, Any]) -> Any:
        """Execute a local tool function."""
        if tool.name not in self._local_tools:
            raise ValueError(f"Local tool function not loaded: {tool.name}")

        func = self._local_tools[tool.name]

        # Validate parameters against schema if available
        # TODO: Add parameter validation in Phase 2

        return func(**parameters)

    async def _execute_mcp_tool(self, tool: models.Tool, parameters: Dict[str, Any], db: Session) -> Any:
        """Execute a tool on an MCP server."""
        from services.mcp_client import mcp_client, MCPServerUnavailableError, MCPToolExecutionError

        if not tool.mcp_server_id:
            raise ValueError(f"MCP tool '{tool.name}' has no associated server")

        # Get the MCP server
        server = crud.get_mcp_server(db, tool.mcp_server_id)
        if not server:
            raise ValueError(f"MCP server not found for tool '{tool.name}'")

        if server.status != "active":
            raise ValueError(f"MCP server '{server.name}' is not active")

        try:
            # Use remote_name if available, otherwise use tool name
            remote_tool_name = tool.remote_name or tool.name

            # Execute the tool on the MCP server
            result = await mcp_client.execute_tool(server=server, tool_name=remote_tool_name, parameters=parameters)

            return result

        except MCPServerUnavailableError as e:
            # Mark server as unhealthy
            crud.update_mcp_server_health(db, server.server_id, False)
            raise ValueError(f"MCP server '{server.name}' is unavailable: {e}")

        except MCPToolExecutionError as e:
            raise ValueError(f"Tool execution failed on MCP server: {e}")

    def register_local_tool(
        self,
        name: str,
        description: str,
        function: Callable,
        parameters_schema: Dict[str, Any],
        db: Session,
        category_name: Optional[str] = None,
        **kwargs,
    ) -> models.Tool:
        """Register a new local tool."""
        # Get or create category
        category_id = None
        if category_name:
            category = crud.get_tool_category_by_name(db, category_name)
            if not category:
                category = crud.create_tool_category(db, schemas.ToolCategoryCreate(name=category_name))
            category_id = category.category_id

        # Create tool in database
        tool_create = schemas.ToolCreate(
            name=name,
            description=description,
            tool_type="local",
            parameters_schema=parameters_schema,
            module_path=function.__module__,
            function_name=function.__name__,
            category_id=category_id,
            **kwargs,
        )

        tool = crud.create_tool(db, tool_create)

        # Add to local tools cache
        self._local_tools[name] = function
        self._tool_cache[name] = tool

        return tool

    def register_mcp_server(self, server_info: schemas.MCPServerRegistration, db: Session) -> models.MCPServer:
        """Register an MCP server (for self-registration)."""
        # Check if server already exists
        existing = crud.get_mcp_server_by_name(db, server_info.name)
        if existing:
            # Update existing server
            server_update = schemas.MCPServerUpdate(
                description=server_info.description,
                host=server_info.host,
                port=server_info.port,
                protocol=server_info.protocol,
                endpoint=server_info.endpoint,
                version=server_info.version,
                capabilities=server_info.capabilities,
                status="active",
            )
            server = crud.update_mcp_server(db, existing.server_id, server_update)
        else:
            # Create new server
            server_create = schemas.MCPServerCreate(
                name=server_info.name,
                description=server_info.description,
                host=server_info.host,
                port=server_info.port,
                protocol=server_info.protocol,
                endpoint=server_info.endpoint,
                version=server_info.version,
                capabilities=server_info.capabilities,
            )
            server = crud.create_mcp_server(db=db, server=server_create)

        # Update cache
        if server:
            self._mcp_servers[server.name] = server

        # TODO: Register tools from the server in Phase 2

        return server


# Global registry instance
tool_registry = ToolRegistry()

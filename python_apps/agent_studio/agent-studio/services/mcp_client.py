"""
MCP Client for Agent Studio

This module provides HTTP client functionality for communicating with MCP (Model Context Protocol) servers.
It handles tool discovery, execution, health checks, and authentication.

Phase 2: Full MCP integration with remote tool execution
"""

import asyncio
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any
from urllib.parse import urljoin
import httpx
from sqlalchemy.orm import Session

from db import models, schemas
import logging

logger = logging.getLogger(__name__)


class MCPClientError(Exception):
    """Base exception for MCP client errors."""

    pass


class MCPServerUnavailableError(MCPClientError):
    """Raised when MCP server is unavailable."""

    pass


class MCPToolExecutionError(MCPClientError):
    """Raised when tool execution fails on MCP server."""

    pass


class MCPClient:
    """
    HTTP client for communicating with MCP servers.

    Handles tool discovery, execution, health checks, and authentication
    for remote MCP servers.
    """

    def __init__(self, timeout: int = 30, max_retries: int = 3):
        self.timeout = timeout
        self.max_retries = max_retries
        self._client_cache: Dict[str, httpx.AsyncClient] = {}

    async def _get_client(self, server: models.MCPServer) -> httpx.AsyncClient:
        """Get or create an HTTP client for the server."""
        server_key = f"{server.host}:{server.port}"

        if server_key not in self._client_cache:
            # Build base URL
            base_url = f"{server.protocol}://{server.host}:{server.port}"
            if server.endpoint:
                base_url = urljoin(base_url, server.endpoint)

            # Configure authentication
            auth = None
            headers = {}

            if server.auth_type == "bearer" and server.auth_config:
                token = server.auth_config.get("token")
                if token:
                    headers["Authorization"] = f"Bearer {token}"
            elif server.auth_type == "basic" and server.auth_config:
                username = server.auth_config.get("username")
                password = server.auth_config.get("password")
                if username and password:
                    auth = httpx.BasicAuth(username, password)
            elif server.auth_type == "api_key" and server.auth_config:
                api_key = server.auth_config.get("api_key")
                key_header = server.auth_config.get("header", "X-API-Key")
                if api_key:
                    headers[key_header] = api_key

            # Create client
            self._client_cache[server_key] = httpx.AsyncClient(
                base_url=base_url, timeout=self.timeout, auth=auth, headers=headers
            )

        return self._client_cache[server_key]

    async def health_check(self, server: models.MCPServer) -> bool:
        """
        Perform health check on MCP server.

        Args:
            server: MCP server model instance

        Returns:
            True if server is healthy, False otherwise
        """
        try:
            client = await self._get_client(server)

            # Try health check endpoint first
            try:
                response = await client.get("/health")
                if response.status_code == 200:
                    return True
            except httpx.RequestError:
                pass

            # Fallback to tools discovery endpoint
            try:
                response = await client.get("/tools")
                return response.status_code == 200
            except httpx.RequestError:
                return False

        except Exception as e:
            logger.error(f"Health check failed for server {server.name}: {e}")
            return False

    async def discover_tools(self, server: models.MCPServer) -> List[Dict[str, Any]]:
        """
        Discover available tools from MCP server.

        Args:
            server: MCP server model instance

        Returns:
            List of tool definitions

        Raises:
            MCPServerUnavailableError: If server is not reachable
            MCPClientError: If discovery fails
        """
        try:
            client = await self._get_client(server)

            for attempt in range(self.max_retries):
                try:
                    response = await client.get("/tools")

                    if response.status_code == 200:
                        data = response.json()

                        # Handle different response formats
                        if isinstance(data, list):
                            return data
                        elif isinstance(data, dict) and "tools" in data:
                            return data["tools"]
                        else:
                            logger.warning(f"Unexpected tools response format from {server.name}: {data}")
                            return []

                    elif response.status_code == 404:
                        # Server doesn't support tool discovery
                        logger.info(f"Server {server.name} doesn't support tool discovery")
                        return []

                    else:
                        logger.warning(f"Tool discovery failed for {server.name}: {response.status_code}")
                        if attempt == self.max_retries - 1:
                            raise MCPClientError(f"Tool discovery failed: HTTP {response.status_code}")

                except httpx.RequestError as e:
                    if attempt == self.max_retries - 1:
                        raise MCPServerUnavailableError(f"Server {server.name} is unavailable: {e}")

                    # Wait before retry
                    try:
                        await asyncio.sleep(2**attempt)
                    except asyncio.CancelledError:
                        # If cancelled during retry wait, re-raise to exit gracefully
                        raise

        except MCPServerUnavailableError:
            raise
        except Exception as e:
            raise MCPClientError(f"Tool discovery failed for {server.name}: {e}")

        # Return empty list as fallback to ensure a return value on all code paths
        return []

    async def execute_tool(
        self, server: models.MCPServer, tool_name: str, parameters: Dict[str, Any], execution_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Execute a tool on the MCP server.

        Args:
            server: MCP server model instance
            tool_name: Name of the tool to execute
            parameters: Tool execution parameters
            execution_id: Optional execution ID for tracking

        Returns:
            Tool execution result

        Raises:
            MCPServerUnavailableError: If server is not reachable
            MCPToolExecutionError: If tool execution fails
        """
        if not execution_id:
            execution_id = str(uuid.uuid4())

        try:
            client = await self._get_client(server)

            # Prepare execution request
            request_data = {
                "tool": tool_name,
                "parameters": parameters,
                "execution_id": execution_id,
                "timestamp": datetime.now().isoformat(),
            }

            for attempt in range(self.max_retries):
                try:
                    response = await client.post("/execute", json=request_data)

                    if response.status_code == 200:
                        return response.json()

                    elif response.status_code == 400:
                        # Bad request - don't retry
                        error_data = (
                            response.json()
                            if response.headers.get("content-type", "").startswith("application/json")
                            else {"error": response.text}
                        )
                        raise MCPToolExecutionError(f"Tool execution failed: {error_data}")

                    elif response.status_code == 404:
                        raise MCPToolExecutionError(f"Tool '{tool_name}' not found on server {server.name}")

                    else:
                        logger.warning(f"Tool execution failed for {tool_name} on {server.name}: {response.status_code}")
                        if attempt == self.max_retries - 1:
                            raise MCPToolExecutionError(f"Tool execution failed: HTTP {response.status_code}")

                except httpx.RequestError as e:
                    if attempt == self.max_retries - 1:
                        raise MCPServerUnavailableError(f"Server {server.name} is unavailable: {e}")

                    # Wait before retry
                    try:
                        await asyncio.sleep(2**attempt)
                    except asyncio.CancelledError:
                        # If cancelled during retry wait, re-raise to exit gracefully
                        raise

        except (MCPServerUnavailableError, MCPToolExecutionError):
            raise
        except Exception as e:
            raise MCPToolExecutionError(f"Tool execution failed for {tool_name} on {server.name}: {e}")

        # This should never be reached, but added for type safety
        raise MCPToolExecutionError(f"Unexpected error during tool execution for {tool_name} on {server.name}")

    async def close(self):
        """Close all HTTP clients."""
        for client in self._client_cache.values():
            await client.aclose()
        self._client_cache.clear()

    async def get_tool_schema(self, server: models.MCPServer, tool_name: str) -> Optional[Dict[str, Any]]:
        """
        Get schema for a specific tool from MCP server.

        Args:
            server: MCP server model instance
            tool_name: Name of the tool

        Returns:
            Tool schema or None if not found
        """
        try:
            client = await self._get_client(server)
            response = await client.get(f"/tools/{tool_name}/schema")

            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                return None
            else:
                logger.warning(f"Failed to get schema for tool {tool_name} from {server.name}: {response.status_code}")
                return None

        except Exception as e:
            logger.error(f"Error getting tool schema for {tool_name} from {server.name}: {e}")
            return None

    async def register_tools_from_server(
        self, server: models.MCPServer, db: Session, category_id: Optional[uuid.UUID] = None
    ) -> List[models.Tool]:
        """
        Discover and register all tools from an MCP server.

        Args:
            server: MCP server model instance
            db: Database session
            category_id: Optional category to assign tools to

        Returns:
            List of registered tool models
        """
        from db import crud  # Import here to avoid circular imports

        try:
            tools_data = await self.discover_tools(server)
            registered_tools = []

            for tool_data in tools_data:
                try:
                    # Extract tool information
                    tool_name = tool_data.get("name")
                    if not tool_name:
                        logger.warning(f"Tool missing name in data from {server.name}: {tool_data}")
                        continue

                    # Check if tool already exists for this server
                    existing_tool = crud.get_tool_by_mcp_server_and_name(db, server.server_id, tool_name)
                    if existing_tool:
                        logger.info(f"Tool {tool_name} already exists for server {server.name}, skipping")
                        continue

                    # Create tool record
                    tool_create = schemas.ToolCreate(
                        name=tool_name,
                        display_name=tool_data.get("display_name", tool_name),
                        description=tool_data.get("description", ""),
                        version=tool_data.get("version", "1.0.0"),
                        tool_type="mcp",
                        execution_type="api",
                        parameters_schema=tool_data.get("parameters_schema", {}),
                        return_schema=tool_data.get("return_schema"),
                        remote_name=tool_name,
                        tags=tool_data.get("tags", []),
                        requires_auth=tool_data.get("requires_auth", False),
                        timeout_seconds=tool_data.get("timeout_seconds", 30),
                        category_id=category_id,
                        mcp_server_id=server.server_id,
                        created_by="mcp_auto_registration",
                    )

                    tool = crud.create_tool(db, tool_create)
                    registered_tools.append(tool)
                    logger.info(f"Registered tool {tool_name} from server {server.name}")

                except Exception as e:
                    logger.error(f"Failed to register tool {tool_data.get('name', 'unknown')} from {server.name}: {e}")
                    continue

            return registered_tools

        except Exception as e:
            logger.error(f"Failed to register tools from server {server.name}: {e}")
            return []


class MCPHealthMonitor:
    """
    Background service for monitoring MCP server health and updating status.
    """

    def __init__(self, client: MCPClient, check_interval: int = 300):
        self.client = client
        self.check_interval = check_interval  # seconds
        self._running = False
        self._task: Optional[asyncio.Task] = None

    async def start_monitoring(self, db_session_factory):
        """Start the health monitoring background task."""
        if self._running:
            return

        self._running = True
        self._task = asyncio.create_task(self._monitor_loop(db_session_factory))
        logger.info("MCP health monitoring started")

    async def stop_monitoring(self):
        """Stop the health monitoring background task."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("MCP health monitoring stopped")

    async def _monitor_loop(self, db_session_factory):
        """Main monitoring loop."""
        from db import crud  # Import here to avoid circular imports

        try:
            while self._running:
                try:
                    # Get database session
                    db = db_session_factory()

                    try:
                        # Get all active MCP servers
                        servers = crud.get_mcp_servers(db, skip=0, limit=1000)

                        for server in servers:
                            if not self._running:
                                break

                            try:
                                # Perform health check
                                is_healthy = await self.client.health_check(server)

                                # Update server status
                                crud.update_mcp_server_health(db, server.server_id, is_healthy)

                                if is_healthy:
                                    logger.debug(f"Health check passed for server {server.name}")
                                else:
                                    logger.warning(f"Health check failed for server {server.name}")

                            except Exception as e:
                                logger.error(f"Error during health check for server {server.name}: {e}")
                                # Mark as unhealthy
                                crud.update_mcp_server_health(db, server.server_id, False)

                    finally:
                        db.close()

                    # Wait before next check
                    await asyncio.sleep(self.check_interval)

                except asyncio.CancelledError:
                    # Task was cancelled, exit gracefully
                    logger.debug("MCP health monitoring loop cancelled")
                    break
                except Exception as e:
                    logger.error(f"Error in health monitoring loop: {e}")
                    try:
                        await asyncio.sleep(60)  # Wait a minute before retrying
                    except asyncio.CancelledError:
                        # If cancelled during error recovery sleep, exit gracefully
                        logger.debug("MCP health monitoring loop cancelled during error recovery")
                        break
        except asyncio.CancelledError:
            # Handle cancellation at the top level
            logger.debug("MCP health monitoring loop cancelled at top level")
            pass


# Global MCP client instance
mcp_client = MCPClient()

# Global health monitor instance
mcp_health_monitor = MCPHealthMonitor(mcp_client)

"""
MCP Client for Workflow Core SDK

This module provides HTTP client functionality for communicating with MCP (Model Context Protocol) servers.
It handles tool discovery, execution, health checks, and authentication.

Supports both:
- Modern Streamable HTTP transport (JSON-RPC 2.0, MCP 2025-06-18)
- Legacy HTTP+SSE transport (REST-style, MCP 2024-11-05)

Based on Agent Studio's MCP client implementation, adapted for workflow-core-sdk.
"""

import asyncio
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any, Literal
import httpx
import logging

logger = logging.getLogger(__name__)

# MCP Protocol Transport Types
MCPTransportType = Literal["auto", "streamable_http", "http_sse"]


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

    Supports both modern Streamable HTTP (JSON-RPC 2.0) and legacy HTTP+SSE transports.
    """

    def __init__(self, timeout: int = 30, max_retries: int = 3, transport: MCPTransportType = "auto"):
        self.timeout = timeout
        self.max_retries = max_retries
        self.transport = transport
        self._client_cache: Dict[str, httpx.AsyncClient] = {}
        self._transport_cache: Dict[str, MCPTransportType] = {}  # Cache detected transport per server
        self._session_cache: Dict[str, str] = {}  # Cache session IDs per server (for Streamable HTTP)
        self._jsonrpc_id_counter = 0

    async def close(self):
        """
        Close all cached HTTP clients and terminate active sessions.

        Per MCP spec: Clients SHOULD send a DELETE request to terminate sessions gracefully.
        """
        # Terminate all active sessions
        for server_key, session_id in list(self._session_cache.items()):
            try:
                await self._terminate_session(server_key, session_id)
            except Exception as e:
                logger.warning(f"Failed to terminate session for {server_key}: {e}")

        # Close HTTP clients
        for client in self._client_cache.values():
            await client.aclose()

        # Clear all caches
        self._client_cache.clear()
        self._transport_cache.clear()
        self._session_cache.clear()

    async def _terminate_session(self, server_key: str, session_id: str) -> None:
        """
        Terminate an active MCP session.

        Per MCP spec: Clients SHOULD send HTTP DELETE to terminate sessions gracefully.

        Args:
            server_key: Server identifier (host:port)
            session_id: Session ID to terminate
        """
        if server_key not in self._client_cache:
            return

        client = self._client_cache[server_key]
        endpoint = getattr(client, "_mcp_endpoint", "")

        headers = {
            "MCP-Protocol-Version": "2025-06-18",
            "Mcp-Session-Id": session_id,
        }

        try:
            response = await client.delete(endpoint, headers=headers)

            # Per spec: Server SHOULD respond with 200 OK or 204 No Content
            if response.status_code in [200, 204]:
                logger.info(f"Successfully terminated session {session_id} for {server_key}")
            else:
                logger.warning(f"Unexpected status code when terminating session: {response.status_code}")
        except Exception as e:
            logger.warning(f"Failed to send DELETE for session termination: {e}")

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()

    async def _get_client(self, server_config: Dict[str, Any]) -> httpx.AsyncClient:
        """
        Get or create an HTTP client for the server.

        Args:
            server_config: Dictionary with server configuration:
                - host: str
                - port: int
                - protocol: str (http|https|ws|wss)
                - endpoint: Optional[str]
                - auth_type: Optional[str] (none|bearer|basic|api_key)
                - auth_config: Optional[Dict[str, Any]]

        Returns:
            Configured httpx.AsyncClient instance
        """
        host = server_config.get("host", "localhost")
        port = server_config.get("port", 8080)
        protocol = server_config.get("protocol", "http")
        endpoint = server_config.get("endpoint")
        auth_type = server_config.get("auth_type")
        auth_config = server_config.get("auth_config", {})

        server_key = f"{host}:{port}"

        if server_key not in self._client_cache:
            # Build base URL - just protocol://host:port, no path
            # We'll add the endpoint path in each request to avoid trailing slash issues
            base_url = f"{protocol}://{host}:{port}"

            # Configure authentication
            auth = None
            headers = {}

            if auth_type == "bearer" and auth_config:
                token = auth_config.get("token")
                if token:
                    headers["Authorization"] = f"Bearer {token}"
            elif auth_type == "basic" and auth_config:
                username = auth_config.get("username")
                password = auth_config.get("password")
                if username and password:
                    auth = httpx.BasicAuth(username, password)
            elif auth_type == "api_key" and auth_config:
                api_key = auth_config.get("api_key")
                key_header = auth_config.get("header", "X-API-Key")
                if api_key:
                    headers[key_header] = api_key

            # Create client - disable automatic redirect following for MCP
            # Store endpoint in client for later use
            client = httpx.AsyncClient(
                base_url=base_url, timeout=self.timeout, auth=auth, headers=headers, follow_redirects=False
            )
            # Store endpoint path separately
            client._mcp_endpoint = endpoint or ""  # type: ignore
            self._client_cache[server_key] = client

        return self._client_cache[server_key]

    def _get_next_jsonrpc_id(self) -> int:
        """Get next JSON-RPC request ID."""
        self._jsonrpc_id_counter += 1
        return self._jsonrpc_id_counter

    async def _detect_transport(self, server_config: Dict[str, Any]) -> MCPTransportType:
        """
        Detect which transport the server uses.

        Per MCP spec, try Streamable HTTP first (POST with JSON-RPC),
        then fall back to HTTP+SSE (GET for SSE stream).

        Args:
            server_config: Server configuration dictionary

        Returns:
            Detected transport type
        """
        host = server_config.get("host", "localhost")
        port = server_config.get("port", 8080)
        server_key = f"{host}:{port}"

        # Check cache first
        if server_key in self._transport_cache:
            return self._transport_cache[server_key]

        # Try Streamable HTTP (JSON-RPC 2.0) first by attempting to initialize a session
        try:
            session_id = await self._initialize_session(server_config)
            if session_id:
                logger.info(f"Detected Streamable HTTP transport for {server_key}")
                self._transport_cache[server_key] = "streamable_http"
                return "streamable_http"
        except Exception as e:
            logger.debug(f"Streamable HTTP detection failed for {server_key}: {e}")

        # Fall back to HTTP+SSE
        logger.info(f"Falling back to HTTP+SSE transport for {server_key}")
        self._transport_cache[server_key] = "http_sse"
        return "http_sse"

    async def _initialize_session(self, server_config: Dict[str, Any]) -> Optional[str]:
        """
        Initialize a session with the MCP server.

        Implements the MCP 2025-06-18 initialization handshake:
        1. Send InitializeRequest
        2. Receive InitializeResponse with optional Mcp-Session-Id header
        3. Send initialized notification

        Args:
            server_config: Server configuration dictionary

        Returns:
            Session ID if server supports sessions, None otherwise

        Raises:
            MCPClientError: If initialization fails
        """
        host = server_config.get("host", "localhost")
        port = server_config.get("port", 8080)
        server_key = f"{host}:{port}"

        # Check if we already have a session
        if server_key in self._session_cache:
            return self._session_cache[server_key]

        client = await self._get_client(server_config)
        endpoint = getattr(client, "_mcp_endpoint", "")

        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
        }

        # Step 1: Send InitializeRequest with capabilities
        request_data = {
            "jsonrpc": "2.0",
            "id": self._get_next_jsonrpc_id(),
            "method": "initialize",
            "params": {
                "protocolVersion": "2025-06-18",
                "capabilities": {
                    "roots": {},  # Support for filesystem roots
                    "sampling": {},  # Support for LLM sampling
                },
                "clientInfo": {
                    "name": "workflow-core-sdk",
                    "version": "1.0.0",
                },
            },
        }

        try:
            # Step 2: Receive InitializeResponse
            response = await client.post(endpoint, json=request_data, headers=headers)

            if response.status_code not in [200, 201]:
                raise MCPClientError(f"Session initialization failed: HTTP {response.status_code}")

            # Extract session ID from response header (optional per MCP spec)
            session_id = response.headers.get("mcp-session-id")

            if session_id:
                # Cache the session ID
                self._session_cache[server_key] = session_id
                logger.info(f"Initialized MCP session for {server_key}: {session_id}")
            else:
                logger.info(f"Server {server_key} does not use session management")

            # Step 3: Send initialized notification
            # Per MCP spec: "After successful initialization, the client MUST send an
            # initialized notification to indicate it is ready to begin normal operations"
            await self._send_initialized_notification(server_config, session_id)

            return session_id

        except httpx.RequestError as e:
            raise MCPServerUnavailableError(f"Server {server_config.get('host')} is unavailable: {e}")
        except MCPClientError:
            raise
        except Exception as e:
            raise MCPClientError(f"Session initialization failed: {e}")

    async def _send_initialized_notification(self, server_config: Dict[str, Any], session_id: Optional[str]) -> None:
        """
        Send the 'initialized' notification after successful initialization.

        Per MCP spec: The client MUST send this notification after receiving InitializeResponse.

        Args:
            server_config: Server configuration dictionary
            session_id: Optional session ID from initialization
        """
        client = await self._get_client(server_config)
        endpoint = getattr(client, "_mcp_endpoint", "")

        headers = {
            "Content-Type": "application/json",
            "MCP-Protocol-Version": "2025-06-18",  # MUST include on all requests after init
        }

        if session_id:
            headers["Mcp-Session-Id"] = session_id

        notification_data = {
            "jsonrpc": "2.0",
            "method": "notifications/initialized",
        }

        try:
            response = await client.post(endpoint, json=notification_data, headers=headers)

            # Per spec: Server MUST respond with 202 Accepted for notifications
            if response.status_code != 202:
                logger.warning(f"Unexpected status code for initialized notification: {response.status_code}")
        except Exception as e:
            logger.warning(f"Failed to send initialized notification: {e}")

    def _parse_sse_response(self, sse_text: str) -> Dict[str, Any]:
        """
        Parse SSE (Server-Sent Events) response to extract JSON-RPC message.

        Args:
            sse_text: Raw SSE response text

        Returns:
            Parsed JSON-RPC message

        Raises:
            MCPClientError: If parsing fails
        """
        import json

        # SSE format:
        # event: message
        # data: {"jsonrpc":"2.0",...}
        #
        # We need to extract the data field
        lines = sse_text.strip().split("\n")
        data_lines = []

        for line in lines:
            if line.startswith("data: "):
                data_lines.append(line[6:])  # Remove "data: " prefix

        if not data_lines:
            raise MCPClientError("No data found in SSE response")

        # Join all data lines (in case data is split across multiple lines)
        data_json = "\n".join(data_lines)

        try:
            return json.loads(data_json)
        except json.JSONDecodeError as e:
            raise MCPClientError(f"Failed to parse SSE data as JSON: {e}")

    async def _jsonrpc_request(
        self, server_config: Dict[str, Any], method: str, params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Make a JSON-RPC 2.0 request to the server.

        Args:
            server_config: Server configuration dictionary
            method: JSON-RPC method name
            params: Optional method parameters

        Returns:
            JSON-RPC result

        Raises:
            MCPClientError: If request fails
        """
        # Initialize session if needed (except for initialize method itself)
        session_id = None
        if method != "initialize":
            session_id = await self._initialize_session(server_config)

        client = await self._get_client(server_config)

        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
        }

        # Per MCP spec: MUST include protocol version header on all requests after initialization
        if method != "initialize":
            headers["MCP-Protocol-Version"] = "2025-06-18"

        # Add session ID header if we have one
        if session_id:
            headers["Mcp-Session-Id"] = session_id

        request_data = {
            "jsonrpc": "2.0",
            "id": self._get_next_jsonrpc_id(),
            "method": method,
        }

        if params is not None:
            request_data["params"] = params

        try:
            # Get the endpoint path from the client (stored during client creation)
            endpoint = getattr(client, "_mcp_endpoint", "")
            logger.debug(f"JSON-RPC request to endpoint: {repr(endpoint)}, method: {method}")
            # Post to the endpoint path without trailing slash
            response = await client.post(endpoint, json=request_data, headers=headers)

            if response.status_code not in [200, 201]:
                raise MCPClientError(f"JSON-RPC request failed: HTTP {response.status_code}")

            # Check Content-Type to determine how to parse response
            content_type = response.headers.get("content-type", "")

            if "text/event-stream" in content_type:
                # Parse SSE response
                logger.debug("Parsing SSE response")
                data = self._parse_sse_response(response.text)
            else:
                # Parse JSON response
                logger.debug("Parsing JSON response")
                data = response.json()

            if "error" in data:
                error = data["error"]
                raise MCPClientError(f"JSON-RPC error: {error.get('message', 'Unknown error')}")

            if "result" not in data:
                raise MCPClientError("JSON-RPC response missing 'result' field")

            return data["result"]

        except httpx.RequestError as e:
            raise MCPServerUnavailableError(f"Server {server_config.get('host')} is unavailable: {e}")
        except MCPClientError:
            raise
        except Exception as e:
            raise MCPClientError(f"JSON-RPC request failed: {e}")

    async def health_check(self, server_config: Dict[str, Any]) -> bool:
        """
        Perform health check on MCP server.

        Args:
            server_config: Server configuration dictionary

        Returns:
            True if server is healthy, False otherwise
        """
        try:
            # Detect transport if not already known
            transport = self.transport
            if transport == "auto":
                try:
                    transport = await self._detect_transport(server_config)
                    return True  # If detection succeeds, server is healthy
                except Exception:
                    return False

            # Use appropriate transport
            if transport == "streamable_http":
                return await self._health_check_jsonrpc(server_config)
            else:
                return await self._health_check_http_sse(server_config)

        except Exception as e:
            logger.error(f"Health check failed for server {server_config.get('host')}: {e}")
            return False

    async def _health_check_jsonrpc(self, server_config: Dict[str, Any]) -> bool:
        """Health check using JSON-RPC (Streamable HTTP transport)."""
        try:
            # Try to call ping method
            await self._jsonrpc_request(server_config, "ping")
            return True
        except Exception:
            # If ping fails, try initialize
            try:
                await self._jsonrpc_request(
                    server_config,
                    "initialize",
                    {
                        "protocolVersion": "2025-06-18",
                        "capabilities": {},
                        "clientInfo": {"name": "workflow-core-sdk", "version": "1.0.0"},
                    },
                )
                return True
            except Exception:
                return False

    async def _health_check_http_sse(self, server_config: Dict[str, Any]) -> bool:
        """Health check using HTTP+SSE transport (legacy)."""
        try:
            client = await self._get_client(server_config)

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

        except Exception:
            return False

    async def discover_tools(self, server_config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Discover available tools from MCP server.

        Args:
            server_config: Server configuration dictionary

        Returns:
            List of tool definitions

        Raises:
            MCPServerUnavailableError: If server is not reachable
            MCPClientError: If discovery fails
        """
        try:
            # Detect transport if not already known
            transport = self.transport
            if transport == "auto":
                transport = await self._detect_transport(server_config)

            # Use appropriate transport
            if transport == "streamable_http":
                return await self._discover_tools_jsonrpc(server_config)
            else:
                return await self._discover_tools_http_sse(server_config)

        except (MCPServerUnavailableError, MCPClientError):
            raise
        except Exception as e:
            raise MCPClientError(f"Tool discovery failed for {server_config.get('host')}: {e}")

    async def _discover_tools_jsonrpc(self, server_config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Discover tools using JSON-RPC (Streamable HTTP transport)."""
        try:
            result = await self._jsonrpc_request(server_config, "tools/list")

            # Handle different response formats
            if isinstance(result, list):
                return result
            elif isinstance(result, dict) and "tools" in result:
                return result["tools"]
            else:
                logger.warning(f"Unexpected tools response format from {server_config.get('host')}: {result}")
                return []

        except Exception as e:
            logger.error(f"JSON-RPC tool discovery failed for {server_config.get('host')}: {e}")
            raise

    async def _discover_tools_http_sse(self, server_config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Discover tools using HTTP+SSE transport (legacy)."""
        try:
            client = await self._get_client(server_config)

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
                            logger.warning(f"Unexpected tools response format from {server_config.get('host')}: {data}")
                            return []

                    elif response.status_code == 404:
                        # Server doesn't support tool discovery
                        logger.info(f"Server {server_config.get('host')} doesn't support tool discovery")
                        return []

                    else:
                        logger.warning(f"Tool discovery failed for {server_config.get('host')}: {response.status_code}")
                        if attempt == self.max_retries - 1:
                            raise MCPClientError(f"Tool discovery failed: HTTP {response.status_code}")

                except httpx.RequestError as e:
                    if attempt == self.max_retries - 1:
                        raise MCPServerUnavailableError(f"Server {server_config.get('host')} is unavailable: {e}")

                    # Wait before retry
                    await asyncio.sleep(2**attempt)

        except MCPServerUnavailableError:
            raise
        except Exception as e:
            raise MCPClientError(f"HTTP+SSE tool discovery failed for {server_config.get('host')}: {e}")

        return []

    async def execute_tool(
        self,
        server_config: Dict[str, Any],
        tool_name: str,
        parameters: Dict[str, Any],
        execution_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Execute a tool on the MCP server.

        Args:
            server_config: Server configuration dictionary
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
            # Detect transport if not already known
            transport = self.transport
            if transport == "auto":
                transport = await self._detect_transport(server_config)

            # Use appropriate transport
            if transport == "streamable_http":
                return await self._execute_tool_jsonrpc(server_config, tool_name, parameters, execution_id)
            else:
                return await self._execute_tool_http_sse(server_config, tool_name, parameters, execution_id)

        except (MCPServerUnavailableError, MCPToolExecutionError):
            raise
        except Exception as e:
            raise MCPToolExecutionError(f"Tool execution failed for {tool_name} on {server_config.get('host')}: {e}")

    async def _execute_tool_jsonrpc(
        self, server_config: Dict[str, Any], tool_name: str, parameters: Dict[str, Any], execution_id: str
    ) -> Dict[str, Any]:
        """Execute tool using JSON-RPC (Streamable HTTP transport)."""
        try:
            params = {
                "name": tool_name,
                "arguments": parameters,
            }

            result = await self._jsonrpc_request(server_config, "tools/call", params)
            return result

        except MCPClientError as e:
            raise MCPToolExecutionError(f"Tool execution failed for {tool_name}: {e}")
        except Exception as e:
            raise MCPToolExecutionError(f"Tool execution failed for {tool_name}: {e}")

    async def _execute_tool_http_sse(
        self, server_config: Dict[str, Any], tool_name: str, parameters: Dict[str, Any], execution_id: str
    ) -> Dict[str, Any]:
        """Execute tool using HTTP+SSE transport (legacy)."""
        try:
            client = await self._get_client(server_config)

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
                        raise MCPToolExecutionError(f"Tool '{tool_name}' not found on server {server_config.get('host')}")

                    else:
                        logger.warning(
                            f"Tool execution failed for {tool_name} on {server_config.get('host')}: {response.status_code}"
                        )
                        if attempt == self.max_retries - 1:
                            raise MCPToolExecutionError(f"Tool execution failed: HTTP {response.status_code}")

                except httpx.RequestError as e:
                    if attempt == self.max_retries - 1:
                        raise MCPServerUnavailableError(f"Server {server_config.get('host')} is unavailable: {e}")

                    # Wait before retry
                    await asyncio.sleep(2**attempt)

        except (MCPServerUnavailableError, MCPToolExecutionError):
            raise
        except Exception as e:
            raise MCPToolExecutionError(f"HTTP+SSE tool execution failed for {tool_name}: {e}")

        raise MCPToolExecutionError(f"Unexpected error during tool execution for {tool_name}")

    async def close(self):
        """Close all HTTP clients."""
        for client in self._client_cache.values():
            await client.aclose()
        self._client_cache.clear()


# Global MCP client instance
mcp_client = MCPClient()

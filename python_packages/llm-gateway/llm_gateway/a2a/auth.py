"""Authentication interceptors for A2A client requests.

This module provides ClientCallInterceptor implementations for various
authentication methods supported by A2A agents.
"""

import logging
import time
from typing import Any, Dict, Optional, Tuple

import httpx
from a2a.client import ClientCallInterceptor
from a2a.client.middleware import ClientCallContext
from a2a.types import AgentCard

from .types import A2AAuthConfig


logger = logging.getLogger(__name__)


class BearerTokenInterceptor(ClientCallInterceptor):
    """Interceptor that adds Bearer token authentication to requests."""

    def __init__(self, token: str):
        """Initialize with a bearer token.

        Args:
            token: The bearer token to use for authentication.
        """
        self._token = token

    async def intercept(
        self,
        method_name: str,
        request_payload: Dict[str, Any],
        http_kwargs: Dict[str, Any],
        agent_card: AgentCard | None,
        context: ClientCallContext | None,
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """Add Authorization header with Bearer token."""
        headers = http_kwargs.get("headers", {})
        headers["Authorization"] = f"Bearer {self._token}"
        http_kwargs["headers"] = headers
        return request_payload, http_kwargs


class ApiKeyInterceptor(ClientCallInterceptor):
    """Interceptor that adds API key authentication to requests."""

    def __init__(self, api_key: str, header_name: str = "X-API-Key"):
        """Initialize with an API key.

        Args:
            api_key: The API key to use for authentication.
            header_name: The header name to use (default: X-API-Key).
        """
        self._api_key = api_key
        self._header_name = header_name

    async def intercept(
        self,
        method_name: str,
        request_payload: Dict[str, Any],
        http_kwargs: Dict[str, Any],
        agent_card: AgentCard | None,
        context: ClientCallContext | None,
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """Add API key header."""
        headers = http_kwargs.get("headers", {})
        headers[self._header_name] = self._api_key
        http_kwargs["headers"] = headers
        return request_payload, http_kwargs


class OAuth2Interceptor(ClientCallInterceptor):
    """Interceptor that handles OAuth2 authentication with token refresh."""

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        token_url: str,
        scope: Optional[str] = None,
    ):
        """Initialize OAuth2 interceptor.

        Args:
            client_id: OAuth2 client ID.
            client_secret: OAuth2 client secret.
            token_url: URL to fetch access tokens.
            scope: Optional OAuth2 scope.
        """
        self._client_id = client_id
        self._client_secret = client_secret
        self._token_url = token_url
        self._scope = scope
        self._access_token: Optional[str] = None
        self._token_expires_at: float = 0

    async def _refresh_token(self) -> None:
        """Fetch a new access token using client credentials flow."""
        async with httpx.AsyncClient() as client:
            data = {
                "grant_type": "client_credentials",
                "client_id": self._client_id,
                "client_secret": self._client_secret,
            }
            if self._scope:
                data["scope"] = self._scope

            response = await client.post(self._token_url, data=data)
            response.raise_for_status()
            token_data = response.json()

            self._access_token = token_data["access_token"]
            # Set expiry with 60 second buffer
            expires_in = token_data.get("expires_in", 3600)
            self._token_expires_at = time.time() + expires_in - 60
            logger.debug(f"OAuth2 token refreshed, expires in {expires_in}s")

    async def intercept(
        self,
        method_name: str,
        request_payload: Dict[str, Any],
        http_kwargs: Dict[str, Any],
        agent_card: AgentCard | None,
        context: ClientCallContext | None,
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """Add Authorization header with OAuth2 access token, refreshing if needed."""
        # Refresh token if expired or not yet fetched
        if not self._access_token or time.time() >= self._token_expires_at:
            await self._refresh_token()

        headers = http_kwargs.get("headers", {})
        headers["Authorization"] = f"Bearer {self._access_token}"
        http_kwargs["headers"] = headers
        return request_payload, http_kwargs


def create_auth_interceptor(
    auth_config: A2AAuthConfig,
) -> Optional[ClientCallInterceptor]:
    """Create an appropriate interceptor based on auth configuration.

    Args:
        auth_config: The authentication configuration.

    Returns:
        A ClientCallInterceptor instance, or None if auth_type is 'none'.

    Raises:
        ValueError: If required credentials are missing.
    """
    if auth_config.auth_type == "none" or not auth_config.credentials:
        return None

    creds = auth_config.credentials

    if auth_config.auth_type == "bearer":
        token = creds.get("token")
        if not token:
            raise ValueError("Bearer auth requires 'token' in credentials")
        return BearerTokenInterceptor(token)

    elif auth_config.auth_type == "api_key":
        key = creds.get("key")
        if not key:
            raise ValueError("API key auth requires 'key' in credentials")
        header_name = creds.get("header_name", "X-API-Key")
        return ApiKeyInterceptor(key, header_name)

    elif auth_config.auth_type == "oauth2":
        required = ["client_id", "client_secret", "token_url"]
        missing = [k for k in required if not creds.get(k)]
        if missing:
            raise ValueError(f"OAuth2 auth requires: {', '.join(missing)}")
        return OAuth2Interceptor(
            client_id=creds["client_id"],
            client_secret=creds["client_secret"],
            token_url=creds["token_url"],
            scope=creds.get("scope"),
        )

    return None

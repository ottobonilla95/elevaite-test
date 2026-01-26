"""
Brutal unit tests for rbac_sdk.async_client (asynchronous client).

These tests cover:
- Happy path scenarios
- Network failures and timeouts
- Malformed responses
- Edge cases and boundary conditions
- Fail-closed semantics (errors return False, not exceptions)
"""

import pytest
import httpx
from unittest.mock import patch, Mock, AsyncMock
from rbac_sdk.async_client import check_access_async


class TestCheckAccessAsyncHappyPath:
    """Test successful authorization checks."""

    @pytest.mark.asyncio
    @patch("rbac_sdk.async_client.httpx.AsyncClient")
    async def test_check_access_allowed(self, mock_client_class, sample_user_id, sample_action, sample_resource):
        """Test that check_access_async returns True when allowed."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"allowed": True}

        mock_client = AsyncMock()
        mock_client.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
        mock_client_class.return_value = mock_client

        result = await check_access_async(
            user_id=sample_user_id,
            action=sample_action,
            resource=sample_resource,
        )

        assert result is True

    @pytest.mark.asyncio
    @patch("rbac_sdk.async_client.httpx.AsyncClient")
    async def test_check_access_denied(self, mock_client_class, sample_user_id, sample_action, sample_resource):
        """Test that check_access_async returns False when denied."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"allowed": False, "deny_reason": "insufficient_permissions"}

        mock_client = AsyncMock()
        mock_client.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
        mock_client_class.return_value = mock_client

        result = await check_access_async(
            user_id=sample_user_id,
            action=sample_action,
            resource=sample_resource,
        )

        assert result is False

    @pytest.mark.asyncio
    @patch("rbac_sdk.async_client.httpx.AsyncClient")
    async def test_check_access_with_custom_base_url(self, mock_client_class, sample_user_id, sample_action, sample_resource):
        """Test that custom base_url is used correctly."""
        custom_url = "http://custom-auth-api:9000"
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"allowed": True}

        mock_client = AsyncMock()
        mock_post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__.return_value.post = mock_post
        mock_client_class.return_value = mock_client

        await check_access_async(
            user_id=sample_user_id,
            action=sample_action,
            resource=sample_resource,
            base_url=custom_url,
        )

        # Verify the URL was constructed correctly
        call_args = mock_post.call_args
        assert call_args[0][0] == f"{custom_url}/api/authz/check_access"

    @pytest.mark.asyncio
    @patch("rbac_sdk.async_client.httpx.AsyncClient")
    async def test_check_access_custom_timeout(self, mock_client_class, sample_user_id, sample_action, sample_resource):
        """Test that custom timeout is passed to httpx client."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"allowed": True}

        mock_client = AsyncMock()
        mock_client.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
        mock_client_class.return_value = mock_client

        await check_access_async(
            user_id=sample_user_id,
            action=sample_action,
            resource=sample_resource,
            timeout=10.0,
        )

        # Verify timeout was passed to AsyncClient constructor
        mock_client_class.assert_called_once_with(timeout=10.0)


class TestCheckAccessAsyncFailClosed:
    """
    Test fail-closed semantics: all errors should return False, not raise exceptions.
    This is critical for security - we deny access on any error.
    """

    @pytest.mark.asyncio
    @patch("rbac_sdk.async_client.httpx.AsyncClient")
    async def test_check_access_connection_error_returns_false(self, mock_client_class, sample_user_id, sample_action, sample_resource):
        """Test that connection errors return False (fail-closed)."""
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value.post = AsyncMock(side_effect=httpx.ConnectError("Connection refused"))
        mock_client_class.return_value = mock_client

        result = await check_access_async(
            user_id=sample_user_id,
            action=sample_action,
            resource=sample_resource,
        )

        # Should return False, not raise exception
        assert result is False

    @pytest.mark.asyncio
    @patch("rbac_sdk.async_client.httpx.AsyncClient")
    async def test_check_access_timeout_returns_false(self, mock_client_class, sample_user_id, sample_action, sample_resource):
        """Test that timeouts return False (fail-closed)."""
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value.post = AsyncMock(side_effect=httpx.TimeoutException("Request timed out"))
        mock_client_class.return_value = mock_client

        result = await check_access_async(
            user_id=sample_user_id,
            action=sample_action,
            resource=sample_resource,
        )

        assert result is False

    @pytest.mark.asyncio
    @patch("rbac_sdk.async_client.httpx.AsyncClient")
    async def test_check_access_http_error_returns_false(self, mock_client_class, sample_user_id, sample_action, sample_resource):
        """Test that HTTP errors return False (fail-closed)."""
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value.post = AsyncMock(side_effect=httpx.HTTPStatusError("500 error", request=Mock(), response=Mock()))
        mock_client_class.return_value = mock_client

        result = await check_access_async(
            user_id=sample_user_id,
            action=sample_action,
            resource=sample_resource,
        )

        assert result is False

    @pytest.mark.asyncio
    @patch("rbac_sdk.async_client.httpx.AsyncClient")
    async def test_check_access_generic_exception_returns_false(self, mock_client_class, sample_user_id, sample_action, sample_resource):
        """Test that any exception returns False (fail-closed)."""
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value.post = AsyncMock(side_effect=RuntimeError("Unexpected error"))
        mock_client_class.return_value = mock_client

        result = await check_access_async(
            user_id=sample_user_id,
            action=sample_action,
            resource=sample_resource,
        )

        assert result is False

    @pytest.mark.asyncio
    @patch("rbac_sdk.async_client.httpx.AsyncClient")
    async def test_check_access_404_returns_false(self, mock_client_class, sample_user_id, sample_action, sample_resource):
        """Test that 404 status code returns False."""
        mock_response = Mock()
        mock_response.status_code = 404

        mock_client = AsyncMock()
        mock_client.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
        mock_client_class.return_value = mock_client

        result = await check_access_async(
            user_id=sample_user_id,
            action=sample_action,
            resource=sample_resource,
        )

        assert result is False

    @pytest.mark.asyncio
    @patch("rbac_sdk.async_client.httpx.AsyncClient")
    async def test_check_access_500_returns_false(self, mock_client_class, sample_user_id, sample_action, sample_resource):
        """Test that 500 status code returns False."""
        mock_response = Mock()
        mock_response.status_code = 500

        mock_client = AsyncMock()
        mock_client.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
        mock_client_class.return_value = mock_client

        result = await check_access_async(
            user_id=sample_user_id,
            action=sample_action,
            resource=sample_resource,
        )

        assert result is False

    @pytest.mark.asyncio
    @patch("rbac_sdk.async_client.httpx.AsyncClient")
    async def test_check_access_401_returns_false(self, mock_client_class, sample_user_id, sample_action, sample_resource):
        """Test that 401 status code returns False."""
        mock_response = Mock()
        mock_response.status_code = 401

        mock_client = AsyncMock()
        mock_client.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
        mock_client_class.return_value = mock_client

        result = await check_access_async(
            user_id=sample_user_id,
            action=sample_action,
            resource=sample_resource,
        )

        assert result is False

    @pytest.mark.asyncio
    @patch("rbac_sdk.async_client.httpx.AsyncClient")
    async def test_check_access_403_returns_false(self, mock_client_class, sample_user_id, sample_action, sample_resource):
        """Test that 403 status code returns False."""
        mock_response = Mock()
        mock_response.status_code = 403

        mock_client = AsyncMock()
        mock_client.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
        mock_client_class.return_value = mock_client

        result = await check_access_async(
            user_id=sample_user_id,
            action=sample_action,
            resource=sample_resource,
        )

        assert result is False


class TestCheckAccessAsyncMalformedResponses:
    """Test handling of malformed or unexpected responses."""

    @pytest.mark.asyncio
    @patch("rbac_sdk.async_client.httpx.AsyncClient")
    async def test_check_access_missing_allowed_field(self, mock_client_class, sample_user_id, sample_action, sample_resource):
        """Test that missing 'allowed' field defaults to False."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"deny_reason": "some_reason"}

        mock_client = AsyncMock()
        mock_client.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
        mock_client_class.return_value = mock_client

        result = await check_access_async(
            user_id=sample_user_id,
            action=sample_action,
            resource=sample_resource,
        )

        assert result is False

    @pytest.mark.asyncio
    @patch("rbac_sdk.async_client.httpx.AsyncClient")
    async def test_check_access_empty_response(self, mock_client_class, sample_user_id, sample_action, sample_resource):
        """Test that empty JSON response defaults to False."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {}

        mock_client = AsyncMock()
        mock_client.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
        mock_client_class.return_value = mock_client

        result = await check_access_async(
            user_id=sample_user_id,
            action=sample_action,
            resource=sample_resource,
        )

        assert result is False

    @pytest.mark.asyncio
    @patch("rbac_sdk.async_client.httpx.AsyncClient")
    async def test_check_access_invalid_json(self, mock_client_class, sample_user_id, sample_action, sample_resource):
        """Test that invalid JSON returns False (fail-closed)."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.side_effect = ValueError("Invalid JSON")

        mock_client = AsyncMock()
        mock_client.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
        mock_client_class.return_value = mock_client

        result = await check_access_async(
            user_id=sample_user_id,
            action=sample_action,
            resource=sample_resource,
        )

        assert result is False

    @pytest.mark.asyncio
    @patch("rbac_sdk.async_client.httpx.AsyncClient")
    async def test_check_access_allowed_null(self, mock_client_class, sample_user_id, sample_action, sample_resource):
        """Test that null 'allowed' value is treated as False."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"allowed": None}

        mock_client = AsyncMock()
        mock_client.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
        mock_client_class.return_value = mock_client

        result = await check_access_async(
            user_id=sample_user_id,
            action=sample_action,
            resource=sample_resource,
        )

        assert result is False

    @pytest.mark.asyncio
    @patch("rbac_sdk.async_client.httpx.AsyncClient")
    async def test_check_access_allowed_zero(self, mock_client_class, sample_user_id, sample_action, sample_resource):
        """Test that 0 'allowed' value is treated as False."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"allowed": 0}

        mock_client = AsyncMock()
        mock_client.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
        mock_client_class.return_value = mock_client

        result = await check_access_async(
            user_id=sample_user_id,
            action=sample_action,
            resource=sample_resource,
        )

        assert result is False

    @pytest.mark.asyncio
    @patch("rbac_sdk.async_client.httpx.AsyncClient")
    async def test_check_access_allowed_one(self, mock_client_class, sample_user_id, sample_action, sample_resource):
        """Test that 1 'allowed' value is treated as True."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"allowed": 1}

        mock_client = AsyncMock()
        mock_client.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
        mock_client_class.return_value = mock_client

        result = await check_access_async(
            user_id=sample_user_id,
            action=sample_action,
            resource=sample_resource,
        )

        assert result is True


class TestCheckAccessAsyncEdgeCases:
    """Test edge cases and boundary conditions."""

    @pytest.mark.asyncio
    @patch("rbac_sdk.async_client.httpx.AsyncClient")
    async def test_check_access_zero_user_id(self, mock_client_class, sample_action, sample_resource):
        """Test that user_id=0 is handled correctly."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"allowed": True}

        mock_client = AsyncMock()
        mock_post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__.return_value.post = mock_post
        mock_client_class.return_value = mock_client

        result = await check_access_async(
            user_id=0,
            action=sample_action,
            resource=sample_resource,
        )

        assert result is True
        call_args = mock_post.call_args
        assert call_args[1]["json"]["user_id"] == 0

    @pytest.mark.asyncio
    @patch("rbac_sdk.async_client.httpx.AsyncClient")
    async def test_check_access_negative_user_id(self, mock_client_class, sample_action, sample_resource):
        """Test that negative user_id is sent."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"allowed": False}

        mock_client = AsyncMock()
        mock_post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__.return_value.post = mock_post
        mock_client_class.return_value = mock_client

        await check_access_async(
            user_id=-1,
            action=sample_action,
            resource=sample_resource,
        )

        call_args = mock_post.call_args
        assert call_args[1]["json"]["user_id"] == -1


"""
Phase 5.2: Edge Case Scenarios

Tests for unusual but valid configurations and edge cases:
- IPv6 addresses
- Base URLs with paths/query params
- Environment variable conflicts
- Whitespace handling
- Special characters in API keys
- Clock skew
- Empty/missing headers
- Unicode in resource IDs
"""

import os
import time
from datetime import datetime, timedelta, timezone
from unittest.mock import Mock, patch

import jwt
import pytest

from rbac_sdk.fastapi_helpers import (
    api_key_http_validator,
    api_key_jwt_validator,
    resource_builders,
)


class TestIPv6Addresses:
    """Test SDK works with IPv6 addresses."""

    def test_ipv6_base_url(self):
        """Test API key validation with IPv6 base URL."""
        with patch("rbac_sdk.fastapi_helpers.requests.post") as mock_post:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"user_id": "user123"}
            mock_post.return_value = mock_response

            # IPv6 localhost
            validator = api_key_http_validator(
                base_url="http://[::1]:8004", cache_ttl=0.0
            )
            request = Mock()

            result = validator("test-api-key", request)
            assert result == "user123"

            # Verify URL was constructed correctly
            mock_post.assert_called_once()
            call_args = mock_post.call_args
            assert call_args[0][0] == "http://[::1]:8004/api/auth/validate-apikey"

    def test_ipv6_full_address(self):
        """Test with full IPv6 address."""
        with patch("rbac_sdk.fastapi_helpers.requests.post") as mock_post:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"user_id": "user456"}
            mock_post.return_value = mock_response

            # Full IPv6 address
            validator = api_key_http_validator(
                base_url="http://[2001:0db8:85a3:0000:0000:8a2e:0370:7334]:8004",
                cache_ttl=0.0,
            )
            request = Mock()

            result = validator("test-api-key", request)
            assert result == "user456"


class TestBaseURLVariations:
    """Test SDK handles various base URL formats."""

    def test_base_url_with_trailing_slash(self):
        """Test base URL with trailing slash is handled correctly."""
        with patch("rbac_sdk.fastapi_helpers.requests.post") as mock_post:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"user_id": "user123"}
            mock_post.return_value = mock_response

            validator = api_key_http_validator(
                base_url="http://localhost:8004/", cache_ttl=0.0
            )
            request = Mock()

            result = validator("test-api-key", request)
            assert result == "user123"

            # Should not have double slash
            call_args = mock_post.call_args
            assert "//" not in call_args[0][0].replace("http://", "")

    def test_base_url_with_path(self):
        """Test base URL with path prefix."""
        with patch("rbac_sdk.fastapi_helpers.requests.post") as mock_post:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"user_id": "user123"}
            mock_post.return_value = mock_response

            validator = api_key_http_validator(
                base_url="http://localhost:8004/v1/auth",
                path="/validate",
                cache_ttl=0.0,
            )
            request = Mock()

            result = validator("test-api-key", request)
            assert result == "user123"

            # Should combine paths correctly
            call_args = mock_post.call_args
            assert call_args[0][0] == "http://localhost:8004/v1/auth/validate"

    def test_base_url_with_port(self):
        """Test base URL with non-standard port."""
        with patch("rbac_sdk.fastapi_helpers.requests.post") as mock_post:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"user_id": "user123"}
            mock_post.return_value = mock_response

            validator = api_key_http_validator(
                base_url="http://localhost:9999", cache_ttl=0.0
            )
            request = Mock()

            result = validator("test-api-key", request)
            assert result == "user123"

            call_args = mock_post.call_args
            assert ":9999" in call_args[0][0]


class TestEnvironmentVariables:
    """Test environment variable handling and conflicts."""

    def test_env_var_base_url(self):
        """Test that AUTH_API_BASE env var is used when base_url not provided."""
        with patch.dict(os.environ, {"AUTH_API_BASE": "http://env-server:8004"}):
            with patch("rbac_sdk.fastapi_helpers.requests.post") as mock_post:
                mock_response = Mock()
                mock_response.status_code = 200
                mock_response.json.return_value = {"user_id": "user123"}
                mock_post.return_value = mock_response

                validator = api_key_http_validator(cache_ttl=0.0)
                request = Mock()

                result = validator("test-api-key", request)
                assert result == "user123"

                # Should use env var
                call_args = mock_post.call_args
                assert "env-server:8004" in call_args[0][0]

    def test_explicit_base_url_overrides_env(self):
        """Test that explicit base_url overrides environment variable."""
        with patch.dict(os.environ, {"AUTH_API_BASE": "http://env-server:8004"}):
            with patch("rbac_sdk.fastapi_helpers.requests.post") as mock_post:
                mock_response = Mock()
                mock_response.status_code = 200
                mock_response.json.return_value = {"user_id": "user123"}
                mock_post.return_value = mock_response

                validator = api_key_http_validator(
                    base_url="http://explicit-server:8004", cache_ttl=0.0
                )
                request = Mock()

                result = validator("test-api-key", request)
                assert result == "user123"

                # Should use explicit base_url, not env var
                call_args = mock_post.call_args
                assert "explicit-server:8004" in call_args[0][0]
                assert "env-server" not in call_args[0][0]

    def test_missing_env_var_raises_error(self):
        """Test that missing AUTH_API_BASE raises error when base_url not provided."""
        with patch.dict(os.environ, {}, clear=True):
            # Remove AUTH_API_BASE if it exists
            os.environ.pop("AUTH_API_BASE", None)

            with pytest.raises(RuntimeError, match="AUTH_API_BASE must be set"):
                api_key_http_validator(cache_ttl=0.0)


class TestWhitespaceHandling:
    """Test handling of whitespace in various inputs."""

    def test_api_key_with_leading_trailing_whitespace(self):
        """Test API key with whitespace is handled correctly."""
        with patch("rbac_sdk.fastapi_helpers.requests.post") as mock_post:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"user_id": "user123"}
            mock_post.return_value = mock_response

            validator = api_key_http_validator(
                base_url="http://localhost:8004", cache_ttl=0.0
            )
            request = Mock()

            # API key with whitespace
            result = validator("  test-api-key  ", request)
            assert result == "user123"

            # Should send with whitespace preserved
            call_args = mock_post.call_args
            headers = call_args[1]["headers"]
            assert headers["X-elevAIte-apikey"] == "  test-api-key  "

    def test_base_url_with_whitespace(self):
        """Test base URL with whitespace is preserved (not stripped)."""
        with patch("rbac_sdk.fastapi_helpers.requests.post") as mock_post:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"user_id": "user123"}
            mock_post.return_value = mock_response

            validator = api_key_http_validator(
                base_url="  http://localhost:8004  ", cache_ttl=0.0
            )
            request = Mock()

            result = validator("test-api-key", request)
            assert result == "user123"

            # Whitespace is preserved (only trailing slash is stripped)
            call_args = mock_post.call_args
            # The URL will have whitespace preserved
            assert (
                "  http://localhost:8004  /api/auth/validate-apikey" == call_args[0][0]
            )


class TestSpecialCharacters:
    """Test handling of special characters in API keys and resource IDs."""

    def test_api_key_with_special_chars(self):
        """Test API key with special characters."""
        with patch("rbac_sdk.fastapi_helpers.requests.post") as mock_post:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"user_id": "user123"}
            mock_post.return_value = mock_response

            validator = api_key_http_validator(
                base_url="http://localhost:8004", cache_ttl=0.0
            )
            request = Mock()

            # API key with special characters
            special_key = "test-key-!@#$%^&*()_+-=[]{}|;:',.<>?"
            result = validator(special_key, request)
            assert result == "user123"

            # Should preserve special characters
            call_args = mock_post.call_args
            headers = call_args[1]["headers"]
            assert headers["X-elevAIte-apikey"] == special_key

    def test_unicode_in_resource_id(self):
        """Test resource builder with unicode characters in resource ID."""
        builder = resource_builders.project_from_headers(
            project_header="X-Project-ID",
            org_header="X-Org-ID",
            account_header="X-Account-ID",
        )

        request = Mock()
        request.headers = {
            "X-Project-ID": "project-日本語-émojis-🎉",
            "X-Org-ID": "org-123",
            "X-Account-ID": "acc-456",
        }

        resource = builder(request)
        assert resource["type"] == "project"
        assert resource["id"] == "project-日本語-émojis-🎉"
        assert resource["organization_id"] == "org-123"


class TestClockSkew:
    """Test handling of clock skew in JWT tokens."""

    def test_jwt_with_future_iat(self):
        """Test JWT with issued-at time in the future (clock skew)."""
        secret = "test-secret-key-12345"

        # Create token with iat 10 seconds in the future
        future_time = datetime.now(timezone.utc) + timedelta(seconds=10)
        payload = {
            "sub": "user123",
            "type": "api_key",
            "iat": int(future_time.timestamp()),
            "exp": int((future_time + timedelta(hours=1)).timestamp()),
        }
        token = jwt.encode(payload, secret, algorithm="HS256")

        validator = api_key_jwt_validator(algorithm="HS256", secret=secret)
        request = Mock()

        # PyJWT allows some leeway by default
        result = validator(token, request)
        # Should still validate (PyJWT has default leeway)
        assert result == "user123"

    def test_jwt_near_expiration(self):
        """Test JWT that's about to expire."""
        secret = "test-secret-key-12345"

        # Create token that expires in 1 second
        now = datetime.now(timezone.utc)
        payload = {
            "sub": "user123",
            "type": "api_key",
            "iat": int(now.timestamp()),
            "exp": int((now + timedelta(seconds=1)).timestamp()),
        }
        token = jwt.encode(payload, secret, algorithm="HS256")

        validator = api_key_jwt_validator(algorithm="HS256", secret=secret)
        request = Mock()

        # Should still be valid
        result = validator(token, request)
        assert result == "user123"

        # Wait for expiration
        time.sleep(1.5)

        # Should now be expired
        result = validator(token, request)
        assert result is None


class TestEmptyAndMissingHeaders:
    """Test handling of empty and missing headers."""

    def test_missing_project_id_header_raises_error(self):
        """Test resource builder raises error when project ID header is missing."""
        from fastapi import HTTPException

        builder = resource_builders.project_from_headers(
            project_header="X-Project-ID",
            org_header="X-Org-ID",
            account_header="X-Account-ID",
        )

        request = Mock()
        request.headers = {
            "X-Org-ID": "org-123",
            "X-Account-ID": "acc-456",
            # Missing X-Project-ID
        }

        # Should raise HTTPException for missing required header
        with pytest.raises(HTTPException) as exc_info:
            builder(request)
        assert exc_info.value.status_code == 400
        assert "X-Project-ID" in exc_info.value.detail

    def test_missing_org_id_header_raises_error(self):
        """Test resource builder raises error when org ID header is missing."""
        from fastapi import HTTPException

        builder = resource_builders.project_from_headers(
            project_header="X-Project-ID",
            org_header="X-Org-ID",
            account_header="X-Account-ID",
        )

        request = Mock()
        request.headers = {
            "X-Project-ID": "project-123",
            "X-Account-ID": "acc-456",
            # Missing X-Org-ID
        }

        # Should raise HTTPException for missing required header
        with pytest.raises(HTTPException) as exc_info:
            builder(request)
        assert exc_info.value.status_code == 400
        assert "X-Org-ID" in exc_info.value.detail

    def test_missing_account_id_is_optional(self):
        """Test that account ID header is optional."""
        builder = resource_builders.project_from_headers(
            project_header="X-Project-ID",
            org_header="X-Org-ID",
            account_header="X-Account-ID",
        )

        request = Mock()
        request.headers = {
            "X-Project-ID": "project-123",
            "X-Org-ID": "org-123",
            # Missing X-Account-ID (optional)
        }

        # Should work without account_id
        resource = builder(request)
        assert resource["type"] == "project"
        assert resource["id"] == "project-123"
        assert resource["organization_id"] == "org-123"
        assert "account_id" not in resource  # Not included when missing

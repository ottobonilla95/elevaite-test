"""
Brutal unit tests for API key validators in rbac_sdk.fastapi_helpers.

These tests cover:
- HTTP-based API key validation
- JWT-based API key validation
- Caching behavior
- Network failures
- Security edge cases
"""

import pytest
import os
from unittest.mock import Mock, patch
from rbac_sdk.fastapi_helpers import (
    api_key_http_validator,
    api_key_jwt_validator,
)


class TestApiKeyHttpValidator:
    """Test HTTP-based API key validator."""

    @patch("rbac_sdk.fastapi_helpers.requests.post")
    def test_http_validator_success(self, mock_post):
        """Test successful API key validation via HTTP."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"user_id": "service-account-123"}
        mock_post.return_value = mock_response

        validator = api_key_http_validator(base_url="http://auth-api:8004")
        request = Mock()
        user_id = validator("test-api-key", request)

        assert user_id == "service-account-123"
        mock_post.assert_called_once()

    @patch("rbac_sdk.fastapi_helpers.requests.post")
    def test_http_validator_failure_401(self, mock_post):
        """Test that 401 response returns None."""
        mock_response = Mock()
        mock_response.status_code = 401
        mock_post.return_value = mock_response

        validator = api_key_http_validator(base_url="http://auth-api:8004")
        request = Mock()
        user_id = validator("invalid-key", request)

        assert user_id is None

    @patch("rbac_sdk.fastapi_helpers.requests.post")
    def test_http_validator_failure_500(self, mock_post):
        """Test that 500 response returns None."""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_post.return_value = mock_response

        validator = api_key_http_validator(base_url="http://auth-api:8004")
        request = Mock()
        user_id = validator("test-key", request)

        assert user_id is None

    @patch("rbac_sdk.fastapi_helpers.requests.post")
    def test_http_validator_connection_error(self, mock_post):
        """Test that connection errors return None."""
        import requests

        mock_post.side_effect = requests.ConnectionError("Connection refused")

        validator = api_key_http_validator(base_url="http://auth-api:8004")
        request = Mock()
        user_id = validator("test-key", request)

        assert user_id is None

    @patch("rbac_sdk.fastapi_helpers.requests.post")
    def test_http_validator_timeout(self, mock_post):
        """Test that timeouts return None."""
        import requests

        mock_post.side_effect = requests.Timeout("Request timed out")

        validator = api_key_http_validator(base_url="http://auth-api:8004", timeout=1.0)
        request = Mock()
        user_id = validator("test-key", request)

        assert user_id is None

    @patch("rbac_sdk.fastapi_helpers.requests.post")
    def test_http_validator_missing_user_id_in_response(self, mock_post):
        """Test that missing user_id in response returns None."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"message": "success"}  # No user_id
        mock_post.return_value = mock_response

        validator = api_key_http_validator(base_url="http://auth-api:8004")
        request = Mock()
        user_id = validator("test-key", request)

        assert user_id is None

    @patch("rbac_sdk.fastapi_helpers.requests.post")
    def test_http_validator_invalid_json(self, mock_post):
        """Test that invalid JSON returns None."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_post.return_value = mock_response

        validator = api_key_http_validator(base_url="http://auth-api:8004")
        request = Mock()
        user_id = validator("test-key", request)

        assert user_id is None

    @patch("rbac_sdk.fastapi_helpers.requests.post")
    def test_http_validator_custom_path(self, mock_post):
        """Test that custom path is used."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"user_id": "123"}
        mock_post.return_value = mock_response

        validator = api_key_http_validator(base_url="http://auth-api:8004", path="/custom/validate")
        request = Mock()
        validator("test-key", request)

        call_args = mock_post.call_args
        assert call_args[0][0] == "http://auth-api:8004/custom/validate"

    @patch("rbac_sdk.fastapi_helpers.requests.post")
    def test_http_validator_custom_header_name(self, mock_post):
        """Test that custom header name is used."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"user_id": "123"}
        mock_post.return_value = mock_response

        validator = api_key_http_validator(base_url="http://auth-api:8004", header_name="X-Custom-ApiKey")
        request = Mock()
        validator("test-key", request)

        call_args = mock_post.call_args
        assert "X-Custom-ApiKey" in call_args[1]["headers"]
        assert call_args[1]["headers"]["X-Custom-ApiKey"] == "test-key"

    @patch("rbac_sdk.fastapi_helpers.requests.post")
    def test_http_validator_extra_headers(self, mock_post):
        """Test that extra headers are included."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"user_id": "123"}
        mock_post.return_value = mock_response

        validator = api_key_http_validator(base_url="http://auth-api:8004", extra_headers={"X-Tenant-ID": "tenant-123"})
        request = Mock()
        validator("test-key", request)

        call_args = mock_post.call_args
        assert call_args[1]["headers"]["X-Tenant-ID"] == "tenant-123"

    @patch("rbac_sdk.fastapi_helpers.requests.post")
    def test_http_validator_custom_timeout(self, mock_post):
        """Test that custom timeout is used."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"user_id": "123"}
        mock_post.return_value = mock_response

        validator = api_key_http_validator(base_url="http://auth-api:8004", timeout=10.0)
        request = Mock()
        validator("test-key", request)

        call_args = mock_post.call_args
        assert call_args[1]["timeout"] == 10.0

    def test_http_validator_missing_base_url(self):
        """Test that missing base_url raises RuntimeError."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(RuntimeError) as exc_info:
                api_key_http_validator()

            assert "AUTH_API_BASE must be set" in str(exc_info.value)

    @patch.dict(os.environ, {"AUTH_API_BASE": "http://env-auth-api:8004"})
    @patch("rbac_sdk.fastapi_helpers.requests.post")
    def test_http_validator_uses_env_var(self, mock_post):
        """Test that AUTH_API_BASE env var is used when base_url not provided."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"user_id": "123"}
        mock_post.return_value = mock_response

        validator = api_key_http_validator()
        request = Mock()
        validator("test-key", request)

        call_args = mock_post.call_args
        assert call_args[0][0].startswith("http://env-auth-api:8004")


class TestApiKeyHttpValidatorCaching:
    """Test caching behavior of HTTP validator."""

    @patch("rbac_sdk.fastapi_helpers.requests.post")
    @patch("rbac_sdk.fastapi_helpers.time.time")
    def test_http_validator_caches_successful_validation(self, mock_time, mock_post):
        """Test that successful validations are cached."""
        mock_time.return_value = 1000.0
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"user_id": "123"}
        mock_post.return_value = mock_response

        validator = api_key_http_validator(base_url="http://auth-api:8004", cache_ttl=60.0)
        request = Mock()

        # First call
        user_id1 = validator("test-key", request)
        assert user_id1 == "123"
        assert mock_post.call_count == 1

        # Second call with same key - should use cache
        user_id2 = validator("test-key", request)
        assert user_id2 == "123"
        assert mock_post.call_count == 1  # Still 1, not 2

    @patch("rbac_sdk.fastapi_helpers.time.time")
    @patch("rbac_sdk.fastapi_helpers.requests.post")
    def test_http_validator_cache_expires(self, mock_post, mock_time):
        """Test that cache expires after TTL."""
        # First call at t=1000, second call at t=1070 (after 60s TTL)
        mock_time.side_effect = [1000.0, 1070.0]
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"user_id": "123"}
        mock_post.return_value = mock_response

        validator = api_key_http_validator(base_url="http://auth-api:8004", cache_ttl=60.0)
        request = Mock()

        # First call at t=1000
        validator("test-key", request)
        assert mock_post.call_count == 1

        # Second call at t=1070 (after TTL expired) - should make new request
        validator("test-key", request)
        assert mock_post.call_count == 2

    @patch("rbac_sdk.fastapi_helpers.requests.post")
    def test_http_validator_cache_disabled(self, mock_post):
        """Test that cache can be disabled with cache_ttl=0."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"user_id": "123"}
        mock_post.return_value = mock_response

        validator = api_key_http_validator(base_url="http://auth-api:8004", cache_ttl=0.0)
        request = Mock()

        # First call
        validator("test-key", request)
        assert mock_post.call_count == 1

        # Second call - should make new request (no caching)
        validator("test-key", request)
        assert mock_post.call_count == 2

    @patch("rbac_sdk.fastapi_helpers.requests.post")
    @patch("rbac_sdk.fastapi_helpers.time.time")
    def test_http_validator_different_keys_not_cached_together(self, mock_time, mock_post):
        """Test that different API keys are cached separately."""
        mock_time.return_value = 1000.0
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"user_id": "123"}
        mock_post.return_value = mock_response

        validator = api_key_http_validator(base_url="http://auth-api:8004", cache_ttl=60.0)
        request = Mock()

        # First key
        validator("key1", request)
        assert mock_post.call_count == 1

        # Different key - should make new request
        validator("key2", request)
        assert mock_post.call_count == 2

    @patch("rbac_sdk.fastapi_helpers.requests.post")
    def test_http_validator_failed_validation_not_cached(self, mock_post):
        """Test that failed validations are not cached."""
        mock_response = Mock()
        mock_response.status_code = 401
        mock_post.return_value = mock_response

        validator = api_key_http_validator(base_url="http://auth-api:8004", cache_ttl=60.0)
        request = Mock()

        # First call - fails
        result1 = validator("invalid-key", request)
        assert result1 is None
        assert mock_post.call_count == 1

        # Second call - should try again (failures not cached)
        result2 = validator("invalid-key", request)
        assert result2 is None
        assert mock_post.call_count == 2


class TestApiKeyJwtValidator:
    """Test JWT-based API key validator using real jose library."""

    def test_jwt_validator_success_hs256(self):
        """Test successful JWT validation with HS256."""
        from jose import jwt

        secret = "test-secret-key-for-hs256-validation"
        token = jwt.encode(
            {"type": "api_key", "sub": "service-account-123"},
            secret,
            algorithm="HS256",
        )

        validator = api_key_jwt_validator(algorithm="HS256", secret=secret)
        request = Mock()
        user_id = validator(token, request)

        assert user_id == "service-account-123"

    def test_jwt_validator_success_rs256(self):
        """Test successful JWT validation with RS256."""
        from jose import jwt
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.primitives.asymmetric import rsa
        from cryptography.hazmat.backends import default_backend

        # Generate RSA key pair
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend(),
        )
        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        ).decode("utf-8")
        public_pem = (
            private_key.public_key()
            .public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo,
            )
            .decode("utf-8")
        )

        token = jwt.encode(
            {"type": "api_key", "sub": "service-account-456"},
            private_pem,
            algorithm="RS256",
        )

        validator = api_key_jwt_validator(algorithm="RS256", public_key=public_pem)
        request = Mock()
        user_id = validator(token, request)

        assert user_id == "service-account-456"

    def test_jwt_validator_invalid_type(self):
        """Test that wrong token type returns None."""
        from jose import jwt

        secret = "test-secret-key"
        token = jwt.encode(
            {"type": "access_token", "sub": "user-123"},
            secret,
            algorithm="HS256",
        )

        validator = api_key_jwt_validator(algorithm="HS256", secret=secret, require_type="api_key")
        request = Mock()
        user_id = validator(token, request)

        assert user_id is None

    def test_jwt_validator_missing_sub(self):
        """Test that missing 'sub' claim returns None."""
        from jose import jwt

        secret = "test-secret-key"
        token = jwt.encode(
            {"type": "api_key"},  # No 'sub'
            secret,
            algorithm="HS256",
        )

        validator = api_key_jwt_validator(algorithm="HS256", secret=secret)
        request = Mock()
        user_id = validator(token, request)

        assert user_id is None

    def test_jwt_validator_decode_error(self):
        """Test that JWT decode errors return None (invalid signature)."""
        from jose import jwt

        secret = "correct-secret"
        wrong_secret = "wrong-secret"
        token = jwt.encode(
            {"type": "api_key", "sub": "user-123"},
            secret,
            algorithm="HS256",
        )

        # Try to validate with wrong secret
        validator = api_key_jwt_validator(algorithm="HS256", secret=wrong_secret)
        request = Mock()
        user_id = validator(token, request)

        assert user_id is None

    def test_jwt_validator_malformed_token(self):
        """Test that malformed tokens return None."""
        validator = api_key_jwt_validator(algorithm="HS256", secret="test-secret")
        request = Mock()
        user_id = validator("not.a.valid.jwt.token.at.all", request)

        assert user_id is None

    def test_jwt_validator_jose_not_installed(self):
        """Test that missing jose library returns None."""
        with patch.dict("sys.modules", {"jose": None}):
            validator = api_key_jwt_validator(algorithm="HS256", secret="test-secret")
            request = Mock()
            user_id = validator("test.jwt.token", request)

            assert user_id is None

    def test_jwt_validator_no_type_requirement(self):
        """Test that type requirement can be disabled."""
        from jose import jwt

        secret = "test-secret-key"
        token = jwt.encode(
            {"sub": "user-123"},  # No 'type' field
            secret,
            algorithm="HS256",
        )

        validator = api_key_jwt_validator(algorithm="HS256", secret=secret, require_type=None)
        request = Mock()
        user_id = validator(token, request)

        assert user_id == "user-123"

    @patch.dict(os.environ, {"API_KEY_ALGORITHM": "HS256", "API_KEY_SECRET": "env-secret-key"})
    def test_jwt_validator_uses_env_vars(self):
        """Test that environment variables are used when parameters not provided."""
        from jose import jwt

        token = jwt.encode(
            {"type": "api_key", "sub": "user-123"},
            "env-secret-key",
            algorithm="HS256",
        )

        validator = api_key_jwt_validator()
        request = Mock()
        user_id = validator(token, request)

        assert user_id == "user-123"

    def test_jwt_validator_missing_secret_for_hs(self):
        """Test that missing secret for HS algorithm returns None."""
        with patch.dict(os.environ, {}, clear=False):
            # Ensure no env var fallback
            if "API_KEY_SECRET" in os.environ:
                del os.environ["API_KEY_SECRET"]

            validator = api_key_jwt_validator(algorithm="HS256", secret=None)
            request = Mock()
            user_id = validator("test.jwt.token", request)

            assert user_id is None

    def test_jwt_validator_missing_public_key_for_rs(self):
        """Test that missing public key for RS algorithm returns None."""
        with patch.dict(os.environ, {}, clear=False):
            # Ensure no env var fallback
            if "API_KEY_PUBLIC_KEY" in os.environ:
                del os.environ["API_KEY_PUBLIC_KEY"]

            validator = api_key_jwt_validator(algorithm="RS256", public_key=None)
            request = Mock()
            user_id = validator("test.jwt.token", request)

            assert user_id is None

    def test_jwt_validator_unsupported_algorithm(self):
        """Test that unsupported algorithm returns None."""
        validator = api_key_jwt_validator(algorithm="UNSUPPORTED", secret="test-secret")
        request = Mock()
        user_id = validator("test.jwt.token", request)

        assert user_id is None

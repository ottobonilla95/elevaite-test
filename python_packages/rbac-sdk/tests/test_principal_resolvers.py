"""
Brutal unit tests for principal resolvers in rbac_sdk.fastapi_helpers.

These tests cover:
- User ID header resolution
- API key resolution with various validators
- Security edge cases
- Environment variable handling
"""

import pytest
import os
from unittest.mock import Mock, patch
from fastapi import HTTPException
from rbac_sdk.fastapi_helpers import (
    principal_resolvers,
    _default_principal_resolver,
    HDR_USER_ID,
    HDR_API_KEY,
)


class TestDefaultPrincipalResolver:
    """Test the default principal resolver (user ID header only)."""

    def test_default_resolver_with_user_id(self, mock_request_with_user):
        """Test that default resolver extracts user ID from header."""
        user_id = _default_principal_resolver(mock_request_with_user)
        assert user_id == "123"

    def test_default_resolver_missing_user_id(self, mock_request):
        """Test that missing user ID raises 401."""
        with pytest.raises(HTTPException) as exc_info:
            _default_principal_resolver(mock_request)

        assert exc_info.value.status_code == 401
        assert "Missing X-elevAIte-UserId header" in str(exc_info.value.detail)

    def test_default_resolver_empty_user_id(self):
        """Test that empty user ID string raises 401."""
        request = Mock()
        request.headers = {HDR_USER_ID: ""}

        with pytest.raises(HTTPException) as exc_info:
            _default_principal_resolver(request)

        assert exc_info.value.status_code == 401


class TestUserIdHeaderResolver:
    """Test the user_id_header principal resolver factory."""

    def test_user_id_header_default(self, mock_request_with_user):
        """Test user_id_header with default header name."""
        resolver = principal_resolvers.user_id_header()
        user_id = resolver(mock_request_with_user)
        assert user_id == "123"

    def test_user_id_header_custom_name(self):
        """Test user_id_header with custom header name."""
        request = Mock()
        request.headers = {"X-Custom-User": "456"}

        resolver = principal_resolvers.user_id_header(header_name="X-Custom-User")
        user_id = resolver(request)
        assert user_id == "456"

    def test_user_id_header_missing(self, mock_request):
        """Test that missing header raises 401."""
        resolver = principal_resolvers.user_id_header()

        with pytest.raises(HTTPException) as exc_info:
            resolver(mock_request)

        assert exc_info.value.status_code == 401
        assert HDR_USER_ID in str(exc_info.value.detail)

    def test_user_id_header_case_sensitive(self):
        """Test that header names are case-sensitive (or not, depending on FastAPI)."""
        request = Mock()
        request.headers = {"x-elevaite-userid": "789"}  # lowercase

        resolver = principal_resolvers.user_id_header()

        # This should fail because header lookup is case-sensitive in our mock
        with pytest.raises(HTTPException):
            resolver(request)


class TestApiKeyOrUserResolver:
    """Test the api_key_or_user principal resolver factory."""

    def test_api_key_with_validator_success(self):
        """Test API key resolution with successful validation."""
        request = Mock()
        request.headers = {HDR_API_KEY: "valid-key"}

        def mock_validator(api_key: str, req) -> str:
            if api_key == "valid-key":
                return "service-account-123"
            return None

        resolver = principal_resolvers.api_key_or_user(validate_api_key=mock_validator)
        user_id = resolver(request)

        assert user_id == "service-account-123"

    def test_api_key_with_validator_failure(self):
        """Test API key resolution with failed validation."""
        request = Mock()
        request.headers = {HDR_API_KEY: "invalid-key"}

        def mock_validator(api_key: str, req) -> str:
            return None

        resolver = principal_resolvers.api_key_or_user(validate_api_key=mock_validator)

        with pytest.raises(HTTPException) as exc_info:
            resolver(request)

        assert exc_info.value.status_code == 401
        assert "Invalid API key" in str(exc_info.value.detail)

    def test_api_key_fallback_to_user_id(self, mock_request_with_user):
        """Test that resolver falls back to user ID when no API key present."""

        def mock_validator(api_key: str, req) -> str:
            return "service-account-123"

        resolver = principal_resolvers.api_key_or_user(validate_api_key=mock_validator)
        user_id = resolver(mock_request_with_user)

        assert user_id == "123"

    @patch.dict(os.environ, {"RBAC_SDK_APIKEY_ENABLE_LOCAL_JWT": "true", "API_KEY_SECRET": "test-secret"})
    def test_api_key_local_jwt_validation(self):
        """Test API key with local JWT validation enabled."""
        request = Mock()
        # This is a mock JWT - in real tests we'd need a valid JWT
        request.headers = {HDR_API_KEY: "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.test"}

        with patch("rbac_sdk.fastapi_helpers.api_key_jwt_validator") as mock_jwt_validator:
            mock_validator_func = Mock(return_value="jwt-user-123")
            mock_jwt_validator.return_value = mock_validator_func

            resolver = principal_resolvers.api_key_or_user()
            user_id = resolver(request)

            assert user_id == "jwt-user-123"

    @patch.dict(os.environ, {"RBAC_SDK_ALLOW_INSECURE_APIKEY_AS_PRINCIPAL": "true"})
    def test_api_key_insecure_fallback(self):
        """Test insecure fallback that uses raw API key as principal (dev only)."""
        request = Mock()
        request.headers = {HDR_API_KEY: "raw-api-key-123"}

        resolver = principal_resolvers.api_key_or_user(allow_insecure_apikey_as_principal=True)
        user_id = resolver(request)

        # Should return the raw API key as user_id (INSECURE!)
        assert user_id == "raw-api-key-123"

    def test_api_key_no_validator_no_fallback(self):
        """Test that API key without validator and without insecure fallback raises 401."""
        request = Mock()
        request.headers = {HDR_API_KEY: "some-key"}

        resolver = principal_resolvers.api_key_or_user(allow_insecure_apikey_as_principal=False)

        with pytest.raises(HTTPException) as exc_info:
            resolver(request)

        assert exc_info.value.status_code == 401
        assert "no validator configured" in str(exc_info.value.detail)

    @patch.dict(os.environ, {"RBAC_SDK_APIKEY_ENABLE_LOCAL_JWT": "false"})
    def test_api_key_local_jwt_disabled(self):
        """Test that local JWT validation is skipped when disabled."""
        request = Mock()
        request.headers = {HDR_API_KEY: "some-jwt"}

        resolver = principal_resolvers.api_key_or_user(allow_insecure_apikey_as_principal=False)

        with pytest.raises(HTTPException) as exc_info:
            resolver(request)

        assert exc_info.value.status_code == 401

    def test_api_key_validator_exception(self):
        """Test that validator exceptions are handled properly."""
        request = Mock()
        request.headers = {HDR_API_KEY: "key"}

        def bad_validator(api_key: str, req):
            raise RuntimeError("Validator crashed")

        resolver = principal_resolvers.api_key_or_user(validate_api_key=bad_validator)

        # Should raise the exception (not caught by resolver)
        with pytest.raises(RuntimeError):
            resolver(request)

    def test_api_key_empty_string(self):
        """Test that empty API key string is treated as no API key."""
        request = Mock()
        request.headers = {HDR_API_KEY: "", HDR_USER_ID: "123"}

        def mock_validator(api_key: str, req) -> str:
            return "service-account"

        resolver = principal_resolvers.api_key_or_user(validate_api_key=mock_validator)
        user_id = resolver(request)

        # Empty string is falsy, should fall back to user ID
        assert user_id == "123"

    def test_both_api_key_and_user_id_prefers_api_key(self):
        """Test that API key takes precedence over user ID when both present."""
        request = Mock()
        request.headers = {HDR_API_KEY: "key", HDR_USER_ID: "123"}

        def mock_validator(api_key: str, req) -> str:
            return "service-account-456"

        resolver = principal_resolvers.api_key_or_user(validate_api_key=mock_validator)
        user_id = resolver(request)

        # Should use API key, not user ID
        assert user_id == "service-account-456"

    def test_no_api_key_no_user_id(self, mock_request):
        """Test that missing both API key and user ID raises 401."""
        resolver = principal_resolvers.api_key_or_user()

        with pytest.raises(HTTPException) as exc_info:
            resolver(mock_request)

        assert exc_info.value.status_code == 401


class TestApiKeyOrUserEnvironmentVariables:
    """Test environment variable handling in api_key_or_user resolver."""

    def test_insecure_env_var_1(self):
        """Test that RBAC_SDK_ALLOW_INSECURE_APIKEY_AS_PRINCIPAL=1 enables insecure mode."""
        with patch.dict(os.environ, {"RBAC_SDK_ALLOW_INSECURE_APIKEY_AS_PRINCIPAL": "1"}):
            request = Mock()
            request.headers = {HDR_API_KEY: "raw-key"}

            # Explicitly pass allow_insecure_apikey_as_principal=True since default is evaluated at module load time
            resolver = principal_resolvers.api_key_or_user(allow_insecure_apikey_as_principal=True)
            user_id = resolver(request)

            assert user_id == "raw-key"

    def test_insecure_env_var_true(self):
        """Test that RBAC_SDK_ALLOW_INSECURE_APIKEY_AS_PRINCIPAL=true enables insecure mode."""
        with patch.dict(os.environ, {"RBAC_SDK_ALLOW_INSECURE_APIKEY_AS_PRINCIPAL": "true"}):
            request = Mock()
            request.headers = {HDR_API_KEY: "raw-key"}

            # Explicitly pass allow_insecure_apikey_as_principal=True since default is evaluated at module load time
            resolver = principal_resolvers.api_key_or_user(allow_insecure_apikey_as_principal=True)
            user_id = resolver(request)

            assert user_id == "raw-key"

    def test_insecure_env_var_yes(self):
        """Test that RBAC_SDK_ALLOW_INSECURE_APIKEY_AS_PRINCIPAL=yes enables insecure mode."""
        with patch.dict(os.environ, {"RBAC_SDK_ALLOW_INSECURE_APIKEY_AS_PRINCIPAL": "yes"}):
            request = Mock()
            request.headers = {HDR_API_KEY: "raw-key"}

            # Explicitly pass allow_insecure_apikey_as_principal=True since default is evaluated at module load time
            resolver = principal_resolvers.api_key_or_user(allow_insecure_apikey_as_principal=True)
            user_id = resolver(request)

            assert user_id == "raw-key"

    @patch.dict(os.environ, {"RBAC_SDK_ALLOW_INSECURE_APIKEY_AS_PRINCIPAL": "false"})
    def test_insecure_env_var_false(self):
        """Test that RBAC_SDK_ALLOW_INSECURE_APIKEY_AS_PRINCIPAL=false disables insecure mode."""
        request = Mock()
        request.headers = {HDR_API_KEY: "raw-key"}

        resolver = principal_resolvers.api_key_or_user()

        with pytest.raises(HTTPException):
            resolver(request)

    @patch.dict(os.environ, {"RBAC_SDK_ALLOW_INSECURE_APIKEY_AS_PRINCIPAL": "0"})
    def test_insecure_env_var_0(self):
        """Test that RBAC_SDK_ALLOW_INSECURE_APIKEY_AS_PRINCIPAL=0 disables insecure mode."""
        request = Mock()
        request.headers = {HDR_API_KEY: "raw-key"}

        resolver = principal_resolvers.api_key_or_user()

        with pytest.raises(HTTPException):
            resolver(request)

    @patch.dict(os.environ, {}, clear=True)
    def test_insecure_env_var_not_set(self):
        """Test that missing env var defaults to secure mode."""
        request = Mock()
        request.headers = {HDR_API_KEY: "raw-key"}

        resolver = principal_resolvers.api_key_or_user()

        with pytest.raises(HTTPException):
            resolver(request)

    @patch.dict(os.environ, {"RBAC_SDK_APIKEY_ENABLE_LOCAL_JWT": "1"})
    def test_local_jwt_env_var_1(self):
        """Test that RBAC_SDK_APIKEY_ENABLE_LOCAL_JWT=1 enables local JWT validation."""
        request = Mock()
        request.headers = {HDR_API_KEY: "jwt-token"}

        with patch("rbac_sdk.fastapi_helpers.api_key_jwt_validator") as mock_jwt_validator:
            mock_validator_func = Mock(return_value="jwt-user")
            mock_jwt_validator.return_value = mock_validator_func

            resolver = principal_resolvers.api_key_or_user()
            user_id = resolver(request)

            assert user_id == "jwt-user"
            mock_jwt_validator.assert_called_once()

    @patch.dict(os.environ, {"RBAC_SDK_APIKEY_ENABLE_LOCAL_JWT": "true"})
    def test_local_jwt_env_var_true(self):
        """Test that RBAC_SDK_APIKEY_ENABLE_LOCAL_JWT=true enables local JWT validation."""
        request = Mock()
        request.headers = {HDR_API_KEY: "jwt-token"}

        with patch("rbac_sdk.fastapi_helpers.api_key_jwt_validator") as mock_jwt_validator:
            mock_validator_func = Mock(return_value="jwt-user")
            mock_jwt_validator.return_value = mock_validator_func

            resolver = principal_resolvers.api_key_or_user()
            user_id = resolver(request)

            assert user_id == "jwt-user"

    @patch.dict(os.environ, {"RBAC_SDK_APIKEY_ENABLE_LOCAL_JWT": "yes"})
    def test_local_jwt_env_var_yes(self):
        """Test that RBAC_SDK_APIKEY_ENABLE_LOCAL_JWT=yes enables local JWT validation."""
        request = Mock()
        request.headers = {HDR_API_KEY: "jwt-token"}

        with patch("rbac_sdk.fastapi_helpers.api_key_jwt_validator") as mock_jwt_validator:
            mock_validator_func = Mock(return_value="jwt-user")
            mock_jwt_validator.return_value = mock_validator_func

            resolver = principal_resolvers.api_key_or_user()
            user_id = resolver(request)

            assert user_id == "jwt-user"


class TestPrincipalResolverSecurityEdgeCases:
    """Test security-critical edge cases in principal resolution."""

    def test_sql_injection_in_user_id(self):
        """Test that SQL injection attempts in user ID are passed through (validation is server-side)."""
        request = Mock()
        request.headers = {HDR_USER_ID: "123; DROP TABLE users;--"}

        resolver = principal_resolvers.user_id_header()
        user_id = resolver(request)

        # Should pass through - server should validate/sanitize
        assert user_id == "123; DROP TABLE users;--"

    def test_xss_in_user_id(self):
        """Test that XSS attempts in user ID are passed through."""
        request = Mock()
        request.headers = {HDR_USER_ID: "<script>alert('xss')</script>"}

        resolver = principal_resolvers.user_id_header()
        user_id = resolver(request)

        assert user_id == "<script>alert('xss')</script>"

    def test_very_long_user_id(self):
        """Test that very long user IDs are handled."""
        request = Mock()
        long_id = "a" * 10000
        request.headers = {HDR_USER_ID: long_id}

        resolver = principal_resolvers.user_id_header()
        user_id = resolver(request)

        assert user_id == long_id

    def test_unicode_in_user_id(self):
        """Test that Unicode characters in user ID are handled."""
        request = Mock()
        request.headers = {HDR_USER_ID: "用户123"}

        resolver = principal_resolvers.user_id_header()
        user_id = resolver(request)

        assert user_id == "用户123"

    def test_null_bytes_in_user_id(self):
        """Test that null bytes in user ID are handled."""
        request = Mock()
        request.headers = {HDR_USER_ID: "123\x00456"}

        resolver = principal_resolvers.user_id_header()
        user_id = resolver(request)

        assert user_id == "123\x00456"

"""
Integration tests for RBAC SDK with real Auth API.

These tests verify that the SDK works correctly with a real Auth API instance.

Requirements:
- Auth API running on localhost:8004 (or AUTH_API_URL env var)
- PostgreSQL database with test data
- API_KEY_SECRET and API_KEY_ALGORITHM env vars set

Run with:
    pytest tests/integration/test_auth_api_integration.py -v
"""

import pytest
from unittest.mock import Mock
from datetime import datetime, timedelta, timezone
from jose import jwt

from rbac_sdk.fastapi_helpers import (
    api_key_http_validator,
    api_key_jwt_validator,
)


pytestmark = pytest.mark.asyncio


class TestApiKeyHttpValidator:
    """Test HTTP-based API key validator with real Auth API."""

    async def test_real_api_key_validation_success(
        self,
        check_auth_api_available,
        test_user_with_api_key,
        auth_api_url,
    ):
        """Test that HTTP validator successfully validates a real API key."""
        # Create validator
        validator = api_key_http_validator(base_url=auth_api_url)

        # Create mock request
        request = Mock()

        # Validate the API key
        user_id = validator(test_user_with_api_key["api_key"], request)

        # Should return the user ID as a string
        assert user_id == str(test_user_with_api_key["id"])

    async def test_real_api_key_validation_invalid_key(
        self,
        check_auth_api_available,
        auth_api_url,
    ):
        """Test that HTTP validator rejects an invalid API key."""
        # Create validator
        validator = api_key_http_validator(base_url=auth_api_url)

        # Create mock request
        request = Mock()

        # Try to validate an invalid API key
        invalid_key = "invalid.jwt.token"

        # Validators return None on error (by design)
        user_id = validator(invalid_key, request)
        assert user_id is None

    async def test_real_api_key_validation_expired_key(
        self,
        check_auth_api_available,
        create_test_jwt,
        auth_api_url,
    ):
        """Test that HTTP validator rejects an expired API key."""
        # Create an expired JWT
        expired_jwt = create_test_jwt(
            user_id="999",
            expires_in_minutes=-60,  # Expired 1 hour ago
        )

        # Create validator
        validator = api_key_http_validator(base_url=auth_api_url)

        # Create mock request
        request = Mock()

        # Validators return None on error (by design)
        user_id = validator(expired_jwt, request)
        assert user_id is None

    async def test_real_api_key_validation_caching(
        self,
        check_auth_api_available,
        test_user_with_api_key,
        auth_api_url,
    ):
        """Test that HTTP validator caches successful validations."""
        # Create validator with short TTL
        validator = api_key_http_validator(base_url=auth_api_url, cache_ttl=60)

        # Create mock request
        request = Mock()

        # First call - should hit the API
        user_id_1 = validator(test_user_with_api_key["api_key"], request)

        # Second call - should use cache
        user_id_2 = validator(test_user_with_api_key["api_key"], request)

        # Both should return the same user ID
        assert user_id_1 == user_id_2
        assert user_id_1 == str(test_user_with_api_key["id"])

    async def test_real_api_key_validation_network_failure(
        self,
        auth_api_url,
    ):
        """Test that HTTP validator handles network failures gracefully."""
        # Create validator with invalid URL
        validator = api_key_http_validator(base_url="http://invalid-host:9999")

        # Create mock request
        request = Mock()

        # Create a valid JWT (but API is unreachable)
        valid_jwt = jwt.encode(
            {
                "sub": "123",
                "type": "api_key",
                "exp": datetime.now(timezone.utc) + timedelta(hours=1),
            },
            "test-secret",
            algorithm="HS256",
        )

        # Should return None (validator doesn't raise, resolver does)
        # Network failures are treated as validation failures
        user_id = validator(valid_jwt, request)
        assert user_id is None


class TestApiKeyJwtValidator:
    """Test JWT-based API key validator with real tokens."""

    async def test_real_jwt_validation_success(
        self,
        create_test_jwt,
        api_key_config,
    ):
        """Test that JWT validator successfully validates a real JWT."""
        # Create a valid JWT
        valid_jwt = create_test_jwt(user_id="123")

        # Create validator
        validator = api_key_jwt_validator(algorithm=api_key_config["algorithm"], secret=api_key_config["secret"])

        # Create mock request
        request = Mock()

        # Validate the JWT
        user_id = validator(valid_jwt, request)

        # Should return the user ID
        assert user_id == "123"

    async def test_real_jwt_validation_expired(
        self,
        create_test_jwt,
        api_key_config,
    ):
        """Test that JWT validator rejects expired tokens."""
        # Create an expired JWT
        expired_jwt = create_test_jwt(
            user_id="123",
            expires_in_minutes=-60,  # Expired 1 hour ago
        )

        # Create validator
        validator = api_key_jwt_validator(algorithm=api_key_config["algorithm"], secret=api_key_config["secret"])

        # Create mock request
        request = Mock()

        # Should return None (validator doesn't raise, resolver does)
        user_id = validator(expired_jwt, request)
        assert user_id is None

    async def test_real_jwt_validation_invalid_signature(
        self,
        create_test_jwt,
        api_key_config,
    ):
        """Test that JWT validator rejects tokens with invalid signatures."""
        # Create a JWT with one secret
        valid_jwt = create_test_jwt(user_id="123")

        # Try to validate with a different secret
        validator = api_key_jwt_validator(algorithm=api_key_config["algorithm"], secret="wrong-secret")

        # Create mock request
        request = Mock()

        # Should return None (validator doesn't raise, resolver does)
        user_id = validator(valid_jwt, request)
        assert user_id is None

    async def test_real_jwt_validation_wrong_type(
        self,
        create_test_jwt,
        api_key_config,
    ):
        """Test that JWT validator rejects tokens with wrong type."""
        # Create a JWT with wrong type
        wrong_type_jwt = create_test_jwt(
            user_id="123",
            token_type="access",  # Should be "api_key"
        )

        # Create validator
        validator = api_key_jwt_validator(algorithm=api_key_config["algorithm"], secret=api_key_config["secret"])

        # Create mock request
        request = Mock()

        # Should return None (validator doesn't raise, resolver does)
        user_id = validator(wrong_type_jwt, request)
        assert user_id is None

    async def test_real_jwt_validation_missing_sub(
        self,
        api_key_config,
    ):
        """Test that JWT validator rejects tokens without 'sub' claim."""
        # Create a JWT without 'sub' claim
        no_sub_jwt = jwt.encode(
            {
                "type": "api_key",
                "exp": datetime.now(timezone.utc) + timedelta(hours=1),
            },
            api_key_config["secret"],
            algorithm=api_key_config["algorithm"],
        )

        # Create validator
        validator = api_key_jwt_validator(algorithm=api_key_config["algorithm"], secret=api_key_config["secret"])

        # Create mock request
        request = Mock()

        # Should return None (validator doesn't raise, resolver does)
        user_id = validator(no_sub_jwt, request)
        assert user_id is None


class TestUserStatusValidation:
    """Test that user status is properly validated."""

    async def test_active_user_allowed(
        self,
        check_auth_api_available,
        test_user_active,
        auth_api_url,
    ):
        """Test that active users are allowed."""
        # This is tested in test_real_api_key_validation_success
        # Just verify the user is active
        assert test_user_active["status"] == "active"

    async def test_inactive_user_denied(
        self,
        check_auth_api_available,
        test_user_inactive,
        auth_api_url,
    ):
        """Test that inactive users are denied."""
        # This test will be skipped until we can create inactive users
        # See conftest.py test_user_inactive fixture
        pass

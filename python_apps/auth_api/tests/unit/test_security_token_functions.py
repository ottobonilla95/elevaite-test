"""Tests for token-related functions in the security module."""

import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch
from fastapi import HTTPException

from app.core.security import (
    create_access_token,
    create_refresh_token,
    verify_token,
)
from jose import jwt
from app.core.config import settings


class TestTokenFunctions:
    """Tests for token-related functions in the security module."""

    def test_create_access_token(self):
        """Test creating an access token."""
        # Test data
        subject = 1
        tenant_id = "test_tenant"

        # Create token
        token = create_access_token(subject=subject, tenant_id=tenant_id)

        # Verify token is a string
        assert isinstance(token, str)
        assert len(token) > 0

        # Decode the token to verify its contents
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        assert payload["sub"] == str(subject)
        assert payload["tenant_id"] == tenant_id
        assert payload["type"] == "access"

    def test_create_refresh_token(self):
        """Test creating a refresh token."""
        # Test data
        subject = 1
        tenant_id = "test_tenant"

        # Create token
        token = create_refresh_token(subject=subject, tenant_id=tenant_id)

        # Verify token is a string
        assert isinstance(token, str)
        assert len(token) > 0

        # Decode the token to verify its contents
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        assert payload["sub"] == str(subject)
        assert payload["tenant_id"] == tenant_id
        assert payload["type"] == "refresh"

    def test_verify_token_valid(self):
        """Test verifying a valid token."""
        # Test data
        subject = 1
        tenant_id = "test_tenant"

        # Create token
        token = create_access_token(subject=subject, tenant_id=tenant_id)

        # Verify token
        payload = verify_token(token, "access")

        # Verify payload
        assert isinstance(payload, dict)
        assert "sub" in payload
        assert "tenant_id" in payload
        assert payload["sub"] == str(subject)
        assert payload["tenant_id"] == tenant_id

    def test_verify_token_wrong_type(self):
        """Test verifying a token with wrong type."""
        # Test data
        subject = 1
        tenant_id = "test_tenant"

        # Create access token
        token = create_access_token(subject=subject, tenant_id=tenant_id)

        # Verify token with wrong type - should raise an exception
        with pytest.raises(HTTPException) as excinfo:
            verify_token(token, "refresh")

        # Check exception details
        assert excinfo.value.status_code == 401
        assert excinfo.value.detail == "Invalid token type"

    def test_verify_token_expired(self):
        """Test verifying an expired token."""
        # Mock datetime to create an expired token
        with patch("app.core.security.datetime") as mock_datetime:
            # Set current time
            current_time = datetime.now(timezone.utc)
            mock_datetime.now.return_value = current_time

            # Set expiration time in the past
            mock_datetime.timedelta.side_effect = lambda **kwargs: timedelta(**kwargs)

            # Create token with expiration in the past
            subject = 1
            tenant_id = "test_tenant"
            expires_delta = timedelta(minutes=-10)  # Expired 10 minutes ago

            # Create token with custom expiration
            token = create_access_token(
                subject=subject, tenant_id=tenant_id, expires_delta=expires_delta
            )

            # Verify token - should raise an exception
            with pytest.raises(HTTPException) as excinfo:
                verify_token(token, "access")

            # Check exception details
            assert excinfo.value.status_code == 401
            assert "Could not validate credentials" in excinfo.value.detail

    def test_verify_token_invalid(self):
        """Test verifying an invalid token."""
        # Invalid token
        token = "invalid.token.string"

        # Verify token - should raise an exception
        with pytest.raises(HTTPException) as excinfo:
            verify_token(token, "access")

        # Check exception details
        assert excinfo.value.status_code == 401
        assert "Could not validate credentials" in excinfo.value.detail

"""Unit tests for admin endpoints."""

import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import HTTPException

from app.routers.admin import (
    update_user_status,
    suspend_user,
    activate_user,
    deactivate_user,
    get_user_sessions,
    revoke_user_sessions,
    UserStatusUpdateRequest,
)
from app.db.models import User, UserStatus, Session as UserSession


@pytest.fixture
def mock_superuser():
    """Create a mock superuser."""
    user = MagicMock(spec=User)
    user.id = 1
    user.email = "admin@example.com"
    user.is_superuser = True
    user.status = UserStatus.ACTIVE.value
    return user


@pytest.fixture
def mock_target_user():
    """Create a mock target user."""
    user = MagicMock(spec=User)
    user.id = 2
    user.email = "user@example.com"
    user.is_superuser = False
    user.status = UserStatus.ACTIVE.value
    return user


@pytest.fixture
def mock_request():
    """Create a mock request."""
    request = MagicMock()
    request.client.host = "127.0.0.1"
    request.headers.get.return_value = "test-user-agent"
    return request


@pytest.fixture
def mock_session():
    """Create a mock async session."""
    session = AsyncMock()
    return session


class TestUpdateUserStatus:
    """Tests for update_user_status endpoint."""

    @pytest.mark.asyncio
    async def test_update_status_success(
        self, mock_request, mock_superuser, mock_target_user, mock_session
    ):
        """Test successfully updating user status."""
        # Setup
        status_update = UserStatusUpdateRequest(
            status="suspended", reason="Policy violation"
        )

        # Mock database queries
        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = mock_target_user
        mock_session.execute = AsyncMock(return_value=mock_result)

        # Mock log_user_activity
        with patch("app.routers.admin.log_user_activity", new=AsyncMock()):
            result = await update_user_status(
                mock_request, 2, status_update, mock_superuser, mock_session
            )

        # Assertions
        assert result.user_id == 2
        assert result.email == "user@example.com"
        assert result.old_status == UserStatus.ACTIVE.value
        assert result.new_status == "suspended"
        assert result.changed_by == 1
        assert result.reason == "Policy violation"

    @pytest.mark.asyncio
    async def test_cannot_modify_self(
        self, mock_request, mock_superuser, mock_session
    ):
        """Test that user cannot modify their own status."""
        status_update = UserStatusUpdateRequest(status="suspended")

        with pytest.raises(HTTPException) as exc_info:
            await update_user_status(
                mock_request, 1, status_update, mock_superuser, mock_session
            )

        assert exc_info.value.status_code == 400
        assert "Cannot modify your own account status" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_user_not_found(self, mock_request, mock_superuser, mock_session):
        """Test updating status for non-existent user."""
        status_update = UserStatusUpdateRequest(status="suspended")

        # Mock database query returning None
        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = None
        mock_session.execute = AsyncMock(return_value=mock_result)

        with pytest.raises(HTTPException) as exc_info:
            await update_user_status(
                mock_request, 999, status_update, mock_superuser, mock_session
            )

        assert exc_info.value.status_code == 404
        assert "not found" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_invalid_status_value(
        self, mock_request, mock_superuser, mock_target_user, mock_session
    ):
        """Test updating with invalid status value."""
        # Pydantic validation will catch this before the function is called
        from pydantic import ValidationError

        with pytest.raises(ValidationError) as exc_info:
            UserStatusUpdateRequest(status="invalid_status")

        assert "string_pattern_mismatch" in str(exc_info.value)


class TestConvenienceEndpoints:
    """Tests for suspend/activate/deactivate convenience endpoints."""

    @pytest.mark.asyncio
    async def test_suspend_user(
        self, mock_request, mock_superuser, mock_target_user, mock_session
    ):
        """Test suspend_user endpoint."""
        # Mock database queries
        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = mock_target_user
        mock_session.execute = AsyncMock(return_value=mock_result)

        with patch("app.routers.admin.log_user_activity", new=AsyncMock()):
            result = await suspend_user(
                mock_request, 2, "Test suspension", mock_superuser, mock_session
            )

        assert result.new_status == "suspended"
        assert result.reason == "Test suspension"

    @pytest.mark.asyncio
    async def test_activate_user(
        self, mock_request, mock_superuser, mock_target_user, mock_session
    ):
        """Test activate_user endpoint."""
        mock_target_user.status = UserStatus.SUSPENDED.value

        # Mock database queries
        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = mock_target_user
        mock_session.execute = AsyncMock(return_value=mock_result)

        with patch("app.routers.admin.log_user_activity", new=AsyncMock()):
            result = await activate_user(
                mock_request, 2, "Suspension lifted", mock_superuser, mock_session
            )

        assert result.new_status == "active"
        assert result.reason == "Suspension lifted"

    @pytest.mark.asyncio
    async def test_deactivate_user(
        self, mock_request, mock_superuser, mock_target_user, mock_session
    ):
        """Test deactivate_user endpoint."""
        # Mock database queries
        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = mock_target_user
        mock_session.execute = AsyncMock(return_value=mock_result)

        with patch("app.routers.admin.log_user_activity", new=AsyncMock()):
            result = await deactivate_user(
                mock_request, 2, "User left company", mock_superuser, mock_session
            )

        assert result.new_status == "inactive"
        assert result.reason == "User left company"


class TestGetUserSessions:
    """Tests for get_user_sessions endpoint."""

    @pytest.mark.asyncio
    async def test_get_sessions_success(
        self, mock_superuser, mock_target_user, mock_session
    ):
        """Test getting user sessions."""
        # Create mock sessions
        now = datetime.now(timezone.utc)
        active_session = MagicMock(spec=UserSession)
        active_session.id = 1
        active_session.is_active = True
        active_session.expires_at = now + timedelta(hours=1)
        active_session.created_at = now - timedelta(hours=1)
        active_session.ip_address = "192.168.1.1"
        active_session.user_agent = "Mozilla/5.0"

        expired_session = MagicMock(spec=UserSession)
        expired_session.id = 2
        expired_session.is_active = True
        expired_session.expires_at = now - timedelta(hours=1)
        expired_session.created_at = now - timedelta(hours=2)
        expired_session.ip_address = "192.168.1.2"
        expired_session.user_agent = "Chrome/90.0"

        # Mock database queries
        user_result = MagicMock()
        user_result.scalars.return_value.first.return_value = mock_target_user

        sessions_result = MagicMock()
        sessions_result.scalars.return_value.all.return_value = [
            active_session,
            expired_session,
        ]

        mock_session.execute = AsyncMock(
            side_effect=[user_result, sessions_result]
        )

        result = await get_user_sessions(2, mock_superuser, mock_session)

        assert result.user_id == 2
        assert result.email == "user@example.com"
        assert result.total_sessions == 2
        assert result.active_sessions == 1
        assert len(result.sessions) == 2

    @pytest.mark.asyncio
    async def test_get_sessions_user_not_found(self, mock_superuser, mock_session):
        """Test getting sessions for non-existent user."""
        # Mock database query returning None
        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = None
        mock_session.execute = AsyncMock(return_value=mock_result)

        with pytest.raises(HTTPException) as exc_info:
            await get_user_sessions(999, mock_superuser, mock_session)

        assert exc_info.value.status_code == 404


class TestRevokeUserSessions:
    """Tests for revoke_user_sessions endpoint."""

    @pytest.mark.asyncio
    async def test_revoke_sessions_success(
        self, mock_request, mock_superuser, mock_target_user, mock_session
    ):
        """Test revoking user sessions."""
        # Mock database queries
        user_result = MagicMock()
        user_result.scalars.return_value.first.return_value = mock_target_user

        revoke_result = MagicMock()
        revoke_result.rowcount = 3

        mock_session.execute = AsyncMock(
            side_effect=[user_result, revoke_result]
        )

        with patch("app.routers.admin.log_user_activity", new=AsyncMock()):
            result = await revoke_user_sessions(
                mock_request, 2, mock_superuser, mock_session
            )

        assert result["user_id"] == 2
        assert result["sessions_revoked"] == 3
        assert "Successfully revoked" in result["message"]

    @pytest.mark.asyncio
    async def test_revoke_sessions_user_not_found(
        self, mock_request, mock_superuser, mock_session
    ):
        """Test revoking sessions for non-existent user."""
        # Mock database query returning None
        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = None
        mock_session.execute = AsyncMock(return_value=mock_result)

        with pytest.raises(HTTPException) as exc_info:
            await revoke_user_sessions(mock_request, 999, mock_superuser, mock_session)

        assert exc_info.value.status_code == 404


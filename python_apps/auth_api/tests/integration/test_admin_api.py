"""Integration tests for admin API endpoints."""

import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock, AsyncMock
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.routers import admin
from app.db.models import User, UserStatus, Session as UserSession
from app.core.deps import get_current_superuser, get_current_admin_or_superuser
from app.db.orm import get_async_session


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
def mock_admin_user():
    """Create a mock admin user (not superuser)."""
    user = MagicMock(spec=User)
    user.id = 3
    user.email = "admin2@example.com"
    user.is_superuser = False
    user.application_admin = True
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
def mock_session():
    """Create a mock async session."""
    session = AsyncMock()
    return session


@pytest.fixture
def app(mock_superuser, mock_admin_user, mock_session):
    """Create a test FastAPI app with dependency overrides."""
    test_app = FastAPI()
    test_app.include_router(admin.router, prefix="/api/admin", tags=["admin"])

    # Override dependencies
    test_app.dependency_overrides[get_current_superuser] = lambda: mock_superuser
    test_app.dependency_overrides[get_current_admin_or_superuser] = (
        lambda: mock_admin_user
    )
    test_app.dependency_overrides[get_async_session] = lambda: mock_session

    return test_app


@pytest.fixture
def client(app):
    """Create a test client."""
    return TestClient(app)


class TestUpdateUserStatus:
    """Integration tests for user status update endpoints."""

    def test_update_status_success(self, client, mock_target_user, mock_session):
        """Test successfully updating user status."""
        # Mock database queries
        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = mock_target_user
        mock_session.execute = AsyncMock(return_value=mock_result)

        # Mock log_user_activity
        from unittest.mock import patch

        with patch("app.routers.admin.log_user_activity", new=AsyncMock()):
            response = client.post(
                "/api/admin/users/2/status",
                json={"status": "suspended", "reason": "Policy violation"},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == 2
        assert data["new_status"] == "suspended"
        assert data["reason"] == "Policy violation"

    def test_update_status_invalid_value(self, client, mock_target_user, mock_session):
        """Test updating with invalid status value."""
        # Mock database query
        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = mock_target_user
        mock_session.execute = AsyncMock(return_value=mock_result)

        response = client.post(
            "/api/admin/users/2/status",
            json={"status": "invalid_status"},
        )

        assert response.status_code == 422  # Validation error from Pydantic pattern

    def test_update_status_user_not_found(self, client, mock_session):
        """Test updating status for non-existent user."""
        # Mock database query returning None
        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = None
        mock_session.execute = AsyncMock(return_value=mock_result)

        response = client.post(
            "/api/admin/users/999/status",
            json={"status": "suspended"},
        )

        assert response.status_code == 404

    def test_cannot_modify_self(self, client, mock_session):
        """Test that user cannot modify their own status."""
        response = client.post(
            "/api/admin/users/1/status",  # Same as mock_superuser.id
            json={"status": "suspended"},
        )

        assert response.status_code == 400


class TestConvenienceEndpoints:
    """Integration tests for suspend/activate/deactivate endpoints."""

    def test_suspend_user(self, client, mock_target_user, mock_session):
        """Test suspend user endpoint."""
        # Mock database queries
        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = mock_target_user
        mock_session.execute = AsyncMock(return_value=mock_result)

        from unittest.mock import patch

        with patch("app.routers.admin.log_user_activity", new=AsyncMock()):
            response = client.post(
                "/api/admin/users/2/suspend",
                params={"reason": "Test suspension"},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["new_status"] == "suspended"

    def test_activate_user(self, client, mock_target_user, mock_session):
        """Test activate user endpoint."""
        mock_target_user.status = UserStatus.SUSPENDED.value

        # Mock database queries
        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = mock_target_user
        mock_session.execute = AsyncMock(return_value=mock_result)

        from unittest.mock import patch

        with patch("app.routers.admin.log_user_activity", new=AsyncMock()):
            response = client.post("/api/admin/users/2/activate")

        assert response.status_code == 200
        data = response.json()
        assert data["new_status"] == "active"

    def test_deactivate_user(self, client, mock_target_user, mock_session):
        """Test deactivate user endpoint."""
        # Mock database queries
        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = mock_target_user
        mock_session.execute = AsyncMock(return_value=mock_result)

        from unittest.mock import patch

        with patch("app.routers.admin.log_user_activity", new=AsyncMock()):
            response = client.post("/api/admin/users/2/deactivate")

        assert response.status_code == 200
        data = response.json()
        assert data["new_status"] == "inactive"


class TestSessionManagement:
    """Integration tests for session management endpoints."""

    def test_get_user_sessions(self, client, mock_target_user, mock_session):
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

        # Mock database queries
        user_result = MagicMock()
        user_result.scalars.return_value.first.return_value = mock_target_user

        sessions_result = MagicMock()
        sessions_result.scalars.return_value.all.return_value = [active_session]

        mock_session.execute = AsyncMock(side_effect=[user_result, sessions_result])

        # Override dependency for this test to use admin user
        from app.routers.admin import get_current_admin_or_superuser as get_admin

        client.app.dependency_overrides[get_admin] = lambda: mock_target_user

        response = client.get("/api/admin/users/2/sessions")

        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == 2
        assert data["total_sessions"] == 1
        assert data["active_sessions"] == 1

    def test_revoke_user_sessions(self, client, mock_target_user, mock_session):
        """Test revoking user sessions."""
        # Mock database queries
        user_result = MagicMock()
        user_result.scalars.return_value.first.return_value = mock_target_user

        revoke_result = MagicMock()
        revoke_result.rowcount = 3

        mock_session.execute = AsyncMock(side_effect=[user_result, revoke_result])

        from unittest.mock import patch

        with patch("app.routers.admin.log_user_activity", new=AsyncMock()):
            response = client.post("/api/admin/users/2/revoke-sessions")

        assert response.status_code == 200
        data = response.json()
        assert data["sessions_revoked"] == 3
        assert "Successfully revoked" in data["message"]

    def test_get_sessions_user_not_found(self, client, mock_session):
        """Test getting sessions for non-existent user."""
        # Mock database query returning None
        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = None
        mock_session.execute = AsyncMock(return_value=mock_result)

        response = client.get("/api/admin/users/999/sessions")

        assert response.status_code == 404

    def test_revoke_sessions_user_not_found(self, client, mock_session):
        """Test revoking sessions for non-existent user."""
        # Mock database query returning None
        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = None
        mock_session.execute = AsyncMock(return_value=mock_result)

        response = client.post("/api/admin/users/999/revoke-sessions")

        assert response.status_code == 404


class TestRequestValidation:
    """Integration tests for request validation."""

    def test_status_pattern_validation(self, client):
        """Test that status field validates against pattern."""
        response = client.post(
            "/api/admin/users/2/status",
            json={"status": "not_a_valid_status"},
        )

        assert response.status_code == 422  # Validation error

    def test_missing_status_field(self, client):
        """Test that status field is required."""
        response = client.post(
            "/api/admin/users/2/status",
            json={"reason": "Some reason"},
        )

        assert response.status_code == 422  # Validation error

    def test_optional_reason_field(self, client, mock_target_user, mock_session):
        """Test that reason field is optional."""
        # Mock database queries
        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = mock_target_user
        mock_session.execute = AsyncMock(return_value=mock_result)

        from unittest.mock import patch

        with patch("app.routers.admin.log_user_activity", new=AsyncMock()):
            response = client.post(
                "/api/admin/users/2/status",
                json={"status": "suspended"},  # No reason provided
            )

        assert response.status_code == 200
        data = response.json()
        assert data["reason"] is None

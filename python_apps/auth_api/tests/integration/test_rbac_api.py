"""Integration tests for RBAC API endpoints with proper authorization testing."""

import pytest
from datetime import datetime, timezone
from uuid import uuid4
from unittest.mock import MagicMock, AsyncMock
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.routers import rbac
from app.db.models import User, UserStatus
from app.db.models_rbac import (
    Role,
    RolePermission,
    Group,
    GroupPermission,
    UserGroupMembership,
    Organization,
    UserRoleAssignment,
    PermissionOverride,
)
from app.core.deps import get_current_user, get_current_superuser
from app.db.orm import get_tenant_async_db


# ============================================================================
# Fixtures
# ============================================================================


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
def mock_regular_user():
    """Create a mock regular user (not superuser)."""
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
def superuser_app(mock_superuser, mock_session):
    """Create a test app with superuser authentication."""
    test_app = FastAPI()
    test_app.include_router(rbac.router, prefix="/api/rbac", tags=["rbac"])

    # Override dependencies for superuser access
    test_app.dependency_overrides[get_current_user] = lambda: mock_superuser
    test_app.dependency_overrides[get_current_superuser] = lambda: mock_superuser
    test_app.dependency_overrides[get_tenant_async_db] = lambda: mock_session

    return test_app


@pytest.fixture
def regular_user_app(mock_regular_user, mock_session):
    """Create a test app with regular user authentication."""
    test_app = FastAPI()
    test_app.include_router(rbac.router, prefix="/api/rbac", tags=["rbac"])

    # Override dependencies for regular user access
    test_app.dependency_overrides[get_current_user] = lambda: mock_regular_user
    test_app.dependency_overrides[get_tenant_async_db] = lambda: mock_session
    # Note: We do NOT override get_current_superuser, so superuser-only endpoints will fail

    return test_app


@pytest.fixture
def superuser_client(superuser_app):
    """Create a test client with superuser access."""
    return TestClient(superuser_app)


@pytest.fixture
def regular_user_client(regular_user_app):
    """Create a test client with regular user access."""
    return TestClient(regular_user_app)


# ============================================================================
# Test /me Endpoint
# ============================================================================


class TestGetMyRbac:
    """Integration tests for GET /api/rbac/me endpoint."""

    def test_get_my_rbac_as_superuser(self, superuser_client, mock_superuser, mock_session):
        """Test superuser gets their RBAC info with is_superuser=True."""
        # Mock empty results for role assignments, group memberships, overrides
        empty_result = MagicMock()
        empty_result.scalars.return_value.all.return_value = []
        mock_session.execute = AsyncMock(return_value=empty_result)

        response = superuser_client.get("/api/rbac/me")

        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == mock_superuser.id
        assert data["is_superuser"] is True
        assert data["role_assignments"] == []
        assert data["group_memberships"] == []
        assert data["permission_overrides"] == []

    def test_get_my_rbac_as_regular_user(self, regular_user_client, mock_regular_user, mock_session):
        """Test regular user gets their RBAC info with is_superuser=False."""
        empty_result = MagicMock()
        empty_result.scalars.return_value.all.return_value = []
        mock_session.execute = AsyncMock(return_value=empty_result)

        response = regular_user_client.get("/api/rbac/me")

        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == mock_regular_user.id
        assert data["is_superuser"] is False

    def test_get_my_rbac_with_role_assignments(self, superuser_client, mock_superuser, mock_session):
        """Test user with role assignments gets them in response."""
        # Create mock role assignment
        mock_assignment = MagicMock(spec=UserRoleAssignment)
        mock_assignment.user_id = mock_superuser.id
        mock_assignment.role = "admin"
        mock_assignment.resource_type = "organization"
        mock_assignment.resource_id = uuid4()
        mock_assignment.created_at = datetime.now(timezone.utc)

        role_result = MagicMock()
        role_result.scalars.return_value.all.return_value = [mock_assignment]

        empty_result = MagicMock()
        empty_result.scalars.return_value.all.return_value = []

        mock_session.execute = AsyncMock(side_effect=[role_result, empty_result, empty_result])

        response = superuser_client.get("/api/rbac/me")

        assert response.status_code == 200
        data = response.json()
        assert len(data["role_assignments"]) == 1
        assert data["role_assignments"][0]["role"] == "admin"


# ============================================================================
# Test Role Authorization
# ============================================================================


class TestRoleAuthorizationEndpoints:
    """Integration tests for role management authorization."""

    def test_regular_user_cannot_create_role(self, regular_user_client, mock_session):
        """Test that regular user cannot create a role."""
        response = regular_user_client.post(
            "/api/rbac/roles",
            json={
                "name": "test_role",
                "base_type": "editor",
                "scope_type": "project",
            },
        )

        # Should fail because get_current_superuser dependency will reject
        assert response.status_code in [401, 403, 500]  # Depends on how dependency fails

    def test_anyone_can_list_roles(self, regular_user_client, mock_session):
        """Test that any authenticated user can list roles."""
        # Mock role list result
        mock_role = MagicMock(spec=Role)
        mock_role.id = uuid4()
        mock_role.name = "viewer"
        mock_role.base_type = "viewer"
        mock_role.scope_type = "project"
        mock_role.description = "Viewer role"
        mock_role.is_system = True
        mock_role.created_at = datetime.now(timezone.utc)
        mock_role.permissions = []

        list_result = MagicMock()
        list_result.scalars.return_value.all.return_value = [mock_role]
        list_result.scalar.return_value = 1

        mock_session.execute = AsyncMock(return_value=list_result)

        response = regular_user_client.get("/api/rbac/roles")

        assert response.status_code == 200
        data = response.json()
        assert "roles" in data


# ============================================================================
# Test Group Authorization
# ============================================================================


class TestGroupAuthorizationEndpoints:
    """Integration tests for group management authorization."""

    def test_anyone_can_list_groups(self, regular_user_client, mock_session):
        """Test that any authenticated user can list groups."""
        # Mock group list result
        mock_group = MagicMock(spec=Group)
        mock_group.id = uuid4()
        mock_group.organization_id = uuid4()
        mock_group.name = "Test Group"
        mock_group.description = "Test"
        mock_group.created_at = datetime.now(timezone.utc)
        mock_group.updated_at = datetime.now(timezone.utc)
        mock_group.permissions = []

        list_result = MagicMock()
        list_result.scalars.return_value.all.return_value = [mock_group]
        list_result.scalar.return_value = 1

        mock_session.execute = AsyncMock(return_value=list_result)

        response = regular_user_client.get("/api/rbac/groups")

        assert response.status_code == 200

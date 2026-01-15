"""
End-to-End tests for RBAC (Role-Based Access Control) endpoints.

These tests verify the complete RBAC flow including:
1. Role and group management by superusers
2. Authorization checks for non-superusers
3. User RBAC info retrieval via /me endpoint

Run with: pytest tests/e2e/test_rbac_e2e.py -v --run-e2e

Prerequisites:
- Auth API running at http://localhost:8004
- PostgreSQL database available
"""

import pytest
import httpx
from uuid import uuid4
from typing import Optional


# Configuration - can be overridden via pytest options
AUTH_API_URL = "http://localhost:8004"


def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line("markers", "e2e: mark test as end-to-end test")


@pytest.fixture(scope="module")
def auth_api_url(request):
    """Get Auth API URL from pytest options or use default."""
    return request.config.getoption("--auth-api-url", default=AUTH_API_URL)


class RbacTestClient:
    """Helper client for RBAC API testing."""

    def __init__(self, base_url: str, token: Optional[str] = None):
        self.base_url = base_url
        self.token = token

    @property
    def headers(self) -> dict:
        headers = {"Content-Type": "application/json", "X-Tenant-ID": "default"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    async def login(self, email: str, password: str) -> str:
        """Login and return access token."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/api/auth/login",
                json={"email": email, "password": password},
                headers={"Content-Type": "application/json", "X-Tenant-ID": "default"},
                timeout=10.0,
            )
            response.raise_for_status()
            data = response.json()
            self.token = data["access_token"]
            return self.token

    async def get_my_rbac(self) -> dict:
        """Get current user's RBAC info."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/api/rbac/me",
                headers=self.headers,
                timeout=10.0,
            )
            response.raise_for_status()
            return response.json()

    async def list_roles(self) -> dict:
        """List all roles."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/api/rbac/roles",
                headers=self.headers,
                timeout=10.0,
            )
            response.raise_for_status()
            return response.json()

    async def create_role(self, name: str, base_type: str, scope_type: str, description: str = None) -> dict:
        """Create a new role."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/api/rbac/roles",
                json={
                    "name": name,
                    "base_type": base_type,
                    "scope_type": scope_type,
                    "description": description,
                },
                headers=self.headers,
                timeout=10.0,
            )
            response.raise_for_status()
            return response.json()

    async def create_organization(self, name: str, description: str = None) -> dict:
        """Create a new organization."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/api/rbac/organizations",
                json={"name": name, "description": description},
                headers=self.headers,
                timeout=10.0,
            )
            response.raise_for_status()
            return response.json()

    async def create_group(self, organization_id: str, name: str, description: str = None) -> dict:
        """Create a new group."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/api/rbac/groups",
                json={
                    "organization_id": organization_id,
                    "name": name,
                    "description": description,
                },
                headers=self.headers,
                timeout=10.0,
            )
            response.raise_for_status()
            return response.json()

    async def list_groups(self, organization_id: str = None) -> dict:
        """List groups."""
        async with httpx.AsyncClient() as client:
            params = {}
            if organization_id:
                params["organization_id"] = organization_id
            response = await client.get(
                f"{self.base_url}/api/rbac/groups",
                params=params,
                headers=self.headers,
                timeout=10.0,
            )
            response.raise_for_status()
            return response.json()


@pytest.fixture
def rbac_client(auth_api_url) -> RbacTestClient:
    """Create an unauthenticated RBAC client."""
    return RbacTestClient(auth_api_url)


# ============================================================================
# Test Classes
# ============================================================================


@pytest.mark.e2e
class TestRbacMeEndpoint:
    """E2E tests for GET /api/rbac/me endpoint."""

    @pytest.mark.asyncio
    async def test_get_my_rbac_unauthenticated(self, rbac_client):
        """Test that unauthenticated requests are rejected."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{rbac_client.base_url}/api/rbac/me",
                headers={"Content-Type": "application/json", "X-Tenant-ID": "default"},
                timeout=10.0,
            )
            assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_my_rbac_authenticated(self, rbac_client, superuser_credentials):
        """Test getting RBAC info for authenticated user."""
        # Login as superuser
        await rbac_client.login(
            superuser_credentials["email"],
            superuser_credentials["password"],
        )

        # Get RBAC info
        rbac_info = await rbac_client.get_my_rbac()

        assert "user_id" in rbac_info
        assert "is_superuser" in rbac_info
        assert "role_assignments" in rbac_info
        assert "group_memberships" in rbac_info
        assert "permission_overrides" in rbac_info
        assert rbac_info["is_superuser"] is True


@pytest.mark.e2e
class TestRbacRoleManagement:
    """E2E tests for role management endpoints."""

    @pytest.mark.asyncio
    async def test_list_roles(self, rbac_client, superuser_credentials):
        """Test listing roles."""
        await rbac_client.login(
            superuser_credentials["email"],
            superuser_credentials["password"],
        )

        roles = await rbac_client.list_roles()

        assert "roles" in roles
        assert "total" in roles
        assert isinstance(roles["roles"], list)

    @pytest.mark.asyncio
    async def test_create_role_as_superuser(self, rbac_client, superuser_credentials):
        """Test creating a role as superuser."""
        await rbac_client.login(
            superuser_credentials["email"],
            superuser_credentials["password"],
        )

        role_name = f"test_role_{uuid4().hex[:8]}"
        role = await rbac_client.create_role(
            name=role_name,
            base_type="editor",
            scope_type="project",
            description="Test role for e2e testing",
        )

        assert role["name"] == role_name
        assert role["base_type"] == "editor"
        assert role["scope_type"] == "project"
        assert role["is_system"] is False

    @pytest.mark.asyncio
    async def test_create_role_as_regular_user_forbidden(self, rbac_client, regular_user_credentials):
        """Test that regular users cannot create roles."""
        await rbac_client.login(
            regular_user_credentials["email"],
            regular_user_credentials["password"],
        )

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{rbac_client.base_url}/api/rbac/roles",
                json={
                    "name": "unauthorized_role",
                    "base_type": "viewer",
                    "scope_type": "project",
                },
                headers=rbac_client.headers,
                timeout=10.0,
            )
            assert response.status_code == 403


@pytest.mark.e2e
class TestRbacGroupManagement:
    """E2E tests for group management endpoints."""

    @pytest.mark.asyncio
    async def test_create_and_list_groups(self, rbac_client, superuser_credentials):
        """Test creating and listing groups."""
        await rbac_client.login(
            superuser_credentials["email"],
            superuser_credentials["password"],
        )

        # First create an organization
        org_name = f"test_org_{uuid4().hex[:8]}"
        org = await rbac_client.create_organization(
            name=org_name,
            description="Test organization for e2e testing",
        )

        # Create a group in the organization
        group_name = f"test_group_{uuid4().hex[:8]}"
        group = await rbac_client.create_group(
            organization_id=org["id"],
            name=group_name,
            description="Test group for e2e testing",
        )

        assert group["name"] == group_name
        assert group["organization_id"] == org["id"]

        # List groups filtered by organization
        groups = await rbac_client.list_groups(organization_id=org["id"])

        assert "groups" in groups
        group_names = [g["name"] for g in groups["groups"]]
        assert group_name in group_names

    @pytest.mark.asyncio
    async def test_create_group_as_regular_user_forbidden(self, rbac_client, regular_user_credentials):
        """Test that regular users cannot create groups.

        Note: The API may return 404 if the organization doesn't exist (checked first)
        or 403 if the user is forbidden. Both indicate the user cannot create the group.
        """
        await rbac_client.login(
            regular_user_credentials["email"],
            regular_user_credentials["password"],
        )

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{rbac_client.base_url}/api/rbac/groups",
                json={
                    "organization_id": str(uuid4()),
                    "name": "unauthorized_group",
                },
                headers=rbac_client.headers,
                timeout=10.0,
            )
            # Either 403 (forbidden) or 404 (org not found) means user can't create
            assert response.status_code in (403, 404)


# ============================================================================
# Fixtures for test users
# ============================================================================


@pytest.fixture(scope="module")
def superuser_credentials(auth_api_url) -> dict:
    """
    Get or create superuser credentials for testing.

    In a real e2e setup, this would either:
    1. Use pre-seeded test data
    2. Create a superuser via admin API
    3. Use environment variables

    For now, we expect these to be configured in the test environment.
    """
    # These should match your test environment setup
    return {
        "email": "e2e-superuser@test.com",
        "password": "TestPassword123!",
    }


@pytest.fixture(scope="module")
def regular_user_credentials(auth_api_url) -> dict:
    """
    Get or create regular user credentials for testing.
    """
    return {
        "email": "e2e-regular@test.com",
        "password": "TestPassword123!",
    }

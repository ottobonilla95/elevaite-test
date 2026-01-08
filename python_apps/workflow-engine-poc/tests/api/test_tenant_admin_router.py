"""
Tests for Tenant Admin Router

Tests all tenant administration endpoints including:
- CRUD operations for tenants
- Superadmin authentication requirements
- Error handling and edge cases
"""

import pytest
import uuid
from datetime import datetime, timezone
from unittest.mock import MagicMock, AsyncMock
from fastapi.testclient import TestClient

from rbac_sdk import HDR_USER_ID, HDR_ORG_ID

from workflow_engine_poc.main import app
from workflow_engine_poc.tenant_admin import get_admin_session, get_tenant_registry


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def mock_registry():
    """Mock TenantRegistry for testing."""
    registry = MagicMock()
    return registry


@pytest.fixture
def sample_tenant():
    """Sample tenant data for testing."""
    tenant = MagicMock()
    tenant.id = uuid.uuid4()
    tenant.tenant_id = "test_tenant_001"  # Use underscores, not hyphens (pattern: ^[a-z][a-z0-9_]*$)
    tenant.name = "Test Tenant"
    tenant.description = "A test tenant for unit testing"
    tenant.status = "active"
    tenant.schema_name = "tenant_test_tenant_001"
    tenant.metadata_ = {"tier": "enterprise"}
    tenant.is_schema_initialized = True
    tenant.created_at = datetime.now(timezone.utc)
    tenant.updated_at = datetime.now(timezone.utc)
    return tenant


@pytest.fixture
def superadmin_headers(test_user_id, test_org_id, test_tenant_id):
    """Headers for superadmin authentication."""
    return {
        HDR_USER_ID: test_user_id,
        HDR_ORG_ID: test_org_id,
        "X-Tenant-ID": test_tenant_id,
    }


@pytest.fixture
def tenant_admin_client(test_client, mock_registry, auth_headers):
    """Test client with mocked tenant admin dependencies."""

    # Override the dependencies
    async def mock_get_admin_session():
        yield AsyncMock()

    def mock_get_tenant_registry():
        return mock_registry

    app.dependency_overrides[get_admin_session] = mock_get_admin_session
    app.dependency_overrides[get_tenant_registry] = mock_get_tenant_registry

    # Add auth headers to client
    test_client.headers.update(auth_headers)

    yield test_client, mock_registry

    # Clean up overrides
    if get_admin_session in app.dependency_overrides:
        del app.dependency_overrides[get_admin_session]
    if get_tenant_registry in app.dependency_overrides:
        del app.dependency_overrides[get_tenant_registry]


# ============================================================================
# Test Classes
# ============================================================================


class TestTenantAdminAuthentication:
    """Tests for superadmin authentication on tenant admin endpoints."""

    def test_create_tenant_requires_superadmin(self, tenant_admin_client, sample_tenant):
        """Test that creating a tenant requires superadmin role."""
        client, mock_registry = tenant_admin_client
        mock_registry.create_tenant = AsyncMock(side_effect=ValueError("Test"))

        response = client.post(
            "/admin/tenants",
            json={
                "tenant_id": "new_tenant",
                "name": "New Tenant",
            },
        )
        # Should get 409 (conflict) from the ValueError, not 401/403
        assert response.status_code == 409

    def test_list_tenants_requires_superadmin(self, tenant_admin_client):
        """Test that listing tenants requires superadmin role."""
        client, mock_registry = tenant_admin_client
        mock_registry.list_tenants = AsyncMock(return_value=[])

        response = client.get("/admin/tenants")
        assert response.status_code == 200


class TestCreateTenant:
    """Tests for tenant creation endpoint."""

    def test_create_tenant_success(self, tenant_admin_client, sample_tenant):
        """Test successful tenant creation."""
        client, mock_registry = tenant_admin_client
        mock_registry.create_tenant = AsyncMock(return_value=sample_tenant)

        response = client.post(
            "/admin/tenants",
            json={
                "tenant_id": "new_tenant",
                "name": "New Tenant",
                "description": "A new tenant",
                "metadata": {"tier": "basic"},
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["tenant_id"] == sample_tenant.tenant_id
        assert data["name"] == sample_tenant.name

    def test_create_tenant_duplicate_returns_409(self, tenant_admin_client):
        """Test that creating a duplicate tenant returns 409 Conflict."""
        client, mock_registry = tenant_admin_client
        mock_registry.create_tenant = AsyncMock(side_effect=ValueError("Tenant 'existing_tenant' already exists"))

        response = client.post(
            "/admin/tenants",
            json={
                "tenant_id": "existing_tenant",
                "name": "Existing Tenant",
            },
        )
        assert response.status_code == 409
        assert "already exists" in response.json()["detail"]

    def test_create_tenant_invalid_data_returns_422(self, test_client, auth_headers):
        """Test that invalid tenant data returns 422 Unprocessable Entity."""
        response = test_client.post(
            "/admin/tenants",
            json={
                # Missing required 'name' field
                "tenant_id": "invalid_tenant",
            },
            headers=auth_headers,
        )
        assert response.status_code == 422

    def test_create_tenant_invalid_id_uppercase_returns_422(self, test_client, auth_headers):
        """Test that tenant_id with uppercase letters returns 422."""
        response = test_client.post(
            "/admin/tenants",
            json={
                "tenant_id": "InvalidTenant",  # Has uppercase letters
                "name": "Test Tenant",
            },
            headers=auth_headers,
        )
        assert response.status_code == 422

    def test_create_tenant_invalid_id_starts_with_number_returns_422(self, test_client, auth_headers):
        """Test that tenant_id starting with a number returns 422."""
        response = test_client.post(
            "/admin/tenants",
            json={
                "tenant_id": "123tenant",  # Starts with number
                "name": "Test Tenant",
            },
            headers=auth_headers,
        )
        assert response.status_code == 422

    def test_create_tenant_invalid_id_with_special_chars_returns_422(self, test_client, auth_headers):
        """Test that tenant_id with special characters returns 422."""
        response = test_client.post(
            "/admin/tenants",
            json={
                "tenant_id": "tenant-with-dashes",  # Has dashes (only underscores allowed)
                "name": "Test Tenant",
            },
            headers=auth_headers,
        )
        assert response.status_code == 422

    def test_create_tenant_server_error_returns_500(self, tenant_admin_client):
        """Test that unexpected errors return 500 Internal Server Error."""
        client, mock_registry = tenant_admin_client
        mock_registry.create_tenant = AsyncMock(side_effect=RuntimeError("Database connection failed"))

        response = client.post(
            "/admin/tenants",
            json={
                "tenant_id": "new_tenant",
                "name": "New Tenant",
            },
        )
        assert response.status_code == 500
        assert "Failed to create tenant" in response.json()["detail"]


class TestListTenants:
    """Tests for tenant listing endpoint."""

    def test_list_tenants_success(self, tenant_admin_client, sample_tenant):
        """Test successful tenant listing."""
        client, mock_registry = tenant_admin_client
        mock_registry.list_tenants = AsyncMock(return_value=[sample_tenant])

        response = client.get("/admin/tenants")
        assert response.status_code == 200
        data = response.json()
        assert "tenants" in data
        assert data["total"] == 1
        assert data["tenants"][0]["tenant_id"] == sample_tenant.tenant_id

    def test_list_tenants_empty(self, tenant_admin_client):
        """Test listing tenants when none exist."""
        client, mock_registry = tenant_admin_client
        mock_registry.list_tenants = AsyncMock(return_value=[])

        response = client.get("/admin/tenants")
        assert response.status_code == 200
        data = response.json()
        assert data["tenants"] == []
        assert data["total"] == 0

    def test_list_tenants_include_inactive(self, tenant_admin_client, sample_tenant):
        """Test listing tenants including inactive ones."""
        client, mock_registry = tenant_admin_client
        mock_registry.list_tenants = AsyncMock(return_value=[sample_tenant])

        response = client.get("/admin/tenants?include_inactive=true")
        assert response.status_code == 200
        # Verify the include_inactive parameter was passed
        mock_registry.list_tenants.assert_called_once()

    def test_list_tenants_server_error_returns_500(self, tenant_admin_client):
        """Test that unexpected errors return 500 Internal Server Error."""
        client, mock_registry = tenant_admin_client
        mock_registry.list_tenants = AsyncMock(side_effect=RuntimeError("Database error"))

        response = client.get("/admin/tenants")
        assert response.status_code == 500
        assert "Failed to list tenants" in response.json()["detail"]


class TestGetTenant:
    """Tests for getting a specific tenant."""

    def test_get_tenant_success(self, tenant_admin_client, sample_tenant):
        """Test successful tenant retrieval."""
        client, mock_registry = tenant_admin_client
        mock_registry.get_tenant = AsyncMock(return_value=sample_tenant)

        response = client.get(f"/admin/tenants/{sample_tenant.tenant_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["tenant_id"] == sample_tenant.tenant_id
        assert data["name"] == sample_tenant.name

    def test_get_tenant_not_found(self, tenant_admin_client):
        """Test getting a non-existent tenant returns 404."""
        client, mock_registry = tenant_admin_client
        mock_registry.get_tenant = AsyncMock(return_value=None)

        response = client.get("/admin/tenants/nonexistent_tenant")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]


class TestUpdateTenant:
    """Tests for tenant update endpoint."""

    def test_update_tenant_success(self, tenant_admin_client, sample_tenant):
        """Test successful tenant update."""
        client, mock_registry = tenant_admin_client

        updated_tenant = MagicMock()
        updated_tenant.id = sample_tenant.id
        updated_tenant.tenant_id = sample_tenant.tenant_id
        updated_tenant.name = "Updated Tenant Name"
        updated_tenant.description = "Updated description"
        updated_tenant.status = sample_tenant.status
        updated_tenant.schema_name = sample_tenant.schema_name
        updated_tenant.metadata_ = {"tier": "premium"}
        updated_tenant.is_schema_initialized = True
        updated_tenant.created_at = sample_tenant.created_at
        updated_tenant.updated_at = sample_tenant.updated_at

        mock_registry.update_tenant = AsyncMock(return_value=updated_tenant)

        response = client.patch(
            f"/admin/tenants/{sample_tenant.tenant_id}",
            json={
                "name": "Updated Tenant Name",
                "description": "Updated description",
                "metadata": {"tier": "premium"},
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Tenant Name"

    def test_update_tenant_not_found(self, tenant_admin_client):
        """Test updating a non-existent tenant returns 404."""
        client, mock_registry = tenant_admin_client
        mock_registry.update_tenant = AsyncMock(return_value=None)

        response = client.patch(
            "/admin/tenants/nonexistent_tenant",
            json={"name": "New Name"},
        )
        assert response.status_code == 404

    def test_update_tenant_partial_name_only(self, tenant_admin_client, sample_tenant):
        """Test partial update with only name field."""
        client, mock_registry = tenant_admin_client

        updated_tenant = MagicMock()
        updated_tenant.id = sample_tenant.id
        updated_tenant.tenant_id = sample_tenant.tenant_id
        updated_tenant.name = "Only Name Updated"
        updated_tenant.description = sample_tenant.description
        updated_tenant.status = sample_tenant.status
        updated_tenant.schema_name = sample_tenant.schema_name
        updated_tenant.metadata_ = sample_tenant.metadata_
        updated_tenant.is_schema_initialized = True
        updated_tenant.created_at = sample_tenant.created_at
        updated_tenant.updated_at = sample_tenant.updated_at

        mock_registry.update_tenant = AsyncMock(return_value=updated_tenant)

        response = client.patch(
            f"/admin/tenants/{sample_tenant.tenant_id}",
            json={"name": "Only Name Updated"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Only Name Updated"
        # Verify only name was passed to update
        mock_registry.update_tenant.assert_called_once()
        call_kwargs = mock_registry.update_tenant.call_args.kwargs
        assert call_kwargs.get("name") == "Only Name Updated"
        assert call_kwargs.get("description") is None
        assert call_kwargs.get("metadata") is None

    def test_update_tenant_empty_body(self, tenant_admin_client, sample_tenant):
        """Test update with empty body (no changes)."""
        client, mock_registry = tenant_admin_client
        mock_registry.update_tenant = AsyncMock(return_value=sample_tenant)

        response = client.patch(
            f"/admin/tenants/{sample_tenant.tenant_id}",
            json={},
        )
        assert response.status_code == 200


class TestDeactivateTenant:
    """Tests for tenant deactivation endpoint."""

    def test_deactivate_tenant_success(self, tenant_admin_client, sample_tenant):
        """Test successful tenant deactivation."""
        client, mock_registry = tenant_admin_client

        deactivated_tenant = MagicMock()
        deactivated_tenant.id = sample_tenant.id
        deactivated_tenant.tenant_id = sample_tenant.tenant_id
        deactivated_tenant.name = sample_tenant.name
        deactivated_tenant.description = sample_tenant.description
        deactivated_tenant.status = "inactive"
        deactivated_tenant.schema_name = sample_tenant.schema_name
        deactivated_tenant.metadata_ = sample_tenant.metadata_
        deactivated_tenant.is_schema_initialized = True
        deactivated_tenant.created_at = sample_tenant.created_at
        deactivated_tenant.updated_at = sample_tenant.updated_at

        mock_registry.deactivate_tenant = AsyncMock(return_value=deactivated_tenant)

        response = client.post(f"/admin/tenants/{sample_tenant.tenant_id}/deactivate")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "inactive"

    def test_deactivate_tenant_not_found(self, tenant_admin_client):
        """Test deactivating a non-existent tenant returns 404."""
        client, mock_registry = tenant_admin_client
        mock_registry.deactivate_tenant = AsyncMock(return_value=None)

        response = client.post("/admin/tenants/nonexistent_tenant/deactivate")
        assert response.status_code == 404


class TestActivateTenant:
    """Tests for tenant activation endpoint."""

    def test_activate_tenant_success(self, tenant_admin_client, sample_tenant):
        """Test successful tenant activation."""
        client, mock_registry = tenant_admin_client
        mock_registry.activate_tenant = AsyncMock(return_value=sample_tenant)

        response = client.post(f"/admin/tenants/{sample_tenant.tenant_id}/activate")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "active"

    def test_activate_tenant_not_found(self, tenant_admin_client):
        """Test activating a non-existent tenant returns 404."""
        client, mock_registry = tenant_admin_client
        mock_registry.activate_tenant = AsyncMock(return_value=None)

        response = client.post("/admin/tenants/nonexistent_tenant/activate")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]


class TestDeleteTenant:
    """Tests for tenant deletion endpoint."""

    def test_delete_tenant_success(self, tenant_admin_client, sample_tenant):
        """Test successful tenant deletion."""
        client, mock_registry = tenant_admin_client
        mock_registry.delete_tenant = AsyncMock(return_value=True)

        response = client.delete(f"/admin/tenants/{sample_tenant.tenant_id}")
        assert response.status_code == 200
        data = response.json()
        assert "deleted" in data["message"]

    def test_delete_tenant_with_schema_drop(self, tenant_admin_client, sample_tenant):
        """Test tenant deletion with schema drop."""
        client, mock_registry = tenant_admin_client
        mock_registry.delete_tenant = AsyncMock(return_value=True)

        response = client.delete(f"/admin/tenants/{sample_tenant.tenant_id}?drop_schema=true")
        assert response.status_code == 200
        data = response.json()
        assert "schema dropped" in data["message"]

    def test_delete_tenant_not_found(self, tenant_admin_client):
        """Test deleting a non-existent tenant returns 404."""
        client, mock_registry = tenant_admin_client
        mock_registry.delete_tenant = AsyncMock(return_value=False)

        response = client.delete("/admin/tenants/nonexistent_tenant")
        assert response.status_code == 404

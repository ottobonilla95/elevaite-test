"""
Tests for the dependencies module of db-core package.
"""

import pytest
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.testclient import TestClient

from db_core import get_tenant_db, get_tenant_async_db
from db_core.dependencies import (
    AdminOnly,
    TenantValidator,
    get_multitenancy_settings,
    get_tenant_id,
    multitenancy_settings_dependency,
    tenant_id_dependency,
)
from db_core.middleware import TenantMiddleware, set_current_tenant_id


class TestDependencies:
    """Tests for FastAPI dependencies."""

    def test_get_multitenancy_settings(self):
        """Test get_multitenancy_settings function."""
        # The function should return a MultitenancySettings instance
        settings = get_multitenancy_settings()
        assert settings is not None
        assert settings.tenant_id_header == "X-Tenant-ID"
        
        # The function should cache its result (test lru_cache)
        settings2 = get_multitenancy_settings()
        assert settings is settings2  # Should be the same instance

    def test_get_tenant_id(self, multitenancy_settings):
        """Test get_tenant_id function."""
        # Set tenant ID
        set_current_tenant_id("test-tenant")
        
        try:
            # Get tenant ID
            tenant_id = get_tenant_id(multitenancy_settings)
            assert tenant_id == "test-tenant"
            
            # Reset tenant ID
            set_current_tenant_id(None)
            
            # Without tenant ID and no default, should raise exception
            with pytest.raises(HTTPException) as excinfo:
                get_tenant_id(multitenancy_settings)
            assert excinfo.value.status_code == status.HTTP_400_BAD_REQUEST
            
            # With default tenant ID
            settings = multitenancy_settings.copy()
            settings.default_tenant_id = "default-tenant"
            tenant_id = get_tenant_id(settings)
            assert tenant_id == "default-tenant"
        finally:
            # Reset tenant ID
            set_current_tenant_id(None)

    @pytest.mark.db
    def test_get_tenant_db_dependency(self, fastapi_app, multitenancy_settings, setup_db, init_db_config):
        """Test get_tenant_db dependency."""
        # Add a route with the dependency
        @fastapi_app.get("/test-db-dependency")
        def test_route(db=Depends(get_tenant_db)):
            # Just check that we get a valid session
            return {"success": True}
        
        # Create test client
        client = TestClient(fastapi_app)
        
        # Make a request with tenant ID
        response = client.get("/test-db-dependency", headers={"X-Tenant-ID": "tenant1"})
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {"success": True}
        
        # Without tenant ID should fail
        response = client.get("/test-db-dependency")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_tenant_validator(self, fastapi_app, multitenancy_settings):
        """Test TenantValidator dependency."""
        # Create a validation function
        def validate_tenant(tenant_id: str) -> bool:
            return tenant_id in ["valid-tenant"]
        
        # Create validator dependency
        validator = TenantValidator(tenant_callback=validate_tenant, settings=multitenancy_settings)
        
        # Add a route with the dependency
        @fastapi_app.get("/test-validator")
        def test_route(tenant_id=Depends(validator)):
            return {"tenant_id": tenant_id}
        
        # Create test client
        client = TestClient(fastapi_app)
        
        # Make a request with valid tenant ID
        response = client.get("/test-validator", headers={"X-Tenant-ID": "valid-tenant"})
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {"tenant_id": "valid-tenant"}
        
        # Make a request with invalid tenant ID
        response = client.get("/test-validator", headers={"X-Tenant-ID": "invalid-tenant"})
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "tenant not found" in response.json()["detail"].lower()

    def test_admin_only(self, fastapi_app, multitenancy_settings):
        """Test AdminOnly dependency."""
        # Create settings with admin tenant ID
        settings = multitenancy_settings.copy()
        settings.admin_tenant_id = "admin-tenant"
        
        # Create app with middleware and updated settings
        app = FastAPI()
        app.add_middleware(TenantMiddleware, settings=settings)
        
        # Create admin-only dependency
        admin_only = AdminOnly(settings=settings)
        
        # Add a route with the dependency
        @app.get("/admin-only")
        def admin_route(tenant_id=Depends(admin_only)):
            return {"tenant_id": tenant_id}
        
        # Create test client
        client = TestClient(app)
        
        # Make a request with admin tenant ID
        response = client.get("/admin-only", headers={"X-Tenant-ID": "admin-tenant"})
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {"tenant_id": "admin-tenant"}
        
        # Make a request with non-admin tenant ID
        response = client.get("/admin-only", headers={"X-Tenant-ID": "tenant1"})
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "admin access required" in response.json()["detail"].lower()
        
        # Test with no admin tenant configured
        settings_no_admin = multitenancy_settings.copy()
        settings_no_admin.admin_tenant_id = None
        
        app2 = FastAPI()
        app2.add_middleware(TenantMiddleware, settings=settings_no_admin)
        
        admin_only2 = AdminOnly(settings=settings_no_admin)
        
        @app2.get("/admin-only-2")
        def admin_route2(tenant_id=Depends(admin_only2)):
            return {"tenant_id": tenant_id}
        
        client2 = TestClient(app2)
        
        response = client2.get("/admin-only-2", headers={"X-Tenant-ID": "any-tenant"})
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "admin tenant id not configured" in response.json()["detail"].lower()
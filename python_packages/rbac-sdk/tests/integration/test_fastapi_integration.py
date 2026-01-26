"""
Integration tests for RBAC SDK with FastAPI.

These tests verify that the SDK's guards work correctly in a real FastAPI application.

Requirements:
- Auth API running on localhost:8004 (or AUTH_API_URL env var)
- PostgreSQL database with test data
- OPA running on localhost:8181

Run with:
    pytest tests/integration/test_fastapi_integration.py -v
"""

import pytest
from fastapi import FastAPI, Depends
from fastapi.testclient import TestClient

from rbac_sdk.fastapi_helpers import (
    require_permission,
    require_permission_async,
    resource_builders,
    principal_resolvers,
)


pytestmark = pytest.mark.asyncio


@pytest.fixture
def fastapi_app():
    """Create a FastAPI app for testing."""
    return FastAPI()


@pytest.fixture
def test_client(fastapi_app):
    """Create a test client for the FastAPI app."""
    return TestClient(fastapi_app)


class TestSyncGuard:
    """Test synchronous require_permission guard."""

    async def test_sync_guard_allows_authorized_request(
        self,
        check_auth_api_available,
        fastapi_app,
        test_client,
        test_user_active,
        test_project,
        test_viewer_assignment,
    ):
        """Test that sync guard allows authorized requests."""
        # Create a guard
        guard = require_permission(
            action="view_project",
            resource_builder=resource_builders.project_from_headers(),
            principal_resolver=lambda req: str(test_user_active["id"]),
        )

        # Add a route with the guard
        @fastapi_app.get("/projects", dependencies=[Depends(guard)])
        def list_projects():
            return {"projects": ["project1", "project2"]}

        # Make request with proper headers
        response = test_client.get(
            "/projects",
            headers={
                "X-elevAIte-ProjectId": str(test_project["id"]),
                "X-elevAIte-OrganizationId": str(test_project["organization_id"]),
                "X-elevAIte-AccountId": str(test_project["account_id"]),
            },
        )

        # Should succeed
        assert response.status_code == 200
        assert response.json() == {"projects": ["project1", "project2"]}

    async def test_sync_guard_denies_unauthorized_request(
        self,
        check_auth_api_available,
        fastapi_app,
        test_client,
        test_user_no_assignments,
        test_project,
    ):
        """Test that sync guard denies unauthorized requests."""
        # Create a guard
        guard = require_permission(
            action="view_project",
            resource_builder=resource_builders.project_from_headers(),
            principal_resolver=lambda req: str(test_user_no_assignments["id"]),
        )

        # Add a route with the guard
        @fastapi_app.get("/projects", dependencies=[Depends(guard)])
        def list_projects():
            return {"projects": ["project1", "project2"]}

        # Make request with proper headers
        response = test_client.get(
            "/projects",
            headers={
                "X-elevAIte-ProjectId": str(test_project["id"]),
                "X-elevAIte-OrganizationId": str(test_project["organization_id"]),
                "X-elevAIte-AccountId": str(test_project["account_id"]),
            },
        )

        # Should be forbidden
        assert response.status_code == 403
        assert response.json() == {"detail": "Forbidden"}


class TestAsyncGuard:
    """Test asynchronous require_permission_async guard."""

    async def test_async_guard_allows_authorized_request(
        self,
        check_auth_api_available,
        fastapi_app,
        test_client,
        test_user_active,
        test_project,
        test_viewer_assignment,
    ):
        """Test that async guard allows authorized requests."""
        # Create a guard
        guard = require_permission_async(
            action="view_project",
            resource_builder=resource_builders.project_from_headers(),
            principal_resolver=lambda req: str(test_user_active["id"]),
        )

        # Add a route with the guard
        @fastapi_app.get("/async-projects", dependencies=[Depends(guard)])
        async def list_projects():
            return {"projects": ["project1", "project2"]}

        # Make request with proper headers
        response = test_client.get(
            "/async-projects",
            headers={
                "X-elevAIte-ProjectId": str(test_project["id"]),
                "X-elevAIte-OrganizationId": str(test_project["organization_id"]),
                "X-elevAIte-AccountId": str(test_project["account_id"]),
            },
        )

        # Should succeed
        assert response.status_code == 200
        assert response.json() == {"projects": ["project1", "project2"]}

    async def test_async_guard_denies_unauthorized_request(
        self,
        check_auth_api_available,
        fastapi_app,
        test_client,
        test_user_no_assignments,
        test_project,
    ):
        """Test that async guard denies unauthorized requests."""
        # Create a guard
        guard = require_permission_async(
            action="view_project",
            resource_builder=resource_builders.project_from_headers(),
            principal_resolver=lambda req: str(test_user_no_assignments["id"]),
        )

        # Add a route with the guard
        @fastapi_app.get("/async-projects", dependencies=[Depends(guard)])
        async def list_projects():
            return {"projects": ["project1", "project2"]}

        # Make request with proper headers
        response = test_client.get(
            "/async-projects",
            headers={
                "X-elevAIte-ProjectId": str(test_project["id"]),
                "X-elevAIte-OrganizationId": str(test_project["organization_id"]),
                "X-elevAIte-AccountId": str(test_project["account_id"]),
            },
        )

        # Should be forbidden
        assert response.status_code == 403
        assert response.json() == {"detail": "Forbidden"}


class TestMultipleGuards:
    """Test multiple guards on the same endpoint."""

    async def test_multiple_guards_all_pass(
        self,
        check_auth_api_available,
        fastapi_app,
        test_client,
        test_user_active,
        test_project,
        test_viewer_assignment,
    ):
        """Test that multiple guards all pass when authorized."""
        # Create two guards
        guard1 = require_permission_async(
            action="view_project",
            resource_builder=resource_builders.project_from_headers(),
            principal_resolver=lambda req: str(test_user_active["id"]),
        )

        guard2 = require_permission_async(
            action="view_project",
            resource_builder=resource_builders.project_from_headers(),
            principal_resolver=lambda req: str(test_user_active["id"]),
        )

        # Add a route with both guards
        @fastapi_app.get(
            "/multi-guard", dependencies=[Depends(guard1), Depends(guard2)]
        )
        async def protected_endpoint():
            return {"status": "success"}

        # Make request
        response = test_client.get(
            "/multi-guard",
            headers={
                "X-elevAIte-ProjectId": str(test_project["id"]),
                "X-elevAIte-OrganizationId": str(test_project["organization_id"]),
                "X-elevAIte-AccountId": str(test_project["account_id"]),
            },
        )

        # Should succeed
        assert response.status_code == 200
        assert response.json() == {"status": "success"}

    async def test_multiple_guards_first_fails(
        self,
        check_auth_api_available,
        fastapi_app,
        test_client,
        test_user_no_assignments,
        test_project,
    ):
        """Test that request fails if first guard denies."""
        # Create two guards - first will fail
        guard1 = require_permission_async(
            action="view_project",
            resource_builder=resource_builders.project_from_headers(),
            principal_resolver=lambda req: str(test_user_no_assignments["id"]),
        )

        guard2 = require_permission_async(
            action="view_project",
            resource_builder=resource_builders.project_from_headers(),
            principal_resolver=lambda req: str(test_user_no_assignments["id"]),
        )

        # Add a route with both guards
        @fastapi_app.get(
            "/multi-guard-fail", dependencies=[Depends(guard1), Depends(guard2)]
        )
        async def protected_endpoint():
            return {"status": "success"}

        # Make request
        response = test_client.get(
            "/multi-guard-fail",
            headers={
                "X-elevAIte-ProjectId": str(test_project["id"]),
                "X-elevAIte-OrganizationId": str(test_project["organization_id"]),
                "X-elevAIte-AccountId": str(test_project["account_id"]),
            },
        )

        # Should be forbidden
        assert response.status_code == 403


class TestCustomResolvers:
    """Test custom principal resolvers."""

    async def test_api_key_resolver_with_valid_key(
        self,
        check_auth_api_available,
        fastapi_app,
        test_client,
        test_user_active,
        test_project,
        test_viewer_assignment,
        auth_api_url,
    ):
        """Test API key resolver with valid API key."""
        # Create a guard with API key resolver
        guard = require_permission_async(
            action="view_project",
            resource_builder=resource_builders.project_from_headers(),
            principal_resolver=principal_resolvers.api_key_or_user(
                validate_api_key=lambda key, req: str(test_user_active["id"])
                if key == "valid-key"
                else None
            ),
        )

        # Add a route with the guard
        @fastapi_app.get("/api-key-protected", dependencies=[Depends(guard)])
        async def protected_endpoint():
            return {"status": "authenticated"}

        # Make request with API key
        response = test_client.get(
            "/api-key-protected",
            headers={
                "X-elevAIte-apikey": "valid-key",
                "X-elevAIte-ProjectId": str(test_project["id"]),
                "X-elevAIte-OrganizationId": str(test_project["organization_id"]),
                "X-elevAIte-AccountId": str(test_project["account_id"]),
            },
        )

        # Should succeed
        assert response.status_code == 200
        assert response.json() == {"status": "authenticated"}

    async def test_api_key_resolver_with_invalid_key(
        self,
        check_auth_api_available,
        fastapi_app,
        test_client,
        test_project,
    ):
        """Test API key resolver with invalid API key."""
        # Create a guard with API key resolver
        guard = require_permission_async(
            action="view_project",
            resource_builder=resource_builders.project_from_headers(),
            principal_resolver=principal_resolvers.api_key_or_user(
                validate_api_key=lambda key, req: None  # Always returns None (invalid)
            ),
        )

        # Add a route with the guard
        @fastapi_app.get("/api-key-invalid", dependencies=[Depends(guard)])
        async def protected_endpoint():
            return {"status": "authenticated"}

        # Make request with API key
        response = test_client.get(
            "/api-key-invalid",
            headers={
                "X-elevAIte-apikey": "invalid-key",
                "X-elevAIte-ProjectId": str(test_project["id"]),
                "X-elevAIte-OrganizationId": str(test_project["organization_id"]),
                "X-elevAIte-AccountId": str(test_project["account_id"]),
            },
        )

        # Should be unauthorized
        assert response.status_code == 401
        assert response.json() == {"detail": "Invalid API key"}


class TestCustomResourceBuilders:
    """Test custom resource builders."""

    async def test_project_from_headers(
        self,
        check_auth_api_available,
        fastapi_app,
        test_client,
        test_user_active,
        test_project,
        test_viewer_assignment,
    ):
        """Test project resource builder from headers."""
        # Create a guard with project resource builder
        guard = require_permission_async(
            action="view_project",
            resource_builder=resource_builders.project_from_headers(),
            principal_resolver=lambda req: str(test_user_active["id"]),
        )

        # Add a route with the guard
        @fastapi_app.get("/project-resource", dependencies=[Depends(guard)])
        async def protected_endpoint():
            return {"resource_type": "project"}

        # Make request with project headers
        response = test_client.get(
            "/project-resource",
            headers={
                "X-elevAIte-ProjectId": str(test_project["id"]),
                "X-elevAIte-OrganizationId": str(test_project["organization_id"]),
                "X-elevAIte-AccountId": str(test_project["account_id"]),
            },
        )

        # Should succeed
        assert response.status_code == 200
        assert response.json() == {"resource_type": "project"}

    async def test_account_from_headers(
        self,
        check_auth_api_available,
        fastapi_app,
        test_client,
        test_user_active,
        test_account,
        test_admin_assignment,
    ):
        """Test account resource builder from headers."""
        # Create a guard with account resource builder
        guard = require_permission_async(
            action="manage_account",
            resource_builder=resource_builders.account_from_headers(),
            principal_resolver=lambda req: str(test_user_active["id"]),
        )

        # Add a route with the guard
        @fastapi_app.get("/account-resource", dependencies=[Depends(guard)])
        async def protected_endpoint():
            return {"resource_type": "account"}

        # Make request with account headers
        response = test_client.get(
            "/account-resource",
            headers={
                "X-elevAIte-AccountId": str(test_account["id"]),
                "X-elevAIte-OrganizationId": str(test_account["organization_id"]),
            },
        )

        # Should succeed
        assert response.status_code == 200
        assert response.json() == {"resource_type": "account"}

    async def test_organization_from_headers(
        self,
        check_auth_api_available,
        fastapi_app,
        test_client,
        test_user_active,
        test_organization,
        test_superadmin_assignment,
    ):
        """Test organization resource builder from headers."""
        # Create a guard with organization resource builder
        guard = require_permission_async(
            action="manage_organization",
            resource_builder=resource_builders.organization_from_headers(),
            principal_resolver=lambda req: str(test_user_active["id"]),
        )

        # Add a route with the guard
        @fastapi_app.get("/org-resource", dependencies=[Depends(guard)])
        async def protected_endpoint():
            return {"resource_type": "organization"}

        # Make request with organization headers
        response = test_client.get(
            "/org-resource",
            headers={
                "X-elevAIte-OrganizationId": str(test_organization["id"]),
            },
        )

        # Should succeed
        assert response.status_code == 200
        assert response.json() == {"resource_type": "organization"}


class TestErrorPropagation:
    """Test error propagation and HTTP status codes."""

    async def test_missing_principal_returns_401(
        self,
        check_auth_api_available,
        fastapi_app,
        test_client,
        test_project,
    ):
        """Test that missing principal returns 401."""

        # Create a guard with resolver that raises 401
        def failing_resolver(req):
            from fastapi import HTTPException

            raise HTTPException(status_code=401, detail="Authentication required")

        guard = require_permission_async(
            action="view_project",
            resource_builder=resource_builders.project_from_headers(),
            principal_resolver=failing_resolver,
        )

        # Add a route with the guard
        @fastapi_app.get("/auth-required", dependencies=[Depends(guard)])
        async def protected_endpoint():
            return {"status": "success"}

        # Make request
        response = test_client.get(
            "/auth-required",
            headers={
                "X-elevAIte-ProjectId": str(test_project["id"]),
                "X-elevAIte-OrganizationId": str(test_project["organization_id"]),
                "X-elevAIte-AccountId": str(test_project["account_id"]),
            },
        )

        # Should be unauthorized
        assert response.status_code == 401
        assert response.json() == {"detail": "Authentication required"}

    async def test_missing_resource_headers_returns_400(
        self,
        check_auth_api_available,
        fastapi_app,
        test_client,
        test_user_active,
    ):
        """Test that missing resource headers returns 400."""
        # Create a guard
        guard = require_permission_async(
            action="view_project",
            resource_builder=resource_builders.project_from_headers(),
            principal_resolver=lambda req: str(test_user_active["id"]),
        )

        # Add a route with the guard
        @fastapi_app.get("/missing-headers", dependencies=[Depends(guard)])
        async def protected_endpoint():
            return {"status": "success"}

        # Make request WITHOUT required headers
        response = test_client.get("/missing-headers")

        # Should be bad request
        assert response.status_code == 400
        assert (
            "Missing" in response.json()["detail"]
            and "header" in response.json()["detail"]
        )

    async def test_guard_runs_before_handler(
        self,
        check_auth_api_available,
        fastapi_app,
        test_client,
        test_user_no_assignments,
        test_project,
    ):
        """Test that guard runs before handler (handler should not execute if guard fails)."""
        handler_called = False

        # Create a guard that will fail
        guard = require_permission_async(
            action="view_project",
            resource_builder=resource_builders.project_from_headers(),
            principal_resolver=lambda req: str(test_user_no_assignments["id"]),
        )

        # Add a route with the guard
        @fastapi_app.get("/guard-first", dependencies=[Depends(guard)])
        async def protected_endpoint():
            nonlocal handler_called
            handler_called = True
            return {"status": "success"}

        # Make request
        response = test_client.get(
            "/guard-first",
            headers={
                "X-elevAIte-ProjectId": str(test_project["id"]),
                "X-elevAIte-OrganizationId": str(test_project["organization_id"]),
                "X-elevAIte-AccountId": str(test_project["account_id"]),
            },
        )

        # Should be forbidden
        assert response.status_code == 403
        # Handler should NOT have been called
        assert handler_called is False

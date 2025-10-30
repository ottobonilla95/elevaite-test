"""
Test that all code examples in documentation work correctly.

This ensures documentation stays up-to-date and examples are accurate.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from fastapi import FastAPI, Depends, Request, HTTPException
from fastapi.testclient import TestClient


class TestQuickStartExamples:
    """Test examples from README Quick Start section."""

    def test_basic_setup_example(self):
        """Test the basic setup example from README."""
        from rbac_sdk import (
            require_permission_async,
            resource_builders,
            principal_resolvers,
        )

        app = FastAPI()

        # Create a guard for viewing projects
        guard_view = require_permission_async(
            action="view_project",
            resource_builder=resource_builders.project_from_headers(),
            principal_resolver=principal_resolvers.api_key_or_user(),
        )

        # Use the guard in your endpoint
        @app.get("/projects", dependencies=[Depends(guard_view)])
        async def list_projects():
            return {"projects": []}

        # Verify guard was created
        assert guard_view is not None
        assert callable(guard_view)

    def test_environment_configuration_example(self):
        """Test environment variable configuration."""
        import os
        from rbac_sdk import api_key_http_validator

        # Set environment variables
        os.environ["AUTH_API_BASE"] = "http://localhost:8004"

        # Create validator (should use env var)
        validator = api_key_http_validator()

        assert validator is not None
        assert callable(validator)


class TestUsagePatterns:
    """Test examples from README Usage Patterns section."""

    def test_pattern1_simple_guard(self):
        """Test Pattern 1: Simple Guard."""
        from rbac_sdk import (
            require_permission_async,
            resource_builders,
            principal_resolvers,
        )

        # Create reusable guards
        guard_view = require_permission_async(
            action="view_project",
            resource_builder=resource_builders.project_from_headers(),
            principal_resolver=principal_resolvers.api_key_or_user(),
        )

        guard_edit = require_permission_async(
            action="edit_project",
            resource_builder=resource_builders.project_from_headers(),
            principal_resolver=principal_resolvers.api_key_or_user(),
        )

        # Verify guards were created
        assert guard_view is not None
        assert guard_edit is not None

    def test_pattern2_helper_function(self):
        """Test Pattern 2: Helper Function."""
        from typing import Awaitable, Callable
        from fastapi import Request
        from rbac_sdk import (
            require_permission_async,
            resource_builders,
            principal_resolvers,
            HDR_PROJECT_ID,
            HDR_ACCOUNT_ID,
            HDR_ORG_ID,
        )

        def api_key_or_user_guard(action: str) -> Callable[[Request], Awaitable[None]]:
            """Create a guard for the given action with standard configuration."""
            return require_permission_async(
                action=action,
                resource_builder=resource_builders.project_from_headers(
                    project_header=HDR_PROJECT_ID,
                    account_header=HDR_ACCOUNT_ID,
                    org_header=HDR_ORG_ID,
                ),
                principal_resolver=principal_resolvers.api_key_or_user(),
            )

        # Use it
        guard = api_key_or_user_guard("view_agent")
        assert guard is not None
        assert callable(guard)

    def test_pattern3_custom_principal_resolver(self):
        """Test Pattern 3: Custom Principal Resolver."""
        from rbac_sdk import principal_resolvers, require_permission_async, resource_builders

        # Use custom header for user ID
        custom_resolver = principal_resolvers.user_id_header(header_name="X-Custom-User")

        guard = require_permission_async(
            action="view_project",
            resource_builder=resource_builders.project_from_headers(),
            principal_resolver=custom_resolver,
        )

        assert guard is not None
        assert callable(guard)

    def test_pattern4_api_key_validation_with_caching(self):
        """Test Pattern 4: API Key Validation with Caching."""
        from rbac_sdk import api_key_http_validator, principal_resolvers, require_permission_async, resource_builders

        # Create validator with caching (60s TTL)
        validator = api_key_http_validator(
            base_url="http://localhost:8004",
            cache_ttl=60.0,  # Cache for 60 seconds
        )

        # Use in principal resolver
        guard = require_permission_async(
            action="view_project",
            resource_builder=resource_builders.project_from_headers(),
            principal_resolver=principal_resolvers.api_key_or_user(validate_api_key=validator),
        )

        assert guard is not None
        assert callable(guard)

    def test_pattern5_jwt_api_key_validation(self):
        """Test Pattern 5: JWT API Key Validation."""
        from rbac_sdk import api_key_jwt_validator, principal_resolvers, require_permission_async, resource_builders

        # Create JWT validator
        validator = api_key_jwt_validator(
            algorithm="HS256",
            secret="your-secret-key",
        )

        # Use in principal resolver
        guard = require_permission_async(
            action="view_project",
            resource_builder=resource_builders.project_from_headers(),
            principal_resolver=principal_resolvers.api_key_or_user(validate_api_key=validator),
        )

        assert guard is not None
        assert callable(guard)

    @pytest.mark.asyncio
    async def test_pattern6_direct_access_check(self):
        """Test Pattern 6: Direct Access Check."""
        from rbac_sdk import check_access, check_access_async

        # Mock the HTTP call (sync uses requests)
        with patch("rbac_sdk.client.requests.post") as mock_post:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"allowed": True}
            mock_post.return_value = mock_response

            # Sync version
            allowed = check_access(
                user_id="user-123",
                action="view_project",
                resource={
                    "type": "project",
                    "id": "project-uuid",
                    "organization_id": "org-uuid",
                    "account_id": "account-uuid",
                },
            )
            assert allowed is True

        # Mock the async HTTP call (async uses httpx)
        with patch("rbac_sdk.async_client.httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"allowed": True}
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            # Async version
            allowed = await check_access_async(
                user_id="user-123",
                action="view_project",
                resource={
                    "type": "project",
                    "id": "project-uuid",
                    "organization_id": "org-uuid",
                    "account_id": "account-uuid",
                },
            )
            assert allowed is True


class TestAPIReferenceExamples:
    """Test examples from API_REFERENCE.md."""

    @pytest.mark.asyncio
    async def test_require_permission_async_example(self):
        """Test require_permission_async example."""
        from rbac_sdk import require_permission_async, resource_builders, principal_resolvers

        guard = require_permission_async(
            action="view_project",
            resource_builder=resource_builders.project_from_headers(),
            principal_resolver=principal_resolvers.api_key_or_user(),
        )

        # Create a FastAPI app with the guard
        app = FastAPI()

        @app.get("/projects", dependencies=[Depends(guard)])
        async def list_projects():
            return {"projects": []}

        # Verify endpoint exists
        assert app.routes is not None

    def test_resource_builders_examples(self):
        """Test resource builder examples."""
        from rbac_sdk import resource_builders

        # project_from_headers
        builder1 = resource_builders.project_from_headers()
        assert builder1 is not None

        # account_from_headers
        builder2 = resource_builders.account_from_headers()
        assert builder2 is not None

        # organization_from_headers
        builder3 = resource_builders.organization_from_headers()
        assert builder3 is not None

    def test_principal_resolvers_examples(self):
        """Test principal resolver examples."""
        from rbac_sdk import principal_resolvers, api_key_http_validator

        # user_id_header
        resolver1 = principal_resolvers.user_id_header()
        assert resolver1 is not None

        # api_key_or_user with validation
        validator = api_key_http_validator(base_url="http://localhost:8004")
        resolver2 = principal_resolvers.api_key_or_user(validate_api_key=validator)
        assert resolver2 is not None

        # api_key_or_user without validation
        resolver3 = principal_resolvers.api_key_or_user()
        assert resolver3 is not None

    def test_api_key_validators_examples(self):
        """Test API key validator examples."""
        from rbac_sdk import api_key_http_validator, api_key_jwt_validator

        # HTTP validator
        validator1 = api_key_http_validator(
            base_url="http://localhost:8004",
            cache_ttl=60.0,
        )
        assert validator1 is not None

        # JWT validator
        validator2 = api_key_jwt_validator(
            algorithm="HS256",
            secret="your-secret-key",
        )
        assert validator2 is not None

    def test_constants_examples(self):
        """Test constants examples."""
        from rbac_sdk import (
            HDR_USER_ID,
            HDR_ORG_ID,
            HDR_ACCOUNT_ID,
            HDR_PROJECT_ID,
            HDR_API_KEY,
        )

        # Verify constants are defined
        assert HDR_USER_ID == "X-elevAIte-UserId"
        assert HDR_ORG_ID == "X-elevAIte-OrganizationId"
        assert HDR_ACCOUNT_ID == "X-elevAIte-AccountId"
        assert HDR_PROJECT_ID == "X-elevAIte-ProjectId"
        assert HDR_API_KEY == "X-elevAIte-apikey"


class TestMigrationGuideExamples:
    """Test examples from MIGRATION.md."""

    def test_new_pattern_imports(self):
        """Test new SDK imports work."""
        from rbac_sdk import (
            require_permission_async,
            resource_builders,
            principal_resolvers,
            api_key_http_validator,
            api_key_jwt_validator,
        )

        # Verify all imports work
        assert require_permission_async is not None
        assert resource_builders is not None
        assert principal_resolvers is not None
        assert api_key_http_validator is not None
        assert api_key_jwt_validator is not None

    def test_migration_helper_function_pattern(self):
        """Test the helper function pattern from migration guide."""
        from typing import Awaitable, Callable
        from fastapi import Request
        from rbac_sdk import (
            require_permission_async,
            resource_builders,
            principal_resolvers,
            HDR_PROJECT_ID,
            HDR_ACCOUNT_ID,
            HDR_ORG_ID,
        )

        def api_key_or_user_guard(action: str) -> Callable[[Request], Awaitable[None]]:
            """Create a guard for the given action with standard configuration."""
            return require_permission_async(
                action=action,
                resource_builder=resource_builders.project_from_headers(
                    project_header=HDR_PROJECT_ID,
                    account_header=HDR_ACCOUNT_ID,
                    org_header=HDR_ORG_ID,
                ),
                principal_resolver=principal_resolvers.api_key_or_user(),
            )

        # Use it
        guard = api_key_or_user_guard("view_project")
        assert guard is not None


class TestPerformanceGuideExamples:
    """Test examples from PERFORMANCE.md."""

    def test_caching_enabled_example(self):
        """Test caching enabled example."""
        from rbac_sdk import api_key_http_validator

        # With caching - 208x faster
        validator = api_key_http_validator(
            base_url="http://localhost:8004",
            cache_ttl=60.0,  # Cache for 60 seconds
        )

        assert validator is not None

    def test_jwt_validation_example(self):
        """Test JWT validation example."""
        from rbac_sdk import api_key_jwt_validator

        # JWT validation - local only, no network call
        validator = api_key_jwt_validator(
            algorithm="HS256",
            secret="your-secret-key",
        )

        assert validator is not None

    def test_async_guard_example(self):
        """Test async guard example."""
        from rbac_sdk import require_permission_async, resource_builders, principal_resolvers

        # Async guard - non-blocking
        guard = require_permission_async(
            action="view_project",
            resource_builder=resource_builders.project_from_headers(),
            principal_resolver=principal_resolvers.api_key_or_user(),
        )

        assert guard is not None

    def test_production_configuration_example(self):
        """Test production configuration example."""
        from rbac_sdk import (
            api_key_http_validator,
            require_permission_async,
            resource_builders,
            principal_resolvers,
        )

        # Use HTTP validator with caching
        validator = api_key_http_validator(
            base_url="http://localhost:8004",
            cache_ttl=60.0,  # 60 second cache
            timeout=3.0,  # 3 second timeout
        )

        # Create guard
        guard = require_permission_async(
            action="view_project",
            resource_builder=resource_builders.project_from_headers(),
            principal_resolver=principal_resolvers.api_key_or_user(validate_api_key=validator),
        )

        assert guard is not None

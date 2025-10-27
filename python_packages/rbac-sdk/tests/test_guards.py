"""
Brutal unit tests for RBAC guards (require_permission and require_permission_async).

These tests cover:
- Successful authorization
- Denied authorization
- Principal resolution failures
- Resource building failures
- RBAC service failures
- Integration scenarios
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from fastapi import HTTPException
from rbac_sdk.fastapi_helpers import (
    require_permission,
    require_permission_async,
    resource_builders,
    principal_resolvers,
)


class TestRequirePermissionSync:
    """Test synchronous require_permission guard."""

    @patch("rbac_sdk.fastapi_helpers.check_access")
    def test_require_permission_allowed(self, mock_check_access, mock_request_with_project_headers):
        """Test that allowed access passes through."""
        mock_check_access.return_value = True

        guard = require_permission(
            action="view_project",
            resource_builder=resource_builders.project_from_headers(),
        )

        # Should not raise exception
        guard(mock_request_with_project_headers)

        mock_check_access.assert_called_once()

    @patch("rbac_sdk.fastapi_helpers.check_access")
    def test_require_permission_denied(self, mock_check_access, mock_request_with_project_headers):
        """Test that denied access raises 403."""
        mock_check_access.return_value = False

        guard = require_permission(
            action="delete_project",
            resource_builder=resource_builders.project_from_headers(),
        )

        with pytest.raises(HTTPException) as exc_info:
            guard(mock_request_with_project_headers)

        assert exc_info.value.status_code == 403
        assert "Forbidden" in str(exc_info.value.detail)

    @patch("rbac_sdk.fastapi_helpers.check_access")
    def test_require_permission_missing_user_id(self, mock_check_access, mock_request):
        """Test that missing user ID raises 401."""
        guard = require_permission(
            action="view_project",
            resource_builder=resource_builders.project_from_headers(),
        )

        with pytest.raises(HTTPException) as exc_info:
            guard(mock_request)

        assert exc_info.value.status_code == 401

    @patch("rbac_sdk.fastapi_helpers.check_access")
    def test_require_permission_missing_resource_headers(self, mock_check_access, mock_request_with_user):
        """Test that missing resource headers raises 400."""
        guard = require_permission(
            action="view_project",
            resource_builder=resource_builders.project_from_headers(),
        )

        with pytest.raises(HTTPException) as exc_info:
            guard(mock_request_with_user)

        assert exc_info.value.status_code == 400

    @patch("rbac_sdk.fastapi_helpers.check_access")
    def test_require_permission_custom_principal_resolver(self, mock_check_access):
        """Test that custom principal resolver is used."""
        mock_check_access.return_value = True

        request = Mock()
        request.headers = {
            "X-Custom-User": "custom-user-123",
            "X-elevAIte-ProjectId": "proj-123",
            "X-elevAIte-OrganizationId": "org-456",
        }

        custom_resolver = principal_resolvers.user_id_header(header_name="X-Custom-User")

        guard = require_permission(
            action="view_project",
            resource_builder=resource_builders.project_from_headers(),
            principal_resolver=custom_resolver,
        )

        guard(request)

        # Verify check_access was called with custom user ID
        call_args = mock_check_access.call_args
        assert call_args[1]["user_id"] == "custom-user-123"

    @patch("rbac_sdk.fastapi_helpers.check_access")
    def test_require_permission_custom_base_url(self, mock_check_access, mock_request_with_project_headers):
        """Test that custom base_url is passed to check_access."""
        mock_check_access.return_value = True

        guard = require_permission(
            action="view_project",
            resource_builder=resource_builders.project_from_headers(),
            base_url="http://custom-authz:9000",
        )

        guard(mock_request_with_project_headers)

        call_args = mock_check_access.call_args
        assert call_args[1]["base_url"] == "http://custom-authz:9000"

    @patch("rbac_sdk.fastapi_helpers.check_access")
    def test_require_permission_rbac_service_error(self, mock_check_access, mock_request_with_project_headers):
        """Test that RBAC service errors raise RBACClientError."""
        from rbac_sdk.client import RBACClientError
        mock_check_access.side_effect = RBACClientError("Service unavailable")

        guard = require_permission(
            action="view_project",
            resource_builder=resource_builders.project_from_headers(),
        )

        with pytest.raises(RBACClientError):
            guard(mock_request_with_project_headers)


class TestRequirePermissionAsync:
    """Test asynchronous require_permission_async guard."""

    @pytest.mark.asyncio
    @patch("rbac_sdk.fastapi_helpers.check_access_async")
    async def test_require_permission_async_allowed(self, mock_check_access, mock_request_with_project_headers):
        """Test that allowed access passes through."""
        mock_check_access.return_value = True

        guard = require_permission_async(
            action="view_project",
            resource_builder=resource_builders.project_from_headers(),
        )

        # Should not raise exception
        await guard(mock_request_with_project_headers)

        mock_check_access.assert_called_once()

    @pytest.mark.asyncio
    @patch("rbac_sdk.fastapi_helpers.check_access_async")
    async def test_require_permission_async_denied(self, mock_check_access, mock_request_with_project_headers):
        """Test that denied access raises 403."""
        mock_check_access.return_value = False

        guard = require_permission_async(
            action="delete_project",
            resource_builder=resource_builders.project_from_headers(),
        )

        with pytest.raises(HTTPException) as exc_info:
            await guard(mock_request_with_project_headers)

        assert exc_info.value.status_code == 403
        assert "Forbidden" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    @patch("rbac_sdk.fastapi_helpers.check_access_async")
    async def test_require_permission_async_missing_user_id(self, mock_check_access, mock_request):
        """Test that missing user ID raises 401."""
        guard = require_permission_async(
            action="view_project",
            resource_builder=resource_builders.project_from_headers(),
        )

        with pytest.raises(HTTPException) as exc_info:
            await guard(mock_request)

        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    @patch("rbac_sdk.fastapi_helpers.check_access_async")
    async def test_require_permission_async_missing_resource_headers(self, mock_check_access, mock_request_with_user):
        """Test that missing resource headers raises 400."""
        guard = require_permission_async(
            action="view_project",
            resource_builder=resource_builders.project_from_headers(),
        )

        with pytest.raises(HTTPException) as exc_info:
            await guard(mock_request_with_user)

        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    @patch("rbac_sdk.fastapi_helpers.check_access_async")
    async def test_require_permission_async_custom_principal_resolver(self, mock_check_access):
        """Test that custom principal resolver is used."""
        mock_check_access.return_value = True

        request = Mock()
        request.headers = {
            "X-Custom-User": "custom-user-456",
            "X-elevAIte-ProjectId": "proj-123",
            "X-elevAIte-OrganizationId": "org-456",
        }

        custom_resolver = principal_resolvers.user_id_header(header_name="X-Custom-User")

        guard = require_permission_async(
            action="view_project",
            resource_builder=resource_builders.project_from_headers(),
            principal_resolver=custom_resolver,
        )

        await guard(request)

        # Verify check_access_async was called with custom user ID
        call_args = mock_check_access.call_args
        assert call_args[1]["user_id"] == "custom-user-456"

    @pytest.mark.asyncio
    @patch("rbac_sdk.fastapi_helpers.check_access_async")
    async def test_require_permission_async_custom_base_url(self, mock_check_access, mock_request_with_project_headers):
        """Test that custom base_url is passed to check_access_async."""
        mock_check_access.return_value = True

        guard = require_permission_async(
            action="view_project",
            resource_builder=resource_builders.project_from_headers(),
            base_url="http://custom-authz:9000",
        )

        await guard(mock_request_with_project_headers)

        call_args = mock_check_access.call_args
        assert call_args[1]["base_url"] == "http://custom-authz:9000"

    @pytest.mark.asyncio
    @patch("rbac_sdk.fastapi_helpers.check_access_async")
    async def test_require_permission_async_service_failure_returns_false(self, mock_check_access, mock_request_with_project_headers):
        """Test that async client returns False on service failure (fail-closed)."""
        # Async client returns False on errors, not exceptions
        mock_check_access.return_value = False

        guard = require_permission_async(
            action="view_project",
            resource_builder=resource_builders.project_from_headers(),
        )

        with pytest.raises(HTTPException) as exc_info:
            await guard(mock_request_with_project_headers)

        assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_require_permission_async_client_not_available(self, mock_request_with_project_headers):
        """Test that missing async client raises 500."""
        with patch("rbac_sdk.fastapi_helpers.check_access_async", None):
            guard = require_permission_async(
                action="view_project",
                resource_builder=resource_builders.project_from_headers(),
            )

            with pytest.raises(HTTPException) as exc_info:
                await guard(mock_request_with_project_headers)

            assert exc_info.value.status_code == 500
            assert "Async RBAC client not available" in str(exc_info.value.detail)


class TestGuardIntegration:
    """Test integration scenarios with guards."""

    @pytest.mark.asyncio
    @patch("rbac_sdk.fastapi_helpers.check_access_async")
    async def test_multiple_guards_on_same_endpoint(self, mock_check_access, mock_request_with_project_headers):
        """Test that multiple guards can be applied to same endpoint."""
        mock_check_access.return_value = True

        guard1 = require_permission_async(
            action="view_project",
            resource_builder=resource_builders.project_from_headers(),
        )

        guard2 = require_permission_async(
            action="edit_project",
            resource_builder=resource_builders.project_from_headers(),
        )

        # Both should pass
        await guard1(mock_request_with_project_headers)
        await guard2(mock_request_with_project_headers)

        assert mock_check_access.call_count == 2

    @pytest.mark.asyncio
    @patch("rbac_sdk.fastapi_helpers.check_access_async")
    async def test_guard_with_api_key_authentication(self, mock_check_access):
        """Test guard with API key authentication."""
        mock_check_access.return_value = True

        request = Mock()
        request.headers = {
            "X-elevAIte-apikey": "test-api-key",
            "X-elevAIte-ProjectId": "proj-123",
            "X-elevAIte-OrganizationId": "org-456",
        }

        def mock_api_key_validator(api_key: str, req):
            if api_key == "test-api-key":
                return "service-account-789"
            return None

        guard = require_permission_async(
            action="view_project",
            resource_builder=resource_builders.project_from_headers(),
            principal_resolver=principal_resolvers.api_key_or_user(validate_api_key=mock_api_key_validator),
        )

        await guard(request)

        # Verify service account ID was used
        call_args = mock_check_access.call_args
        assert call_args[1]["user_id"] == "service-account-789"

    @patch("rbac_sdk.fastapi_helpers.check_access")
    def test_guard_with_different_resource_types(self, mock_check_access):
        """Test guards with different resource types (project, account, org)."""
        mock_check_access.return_value = True

        # Project guard
        request_project = Mock()
        request_project.headers = {
            "X-elevAIte-UserId": "123",
            "X-elevAIte-ProjectId": "proj-123",
            "X-elevAIte-OrganizationId": "org-456",
        }

        guard_project = require_permission(
            action="view_project",
            resource_builder=resource_builders.project_from_headers(),
        )
        guard_project(request_project)

        # Account guard
        request_account = Mock()
        request_account.headers = {
            "X-elevAIte-UserId": "123",
            "X-elevAIte-AccountId": "acc-789",
            "X-elevAIte-OrganizationId": "org-456",
        }

        guard_account = require_permission(
            action="view_account",
            resource_builder=resource_builders.account_from_headers(),
        )
        guard_account(request_account)

        # Organization guard
        request_org = Mock()
        request_org.headers = {
            "X-elevAIte-UserId": "123",
            "X-elevAIte-OrganizationId": "org-456",
        }

        guard_org = require_permission(
            action="view_organization",
            resource_builder=resource_builders.organization_from_headers(),
        )
        guard_org(request_org)

        assert mock_check_access.call_count == 3

        # Verify resource types
        calls = mock_check_access.call_args_list
        assert calls[0][1]["resource"]["type"] == "project"
        assert calls[1][1]["resource"]["type"] == "account"
        assert calls[2][1]["resource"]["type"] == "organization"


class TestGuardErrorHandling:
    """Test error handling in guards."""

    @patch("rbac_sdk.fastapi_helpers.check_access")
    def test_guard_principal_resolver_exception(self, mock_check_access):
        """Test that principal resolver exceptions are propagated."""
        def bad_resolver(request):
            raise RuntimeError("Resolver crashed")

        guard = require_permission(
            action="view_project",
            resource_builder=resource_builders.project_from_headers(),
            principal_resolver=bad_resolver,
        )

        request = Mock()
        request.headers = {}

        with pytest.raises(RuntimeError):
            guard(request)

    @patch("rbac_sdk.fastapi_helpers.check_access")
    def test_guard_resource_builder_exception(self, mock_check_access):
        """Test that resource builder exceptions are propagated."""
        def bad_builder(request):
            raise RuntimeError("Builder crashed")

        guard = require_permission(
            action="view_project",
            resource_builder=bad_builder,
        )

        request = Mock()
        request.headers = {"X-elevAIte-UserId": "123"}

        with pytest.raises(RuntimeError):
            guard(request)


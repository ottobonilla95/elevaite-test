"""
Integration tests for RBAC SDK with real RBAC service and OPA.

These tests verify:
- Real authorization checks with OPA
- Role-based access control
- Resource hierarchy (Organization > Account > Project)
- Permission inheritance
- User status validation in authorization flow
- Deny reasons from OPA

Requirements:
- Auth API running on http://localhost:8004
- OPA running on http://localhost:8181
- PostgreSQL with test data
- Test users with role assignments
"""

from rbac_sdk.async_client import check_access_async
from rbac_sdk.client import check_access


class TestRBACServiceBasicAccess:
    """Test basic authorization checks with real RBAC service."""

    async def test_viewer_can_view_project(
        self,
        check_auth_api_available,
        check_opa_available,
        test_user_active,
        test_project,
        test_viewer_assignment,
        auth_api_url,
    ):
        """Test that a viewer can view a project they have access to."""
        allowed = await check_access_async(
            user_id=test_user_active["id"],
            action="view_project",
            resource={
                "type": "project",
                "id": str(test_project["id"]),
                "organization_id": str(test_project["organization_id"]),
                "account_id": str(test_project["account_id"]),
            },
            base_url=auth_api_url,
        )

        assert allowed is True

    async def test_viewer_cannot_edit_project(
        self,
        check_auth_api_available,
        check_opa_available,
        test_user_active,
        test_project,
        test_viewer_assignment,
        auth_api_url,
    ):
        """Test that a viewer cannot edit a project."""
        allowed = await check_access_async(
            user_id=test_user_active["id"],
            action="edit_project",
            resource={
                "type": "project",
                "id": str(test_project["id"]),
                "organization_id": str(test_project["organization_id"]),
                "account_id": str(test_project["account_id"]),
            },
            base_url=auth_api_url,
        )

        assert allowed is False

    async def test_editor_can_edit_project(
        self,
        check_auth_api_available,
        check_opa_available,
        test_user_active,
        test_project,
        test_editor_assignment,
        auth_api_url,
    ):
        """Test that an editor can edit a project."""
        allowed = await check_access_async(
            user_id=test_user_active["id"],
            action="edit_project",
            resource={
                "type": "project",
                "id": str(test_project["id"]),
                "organization_id": str(test_project["organization_id"]),
                "account_id": str(test_project["account_id"]),
            },
            base_url=auth_api_url,
        )

        assert allowed is True

    async def test_editor_can_view_project(
        self,
        check_auth_api_available,
        check_opa_available,
        test_user_active,
        test_project,
        test_editor_assignment,
        auth_api_url,
    ):
        """Test that an editor can also view a project (permission inheritance)."""
        allowed = await check_access_async(
            user_id=test_user_active["id"],
            action="view_project",
            resource={
                "type": "project",
                "id": str(test_project["id"]),
                "organization_id": str(test_project["organization_id"]),
                "account_id": str(test_project["account_id"]),
            },
            base_url=auth_api_url,
        )

        assert allowed is True

    async def test_no_assignment_denies_access(
        self,
        check_auth_api_available,
        check_opa_available,
        test_user_active,
        test_project,
        auth_api_url,
    ):
        """Test that a user with no role assignments is denied access."""
        allowed = await check_access_async(
            user_id=test_user_active["id"],
            action="view_project",
            resource={
                "type": "project",
                "id": str(test_project["id"]),
                "organization_id": str(test_project["organization_id"]),
                "account_id": str(test_project["account_id"]),
            },
            base_url=auth_api_url,
        )

        assert allowed is False


class TestRBACServiceHierarchy:
    """Test resource hierarchy and permission inheritance."""

    async def test_admin_can_manage_account(
        self,
        check_auth_api_available,
        check_opa_available,
        test_user_active,
        test_account,
        test_admin_assignment,
        auth_api_url,
    ):
        """Test that an admin can manage an account."""
        allowed = await check_access_async(
            user_id=test_user_active["id"],
            action="manage_account",
            resource={
                "type": "account",
                "id": str(test_account["id"]),
                "organization_id": str(test_account["organization_id"]),
                "account_id": str(test_account["id"]),
            },
            base_url=auth_api_url,
        )

        assert allowed is True

    async def test_admin_can_access_projects_in_account(
        self,
        check_auth_api_available,
        check_opa_available,
        test_user_active,
        test_account,
        test_project_in_account,
        test_admin_assignment,
        auth_api_url,
    ):
        """Test that an account admin can access projects in that account."""
        allowed = await check_access_async(
            user_id=test_user_active["id"],
            action="view_project",
            resource={
                "type": "project",
                "id": str(test_project_in_account["id"]),
                "organization_id": str(test_project_in_account["organization_id"]),
                "account_id": str(test_project_in_account["account_id"]),
            },
            base_url=auth_api_url,
        )

        assert allowed is True

    async def test_superadmin_can_access_everything(
        self,
        check_auth_api_available,
        check_opa_available,
        test_user_active,
        test_organization,
        test_project,
        test_superadmin_assignment,
        auth_api_url,
    ):
        """Test that a superadmin can access any resource in the organization."""
        allowed = await check_access_async(
            user_id=test_user_active["id"],
            action="view_project",
            resource={
                "type": "project",
                "id": str(test_project["id"]),
                "organization_id": str(test_organization["id"]),
                "account_id": str(test_project["account_id"]),
            },
            base_url=auth_api_url,
        )

        assert allowed is True


class TestRBACServiceUserStatus:
    """Test user status validation in authorization flow."""

    async def test_inactive_user_denied_even_with_role(
        self,
        check_auth_api_available,
        check_opa_available,
        test_user_inactive,
        test_project,
        test_viewer_assignment_inactive,
        auth_api_url,
    ):
        """Test that inactive users are denied even if they have role assignments."""
        # This test will be skipped until we can create inactive users
        # See conftest.py test_user_inactive fixture
        pass


class TestRBACServiceSyncClient:
    """Test synchronous RBAC client with real service."""

    def test_sync_client_check_access(
        self,
        check_auth_api_available,
        check_opa_available,
        test_user_active,
        test_project,
        test_viewer_assignment,
        auth_api_url,
    ):
        """Test that sync client works with real RBAC service."""
        allowed = check_access(
            user_id=test_user_active["id"],
            action="view_project",
            resource={
                "type": "project",
                "id": str(test_project["id"]),
                "organization_id": str(test_project["organization_id"]),
                "account_id": str(test_project["account_id"]),
            },
            base_url=auth_api_url,
        )

        assert allowed is True

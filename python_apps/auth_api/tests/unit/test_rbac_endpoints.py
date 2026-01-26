"""Unit tests for RBAC (Role-Based Access Control) endpoints."""

import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from fastapi import HTTPException

from app.routers.rbac import (
    list_roles,
    get_role,
    create_role,
    add_role_permission,
    list_groups,
    get_group,
    create_group,
    update_group,
    delete_group,
    add_group_permission,
    update_group_permission,
    delete_group_permission,
    list_group_members,
    add_group_member,
    remove_group_member,
    list_user_groups,
    get_my_rbac,
)
from app.schemas.rbac import (
    RoleCreate,
    RolePermissionCreate,
    GroupCreate,
    GroupUpdate,
    GroupPermissionCreate,
    GroupPermissionUpdate,
    UserGroupMembershipCreate,
    RoleType,
    ResourceType,
)
from app.db.models import User
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


@pytest.fixture
def mock_superuser():
    """Create a mock superuser."""
    user = MagicMock(spec=User)
    user.id = 1
    user.email = "admin@example.com"
    user.is_superuser = True
    user.status = "active"
    return user


@pytest.fixture
def mock_regular_user():
    """Create a mock regular (non-superuser) user."""
    user = MagicMock(spec=User)
    user.id = 2
    user.email = "user@example.com"
    user.is_superuser = False
    user.status = "active"
    return user


@pytest.fixture
def mock_session():
    """Create a mock async session."""
    session = AsyncMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    session.delete = AsyncMock()
    return session


@pytest.fixture
def mock_role():
    """Create a mock role."""
    role = MagicMock(spec=Role)
    role.id = uuid4()
    role.name = "Test Role"
    role.description = "A test role"
    role.base_type = "viewer"
    role.scope_type = "project"
    role.is_system = False
    role.created_at = datetime.now(timezone.utc)
    role.updated_at = datetime.now(timezone.utc)
    role.permissions = []
    return role


@pytest.fixture
def mock_group():
    """Create a mock group."""
    group = MagicMock(spec=Group)
    group.id = uuid4()
    group.organization_id = uuid4()
    group.name = "Test Group"
    group.description = "A test group"
    group.created_at = datetime.now(timezone.utc)
    group.updated_at = datetime.now(timezone.utc)
    group.permissions = []
    return group


@pytest.fixture
def mock_organization():
    """Create a mock organization."""
    org = MagicMock(spec=Organization)
    org.id = uuid4()
    org.name = "Test Organization"
    return org


# ============================================================================
# Role Tests
# ============================================================================


class TestListRoles:
    """Tests for list_roles endpoint."""

    @pytest.mark.asyncio
    async def test_list_roles_success(self, mock_superuser, mock_session, mock_role):
        """Test successfully listing roles."""
        # Mock database queries
        count_result = MagicMock()
        count_result.scalar.return_value = 1

        roles_result = MagicMock()
        roles_result.scalars.return_value.all.return_value = [mock_role]

        mock_session.execute = AsyncMock(side_effect=[count_result, roles_result])

        result = await list_roles(
            is_system=None,
            base_type=None,
            scope_type=None,
            skip=0,
            limit=100,
            session=mock_session,
            current_user=mock_superuser,
        )

        assert result.total == 1
        assert len(result.roles) == 1
        assert result.roles[0].name == "Test Role"

    @pytest.mark.asyncio
    async def test_list_roles_with_filters(self, mock_superuser, mock_session, mock_role):
        """Test listing roles with filters."""
        count_result = MagicMock()
        count_result.scalar.return_value = 1

        roles_result = MagicMock()
        roles_result.scalars.return_value.all.return_value = [mock_role]

        mock_session.execute = AsyncMock(side_effect=[count_result, roles_result])

        result = await list_roles(
            is_system=False,
            base_type="viewer",
            scope_type="project",
            skip=0,
            limit=100,
            session=mock_session,
            current_user=mock_superuser,
        )

        assert result.total == 1


class TestGetRole:
    """Tests for get_role endpoint."""

    @pytest.mark.asyncio
    async def test_get_role_success(self, mock_superuser, mock_session, mock_role):
        """Test successfully getting a role by ID."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = mock_role
        mock_session.execute = AsyncMock(return_value=mock_result)

        result = await get_role(
            role_id=mock_role.id,
            session=mock_session,
            current_user=mock_superuser,
        )

        assert result.id == mock_role.id
        assert result.name == "Test Role"

    @pytest.mark.asyncio
    async def test_get_role_not_found(self, mock_superuser, mock_session):
        """Test getting a non-existent role."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = None
        mock_session.execute = AsyncMock(return_value=mock_result)

        with pytest.raises(HTTPException) as exc_info:
            await get_role(
                role_id=uuid4(),
                session=mock_session,
                current_user=mock_superuser,
            )

        assert exc_info.value.status_code == 404
        assert "not found" in str(exc_info.value.detail)


class TestCreateRole:
    """Tests for create_role endpoint."""

    @pytest.mark.asyncio
    async def test_create_role_success(self, mock_superuser, mock_session):
        """Test successfully creating a role."""
        role_data = RoleCreate(
            name="New Role",
            description="A new role",
            base_type=RoleType.EDITOR,
            scope_type=ResourceType.ACCOUNT,
        )

        # Mock no existing role with same name
        existing_result = MagicMock()
        existing_result.scalars.return_value.first.return_value = None
        mock_session.execute = AsyncMock(return_value=existing_result)

        # Mock the add operation
        mock_session.add = MagicMock()

        # Mock refresh to set the role attributes
        async def mock_refresh(obj):
            obj.id = uuid4()
            obj.created_at = datetime.now(timezone.utc)
            obj.updated_at = datetime.now(timezone.utc)

        mock_session.refresh = mock_refresh

        result = await create_role(
            role_data=role_data,
            session=mock_session,
            current_user=mock_superuser,
        )

        assert result.name == "New Role"
        mock_session.add.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_role_forbidden_non_superuser(self, mock_regular_user, mock_session):
        """Test that non-superusers cannot create roles."""
        role_data = RoleCreate(
            name="New Role",
            description="A new role",
            base_type=RoleType.EDITOR,
            scope_type=ResourceType.ACCOUNT,
        )

        with pytest.raises(HTTPException) as exc_info:
            await create_role(
                role_data=role_data,
                session=mock_session,
                current_user=mock_regular_user,
            )

        assert exc_info.value.status_code == 403
        assert "superusers" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_create_role_duplicate_name(self, mock_superuser, mock_session, mock_role):
        """Test creating a role with duplicate name."""
        role_data = RoleCreate(
            name="Test Role",  # Same as mock_role
            description="A duplicate role",
            base_type=RoleType.EDITOR,
            scope_type=ResourceType.ACCOUNT,
        )

        # Mock existing role with same name
        existing_result = MagicMock()
        existing_result.scalars.return_value.first.return_value = mock_role
        mock_session.execute = AsyncMock(return_value=existing_result)

        with pytest.raises(HTTPException) as exc_info:
            await create_role(
                role_data=role_data,
                session=mock_session,
                current_user=mock_superuser,
            )

        assert exc_info.value.status_code == 409
        assert "already exists" in str(exc_info.value.detail)


class TestAddRolePermission:
    """Tests for add_role_permission endpoint."""

    @pytest.mark.asyncio
    async def test_add_role_permission_success(self, mock_superuser, mock_session, mock_role):
        """Test successfully adding a permission to a role."""
        permission_data = RolePermissionCreate(
            service_name="test_service",
            allowed_actions=["read", "write"],
        )

        # Mock role exists
        role_result = MagicMock()
        role_result.scalars.return_value.first.return_value = mock_role

        # Mock no existing permission
        existing_result = MagicMock()
        existing_result.scalars.return_value.first.return_value = None

        mock_session.execute = AsyncMock(side_effect=[role_result, existing_result])
        mock_session.add = MagicMock()

        async def mock_refresh(obj):
            obj.id = uuid4()
            obj.role_id = mock_role.id
            obj.created_at = datetime.now(timezone.utc)
            obj.updated_at = datetime.now(timezone.utc)

        mock_session.refresh = mock_refresh

        result = await add_role_permission(
            role_id=mock_role.id,
            permission_data=permission_data,
            session=mock_session,
            current_user=mock_superuser,
        )

        assert result.service_name == "test_service"
        assert result.allowed_actions == ["read", "write"]

    @pytest.mark.asyncio
    async def test_add_role_permission_role_not_found(self, mock_superuser, mock_session):
        """Test adding permission to non-existent role."""
        permission_data = RolePermissionCreate(
            service_name="test_service",
            allowed_actions=["read"],
        )

        role_result = MagicMock()
        role_result.scalars.return_value.first.return_value = None
        mock_session.execute = AsyncMock(return_value=role_result)

        with pytest.raises(HTTPException) as exc_info:
            await add_role_permission(
                role_id=uuid4(),
                permission_data=permission_data,
                session=mock_session,
                current_user=mock_superuser,
            )

        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_add_role_permission_forbidden_non_superuser(self, mock_regular_user, mock_session):
        """Test that non-superusers cannot add role permissions."""
        permission_data = RolePermissionCreate(
            service_name="test_service",
            allowed_actions=["read"],
        )

        with pytest.raises(HTTPException) as exc_info:
            await add_role_permission(
                role_id=uuid4(),
                permission_data=permission_data,
                session=mock_session,
                current_user=mock_regular_user,
            )

        assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_add_role_permission_duplicate(self, mock_superuser, mock_session, mock_role):
        """Test adding duplicate permission to role."""
        permission_data = RolePermissionCreate(
            service_name="test_service",
            allowed_actions=["read"],
        )

        # Mock role exists
        role_result = MagicMock()
        role_result.scalars.return_value.first.return_value = mock_role

        # Mock existing permission
        existing_permission = MagicMock(spec=RolePermission)
        existing_result = MagicMock()
        existing_result.scalars.return_value.first.return_value = existing_permission

        mock_session.execute = AsyncMock(side_effect=[role_result, existing_result])

        with pytest.raises(HTTPException) as exc_info:
            await add_role_permission(
                role_id=mock_role.id,
                permission_data=permission_data,
                session=mock_session,
                current_user=mock_superuser,
            )

        assert exc_info.value.status_code == 409


# ============================================================================
# Group Tests
# ============================================================================


class TestListGroups:
    """Tests for list_groups endpoint."""

    @pytest.mark.asyncio
    async def test_list_groups_success(self, mock_superuser, mock_session, mock_group):
        """Test successfully listing groups."""
        count_result = MagicMock()
        count_result.scalar.return_value = 1

        groups_result = MagicMock()
        groups_result.scalars.return_value.all.return_value = [mock_group]

        mock_session.execute = AsyncMock(side_effect=[count_result, groups_result])

        result = await list_groups(
            organization_id=None,
            skip=0,
            limit=100,
            session=mock_session,
            current_user=mock_superuser,
        )

        assert result.total == 1
        assert len(result.groups) == 1
        assert result.groups[0].name == "Test Group"

    @pytest.mark.asyncio
    async def test_list_groups_with_org_filter(self, mock_superuser, mock_session, mock_group):
        """Test listing groups with organization filter."""
        count_result = MagicMock()
        count_result.scalar.return_value = 1

        groups_result = MagicMock()
        groups_result.scalars.return_value.all.return_value = [mock_group]

        mock_session.execute = AsyncMock(side_effect=[count_result, groups_result])

        result = await list_groups(
            organization_id=mock_group.organization_id,
            skip=0,
            limit=100,
            session=mock_session,
            current_user=mock_superuser,
        )

        assert result.total == 1


class TestGetGroup:
    """Tests for get_group endpoint."""

    @pytest.mark.asyncio
    async def test_get_group_success(self, mock_superuser, mock_session, mock_group):
        """Test successfully getting a group by ID."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = mock_group
        mock_session.execute = AsyncMock(return_value=mock_result)

        result = await get_group(
            group_id=mock_group.id,
            session=mock_session,
            current_user=mock_superuser,
        )

        assert result.id == mock_group.id
        assert result.name == "Test Group"

    @pytest.mark.asyncio
    async def test_get_group_not_found(self, mock_superuser, mock_session):
        """Test getting a non-existent group."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = None
        mock_session.execute = AsyncMock(return_value=mock_result)

        with pytest.raises(HTTPException) as exc_info:
            await get_group(
                group_id=uuid4(),
                session=mock_session,
                current_user=mock_superuser,
            )

        assert exc_info.value.status_code == 404


class TestCreateGroup:
    """Tests for create_group endpoint."""

    @pytest.mark.asyncio
    async def test_create_group_success(self, mock_superuser, mock_session, mock_organization):
        """Test successfully creating a group."""
        group_data = GroupCreate(
            organization_id=mock_organization.id,
            name="New Group",
            description="A new group",
        )

        # Mock org exists
        org_result = MagicMock()
        org_result.scalars.return_value.first.return_value = mock_organization

        # Mock no existing group with same name
        existing_result = MagicMock()
        existing_result.scalars.return_value.first.return_value = None

        mock_session.execute = AsyncMock(side_effect=[org_result, existing_result])
        mock_session.add = MagicMock()

        async def mock_refresh(obj):
            obj.id = uuid4()
            obj.created_at = datetime.now(timezone.utc)
            obj.updated_at = datetime.now(timezone.utc)

        mock_session.refresh = mock_refresh

        result = await create_group(
            group_data=group_data,
            session=mock_session,
            current_user=mock_superuser,
        )

        assert result.name == "New Group"

    @pytest.mark.asyncio
    async def test_create_group_forbidden_non_superuser(self, mock_regular_user, mock_session, mock_organization):
        """Test that non-superusers cannot create groups."""
        group_data = GroupCreate(
            organization_id=mock_organization.id,
            name="New Group",
            description="A new group",
        )

        # Mock org exists
        org_result = MagicMock()
        org_result.scalars.return_value.first.return_value = mock_organization
        mock_session.execute = AsyncMock(return_value=org_result)

        with pytest.raises(HTTPException) as exc_info:
            await create_group(
                group_data=group_data,
                session=mock_session,
                current_user=mock_regular_user,
            )

        assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_create_group_org_not_found(self, mock_superuser, mock_session):
        """Test creating a group in non-existent organization."""
        group_data = GroupCreate(
            organization_id=uuid4(),
            name="New Group",
            description="A new group",
        )

        org_result = MagicMock()
        org_result.scalars.return_value.first.return_value = None
        mock_session.execute = AsyncMock(return_value=org_result)

        with pytest.raises(HTTPException) as exc_info:
            await create_group(
                group_data=group_data,
                session=mock_session,
                current_user=mock_superuser,
            )

        assert exc_info.value.status_code == 404


class TestUpdateGroup:
    """Tests for update_group endpoint."""

    @pytest.mark.asyncio
    async def test_update_group_success(self, mock_superuser, mock_session, mock_group):
        """Test successfully updating a group."""
        group_data = GroupUpdate(name="Updated Group Name")

        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = mock_group
        mock_session.execute = AsyncMock(return_value=mock_result)

        async def mock_refresh(obj):
            obj.name = "Updated Group Name"

        mock_session.refresh = mock_refresh

        await update_group(
            group_id=mock_group.id,
            group_data=group_data,
            session=mock_session,
            current_user=mock_superuser,
        )

        assert mock_group.name == "Updated Group Name"

    @pytest.mark.asyncio
    async def test_update_group_not_found(self, mock_superuser, mock_session):
        """Test updating a non-existent group."""
        group_data = GroupUpdate(name="Updated Name")

        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = None
        mock_session.execute = AsyncMock(return_value=mock_result)

        with pytest.raises(HTTPException) as exc_info:
            await update_group(
                group_id=uuid4(),
                group_data=group_data,
                session=mock_session,
                current_user=mock_superuser,
            )

        assert exc_info.value.status_code == 404


class TestDeleteGroup:
    """Tests for delete_group endpoint."""

    @pytest.mark.asyncio
    async def test_delete_group_success(self, mock_superuser, mock_session, mock_group):
        """Test successfully deleting a group."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = mock_group
        mock_session.execute = AsyncMock(return_value=mock_result)

        result = await delete_group(
            group_id=mock_group.id,
            session=mock_session,
            current_user=mock_superuser,
        )

        assert result is None
        mock_session.delete.assert_called_once_with(mock_group)

    @pytest.mark.asyncio
    async def test_delete_group_not_found(self, mock_superuser, mock_session):
        """Test deleting a non-existent group."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = None
        mock_session.execute = AsyncMock(return_value=mock_result)

        with pytest.raises(HTTPException) as exc_info:
            await delete_group(
                group_id=uuid4(),
                session=mock_session,
                current_user=mock_superuser,
            )

        assert exc_info.value.status_code == 404


# ============================================================================
# Group Permission Tests
# ============================================================================


class TestAddGroupPermission:
    """Tests for add_group_permission endpoint."""

    @pytest.mark.asyncio
    async def test_add_group_permission_success(self, mock_superuser, mock_session, mock_group):
        """Test successfully adding a permission to a group."""
        permission_data = GroupPermissionCreate(
            service_name="test_service",
            allow_actions=["read"],
            deny_actions=["delete"],
        )

        # Mock group exists
        group_result = MagicMock()
        group_result.scalars.return_value.first.return_value = mock_group

        # Mock no existing permission
        existing_result = MagicMock()
        existing_result.scalars.return_value.first.return_value = None

        mock_session.execute = AsyncMock(side_effect=[group_result, existing_result])
        mock_session.add = MagicMock()

        async def mock_refresh(obj):
            obj.id = uuid4()
            obj.group_id = mock_group.id
            obj.created_at = datetime.now(timezone.utc)
            obj.updated_at = datetime.now(timezone.utc)

        mock_session.refresh = mock_refresh

        result = await add_group_permission(
            group_id=mock_group.id,
            permission_data=permission_data,
            session=mock_session,
            current_user=mock_superuser,
        )

        assert result.service_name == "test_service"
        assert result.allow_actions == ["read"]
        assert result.deny_actions == ["delete"]

    @pytest.mark.asyncio
    async def test_add_group_permission_group_not_found(self, mock_superuser, mock_session):
        """Test adding permission to non-existent group."""
        permission_data = GroupPermissionCreate(
            service_name="test_service",
            allow_actions=["read"],
        )

        group_result = MagicMock()
        group_result.scalars.return_value.first.return_value = None
        mock_session.execute = AsyncMock(return_value=group_result)

        with pytest.raises(HTTPException) as exc_info:
            await add_group_permission(
                group_id=uuid4(),
                permission_data=permission_data,
                session=mock_session,
                current_user=mock_superuser,
            )

        assert exc_info.value.status_code == 404


class TestUpdateGroupPermission:
    """Tests for update_group_permission endpoint."""

    @pytest.mark.asyncio
    async def test_update_group_permission_success(self, mock_superuser, mock_session, mock_group):
        """Test successfully updating a group permission."""
        permission_id = uuid4()
        permission_data = GroupPermissionUpdate(
            allow_actions=["read", "write"],
            deny_actions=["delete"],
        )

        mock_permission = MagicMock(spec=GroupPermission)
        mock_permission.id = permission_id
        mock_permission.group_id = mock_group.id
        mock_permission.service_name = "test_service"
        mock_permission.allow_actions = ["read"]
        mock_permission.deny_actions = []
        mock_permission.created_at = datetime.now(timezone.utc)
        mock_permission.updated_at = datetime.now(timezone.utc)

        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = mock_permission
        mock_session.execute = AsyncMock(return_value=mock_result)

        async def mock_refresh(obj):
            obj.allow_actions = ["read", "write"]
            obj.deny_actions = ["delete"]
            obj.updated_at = datetime.now(timezone.utc)

        mock_session.refresh = mock_refresh

        await update_group_permission(
            group_id=mock_group.id,
            permission_id=permission_id,
            permission_data=permission_data,
            session=mock_session,
            current_user=mock_superuser,
        )

        assert mock_permission.allow_actions == ["read", "write"]
        assert mock_permission.deny_actions == ["delete"]


class TestDeleteGroupPermission:
    """Tests for delete_group_permission endpoint."""

    @pytest.mark.asyncio
    async def test_delete_group_permission_success(self, mock_superuser, mock_session, mock_group):
        """Test successfully deleting a group permission."""
        permission_id = uuid4()
        mock_permission = MagicMock(spec=GroupPermission)
        mock_permission.id = permission_id
        mock_permission.group_id = mock_group.id

        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = mock_permission
        mock_session.execute = AsyncMock(return_value=mock_result)

        result = await delete_group_permission(
            group_id=mock_group.id,
            permission_id=permission_id,
            session=mock_session,
            current_user=mock_superuser,
        )

        assert result is None
        mock_session.delete.assert_called_once_with(mock_permission)


# ============================================================================
# User Group Membership Tests
# ============================================================================


class TestListGroupMembers:
    """Tests for list_group_members endpoint."""

    @pytest.mark.asyncio
    async def test_list_group_members_success(self, mock_superuser, mock_session, mock_group):
        """Test successfully listing group members."""
        # Mock group exists
        group_result = MagicMock()
        group_result.scalars.return_value.first.return_value = mock_group

        # Mock count
        count_result = MagicMock()
        count_result.scalar.return_value = 1

        # Mock memberships
        mock_membership = MagicMock(spec=UserGroupMembership)
        mock_membership.user_id = 2
        mock_membership.group_id = mock_group.id
        mock_membership.resource_id = uuid4()
        mock_membership.resource_type = "organization"
        mock_membership.created_at = datetime.now(timezone.utc)
        mock_membership.group = None

        members_result = MagicMock()
        members_result.scalars.return_value.all.return_value = [mock_membership]

        mock_session.execute = AsyncMock(side_effect=[group_result, count_result, members_result])

        result = await list_group_members(
            group_id=mock_group.id,
            resource_id=None,
            skip=0,
            limit=100,
            session=mock_session,
            current_user=mock_superuser,
        )

        assert result.total == 1
        assert len(result.memberships) == 1

    @pytest.mark.asyncio
    async def test_list_group_members_group_not_found(self, mock_superuser, mock_session):
        """Test listing members of non-existent group."""
        group_result = MagicMock()
        group_result.scalars.return_value.first.return_value = None
        mock_session.execute = AsyncMock(return_value=group_result)

        with pytest.raises(HTTPException) as exc_info:
            await list_group_members(
                group_id=uuid4(),
                resource_id=None,
                skip=0,
                limit=100,
                session=mock_session,
                current_user=mock_superuser,
            )

        assert exc_info.value.status_code == 404


class TestAddGroupMember:
    """Tests for add_group_member endpoint."""

    @pytest.mark.asyncio
    async def test_add_group_member_success(self, mock_superuser, mock_session, mock_group, mock_organization):
        """Test successfully adding a member to a group."""
        membership_data = UserGroupMembershipCreate(
            user_id=2,
            resource_id=mock_organization.id,
            resource_type=ResourceType.ORGANIZATION,
        )

        # Mock group exists
        group_result = MagicMock()
        group_result.scalars.return_value.first.return_value = mock_group

        # Mock user exists
        mock_user = MagicMock(spec=User)
        mock_user.id = 2
        user_result = MagicMock()
        user_result.scalars.return_value.first.return_value = mock_user

        # Mock resource exists
        resource_result = MagicMock()
        resource_result.scalars.return_value.first.return_value = mock_organization

        # Mock no existing membership
        existing_result = MagicMock()
        existing_result.scalars.return_value.first.return_value = None

        mock_session.execute = AsyncMock(side_effect=[group_result, user_result, resource_result, existing_result])
        mock_session.add = MagicMock()

        async def mock_refresh(obj):
            obj.created_at = datetime.now(timezone.utc)

        mock_session.refresh = mock_refresh

        result = await add_group_member(
            group_id=mock_group.id,
            membership_data=membership_data,
            session=mock_session,
            current_user=mock_superuser,
        )

        assert result.user_id == 2
        assert result.group_id == mock_group.id

    @pytest.mark.asyncio
    async def test_add_group_member_forbidden_non_superuser(self, mock_regular_user, mock_session, mock_group):
        """Test that non-superusers cannot add group members."""
        membership_data = UserGroupMembershipCreate(
            user_id=3,
            resource_id=uuid4(),
            resource_type=ResourceType.ORGANIZATION,
        )

        with pytest.raises(HTTPException) as exc_info:
            await add_group_member(
                group_id=mock_group.id,
                membership_data=membership_data,
                session=mock_session,
                current_user=mock_regular_user,
            )

        assert exc_info.value.status_code == 403


class TestRemoveGroupMember:
    """Tests for remove_group_member endpoint."""

    @pytest.mark.asyncio
    async def test_remove_group_member_success(self, mock_superuser, mock_session, mock_group):
        """Test successfully removing a member from a group."""
        resource_id = uuid4()
        mock_membership = MagicMock(spec=UserGroupMembership)
        mock_membership.user_id = 2
        mock_membership.group_id = mock_group.id
        mock_membership.resource_id = resource_id

        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = mock_membership
        mock_session.execute = AsyncMock(return_value=mock_result)

        result = await remove_group_member(
            group_id=mock_group.id,
            user_id=2,
            resource_id=resource_id,
            session=mock_session,
            current_user=mock_superuser,
        )

        assert result is None
        mock_session.delete.assert_called_once_with(mock_membership)

    @pytest.mark.asyncio
    async def test_remove_group_member_not_found(self, mock_superuser, mock_session, mock_group):
        """Test removing non-existent membership."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = None
        mock_session.execute = AsyncMock(return_value=mock_result)

        with pytest.raises(HTTPException) as exc_info:
            await remove_group_member(
                group_id=mock_group.id,
                user_id=999,
                resource_id=uuid4(),
                session=mock_session,
                current_user=mock_superuser,
            )

        assert exc_info.value.status_code == 404


class TestListUserGroups:
    """Tests for list_user_groups endpoint."""

    @pytest.mark.asyncio
    async def test_list_user_groups_success(self, mock_superuser, mock_session, mock_group):
        """Test successfully listing a user's groups."""
        # Mock user exists
        mock_user = MagicMock(spec=User)
        mock_user.id = 2
        user_result = MagicMock()
        user_result.scalars.return_value.first.return_value = mock_user

        # Mock count
        count_result = MagicMock()
        count_result.scalar.return_value = 1

        # Mock memberships
        mock_membership = MagicMock(spec=UserGroupMembership)
        mock_membership.user_id = 2
        mock_membership.group_id = mock_group.id
        mock_membership.resource_id = uuid4()
        mock_membership.resource_type = "organization"
        mock_membership.created_at = datetime.now(timezone.utc)
        mock_membership.group = mock_group

        memberships_result = MagicMock()
        memberships_result.scalars.return_value.all.return_value = [mock_membership]

        mock_session.execute = AsyncMock(side_effect=[user_result, count_result, memberships_result])

        result = await list_user_groups(
            user_id=2,
            resource_id=None,
            skip=0,
            limit=100,
            session=mock_session,
            current_user=mock_superuser,
        )

        assert result.total == 1
        assert len(result.memberships) == 1

    @pytest.mark.asyncio
    async def test_list_user_groups_user_not_found(self, mock_superuser, mock_session):
        """Test listing groups for non-existent user."""
        user_result = MagicMock()
        user_result.scalars.return_value.first.return_value = None
        mock_session.execute = AsyncMock(return_value=user_result)

        with pytest.raises(HTTPException) as exc_info:
            await list_user_groups(
                user_id=999,
                resource_id=None,
                skip=0,
                limit=100,
                session=mock_session,
                current_user=mock_superuser,
            )

        assert exc_info.value.status_code == 404


# ============================================================================
# Current User RBAC Tests
# ============================================================================


class TestGetMyRbac:
    """Tests for get_my_rbac endpoint."""

    @pytest.mark.asyncio
    async def test_get_my_rbac_success_with_all_data(self, mock_superuser, mock_session, mock_group):
        """Test getting current user's RBAC info with roles, groups, and overrides."""
        # Mock role assignment
        mock_role_assignment = MagicMock(spec=UserRoleAssignment)
        mock_role_assignment.user_id = mock_superuser.id
        mock_role_assignment.role = "admin"
        mock_role_assignment.resource_type = "organization"
        mock_role_assignment.resource_id = uuid4()
        mock_role_assignment.created_at = datetime.now(timezone.utc)

        # Mock group membership
        mock_membership = MagicMock(spec=UserGroupMembership)
        mock_membership.user_id = mock_superuser.id
        mock_membership.group_id = mock_group.id
        mock_membership.resource_id = uuid4()
        mock_membership.resource_type = "organization"
        mock_membership.created_at = datetime.now(timezone.utc)
        mock_membership.group = mock_group

        # Mock permission override
        mock_override = MagicMock(spec=PermissionOverride)
        mock_override.user_id = mock_superuser.id
        mock_override.resource_type = "project"
        mock_override.resource_id = uuid4()
        mock_override.allow_actions = ["custom_action"]
        mock_override.deny_actions = []
        mock_override.created_at = datetime.now(timezone.utc)
        mock_override.updated_at = datetime.now(timezone.utc)

        # Setup mock returns
        role_result = MagicMock()
        role_result.scalars.return_value.all.return_value = [mock_role_assignment]

        membership_result = MagicMock()
        membership_result.scalars.return_value.all.return_value = [mock_membership]

        override_result = MagicMock()
        override_result.scalars.return_value.all.return_value = [mock_override]

        mock_session.execute = AsyncMock(side_effect=[role_result, membership_result, override_result])

        result = await get_my_rbac(
            session=mock_session,
            current_user=mock_superuser,
        )

        assert result.user_id == mock_superuser.id
        assert result.is_superuser is True
        assert len(result.role_assignments) == 1
        assert len(result.group_memberships) == 1
        assert len(result.permission_overrides) == 1

    @pytest.mark.asyncio
    async def test_get_my_rbac_empty_for_new_user(self, mock_regular_user, mock_session):
        """Test getting RBAC info for user with no assignments."""
        # Mock empty results
        role_result = MagicMock()
        role_result.scalars.return_value.all.return_value = []

        membership_result = MagicMock()
        membership_result.scalars.return_value.all.return_value = []

        override_result = MagicMock()
        override_result.scalars.return_value.all.return_value = []

        mock_session.execute = AsyncMock(side_effect=[role_result, membership_result, override_result])

        result = await get_my_rbac(
            session=mock_session,
            current_user=mock_regular_user,
        )

        assert result.user_id == mock_regular_user.id
        assert result.is_superuser is False
        assert len(result.role_assignments) == 0
        assert len(result.group_memberships) == 0
        assert len(result.permission_overrides) == 0

    @pytest.mark.asyncio
    async def test_get_my_rbac_multiple_assignments(self, mock_superuser, mock_session):
        """Test user with multiple role assignments."""
        # Create multiple role assignments
        assignments = []
        for i in range(3):
            mock_assignment = MagicMock(spec=UserRoleAssignment)
            mock_assignment.user_id = mock_superuser.id
            mock_assignment.role = ["admin", "editor", "viewer"][i]
            mock_assignment.resource_type = "project"
            mock_assignment.resource_id = uuid4()
            mock_assignment.created_at = datetime.now(timezone.utc)
            assignments.append(mock_assignment)

        role_result = MagicMock()
        role_result.scalars.return_value.all.return_value = assignments

        membership_result = MagicMock()
        membership_result.scalars.return_value.all.return_value = []

        override_result = MagicMock()
        override_result.scalars.return_value.all.return_value = []

        mock_session.execute = AsyncMock(side_effect=[role_result, membership_result, override_result])

        result = await get_my_rbac(
            session=mock_session,
            current_user=mock_superuser,
        )

        assert len(result.role_assignments) == 3


class TestCheckAccessRoleResolution:
    """Tests for check_access endpoint role resolution.

    These tests verify that the check_access endpoint correctly resolves
    role names from either:
    1. role_ref.base_type (new FK-based approach)
    2. role string field (legacy approach)
    """

    @pytest.mark.asyncio
    async def test_check_access_uses_role_ref_base_type(self, mock_superuser, mock_session):
        """Test that check_access uses role_ref.base_type when role_id FK is set."""
        from app.routers.authz import check_access
        from app.schemas.rbac import AccessCheckRequest, ResourceInfo

        # Mock user query
        user_result = MagicMock()
        user_result.scalars.return_value.first.return_value = mock_superuser

        # Create mock role with base_type
        mock_role = MagicMock(spec=Role)
        mock_role.base_type = "superadmin"

        # Create mock assignment with role_ref (FK approach) but NO legacy role string
        mock_assignment = MagicMock(spec=UserRoleAssignment)
        mock_assignment.user_id = mock_superuser.id
        mock_assignment.role = None  # Legacy field is NULL
        mock_assignment.role_ref = mock_role  # FK relationship is set
        mock_assignment.resource_type = "organization"
        mock_assignment.resource_id = uuid4()

        assignments_result = MagicMock()
        assignments_result.scalars.return_value.all.return_value = [mock_assignment]

        # Mock permission overrides (empty)
        overrides_result = MagicMock()
        overrides_result.scalars.return_value.first.return_value = None

        # Mock group memberships (empty)
        memberships_result = MagicMock()
        memberships_result.scalars.return_value.all.return_value = []

        mock_session.execute = AsyncMock(
            side_effect=[
                user_result,
                assignments_result,
                overrides_result,
                memberships_result,
            ]
        )

        # Mock OPA service
        with patch("app.routers.authz.get_opa_service") as mock_opa:
            mock_opa_instance = MagicMock()
            mock_opa_instance.check_access = AsyncMock(return_value={"allowed": True})
            mock_opa.return_value = mock_opa_instance

            request = AccessCheckRequest(
                user_id=mock_superuser.id,
                action="view_workflow",
                resource=ResourceInfo(
                    type="project",
                    id=str(uuid4()),
                    organization_id=str(uuid4()),
                ),
            )

            await check_access(request=request, session=mock_session)

            # Verify OPA was called with correct role from role_ref.base_type
            call_args = mock_opa_instance.check_access.call_args
            user_assignments = call_args.kwargs["user_assignments"]
            assert len(user_assignments) == 1
            assert user_assignments[0]["role"] == "superadmin"

    @pytest.mark.asyncio
    async def test_check_access_falls_back_to_legacy_role_string(self, mock_superuser, mock_session):
        """Test that check_access falls back to legacy role string when role_ref is None."""
        from app.routers.authz import check_access
        from app.schemas.rbac import AccessCheckRequest, ResourceInfo

        # Mock user query
        user_result = MagicMock()
        user_result.scalars.return_value.first.return_value = mock_superuser

        # Create mock assignment with legacy role string but NO role_ref
        mock_assignment = MagicMock(spec=UserRoleAssignment)
        mock_assignment.user_id = mock_superuser.id
        mock_assignment.role = "admin"  # Legacy field is set
        mock_assignment.role_ref = None  # FK relationship is NOT set
        mock_assignment.resource_type = "organization"
        mock_assignment.resource_id = uuid4()

        assignments_result = MagicMock()
        assignments_result.scalars.return_value.all.return_value = [mock_assignment]

        # Mock permission overrides (empty)
        overrides_result = MagicMock()
        overrides_result.scalars.return_value.first.return_value = None

        # Mock group memberships (empty)
        memberships_result = MagicMock()
        memberships_result.scalars.return_value.all.return_value = []

        mock_session.execute = AsyncMock(
            side_effect=[
                user_result,
                assignments_result,
                overrides_result,
                memberships_result,
            ]
        )

        # Mock OPA service
        with patch("app.routers.authz.get_opa_service") as mock_opa:
            mock_opa_instance = MagicMock()
            mock_opa_instance.check_access = AsyncMock(return_value={"allowed": True})
            mock_opa.return_value = mock_opa_instance

            request = AccessCheckRequest(
                user_id=mock_superuser.id,
                action="view_workflow",
                resource=ResourceInfo(
                    type="project",
                    id=str(uuid4()),
                    organization_id=str(uuid4()),
                ),
            )

            await check_access(request=request, session=mock_session)

            # Verify OPA was called with correct role from legacy string
            call_args = mock_opa_instance.check_access.call_args
            user_assignments = call_args.kwargs["user_assignments"]
            assert len(user_assignments) == 1
            assert user_assignments[0]["role"] == "admin"

    @pytest.mark.asyncio
    async def test_check_access_handles_both_role_fields_null(self, mock_superuser, mock_session):
        """Test that check_access handles edge case where both role fields are null."""
        from app.routers.authz import check_access
        from app.schemas.rbac import AccessCheckRequest, ResourceInfo

        # Mock user query
        user_result = MagicMock()
        user_result.scalars.return_value.first.return_value = mock_superuser

        # Create mock assignment with BOTH fields null (edge case / data issue)
        mock_assignment = MagicMock(spec=UserRoleAssignment)
        mock_assignment.user_id = mock_superuser.id
        mock_assignment.role = None  # Legacy field is NULL
        mock_assignment.role_ref = None  # FK relationship is also NULL
        mock_assignment.resource_type = "organization"
        mock_assignment.resource_id = uuid4()

        assignments_result = MagicMock()
        assignments_result.scalars.return_value.all.return_value = [mock_assignment]

        # Mock permission overrides (empty)
        overrides_result = MagicMock()
        overrides_result.scalars.return_value.first.return_value = None

        # Mock group memberships (empty)
        memberships_result = MagicMock()
        memberships_result.scalars.return_value.all.return_value = []

        mock_session.execute = AsyncMock(
            side_effect=[
                user_result,
                assignments_result,
                overrides_result,
                memberships_result,
            ]
        )

        # Mock OPA service
        with patch("app.routers.authz.get_opa_service") as mock_opa:
            mock_opa_instance = MagicMock()
            mock_opa_instance.check_access = AsyncMock(return_value={"allowed": False, "deny_reason": "no_matching_role"})
            mock_opa.return_value = mock_opa_instance

            request = AccessCheckRequest(
                user_id=mock_superuser.id,
                action="view_workflow",
                resource=ResourceInfo(
                    type="project",
                    id=str(uuid4()),
                    organization_id=str(uuid4()),
                ),
            )

            await check_access(request=request, session=mock_session)

            # Verify OPA was called with null role (will be denied by OPA)
            call_args = mock_opa_instance.check_access.call_args
            user_assignments = call_args.kwargs["user_assignments"]
            assert len(user_assignments) == 1
            assert user_assignments[0]["role"] is None

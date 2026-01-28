"""RBAC (Role-Based Access Control) management endpoints."""

import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from sqlalchemy.orm import selectinload

from app.core.deps import get_current_user
from app.db.models import User
from app.db.models_rbac import (
    Organization,
    Account,
    Project,
    UserRoleAssignment,
    PermissionOverride,
    Role,
    RolePermission,
    Group,
    GroupPermission,
    UserGroupMembership,
)
from app.db.tenant_db import get_tenant_async_db
from app.schemas.rbac import (
    OrganizationCreate,
    OrganizationResponse,
    OrganizationListResponse,
    AccountCreate,
    AccountResponse,
    AccountListResponse,
    ProjectCreate,
    ProjectResponse,
    ProjectListResponse,
    UserRoleAssignmentCreate,
    UserRoleAssignmentResponse,
    UserRoleAssignmentListResponse,
    PermissionOverrideCreate,
    PermissionOverrideUpdate,
    PermissionOverrideResponse,
    PermissionOverrideListResponse,
    # Role schemas
    RoleResponse,
    RoleListResponse,
    RoleCreate,
    RolePermissionResponse,
    RolePermissionCreate,
    # Group schemas
    GroupResponse,
    GroupListResponse,
    GroupCreate,
    GroupUpdate,
    GroupPermissionResponse,
    GroupPermissionCreate,
    GroupPermissionUpdate,
    # User group membership schemas
    UserGroupMembershipResponse,
    UserGroupMembershipListResponse,
    UserGroupMembershipCreate,
    # Current user RBAC
    UserRbacResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter()


# ============================================================================
# Organizations
# ============================================================================


@router.post(
    "/organizations",
    response_model=OrganizationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_organization(
    org_data: OrganizationCreate,
    session: AsyncSession = Depends(get_tenant_async_db),
    current_user: User = Depends(get_current_user),
) -> OrganizationResponse:
    """
    Create a new organization.

    **Requires:** Superuser privileges
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only superusers can create organizations",
        )

    # Check if organization name already exists
    result = await session.execute(
        select(Organization).where(Organization.name == org_data.name)
    )
    if result.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Organization '{org_data.name}' already exists",
        )

    org = Organization(
        name=org_data.name,
        description=org_data.description,
    )
    session.add(org)
    await session.commit()
    await session.refresh(org)

    logger.info(f"Organization '{org.name}' created by user {current_user.id}")

    return OrganizationResponse.model_validate(org)


@router.get("/organizations", response_model=OrganizationListResponse)
async def list_organizations(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    session: AsyncSession = Depends(get_tenant_async_db),
    current_user: User = Depends(get_current_user),
) -> OrganizationListResponse:
    """List all organizations."""
    # Get total count
    count_result = await session.execute(select(func.count(Organization.id)))
    total = count_result.scalar()

    # Get organizations
    result = await session.execute(select(Organization).offset(skip).limit(limit))
    organizations = result.scalars().all()

    return OrganizationListResponse(
        organizations=[
            OrganizationResponse.model_validate(org) for org in organizations
        ],
        total=total,
    )


@router.get("/organizations/{org_id}", response_model=OrganizationResponse)
async def get_organization(
    org_id: UUID,
    session: AsyncSession = Depends(get_tenant_async_db),
    current_user: User = Depends(get_current_user),
) -> OrganizationResponse:
    """Get organization by ID."""
    result = await session.execute(
        select(Organization).where(Organization.id == org_id)
    )
    org = result.scalars().first()

    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Organization {org_id} not found",
        )

    return OrganizationResponse.model_validate(org)


# ============================================================================
# Accounts
# ============================================================================


@router.post(
    "/accounts", response_model=AccountResponse, status_code=status.HTTP_201_CREATED
)
async def create_account(
    account_data: AccountCreate,
    session: AsyncSession = Depends(get_tenant_async_db),
    current_user: User = Depends(get_current_user),
) -> AccountResponse:
    """
    Create a new account within an organization.

    **Requires:** Superuser or organization admin
    """
    # Verify organization exists
    org_result = await session.execute(
        select(Organization).where(Organization.id == account_data.organization_id)
    )
    if not org_result.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Organization {account_data.organization_id} not found",
        )

    # TODO: Check if user has admin role on organization (once we have check_access working)
    # For now, require superuser
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only superusers can create accounts",
        )

    account = Account(
        organization_id=account_data.organization_id,
        name=account_data.name,
        description=account_data.description,
    )
    session.add(account)
    await session.commit()
    await session.refresh(account)

    logger.info(
        f"Account '{account.name}' created in org {account.organization_id} by user {current_user.id}"
    )

    return AccountResponse.model_validate(account)


@router.get("/accounts", response_model=AccountListResponse)
async def list_accounts(
    organization_id: Optional[UUID] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    session: AsyncSession = Depends(get_tenant_async_db),
    current_user: User = Depends(get_current_user),
) -> AccountListResponse:
    """List accounts, optionally filtered by organization."""
    query = select(Account)
    count_query = select(func.count(Account.id))

    if organization_id:
        query = query.where(Account.organization_id == organization_id)
        count_query = count_query.where(Account.organization_id == organization_id)

    # Get total count
    count_result = await session.execute(count_query)
    total = count_result.scalar()

    # Get accounts
    result = await session.execute(query.offset(skip).limit(limit))
    accounts = result.scalars().all()

    return AccountListResponse(
        accounts=[AccountResponse.model_validate(acc) for acc in accounts],
        total=total,
    )


@router.get("/accounts/{account_id}", response_model=AccountResponse)
async def get_account(
    account_id: UUID,
    session: AsyncSession = Depends(get_tenant_async_db),
    current_user: User = Depends(get_current_user),
) -> AccountResponse:
    """Get account by ID."""
    result = await session.execute(select(Account).where(Account.id == account_id))
    account = result.scalars().first()

    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Account {account_id} not found",
        )

    return AccountResponse.model_validate(account)


# ============================================================================
# Projects
# ============================================================================


@router.post(
    "/projects", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED
)
async def create_project(
    project_data: ProjectCreate,
    session: AsyncSession = Depends(get_tenant_async_db),
    current_user: User = Depends(get_current_user),
) -> ProjectResponse:
    """
    Create a new project within an account.

    **Requires:** Superuser or account admin
    """
    # Verify account exists and belongs to organization
    account_result = await session.execute(
        select(Account).where(Account.id == project_data.account_id)
    )
    account = account_result.scalars().first()

    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Account {project_data.account_id} not found",
        )

    if account.organization_id != project_data.organization_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Account {project_data.account_id} does not belong to organization {project_data.organization_id}",
        )

    # TODO: Check if user has admin role on account (once we have check_access working)
    # For now, require superuser
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only superusers can create projects",
        )

    project = Project(
        account_id=project_data.account_id,
        organization_id=project_data.organization_id,
        name=project_data.name,
        description=project_data.description,
    )
    session.add(project)
    await session.commit()
    await session.refresh(project)

    logger.info(
        f"Project '{project.name}' created in account {project.account_id} by user {current_user.id}"
    )

    return ProjectResponse.model_validate(project)


@router.get("/projects", response_model=ProjectListResponse)
async def list_projects(
    organization_id: Optional[UUID] = Query(None),
    account_id: Optional[UUID] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    session: AsyncSession = Depends(get_tenant_async_db),
    current_user: User = Depends(get_current_user),
) -> ProjectListResponse:
    """List projects, optionally filtered by organization or account."""
    query = select(Project)
    count_query = select(func.count(Project.id))

    if organization_id:
        query = query.where(Project.organization_id == organization_id)
        count_query = count_query.where(Project.organization_id == organization_id)

    if account_id:
        query = query.where(Project.account_id == account_id)
        count_query = count_query.where(Project.account_id == account_id)

    # Get total count
    count_result = await session.execute(count_query)
    total = count_result.scalar()

    # Get projects
    result = await session.execute(query.offset(skip).limit(limit))
    projects = result.scalars().all()

    return ProjectListResponse(
        projects=[ProjectResponse.model_validate(proj) for proj in projects],
        total=total,
    )


@router.get("/projects/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: UUID,
    session: AsyncSession = Depends(get_tenant_async_db),
    current_user: User = Depends(get_current_user),
) -> ProjectResponse:
    """Get project by ID."""
    result = await session.execute(select(Project).where(Project.id == project_id))
    project = result.scalars().first()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found",
        )

    return ProjectResponse.model_validate(project)


# ============================================================================
# User Role Assignments
# ============================================================================


@router.post(
    "/user_role_assignments",
    response_model=UserRoleAssignmentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_user_role_assignment(
    assignment_data: UserRoleAssignmentCreate,
    session: AsyncSession = Depends(get_tenant_async_db),
    current_user: User = Depends(get_current_user),
) -> UserRoleAssignmentResponse:
    """
    Assign a role to a user on a resource.

    **Requires:** Superuser or admin on the resource
    """
    # Verify user exists
    user_result = await session.execute(
        select(User).where(User.id == assignment_data.user_id)
    )
    if not user_result.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User {assignment_data.user_id} not found",
        )

    # Verify resource exists based on type
    if assignment_data.resource_type.value == "organization":
        resource_result = await session.execute(
            select(Organization).where(Organization.id == assignment_data.resource_id)
        )
    elif assignment_data.resource_type.value == "account":
        resource_result = await session.execute(
            select(Account).where(Account.id == assignment_data.resource_id)
        )
    elif assignment_data.resource_type.value == "project":
        resource_result = await session.execute(
            select(Project).where(Project.id == assignment_data.resource_id)
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid resource type: {assignment_data.resource_type}",
        )

    if not resource_result.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{assignment_data.resource_type.value.capitalize()} {assignment_data.resource_id} not found",
        )

    # TODO: Check if current user has admin role on resource (once we have check_access working)
    # For now, require superuser
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only superusers can assign roles",
        )

    # Check if assignment already exists
    existing_result = await session.execute(
        select(UserRoleAssignment).where(
            UserRoleAssignment.user_id == assignment_data.user_id,
            UserRoleAssignment.resource_id == assignment_data.resource_id,
        )
    )
    existing = existing_result.scalars().first()

    if existing:
        # Update existing assignment
        existing.role = assignment_data.role.value
        existing.resource_type = assignment_data.resource_type.value
        await session.commit()
        await session.refresh(existing)
        logger.info(
            f"Updated role assignment for user {assignment_data.user_id} to {assignment_data.role.value}"
        )
        return UserRoleAssignmentResponse.model_validate(existing)

    # Create new assignment
    assignment = UserRoleAssignment(
        user_id=assignment_data.user_id,
        role=assignment_data.role.value,
        resource_type=assignment_data.resource_type.value,
        resource_id=assignment_data.resource_id,
    )
    session.add(assignment)
    await session.commit()
    await session.refresh(assignment)

    logger.info(
        f"Assigned role {assignment.role} to user {assignment.user_id} on {assignment.resource_type} {assignment.resource_id}"
    )

    return UserRoleAssignmentResponse.model_validate(assignment)


@router.get("/user_role_assignments", response_model=UserRoleAssignmentListResponse)
async def list_user_role_assignments(
    user_id: Optional[int] = Query(None),
    resource_id: Optional[UUID] = Query(None),
    resource_type: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    session: AsyncSession = Depends(get_tenant_async_db),
    current_user: User = Depends(get_current_user),
) -> UserRoleAssignmentListResponse:
    """List user role assignments with optional filters."""
    query = select(UserRoleAssignment)
    count_query = select(func.count(UserRoleAssignment.user_id))

    if user_id:
        query = query.where(UserRoleAssignment.user_id == user_id)
        count_query = count_query.where(UserRoleAssignment.user_id == user_id)

    if resource_id:
        query = query.where(UserRoleAssignment.resource_id == resource_id)
        count_query = count_query.where(UserRoleAssignment.resource_id == resource_id)

    if resource_type:
        query = query.where(UserRoleAssignment.resource_type == resource_type)
        count_query = count_query.where(
            UserRoleAssignment.resource_type == resource_type
        )

    # Get total count
    count_result = await session.execute(count_query)
    total = count_result.scalar()

    # Get assignments
    result = await session.execute(query.offset(skip).limit(limit))
    assignments = result.scalars().all()

    return UserRoleAssignmentListResponse(
        assignments=[UserRoleAssignmentResponse.model_validate(a) for a in assignments],
        total=total,
    )


@router.delete(
    "/user_role_assignments/{user_id}/{resource_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_user_role_assignment(
    user_id: int,
    resource_id: UUID,
    session: AsyncSession = Depends(get_tenant_async_db),
    current_user: User = Depends(get_current_user),
):
    """
    Remove a role assignment from a user.

    **Requires:** Superuser or admin on the resource
    """
    # TODO: Check if current user has admin role on resource
    # For now, require superuser
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only superusers can remove role assignments",
        )

    result = await session.execute(
        select(UserRoleAssignment).where(
            UserRoleAssignment.user_id == user_id,
            UserRoleAssignment.resource_id == resource_id,
        )
    )
    assignment = result.scalars().first()

    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Role assignment not found for user {user_id} on resource {resource_id}",
        )

    await session.delete(assignment)
    await session.commit()

    logger.info(f"Removed role assignment for user {user_id} on resource {resource_id}")

    return None


# ============================================================================
# Permission Overrides
# ============================================================================


@router.post(
    "/permission_overrides",
    response_model=PermissionOverrideResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_permission_override(
    override_data: PermissionOverrideCreate,
    session: AsyncSession = Depends(get_tenant_async_db),
    current_user: User = Depends(get_current_user),
) -> PermissionOverrideResponse:
    """
    Create or update a permission override for a user on a resource.

    Permission overrides allow fine-grained control beyond role-based permissions:
    - **allow_actions**: List of actions explicitly allowed
    - **deny_actions**: List of actions explicitly denied (takes precedence)

    **Requires:** Superuser or admin on the resource
    """
    # TODO: Check if current user has admin role on resource
    # For now, require superuser
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only superusers can create permission overrides",
        )

    # Validate user exists
    user_result = await session.execute(
        select(User).where(User.id == override_data.user_id)
    )
    user = user_result.scalars().first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User {override_data.user_id} not found",
        )

    # Validate resource exists
    resource_model = {
        "organization": Organization,
        "account": Account,
        "project": Project,
    }.get(override_data.resource_type.value)

    if resource_model:
        resource_result = await session.execute(
            select(resource_model).where(resource_model.id == override_data.resource_id)
        )
        if not resource_result.scalars().first():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"{override_data.resource_type.value.capitalize()} {override_data.resource_id} not found",
            )

    # Check if override already exists (upsert behavior)
    result = await session.execute(
        select(PermissionOverride).where(
            PermissionOverride.user_id == override_data.user_id,
            PermissionOverride.resource_id == override_data.resource_id,
        )
    )
    existing_override = result.scalars().first()

    if existing_override:
        # Update existing override
        existing_override.allow_actions = override_data.allow_actions or []
        existing_override.deny_actions = override_data.deny_actions or []
        existing_override.resource_type = override_data.resource_type.value
        await session.commit()
        await session.refresh(existing_override)
        logger.info(
            f"Updated permission override for user {override_data.user_id} on resource {override_data.resource_id}"
        )
        return PermissionOverrideResponse.model_validate(existing_override)
    else:
        # Create new override
        override = PermissionOverride(
            user_id=override_data.user_id,
            resource_id=override_data.resource_id,
            resource_type=override_data.resource_type.value,
            allow_actions=override_data.allow_actions or [],
            deny_actions=override_data.deny_actions or [],
        )
        session.add(override)
        await session.commit()
        await session.refresh(override)
        logger.info(
            f"Created permission override for user {override_data.user_id} on resource {override_data.resource_id}"
        )
        return PermissionOverrideResponse.model_validate(override)


@router.get("/permission_overrides", response_model=PermissionOverrideListResponse)
async def list_permission_overrides(
    user_id: Optional[int] = Query(None, description="Filter by user ID"),
    resource_id: Optional[UUID] = Query(None, description="Filter by resource ID"),
    resource_type: Optional[str] = Query(None, description="Filter by resource type"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    session: AsyncSession = Depends(get_tenant_async_db),
    current_user: User = Depends(get_current_user),
) -> PermissionOverrideListResponse:
    """
    List permission overrides with optional filters.

    **Requires:** Superuser or admin on the resource
    """
    # TODO: Filter based on current user's permissions
    # For now, require superuser
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only superusers can list permission overrides",
        )

    # Build query with filters
    query = select(PermissionOverride)
    count_query = select(func.count(PermissionOverride.user_id))

    if user_id is not None:
        query = query.where(PermissionOverride.user_id == user_id)
        count_query = count_query.where(PermissionOverride.user_id == user_id)

    if resource_id is not None:
        query = query.where(PermissionOverride.resource_id == resource_id)
        count_query = count_query.where(PermissionOverride.resource_id == resource_id)

    if resource_type is not None:
        query = query.where(PermissionOverride.resource_type == resource_type)
        count_query = count_query.where(
            PermissionOverride.resource_type == resource_type
        )

    # Get total count
    count_result = await session.execute(count_query)
    total = count_result.scalar()

    # Get overrides
    result = await session.execute(query.offset(skip).limit(limit))
    overrides = result.scalars().all()

    return PermissionOverrideListResponse(
        overrides=[PermissionOverrideResponse.model_validate(o) for o in overrides],
        total=total,
    )


@router.patch(
    "/permission_overrides/{user_id}/{resource_id}",
    response_model=PermissionOverrideResponse,
)
async def update_permission_override(
    user_id: int,
    resource_id: UUID,
    override_data: PermissionOverrideUpdate,
    session: AsyncSession = Depends(get_tenant_async_db),
    current_user: User = Depends(get_current_user),
) -> PermissionOverrideResponse:
    """
    Update an existing permission override.

    **Requires:** Superuser or admin on the resource
    """
    # TODO: Check if current user has admin role on resource
    # For now, require superuser
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only superusers can update permission overrides",
        )

    result = await session.execute(
        select(PermissionOverride).where(
            PermissionOverride.user_id == user_id,
            PermissionOverride.resource_id == resource_id,
        )
    )
    override = result.scalars().first()

    if not override:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Permission override not found for user {user_id} on resource {resource_id}",
        )

    # Update fields if provided
    if override_data.allow_actions is not None:
        override.allow_actions = override_data.allow_actions
    if override_data.deny_actions is not None:
        override.deny_actions = override_data.deny_actions

    await session.commit()
    await session.refresh(override)

    logger.info(
        f"Updated permission override for user {user_id} on resource {resource_id}"
    )

    return PermissionOverrideResponse.model_validate(override)


@router.delete(
    "/permission_overrides/{user_id}/{resource_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_permission_override(
    user_id: int,
    resource_id: UUID,
    session: AsyncSession = Depends(get_tenant_async_db),
    current_user: User = Depends(get_current_user),
) -> None:
    """
    Remove a permission override.

    **Requires:** Superuser or admin on the resource
    """
    # TODO: Check if current user has admin role on resource
    # For now, require superuser
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only superusers can delete permission overrides",
        )

    result = await session.execute(
        select(PermissionOverride).where(
            PermissionOverride.user_id == user_id,
            PermissionOverride.resource_id == resource_id,
        )
    )
    override = result.scalars().first()

    if not override:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Permission override not found for user {user_id} on resource {resource_id}",
        )

    await session.delete(override)
    await session.commit()

    logger.info(
        f"Deleted permission override for user {user_id} on resource {resource_id}"
    )

    return None


# ============================================================================
# Roles (System and Custom)
# ============================================================================


@router.get("/roles", response_model=RoleListResponse)
async def list_roles(
    is_system: Optional[bool] = Query(None, description="Filter by system roles only"),
    base_type: Optional[str] = Query(
        None, description="Filter by base type (superadmin, admin, editor, viewer)"
    ),
    scope_type: Optional[str] = Query(
        None, description="Filter by scope type (organization, account, project)"
    ),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    session: AsyncSession = Depends(get_tenant_async_db),
    current_user: User = Depends(get_current_user),
) -> RoleListResponse:
    """List all roles with optional filters."""
    query = select(Role).options(selectinload(Role.permissions))
    count_query = select(func.count(Role.id))

    if is_system is not None:
        query = query.where(Role.is_system == is_system)
        count_query = count_query.where(Role.is_system == is_system)

    if base_type:
        query = query.where(Role.base_type == base_type)
        count_query = count_query.where(Role.base_type == base_type)

    if scope_type:
        query = query.where(Role.scope_type == scope_type)
        count_query = count_query.where(Role.scope_type == scope_type)

    count_result = await session.execute(count_query)
    total = count_result.scalar()

    result = await session.execute(query.offset(skip).limit(limit))
    roles = result.scalars().all()

    return RoleListResponse(
        roles=[RoleResponse.model_validate(r) for r in roles],
        total=total,
    )


@router.get("/roles/{role_id}", response_model=RoleResponse)
async def get_role(
    role_id: UUID,
    session: AsyncSession = Depends(get_tenant_async_db),
    current_user: User = Depends(get_current_user),
) -> RoleResponse:
    """Get role by ID with its permissions."""
    result = await session.execute(
        select(Role).options(selectinload(Role.permissions)).where(Role.id == role_id)
    )
    role = result.scalars().first()

    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Role {role_id} not found",
        )

    return RoleResponse.model_validate(role)


@router.post("/roles", response_model=RoleResponse, status_code=status.HTTP_201_CREATED)
async def create_role(
    role_data: RoleCreate,
    session: AsyncSession = Depends(get_tenant_async_db),
    current_user: User = Depends(get_current_user),
) -> RoleResponse:
    """
    Create a custom role.

    **Note:** System roles cannot be created via API.

    **Requires:** Superuser privileges
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only superusers can create roles",
        )

    # Check for duplicate name
    existing = await session.execute(select(Role).where(Role.name == role_data.name))
    if existing.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Role '{role_data.name}' already exists",
        )

    role = Role(
        name=role_data.name,
        description=role_data.description,
        base_type=role_data.base_type.value,
        scope_type=role_data.scope_type.value,
        is_system=False,  # Custom roles are never system roles
    )
    session.add(role)
    await session.commit()
    await session.refresh(role)

    logger.info(f"Created custom role '{role.name}' by user {current_user.id}")

    return RoleResponse.model_validate(role)


@router.post(
    "/roles/{role_id}/permissions",
    response_model=RolePermissionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_role_permission(
    role_id: UUID,
    permission_data: RolePermissionCreate,
    session: AsyncSession = Depends(get_tenant_async_db),
    current_user: User = Depends(get_current_user),
) -> RolePermissionResponse:
    """
    Add a permission to a role.

    **Requires:** Superuser privileges
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only superusers can modify role permissions",
        )

    # Verify role exists
    role_result = await session.execute(select(Role).where(Role.id == role_id))
    role = role_result.scalars().first()
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Role {role_id} not found",
        )

    # Check for existing permission for this service
    existing = await session.execute(
        select(RolePermission).where(
            RolePermission.role_id == role_id,
            RolePermission.service_name == permission_data.service_name,
        )
    )
    if existing.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Permission for service '{permission_data.service_name}' already exists on role",
        )

    permission = RolePermission(
        role_id=role_id,
        service_name=permission_data.service_name,
        allowed_actions=permission_data.allowed_actions,
    )
    session.add(permission)
    await session.commit()
    await session.refresh(permission)

    logger.info(
        f"Added permission for service '{permission_data.service_name}' to role {role_id}"
    )

    return RolePermissionResponse.model_validate(permission)


# ============================================================================
# Groups (Organization-defined)
# ============================================================================


@router.get("/groups", response_model=GroupListResponse)
async def list_groups(
    organization_id: Optional[UUID] = Query(None, description="Filter by organization"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    session: AsyncSession = Depends(get_tenant_async_db),
    current_user: User = Depends(get_current_user),
) -> GroupListResponse:
    """List groups with optional organization filter."""
    query = select(Group).options(selectinload(Group.permissions))
    count_query = select(func.count(Group.id))

    if organization_id:
        query = query.where(Group.organization_id == organization_id)
        count_query = count_query.where(Group.organization_id == organization_id)

    count_result = await session.execute(count_query)
    total = count_result.scalar()

    result = await session.execute(query.offset(skip).limit(limit))
    groups = result.scalars().all()

    return GroupListResponse(
        groups=[GroupResponse.model_validate(g) for g in groups],
        total=total,
    )


@router.get("/groups/{group_id}", response_model=GroupResponse)
async def get_group(
    group_id: UUID,
    session: AsyncSession = Depends(get_tenant_async_db),
    current_user: User = Depends(get_current_user),
) -> GroupResponse:
    """Get group by ID with its permissions."""
    result = await session.execute(
        select(Group)
        .options(selectinload(Group.permissions))
        .where(Group.id == group_id)
    )
    group = result.scalars().first()

    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Group {group_id} not found",
        )

    return GroupResponse.model_validate(group)


@router.post(
    "/groups", response_model=GroupResponse, status_code=status.HTTP_201_CREATED
)
async def create_group(
    group_data: GroupCreate,
    session: AsyncSession = Depends(get_tenant_async_db),
    current_user: User = Depends(get_current_user),
) -> GroupResponse:
    """
    Create a new group within an organization.

    **Requires:** Superuser or organization admin
    """
    # Verify organization exists
    org_result = await session.execute(
        select(Organization).where(Organization.id == group_data.organization_id)
    )
    if not org_result.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Organization {group_data.organization_id} not found",
        )

    # TODO: Check if user has admin role on organization
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only superusers can create groups",
        )

    # Check for duplicate name in organization
    existing = await session.execute(
        select(Group).where(
            Group.organization_id == group_data.organization_id,
            Group.name == group_data.name,
        )
    )
    if existing.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Group '{group_data.name}' already exists in this organization",
        )

    group = Group(
        organization_id=group_data.organization_id,
        name=group_data.name,
        description=group_data.description,
    )
    session.add(group)
    await session.commit()
    await session.refresh(group)

    logger.info(
        f"Created group '{group.name}' in org {group.organization_id} by user {current_user.id}"
    )

    return GroupResponse.model_validate(group)


@router.patch("/groups/{group_id}", response_model=GroupResponse)
async def update_group(
    group_id: UUID,
    group_data: GroupUpdate,
    session: AsyncSession = Depends(get_tenant_async_db),
    current_user: User = Depends(get_current_user),
) -> GroupResponse:
    """
    Update a group.

    **Requires:** Superuser or organization admin
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only superusers can update groups",
        )

    result = await session.execute(select(Group).where(Group.id == group_id))
    group = result.scalars().first()

    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Group {group_id} not found",
        )

    if group_data.name is not None:
        group.name = group_data.name
    if group_data.description is not None:
        group.description = group_data.description

    await session.commit()
    await session.refresh(group)

    logger.info(f"Updated group {group_id} by user {current_user.id}")

    return GroupResponse.model_validate(group)


@router.delete("/groups/{group_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_group(
    group_id: UUID,
    session: AsyncSession = Depends(get_tenant_async_db),
    current_user: User = Depends(get_current_user),
) -> None:
    """
    Delete a group.

    **Requires:** Superuser or organization admin
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only superusers can delete groups",
        )

    result = await session.execute(select(Group).where(Group.id == group_id))
    group = result.scalars().first()

    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Group {group_id} not found",
        )

    await session.delete(group)
    await session.commit()

    logger.info(f"Deleted group {group_id} by user {current_user.id}")

    return None


# ============================================================================
# Group Permissions
# ============================================================================


@router.post(
    "/groups/{group_id}/permissions",
    response_model=GroupPermissionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_group_permission(
    group_id: UUID,
    permission_data: GroupPermissionCreate,
    session: AsyncSession = Depends(get_tenant_async_db),
    current_user: User = Depends(get_current_user),
) -> GroupPermissionResponse:
    """
    Add a permission to a group.

    Groups can have allow_actions and deny_actions per service.
    Note: Groups can only restrict role permissions (deny), not expand them.

    **Requires:** Superuser or organization admin
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only superusers can modify group permissions",
        )

    # Verify group exists
    group_result = await session.execute(select(Group).where(Group.id == group_id))
    group = group_result.scalars().first()
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Group {group_id} not found",
        )

    # Check for existing permission for this service
    existing = await session.execute(
        select(GroupPermission).where(
            GroupPermission.group_id == group_id,
            GroupPermission.service_name == permission_data.service_name,
        )
    )
    if existing.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Permission for service '{permission_data.service_name}' already exists on group",
        )

    permission = GroupPermission(
        group_id=group_id,
        service_name=permission_data.service_name,
        allow_actions=permission_data.allow_actions,
        deny_actions=permission_data.deny_actions,
    )
    session.add(permission)
    await session.commit()
    await session.refresh(permission)

    logger.info(
        f"Added permission for service '{permission_data.service_name}' to group {group_id}"
    )

    return GroupPermissionResponse.model_validate(permission)


@router.patch(
    "/groups/{group_id}/permissions/{permission_id}",
    response_model=GroupPermissionResponse,
)
async def update_group_permission(
    group_id: UUID,
    permission_id: UUID,
    permission_data: GroupPermissionUpdate,
    session: AsyncSession = Depends(get_tenant_async_db),
    current_user: User = Depends(get_current_user),
) -> GroupPermissionResponse:
    """
    Update a group permission.

    **Requires:** Superuser or organization admin
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only superusers can modify group permissions",
        )

    result = await session.execute(
        select(GroupPermission).where(
            GroupPermission.id == permission_id,
            GroupPermission.group_id == group_id,
        )
    )
    permission = result.scalars().first()

    if not permission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Permission {permission_id} not found on group {group_id}",
        )

    if permission_data.allow_actions is not None:
        permission.allow_actions = permission_data.allow_actions
    if permission_data.deny_actions is not None:
        permission.deny_actions = permission_data.deny_actions

    await session.commit()
    await session.refresh(permission)

    logger.info(f"Updated permission {permission_id} on group {group_id}")

    return GroupPermissionResponse.model_validate(permission)


@router.delete(
    "/groups/{group_id}/permissions/{permission_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_group_permission(
    group_id: UUID,
    permission_id: UUID,
    session: AsyncSession = Depends(get_tenant_async_db),
    current_user: User = Depends(get_current_user),
) -> None:
    """
    Delete a group permission.

    **Requires:** Superuser or organization admin
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only superusers can delete group permissions",
        )

    result = await session.execute(
        select(GroupPermission).where(
            GroupPermission.id == permission_id,
            GroupPermission.group_id == group_id,
        )
    )
    permission = result.scalars().first()

    if not permission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Permission {permission_id} not found on group {group_id}",
        )

    await session.delete(permission)
    await session.commit()

    logger.info(f"Deleted permission {permission_id} from group {group_id}")

    return None


# ============================================================================
# User Group Memberships
# ============================================================================


@router.get(
    "/groups/{group_id}/members", response_model=UserGroupMembershipListResponse
)
async def list_group_members(
    group_id: UUID,
    resource_id: Optional[UUID] = Query(None, description="Filter by resource"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    session: AsyncSession = Depends(get_tenant_async_db),
    current_user: User = Depends(get_current_user),
) -> UserGroupMembershipListResponse:
    """List members of a group."""
    # Verify group exists
    group_result = await session.execute(select(Group).where(Group.id == group_id))
    if not group_result.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Group {group_id} not found",
        )

    query = select(UserGroupMembership).where(UserGroupMembership.group_id == group_id)
    count_query = select(func.count()).where(UserGroupMembership.group_id == group_id)

    if resource_id:
        query = query.where(UserGroupMembership.resource_id == resource_id)
        count_query = count_query.where(UserGroupMembership.resource_id == resource_id)

    count_result = await session.execute(count_query)
    total = count_result.scalar()

    result = await session.execute(query.offset(skip).limit(limit))
    memberships = result.scalars().all()

    return UserGroupMembershipListResponse(
        memberships=[
            UserGroupMembershipResponse.model_validate(m) for m in memberships
        ],
        total=total,
    )


@router.post(
    "/groups/{group_id}/members",
    response_model=UserGroupMembershipResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_group_member(
    group_id: UUID,
    membership_data: UserGroupMembershipCreate,
    session: AsyncSession = Depends(get_tenant_async_db),
    current_user: User = Depends(get_current_user),
) -> UserGroupMembershipResponse:
    """
    Add a user to a group on a specific resource.

    **Requires:** Superuser or admin on the resource
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only superusers can add group members",
        )

    # Verify group exists
    group_result = await session.execute(select(Group).where(Group.id == group_id))
    if not group_result.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Group {group_id} not found",
        )

    # Verify user exists
    user_result = await session.execute(
        select(User).where(User.id == membership_data.user_id)
    )
    if not user_result.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User {membership_data.user_id} not found",
        )

    # Verify resource exists
    resource_model = {
        "organization": Organization,
        "account": Account,
        "project": Project,
    }.get(membership_data.resource_type.value)

    if resource_model:
        resource_result = await session.execute(
            select(resource_model).where(
                resource_model.id == membership_data.resource_id
            )
        )
        if not resource_result.scalars().first():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"{membership_data.resource_type.value.capitalize()} {membership_data.resource_id} not found",
            )

    # Check for existing membership
    existing = await session.execute(
        select(UserGroupMembership).where(
            UserGroupMembership.user_id == membership_data.user_id,
            UserGroupMembership.group_id == group_id,
            UserGroupMembership.resource_id == membership_data.resource_id,
        )
    )
    if existing.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User is already a member of this group on this resource",
        )

    membership = UserGroupMembership(
        user_id=membership_data.user_id,
        group_id=group_id,
        resource_id=membership_data.resource_id,
        resource_type=membership_data.resource_type.value,
    )
    session.add(membership)
    await session.commit()
    await session.refresh(membership)

    logger.info(
        f"Added user {membership_data.user_id} to group {group_id} on resource {membership_data.resource_id}"
    )

    return UserGroupMembershipResponse.model_validate(membership)


@router.delete(
    "/groups/{group_id}/members/{user_id}/{resource_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def remove_group_member(
    group_id: UUID,
    user_id: int,
    resource_id: UUID,
    session: AsyncSession = Depends(get_tenant_async_db),
    current_user: User = Depends(get_current_user),
) -> None:
    """
    Remove a user from a group on a specific resource.

    **Requires:** Superuser or admin on the resource
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only superusers can remove group members",
        )

    result = await session.execute(
        select(UserGroupMembership).where(
            UserGroupMembership.user_id == user_id,
            UserGroupMembership.group_id == group_id,
            UserGroupMembership.resource_id == resource_id,
        )
    )
    membership = result.scalars().first()

    if not membership:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Membership not found for user {user_id} in group {group_id} on resource {resource_id}",
        )

    await session.delete(membership)
    await session.commit()

    logger.info(
        f"Removed user {user_id} from group {group_id} on resource {resource_id}"
    )

    return None


@router.get("/users/{user_id}/groups", response_model=UserGroupMembershipListResponse)
async def list_user_groups(
    user_id: int,
    resource_id: Optional[UUID] = Query(None, description="Filter by resource"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    session: AsyncSession = Depends(get_tenant_async_db),
    current_user: User = Depends(get_current_user),
) -> UserGroupMembershipListResponse:
    """List all groups a user belongs to."""
    # Verify user exists
    user_result = await session.execute(select(User).where(User.id == user_id))
    if not user_result.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User {user_id} not found",
        )

    query = (
        select(UserGroupMembership)
        .options(selectinload(UserGroupMembership.group))
        .where(UserGroupMembership.user_id == user_id)
    )
    count_query = select(func.count()).where(UserGroupMembership.user_id == user_id)

    if resource_id:
        query = query.where(UserGroupMembership.resource_id == resource_id)
        count_query = count_query.where(UserGroupMembership.resource_id == resource_id)

    count_result = await session.execute(count_query)
    total = count_result.scalar()

    result = await session.execute(query.offset(skip).limit(limit))
    memberships = result.scalars().all()

    return UserGroupMembershipListResponse(
        memberships=[
            UserGroupMembershipResponse.model_validate(m) for m in memberships
        ],
        total=total,
    )


# ============================================================================
# Current User RBAC
# ============================================================================


@router.get("/me", response_model=UserRbacResponse)
async def get_my_rbac(
    session: AsyncSession = Depends(get_tenant_async_db),
    current_user: User = Depends(get_current_user),
) -> UserRbacResponse:
    """
    Get the current user's complete RBAC information.

    Returns all role assignments, group memberships, and permission overrides
    for the authenticated user. This is typically called at login to cache
    the user's permissions client-side.
    """
    # Get role assignments
    role_result = await session.execute(
        select(UserRoleAssignment).where(UserRoleAssignment.user_id == current_user.id)
    )
    role_assignments = role_result.scalars().all()

    # Get group memberships with group details
    membership_result = await session.execute(
        select(UserGroupMembership)
        .options(
            selectinload(UserGroupMembership.group).selectinload(Group.permissions)
        )
        .where(UserGroupMembership.user_id == current_user.id)
    )
    group_memberships = membership_result.scalars().all()

    # Get permission overrides
    override_result = await session.execute(
        select(PermissionOverride).where(PermissionOverride.user_id == current_user.id)
    )
    permission_overrides = override_result.scalars().all()

    return UserRbacResponse(
        user_id=current_user.id,
        is_superuser=current_user.is_superuser,
        role_assignments=[
            UserRoleAssignmentResponse.model_validate(r) for r in role_assignments
        ],
        group_memberships=[
            UserGroupMembershipResponse.model_validate(m) for m in group_memberships
        ],
        permission_overrides=[
            PermissionOverrideResponse.model_validate(o) for o in permission_overrides
        ],
    )

"""RBAC (Role-Based Access Control) management endpoints."""

import logging
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func

from app.core.deps import get_current_user
from app.db.models import User
from app.db.models_rbac import Organization, Account, Project, UserRoleAssignment, PermissionOverride
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
    result = await session.execute(select(Organization).where(Organization.name == org_data.name))
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
        organizations=[OrganizationResponse.model_validate(org) for org in organizations],
        total=total,
    )


@router.get("/organizations/{org_id}", response_model=OrganizationResponse)
async def get_organization(
    org_id: UUID,
    session: AsyncSession = Depends(get_tenant_async_db),
    current_user: User = Depends(get_current_user),
) -> OrganizationResponse:
    """Get organization by ID."""
    result = await session.execute(select(Organization).where(Organization.id == org_id))
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


@router.post("/accounts", response_model=AccountResponse, status_code=status.HTTP_201_CREATED)
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
    org_result = await session.execute(select(Organization).where(Organization.id == account_data.organization_id))
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

    logger.info(f"Account '{account.name}' created in org {account.organization_id} by user {current_user.id}")

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


@router.post("/projects", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
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
    account_result = await session.execute(select(Account).where(Account.id == project_data.account_id))
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

    logger.info(f"Project '{project.name}' created in account {project.account_id} by user {current_user.id}")

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
    user_result = await session.execute(select(User).where(User.id == assignment_data.user_id))
    if not user_result.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User {assignment_data.user_id} not found",
        )

    # Verify resource exists based on type
    if assignment_data.resource_type.value == "organization":
        resource_result = await session.execute(select(Organization).where(Organization.id == assignment_data.resource_id))
    elif assignment_data.resource_type.value == "account":
        resource_result = await session.execute(select(Account).where(Account.id == assignment_data.resource_id))
    elif assignment_data.resource_type.value == "project":
        resource_result = await session.execute(select(Project).where(Project.id == assignment_data.resource_id))
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
        logger.info(f"Updated role assignment for user {assignment_data.user_id} to {assignment_data.role.value}")
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
        count_query = count_query.where(UserRoleAssignment.resource_type == resource_type)

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
    user_result = await session.execute(select(User).where(User.id == override_data.user_id))
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
        resource_result = await session.execute(select(resource_model).where(resource_model.id == override_data.resource_id))
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
        logger.info(f"Updated permission override for user {override_data.user_id} on resource {override_data.resource_id}")
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
        logger.info(f"Created permission override for user {override_data.user_id} on resource {override_data.resource_id}")
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
        count_query = count_query.where(PermissionOverride.resource_type == resource_type)

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

    logger.info(f"Updated permission override for user {user_id} on resource {resource_id}")

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

    logger.info(f"Deleted permission override for user {user_id} on resource {resource_id}")

    return None

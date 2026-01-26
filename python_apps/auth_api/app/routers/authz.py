"""Authorization (authz) endpoints using OPA for policy evaluation."""

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.db.models import User
from app.db.models_rbac import (
    UserRoleAssignment,
    PermissionOverride,
    UserGroupMembership,
    Group,
)
from app.db.tenant_db import get_tenant_async_db
from app.schemas.rbac import AccessCheckRequest, AccessCheckResponse
from app.services.opa_service import get_opa_service

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/check_access", response_model=AccessCheckResponse)
async def check_access(
    request: AccessCheckRequest,
    session: AsyncSession = Depends(get_tenant_async_db),
) -> AccessCheckResponse:
    """
    Check if a user has access to perform an action on a resource.

    This endpoint:
    1. Validates the user exists and gets their status
    2. Checks if user status is 'active' (security requirement)
    3. Retrieves user's role assignments
    4. Calls OPA to evaluate the policy
    5. Returns allowed/denied with reason

    **Security:** Only ACTIVE users can access resources. Inactive, suspended,
    or pending users are immediately denied regardless of role assignments.

    Args:
        request: Access check request with user_id, action, and resource
        session: Database session

    Returns:
        AccessCheckResponse with allowed status and optional deny reason

    Raises:
        HTTPException: If user not found or OPA service unavailable
    """
    # Step 1: Get user and validate status
    result = await session.execute(select(User).where(User.id == request.user_id))
    user = result.scalars().first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User {request.user_id} not found",
        )

    # Step 2: SECURITY CHECK - User must be active
    # This is the critical security fix - we check status BEFORE checking permissions
    if user.status != "active":
        logger.warning(
            f"Access denied for user {user.id} ({user.email}) - User status is '{user.status}', not 'active'"
        )
        return AccessCheckResponse(
            allowed=False,
            deny_reason="user_not_active",
            user_status=user.status,
        )

    # Step 3: Get user's role assignments (with role relationship for base_type)
    assignments_result = await session.execute(
        select(UserRoleAssignment)
        .options(selectinload(UserRoleAssignment.role_ref))
        .where(UserRoleAssignment.user_id == request.user_id)
    )
    assignments = assignments_result.scalars().all()

    # Convert assignments to OPA format
    # Use role_ref.base_type if available, fall back to legacy role string
    user_assignments = [
        {
            "role": assignment.role_ref.base_type
            if assignment.role_ref
            else assignment.role,
            "resource_type": assignment.resource_type,
            "resource_id": str(assignment.resource_id),
        }
        for assignment in assignments
    ]

    logger.info(
        f"User {user.id} ({user.email}) has {len(user_assignments)} role assignments"
    )

    # Step 3.5: Get user's permission overrides for this resource
    overrides_result = await session.execute(
        select(PermissionOverride).where(
            PermissionOverride.user_id == request.user_id,
            PermissionOverride.resource_id == request.resource.id,
        )
    )
    override = overrides_result.scalars().first()

    # Convert overrides to OPA format
    permission_overrides = None
    if override:
        permission_overrides = {
            "resource_id": str(override.resource_id),
            "allow": override.allow_actions or [],
            "deny": override.deny_actions or [],
        }
        logger.info(
            f"User {user.id} has permission overrides on resource {override.resource_id}: "
            f"allow={override.allow_actions}, deny={override.deny_actions}"
        )

    # Step 3.6: Get user's group memberships for this resource
    # Include groups at the resource level and parent levels (org, account)
    group_memberships_result = await session.execute(
        select(UserGroupMembership)
        .options(
            selectinload(UserGroupMembership.group).selectinload(Group.permissions)
        )
        .where(UserGroupMembership.user_id == request.user_id)
    )
    group_memberships = group_memberships_result.scalars().all()

    # Convert group memberships to OPA format
    user_groups = []
    for membership in group_memberships:
        group = membership.group
        if group:
            group_data = {
                "group_id": str(group.id),
                "group_name": group.name,
                "resource_id": str(membership.resource_id),
                "resource_type": membership.resource_type,
                "permissions": [],
            }
            # Include group permissions
            if group.permissions:
                for perm in group.permissions:
                    group_data["permissions"].append(
                        {
                            "service_name": perm.service_name,
                            "allow_actions": perm.allow_actions or [],
                            "deny_actions": perm.deny_actions or [],
                        }
                    )
            user_groups.append(group_data)

    if user_groups:
        logger.info(f"User {user.id} has {len(user_groups)} group memberships")

    # Step 4: Call OPA for policy evaluation
    # Convert resource to dict and ensure all UUIDs are strings for JSON serialization
    resource_dict = request.resource.dict()
    resource_dict["id"] = str(resource_dict["id"])
    resource_dict["organization_id"] = str(resource_dict["organization_id"])
    if resource_dict.get("account_id"):
        resource_dict["account_id"] = str(resource_dict["account_id"])

    opa_service = get_opa_service()
    opa_result = await opa_service.check_access(
        user_id=user.id,
        user_status=user.status,
        user_assignments=user_assignments,
        action=request.action,
        resource=resource_dict,
        permission_overrides=permission_overrides,
        user_groups=user_groups if user_groups else None,
    )

    # Step 5: Return result
    return AccessCheckResponse(
        allowed=opa_result["allowed"],
        deny_reason=opa_result.get("deny_reason"),
        user_status=user.status,
    )


@router.get("/health")
async def authz_health_check():
    """
    Health check for authorization service.

    Checks:
    - OPA service is reachable
    - Database connection is working

    Returns:
        Health status
    """
    opa_service = get_opa_service()
    opa_healthy = await opa_service.health_check()

    return {
        "status": "healthy" if opa_healthy else "degraded",
        "opa": "healthy" if opa_healthy else "unhealthy",
        "message": (
            "Authorization service is operational"
            if opa_healthy
            else "OPA service unavailable"
        ),
    }

"""Admin endpoints for user management."""

from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel, Field
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.core.logging import logger
from app.core.deps import get_current_admin_or_superuser, get_current_superuser
from app.db.activity_log import log_user_activity
from app.db.models import User, UserStatus, Session as UserSession
from app.db.orm import get_async_session

router = APIRouter()


# ============================================================================
# Request/Response Schemas
# ============================================================================


class UserStatusUpdateRequest(BaseModel):
    """Request to update user status."""

    status: str = Field(
        ...,
        description="New status for the user",
        pattern="^(active|inactive|suspended|pending)$",
    )
    reason: Optional[str] = Field(
        None, description="Reason for status change (for audit log)"
    )


class UserStatusResponse(BaseModel):
    """Response for user status operations."""

    user_id: int
    email: str
    old_status: str
    new_status: str
    changed_by: int
    changed_at: str
    reason: Optional[str] = None


class UserSessionInfo(BaseModel):
    """Information about a user's sessions."""

    user_id: int
    email: str
    total_sessions: int
    active_sessions: int
    sessions: list[dict]


# ============================================================================
# User Status Management Endpoints
# ============================================================================


@router.post("/users/{user_id}/status", response_model=UserStatusResponse)
async def update_user_status(
    request: Request,
    user_id: int,
    status_update: UserStatusUpdateRequest,
    current_user: User = Depends(get_current_superuser),
    session: AsyncSession = Depends(get_async_session),
):
    """
    Update a user's account status (superuser only).

    Status values:
    - active: Account is enabled, user can log in
    - inactive: Account is disabled, user cannot log in
    - suspended: Account is temporarily suspended, user cannot log in
    - pending: Account is awaiting activation, user cannot log in

    Note: This is for account lifecycle management, not session state.
    Use GET /admin/users/{user_id}/sessions to check if user is signed in.
    """
    logger.info(
        f"Superuser {current_user.email} (ID: {current_user.id}) "
        f"updating status for user ID {user_id} to '{status_update.status}'"
    )

    # Prevent self-modification
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot modify your own account status",
        )

    # Get the target user
    result = await session.execute(select(User).where(User.id == user_id))
    target_user = result.scalars().first()

    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found",
        )

    # Store old status for response
    old_status = target_user.status

    # Validate status value
    try:
        new_status = UserStatus(status_update.status)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status value: {status_update.status}",
        )

    # Update user status
    now = datetime.now(timezone.utc)
    stmt = (
        update(User)
        .where(User.id == user_id)
        .values(status=new_status.value, updated_at=now)
    )
    await session.execute(stmt)
    await session.commit()

    # Log the activity
    await log_user_activity(
        session,
        current_user.id,
        "admin_changed_user_status",
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        details={
            "target_user_id": user_id,
            "target_user_email": target_user.email,
            "old_status": old_status,
            "new_status": new_status.value,
            "reason": status_update.reason,
        },
    )

    # Also log on the target user's activity
    await log_user_activity(
        session,
        user_id,
        "status_changed_by_admin",
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        details={
            "changed_by_user_id": current_user.id,
            "changed_by_email": current_user.email,
            "old_status": old_status,
            "new_status": new_status.value,
            "reason": status_update.reason,
        },
    )

    logger.info(
        f"User {target_user.email} (ID: {user_id}) status changed "
        f"from '{old_status}' to '{new_status.value}' by {current_user.email}"
    )

    return UserStatusResponse(
        user_id=user_id,
        email=target_user.email,
        old_status=old_status,
        new_status=new_status.value,
        changed_by=current_user.id,
        changed_at=now.isoformat(),
        reason=status_update.reason,
    )


@router.post("/users/{user_id}/suspend")
async def suspend_user(
    request: Request,
    user_id: int,
    reason: Optional[str] = None,
    current_user: User = Depends(get_current_superuser),
    session: AsyncSession = Depends(get_async_session),
):
    """
    Suspend a user account (superuser only).

    This is a convenience endpoint that sets status to 'suspended'.
    Suspended users cannot log in until their account is reactivated.
    """
    status_update = UserStatusUpdateRequest(status="suspended", reason=reason)
    return await update_user_status(
        request, user_id, status_update, current_user, session
    )


@router.post("/users/{user_id}/activate")
async def activate_user(
    request: Request,
    user_id: int,
    reason: Optional[str] = None,
    current_user: User = Depends(get_current_superuser),
    session: AsyncSession = Depends(get_async_session),
):
    """
    Activate a user account (superuser only).

    This is a convenience endpoint that sets status to 'active'.
    Active users can log in normally.
    """
    status_update = UserStatusUpdateRequest(status="active", reason=reason)
    return await update_user_status(
        request, user_id, status_update, current_user, session
    )


@router.post("/users/{user_id}/deactivate")
async def deactivate_user(
    request: Request,
    user_id: int,
    reason: Optional[str] = None,
    current_user: User = Depends(get_current_superuser),
    session: AsyncSession = Depends(get_async_session),
):
    """
    Deactivate a user account (superuser only).

    This is a convenience endpoint that sets status to 'inactive'.
    Inactive users cannot log in until their account is reactivated.
    """
    status_update = UserStatusUpdateRequest(status="inactive", reason=reason)
    return await update_user_status(
        request, user_id, status_update, current_user, session
    )


# ============================================================================
# Session Management Endpoints
# ============================================================================


@router.get("/users/{user_id}/sessions", response_model=UserSessionInfo)
async def get_user_sessions(
    user_id: int,
    current_user: User = Depends(get_current_admin_or_superuser),
    session: AsyncSession = Depends(get_async_session),
):
    """
    Get information about a user's active sessions (admin only).

    This shows whether the user is currently signed in and from which devices.
    """
    # Get the target user
    result = await session.execute(select(User).where(User.id == user_id))
    target_user = result.scalars().first()

    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found",
        )

    # Get all sessions for this user
    result = await session.execute(
        select(UserSession).where(UserSession.user_id == user_id)
    )
    all_sessions = result.scalars().all()

    # Filter active sessions (not expired and is_active=True)
    now = datetime.now(timezone.utc)
    active_sessions = [s for s in all_sessions if s.is_active and s.expires_at > now]

    # Build session info
    session_list = []
    for s in all_sessions:
        is_active = s.is_active and s.expires_at > now
        session_list.append(
            {
                "id": s.id,
                "created_at": s.created_at.isoformat() if s.created_at else None,
                "expires_at": s.expires_at.isoformat() if s.expires_at else None,
                "is_active": is_active,
                "ip_address": s.ip_address,
                "user_agent": s.user_agent,
            }
        )

    return UserSessionInfo(
        user_id=user_id,
        email=target_user.email,
        total_sessions=len(all_sessions),
        active_sessions=len(active_sessions),
        sessions=session_list,
    )


@router.post("/users/{user_id}/revoke-sessions")
async def revoke_user_sessions(
    request: Request,
    user_id: int,
    current_user: User = Depends(get_current_superuser),
    session: AsyncSession = Depends(get_async_session),
):
    """
    Revoke all active sessions for a user (superuser only).

    This will force the user to log in again on all devices.
    Useful when suspending an account or responding to security incidents.
    """
    logger.info(
        f"Superuser {current_user.email} (ID: {current_user.id}) "
        f"revoking all sessions for user ID {user_id}"
    )

    # Get the target user
    result = await session.execute(select(User).where(User.id == user_id))
    target_user = result.scalars().first()

    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found",
        )

    # Revoke all sessions
    stmt = (
        update(UserSession)
        .where(UserSession.user_id == user_id)
        .values(is_active=False)
    )
    result = await session.execute(stmt)
    await session.commit()

    revoked_count = result.rowcount

    # Log the activity
    await log_user_activity(
        session,
        current_user.id,
        "admin_revoked_user_sessions",
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        details={
            "target_user_id": user_id,
            "target_user_email": target_user.email,
            "sessions_revoked": revoked_count,
        },
    )

    logger.info(
        f"Revoked {revoked_count} sessions for user {target_user.email} (ID: {user_id})"
    )

    return {
        "user_id": user_id,
        "email": target_user.email,
        "sessions_revoked": revoked_count,
        "message": f"Successfully revoked {revoked_count} session(s)",
    }

import re
from datetime import datetime, timezone
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.core.logging import logger
from app.core.security import get_current_user, get_password_hash, verify_password
from app.db.activity_log import log_user_activity
from app.db.models import User
from app.db.orm import get_async_session

router = APIRouter()


class SecureChangePasswordRequest(BaseModel):
    """Secure change password request schema that requires current password."""

    current_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=9)

    @field_validator("new_password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        """Validate password strength."""
        if len(v) < 9:
            raise ValueError("Password must be at least 9 characters")

        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one digit")
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", v):
            raise ValueError("Password must contain at least one special character")

        return v


@router.post("/change-password-user")
async def change_password_user(
    request: Request,
    change_data: SecureChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
):
    """Change user password with current password verification."""
    user_id = current_user.id
    user_email = current_user.email

    logger.info(
        f"User-initiated password change requested for user {user_email} (ID: {user_id})"
    )

    # Verify current password
    if not verify_password(change_data.current_password, current_user.hashed_password):
        logger.warning(f"Invalid current password provided for user {user_email}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )

    # Check if new password is the same as current password
    if verify_password(change_data.new_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be different from current password",
        )

    try:
        # Update password
        now = datetime.now(timezone.utc)
        stmt = (
            update(User)
            .where(User.id == user_id)
            .values(
                hashed_password=get_password_hash(change_data.new_password),
                is_password_temporary=False,
                temporary_hashed_password=None,
                temporary_password_expiry=None,
                failed_login_attempts=0,  # Reset failed attempts on successful password change
                locked_until=None,  # Unlock account if it was locked
                updated_at=now,
            )
        )
        await session.execute(stmt)
        await session.commit()

        # Log activity
        await log_user_activity(
            session,
            user_id,
            "password_changed_user",
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )

        logger.info(f"Password successfully changed for user {user_email}")

        # Send password change notification
        try:
            from app.services.email_service import send_password_changed_notification

            name = current_user.full_name.split()[0] if current_user.full_name else ""
            await send_password_changed_notification(current_user.email, name)
        except Exception as e:
            logger.error(f"Error sending password change notification: {e}")

        return {"message": "Password successfully changed"}

    except Exception as e:
        logger.error(f"Error changing password for user {user_email}: {e}")
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to change password",
        )

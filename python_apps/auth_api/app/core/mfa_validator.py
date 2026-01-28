"""Simple MFA validation utility."""

from app.db.models import User
from fastapi import HTTPException, status


def ensure_at_least_one_mfa(user: User, attempting_to_disable: str) -> None:
    """
    Ensures user has at least one MFA method enabled.
    Call this BEFORE disabling any MFA method.

    Args:
        user: User object
        attempting_to_disable: 'email' | 'sms' | 'totp' | 'biometric'

    Raises:
        HTTPException if this is the last MFA method
    """
    # Count what would remain if we disable this method
    remaining = 0

    if attempting_to_disable != "email" and user.email_mfa_enabled:
        remaining += 1
    if attempting_to_disable != "sms" and user.sms_mfa_enabled:
        remaining += 1
    if attempting_to_disable != "totp" and user.mfa_enabled:
        remaining += 1
    if attempting_to_disable != "biometric" and user.biometric_mfa_enabled:
        remaining += 1

    if remaining == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot disable. At least one MFA method must remain enabled.",
        )

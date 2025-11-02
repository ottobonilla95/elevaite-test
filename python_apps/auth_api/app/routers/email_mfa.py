from fastapi import APIRouter, HTTPException, Request, status, Depends
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import User
from app.core.config import settings
from app.core.logging import logger
from app.core.deps import get_current_user
from app.db.orm import get_async_session
from app.core.password_utils import normalize_email
from app.services.email_mfa import email_mfa_service
from app.schemas.mfa import (
    EmailMFASetupRequest,
    EmailMFAVerifyRequest,
    EmailMFAResponse,
)
from app.core.mfa_validator import ensure_at_least_one_mfa

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


@router.post("/setup", response_model=EmailMFAResponse)
@limiter.limit(f"{settings.RATE_LIMIT_PER_MINUTE}/minute")
async def setup_email_mfa(
    request: Request,
    mfa_data: EmailMFASetupRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    try:
        print(f"🔍 Email MFA setup request for user {current_user.id}")
        print(f"  - Current email_mfa_enabled: {current_user.email_mfa_enabled}")
        result = await email_mfa_service.setup_email_mfa(current_user, db)
        return EmailMFAResponse(message=result["message"], email=result.get("email"))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during email MFA setup: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Email MFA setup service error",
        )


@router.post("/send-code", response_model=EmailMFAResponse)
@limiter.limit(f"{settings.RATE_LIMIT_PER_MINUTE}/minute")
async def send_mfa_code(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """Send MFA code to user's email."""
    logger.info(f"Email MFA code request for user {current_user.id}")

    try:
        result = await email_mfa_service.send_mfa_code(current_user, db)
        return EmailMFAResponse(message=result["message"], email=result.get("email"))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during email MFA code sending: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Email MFA code sending service error",
        )


@router.post("/verify", response_model=EmailMFAResponse)
@limiter.limit(f"{settings.RATE_LIMIT_PER_MINUTE}/minute")
async def verify_mfa_code(
    request: Request,
    verify_data: EmailMFAVerifyRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """Verify email MFA code."""
    logger.info(f"Email MFA verification request for user {current_user.id}")

    try:
        result = await email_mfa_service.verify_mfa_code(
            current_user, verify_data.mfa_code, db
        )
        return EmailMFAResponse(message=result["message"], email=None)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during email MFA verification: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Email MFA verification service error",
        )


@router.post("/disable", response_model=EmailMFAResponse)
@limiter.limit(f"{settings.RATE_LIMIT_PER_MINUTE}/minute")
async def disable_email_mfa(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """Disable email MFA for the current user."""
    logger.info(f"Email MFA disable request for user {current_user.id}")

    try:
        ensure_at_least_one_mfa(current_user, 'email')
        result = await email_mfa_service.disable_email_mfa(current_user, db)
        return EmailMFAResponse(message=result["message"], email=None)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during email MFA disable: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Email MFA disable service error",
        )


@router.get("/status", response_model=EmailMFAResponse)
async def get_email_mfa_status(
    current_user: User = Depends(get_current_user),
):
    """Get email MFA status for the current user."""
    logger.info(f"Email MFA status request for user {current_user.id}")

    try:
        status_message = "enabled" if current_user.email_mfa_enabled else "disabled"
        return EmailMFAResponse(
            message=f"Email MFA is {status_message}",
            email=current_user.email if current_user.email_mfa_enabled else None,
        )
    except Exception as e:
        logger.error(f"Unexpected error getting email MFA status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Email MFA status service error",
        )


@router.get("/grace-period")
@limiter.limit(f"{settings.RATE_LIMIT_PER_MINUTE}/minute")
async def get_grace_period_info(
    request: Request,
    current_user: User = Depends(get_current_user),
):
    """Get grace period information for the current user."""
    logger.info(f"Grace period info request for user {current_user.id}")

    try:
        grace_info = email_mfa_service.get_grace_period_info(current_user)
        return grace_info
    except Exception as e:
        logger.error(f"Unexpected error during grace period info retrieval: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Grace period info service error",
        )


@router.post("/send-login-code", response_model=EmailMFAResponse)
@limiter.limit(f"{settings.RATE_LIMIT_PER_MINUTE}/minute")
async def send_email_mfa_code_for_login(
    request: Request,
    login_data: dict,
    db: AsyncSession = Depends(get_async_session),
):
    """Send email MFA code during login process (before authentication)."""
    email = login_data.get("email")
    password = login_data.get("password")

    if not email or not password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email and password are required",
        )

    email = normalize_email(email)

    logger.info(f"Email MFA login code request for email: {email}")

    # Verify credentials first
    from app.services.auth_orm import authenticate_user, get_user_by_email

    try:
        # This will throw an exception if credentials are wrong or if MFA is required
        await authenticate_user(db, email, password, None)
        # If we get here without exception, no MFA is required
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="MFA is not required for this user",
        )
    except HTTPException as e:
        error_detail = str(e.detail)
        if "Email code required" in error_detail or (
            "MFA code required" in error_detail and "Email" in error_detail
        ):
            # This is expected - get the user and send the code
            user = await get_user_by_email(db, email)
            if not user or not user.email_mfa_enabled:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email MFA is not enabled for this user",
                )

            # Send the email MFA code
            try:
                result = await email_mfa_service.send_mfa_code(user, db)
                return EmailMFAResponse(
                    message=result["message"], email=result.get("email")
                )
            except Exception as send_error:
                logger.error(f"Failed to send email MFA code: {send_error}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to send email MFA code",
                )
        else:
            # Re-raise other authentication errors (invalid credentials, etc.)
            raise


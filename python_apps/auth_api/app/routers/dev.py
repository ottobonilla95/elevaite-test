"""Dev endpoints for testing - DO NOT USE IN PRODUCTION."""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy import select

from app.db.tenant_db import get_tenant_session
from app.db.models import User
from app.core.config import settings
from app.core.logging import logger

router = APIRouter()


class EnableMFARequest(BaseModel):
    """Request to enable MFA for a user."""

    email: EmailStr
    mfa_type: str = "email"  # "email", "totp", or "sms"
    phone_number: str | None = None  # Required for SMS MFA


class EnableMFAResponse(BaseModel):
    """Response after enabling MFA."""

    success: bool
    message: str
    mfa_type: str
    totp_secret: str | None = None  # Only for TOTP


@router.post("/enable-mfa", response_model=EnableMFAResponse)
async def dev_enable_mfa(request: EnableMFARequest) -> EnableMFAResponse:
    """
    DEV ONLY: Enable MFA for a user without verification.

    This endpoint is for testing purposes only.
    It directly enables MFA on a user account.

    Supported MFA types:
    - email: Enables email MFA (simplest, no external setup)
    - totp: Enables TOTP MFA with a test secret
    - sms: Enables SMS MFA (requires phone_number)
    """
    if not settings.DEBUG:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This endpoint is only available in development mode",
        )

    async with get_tenant_session() as session:
        # Find user by email
        result = await session.execute(
            select(User).where(User.email == request.email.lower())
        )
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with email {request.email} not found",
            )

        totp_secret = None

        if request.mfa_type == "email":
            user.email_mfa_enabled = True
            message = f"Email MFA enabled for {user.email}"

        elif request.mfa_type == "totp":
            import pyotp

            # Generate a TOTP secret
            totp_secret = pyotp.random_base32()
            user.mfa_secret = totp_secret
            user.mfa_enabled = True
            message = f"TOTP MFA enabled for {user.email}. Use the secret to configure your authenticator app."

        elif request.mfa_type == "sms":
            if not request.phone_number:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="phone_number is required for SMS MFA",
                )
            user.phone_number = request.phone_number
            user.phone_verified = True
            user.sms_mfa_enabled = True
            message = (
                f"SMS MFA enabled for {user.email} with phone {request.phone_number}"
            )

        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid mfa_type: {request.mfa_type}. Use 'email', 'totp', or 'sms'",
            )

        await session.commit()
        logger.info(f"DEV: {message}")

        return EnableMFAResponse(
            success=True,
            message=message,
            mfa_type=request.mfa_type,
            totp_secret=totp_secret,
        )


class DisableMFARequest(BaseModel):
    """Request to disable MFA for a user."""

    email: EmailStr


class DisableMFAResponse(BaseModel):
    """Response after disabling MFA."""

    success: bool
    message: str


@router.post("/disable-mfa", response_model=DisableMFAResponse)
async def dev_disable_mfa(request: DisableMFARequest) -> DisableMFAResponse:
    """
    DEV ONLY: Disable all MFA for a user.

    This endpoint is for testing purposes only.
    """
    if not settings.DEBUG:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This endpoint is only available in development mode",
        )

    async with get_tenant_session() as session:
        result = await session.execute(
            select(User).where(User.email == request.email.lower())
        )
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with email {request.email} not found",
            )

        # Disable all MFA types
        user.mfa_enabled = False
        user.mfa_secret = None
        user.email_mfa_enabled = False
        user.email_mfa_code = None
        user.email_mfa_code_expires = None
        user.sms_mfa_enabled = False
        user.phone_verified = False
        user.biometric_mfa_enabled = False

        await session.commit()
        logger.info(f"DEV: All MFA disabled for {user.email}")

        return DisableMFAResponse(
            success=True,
            message=f"All MFA disabled for {user.email}",
        )


class GetUserMFAStatusRequest(BaseModel):
    """Request to get MFA status for a user."""

    email: EmailStr


class GetUserMFAStatusResponse(BaseModel):
    """Response with user MFA status."""

    email: str
    email_mfa_enabled: bool
    totp_mfa_enabled: bool
    sms_mfa_enabled: bool
    biometric_mfa_enabled: bool
    phone_number: str | None
    has_any_mfa: bool


@router.post("/mfa-status", response_model=GetUserMFAStatusResponse)
async def dev_get_mfa_status(
    request: GetUserMFAStatusRequest,
) -> GetUserMFAStatusResponse:
    """
    DEV ONLY: Get MFA status for a user.
    """
    if not settings.DEBUG:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This endpoint is only available in development mode",
        )

    async with get_tenant_session() as session:
        result = await session.execute(
            select(User).where(User.email == request.email.lower())
        )
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with email {request.email} not found",
            )

        has_any_mfa = (
            user.email_mfa_enabled
            or user.mfa_enabled
            or user.sms_mfa_enabled
            or user.biometric_mfa_enabled
        )

        return GetUserMFAStatusResponse(
            email=user.email,
            email_mfa_enabled=user.email_mfa_enabled,
            totp_mfa_enabled=user.mfa_enabled,
            sms_mfa_enabled=user.sms_mfa_enabled,
            biometric_mfa_enabled=user.biometric_mfa_enabled,
            phone_number=user.phone_number,
            has_any_mfa=has_any_mfa,
        )

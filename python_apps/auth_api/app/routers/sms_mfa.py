from fastapi import APIRouter, HTTPException, Request, status, Depends
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.logging import logger
from app.core.deps import get_current_user
from app.db.orm import get_async_session
from app.services.sms_mfa import sms_mfa_service
from app.schemas.mfa import SMSMFASetupRequest, SMSMFAVerifyRequest, SMSMFAResponse
from app.db.models import User

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


@router.post("/setup", response_model=SMSMFAResponse)
@limiter.limit(f"{settings.RATE_LIMIT_PER_MINUTE}/minute")
async def setup_sms_mfa(
    request: Request,
    mfa_data: SMSMFASetupRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    logger.info(f"SMS MFA setup request for user {current_user.id}")

    try:
        result = await sms_mfa_service.setup_sms_mfa(
            current_user, mfa_data.phone_number, db
        )
        return SMSMFAResponse(message=result["message"], message_id=None)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during SMS MFA setup: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="SMS MFA setup service error",
        )


@router.post("/send-code", response_model=SMSMFAResponse)
@limiter.limit(f"{settings.RATE_LIMIT_PER_MINUTE}/minute")
async def send_mfa_code(
    request: Request,
    current_user: User = Depends(get_current_user),
):
    logger.info(f"SMS MFA code request for user {current_user.id}")

    try:
        result = await sms_mfa_service.send_mfa_code(current_user)
        return SMSMFAResponse(
            message=result["message"], message_id=result.get("message_id")
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during SMS MFA code sending: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="SMS MFA code sending service error",
        )


@router.post("/verify", response_model=SMSMFAResponse)
@limiter.limit(f"{settings.RATE_LIMIT_PER_MINUTE}/minute")
async def verify_mfa_code(
    request: Request,
    verify_data: SMSMFAVerifyRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    logger.info(f"SMS MFA verification request for user {current_user.id}")

    try:
        result = await sms_mfa_service.verify_mfa_code(
            current_user, verify_data.mfa_code, db
        )
        return SMSMFAResponse(message=result["message"], message_id=None)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during SMS MFA verification: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="SMS MFA verification service error",
        )


@router.post("/disable", response_model=SMSMFAResponse)
@limiter.limit(f"{settings.RATE_LIMIT_PER_MINUTE}/minute")
async def disable_sms_mfa(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    logger.info(f"SMS MFA disable request for user {current_user.id}")

    try:
        result = await sms_mfa_service.disable_sms_mfa(current_user, db)
        return SMSMFAResponse(message=result["message"], message_id=None)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during SMS MFA disable: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="SMS MFA disable service error",
        )

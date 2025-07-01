import secrets
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Optional
import boto3
from botocore.exceptions import ClientError
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.logging import logger
from app.db.models import User


class InMemoryMFACache:
    def __init__(self):
        self._cache: Dict[str, tuple] = {}  # key -> (value, expiry_time)

    async def setex(self, key: str, expires_in: int, value: str):
        expiry_time = datetime.now() + timedelta(seconds=expires_in)
        self._cache[key] = (value, expiry_time)

    async def get(self, key: str) -> Optional[str]:
        if key not in self._cache:
            return None

        value, expiry_time = self._cache[key]
        if datetime.now() > expiry_time:
            del self._cache[key]
            return None

        return value

    async def delete(self, key: str):
        if key in self._cache:
            del self._cache[key]


# Global cache instance
mfa_cache = InMemoryMFACache()


class SMSMFAService:
    def __init__(self):
        self.region = settings.AWS_REGION
        self.sns_client = boto3.client("sns", region_name=self.region)

    def _generate_mfa_code(self) -> str:
        return f"{secrets.randbelow(1000000):06d}"

    async def _store_mfa_code(self, user_id: int, code: str, expires_in: int = 300):
        key = f"mfa_code:{user_id}"
        await mfa_cache.setex(key, expires_in, code)

    async def _get_mfa_code(self, user_id: int) -> Optional[str]:
        key = f"mfa_code:{user_id}"
        return await mfa_cache.get(key)

    async def _delete_mfa_code(self, user_id: int):
        key = f"mfa_code:{user_id}"
        await mfa_cache.delete(key)

    async def setup_sms_mfa(
        self, user: User, phone_number: str, db: AsyncSession
    ) -> dict:
        if not phone_number:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Phone number is required for SMS MFA",
            )

        # Update user with phone number and enable SMS MFA
        user.phone_number = phone_number
        user.sms_mfa_enabled = True
        user.phone_verified = False  # Will be verified when they confirm first code

        await db.commit()
        await db.refresh(user)

        logger.info(f"SMS MFA setup for user {user.id}")
        return {"message": "SMS MFA enabled successfully"}

    async def send_mfa_code(self, user: User) -> dict:
        if not user.sms_mfa_enabled:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="SMS MFA is not enabled for this user",
            )

        if not user.phone_number:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No phone number configured for SMS MFA",
            )

        # Generate and store MFA code
        mfa_code = self._generate_mfa_code()
        await self._store_mfa_code(user.id, mfa_code)

        # Send SMS via AWS SNS
        try:
            message = f"Your verification code is: {mfa_code}. This code expires in 5 minutes."

            response = self.sns_client.publish(
                PhoneNumber=user.phone_number,
                Message=message,
                MessageAttributes={
                    "AWS.SNS.SMS.SMSType": {
                        "DataType": "String",
                        "StringValue": "Transactional",
                    }
                },
            )

            logger.info(f"SMS MFA code sent to user {user.id}")
            return {
                "message": "MFA code sent successfully",
                "message_id": response.get("MessageId"),
            }

        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            error_message = e.response["Error"]["Message"]
            logger.error(f"SMS sending failed: {error_code} - {error_message}")

            if error_code == "InvalidParameter":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid phone number format",
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to send SMS",
                )

    async def verify_mfa_code(
        self, user: User, provided_code: str, db: AsyncSession
    ) -> dict:
        if not user.sms_mfa_enabled:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="SMS MFA is not enabled for this user",
            )

        # Get stored code
        stored_code = await self._get_mfa_code(user.id)
        if not stored_code:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No MFA code found or code has expired",
            )

        # Verify code
        if provided_code != stored_code:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid MFA code"
            )

        # Mark phone as verified if this is first successful verification
        if not user.phone_verified:
            user.phone_verified = True
            await db.commit()

        # Delete used code
        await self._delete_mfa_code(user.id)

        logger.info(f"MFA verification successful for user {user.id}")
        return {"message": "MFA verification successful"}

    async def disable_sms_mfa(self, user: User, db: AsyncSession) -> dict:
        user.sms_mfa_enabled = False
        user.phone_verified = False

        # Clean up any pending codes
        await self._delete_mfa_code(user.id)

        await db.commit()
        await db.refresh(user)

        logger.info(f"SMS MFA disabled for user {user.id}")
        return {"message": "SMS MFA disabled successfully"}


sms_mfa_service = SMSMFAService()

import secrets
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Optional
import boto3
from botocore.exceptions import ClientError, NoCredentialsError
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
        self.sender_id = getattr(settings, "SMS_SENDER_ID", None)

        try:
            logger.info("Initializing AWS SNS client for SMS MFA...")
            self.sns_client = boto3.client("sns", region_name=self.region)
            logger.info("AWS SNS client initialized successfully")

            self.sns_client.get_caller_identity = boto3.client(  # type: ignore
                "sts", region_name=self.region
            ).get_caller_identity

        except (NoCredentialsError, ClientError) as e:
            logger.error(f"Failed to initialize AWS SNS client: {e}")
            logger.error("SMS MFA will not function without proper AWS credentials")
            self.sns_client = None
        except Exception as e:
            logger.error(f"Unexpected error initializing SNS client: {e}")
            self.sns_client = None

    def _generate_mfa_code(self) -> str:
        """Generate a secure 6-digit MFA code."""
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

    async def _send_sms(self, phone_number: str, message: str) -> Optional[str]:
        if not self.sns_client:
            logger.error("SNS client not initialized - cannot send SMS")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="SMS service not available",
            )

        try:
            message_attributes = {}
            if self.sender_id:
                message_attributes["AWS.SNS.SMS.SenderID"] = {
                    "DataType": "String",
                    "StringValue": self.sender_id,
                }

            logger.info(f"Sending SMS to {phone_number[:3]}***{phone_number[-4:]}")
            response = self.sns_client.publish(
                PhoneNumber=phone_number,
                Message=message,
                MessageAttributes=message_attributes,
            )

            message_id = response.get("MessageId")
            logger.info(f"SMS sent successfully, MessageId: {message_id}")
            return message_id

        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            error_message = e.response["Error"]["Message"]
            logger.error(f"AWS SNS error ({error_code}): {error_message}")

            if error_code == "InvalidParameter":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid phone number format",
                )
            elif error_code == "OptedOut":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Phone number has opted out of SMS messages",
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to send SMS",
                )
        except Exception as e:
            logger.error(f"Unexpected error sending SMS: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to send SMS",
            )

    async def setup_sms_mfa(
        self, user: User, phone_number: str, db: AsyncSession
    ) -> dict:
        if not phone_number:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Phone number is required for SMS MFA",
            )

        try:
            logger.info(f"Setting up SMS MFA for user {user.id}")

            mfa_code = self._generate_mfa_code()
            await self._store_mfa_code(user.id, mfa_code)

            message = f"Your verification code is: {mfa_code}. This code expires in 5 minutes."
            message_id = await self._send_sms(phone_number, message)

            user.phone_number = phone_number
            user.sms_mfa_enabled = True
            user.phone_verified = False
            await db.commit()
            await db.refresh(user)

            logger.info(f"SMS MFA setup completed for user {user.id}")
            return {
                "message": "SMS MFA enabled and verification code sent to your phone",
                "phone_number": phone_number,
                "message_id": message_id,
            }
        except Exception as e:
            logger.error(f"Failed to setup SMS MFA for user {user.id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to setup SMS MFA",
            )

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

        try:
            logger.info(f"Sending MFA code to user {user.id}")

            mfa_code = self._generate_mfa_code()
            await self._store_mfa_code(user.id, mfa_code)

            message = f"Your login code is: {mfa_code}. This code expires in 5 minutes."
            message_id = await self._send_sms(user.phone_number, message)

            logger.info(f"MFA code sent successfully to user {user.id}")
            return {
                "message": "MFA code sent successfully",
                "phone_number": user.phone_number,
                "message_id": message_id,
            }

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to send MFA code to user {user.id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to send MFA code",
            )

    async def verify_mfa_code(
        self, user: User, provided_code: str, db: AsyncSession
    ) -> dict:
        if not user.sms_mfa_enabled:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="SMS MFA is not enabled for this user",
            )

        try:
            logger.info(f"Verifying MFA code for user {user.id}")

            stored_code = await self._get_mfa_code(user.id)
            if not stored_code:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No MFA code found or code has expired",
                )

            # Verify code
            if provided_code != stored_code:
                logger.warning(f"Invalid MFA code provided for user {user.id}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid MFA code"
                )

            # Mark phone as verified if this is first successful verification
            if not user.phone_verified:
                user.phone_verified = True
                await db.commit()
                await db.refresh(user)

            # Delete used code
            await self._delete_mfa_code(user.id)

            logger.info(f"SMS MFA verification successful for user {user.id}")
            return {"message": "Phone number verified successfully"}

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to verify SMS MFA for user {user.id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to verify MFA code",
            )

    async def disable_sms_mfa(self, user: User, db: AsyncSession) -> dict:
        user.sms_mfa_enabled = False
        user.phone_verified = False

        # Clean up any pending codes
        await self._delete_mfa_code(user.id)

        await db.commit()
        await db.refresh(user)

        logger.info(f"SMS MFA disabled for user {user.id}")
        return {"message": "SMS MFA disabled successfully"}


logger.info("Creating SMS MFA service instance at module level")
sms_mfa_service = SMSMFAService()
logger.info("SMS MFA service instance created successfully")

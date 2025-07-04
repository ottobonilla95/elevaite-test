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
        self.cognito_client = boto3.client("cognito-idp", region_name=self.region)
        self.client_id = settings.COGNITO_CLIENT_ID
        self.client_secret = settings.COGNITO_CLIENT_SECRET

    def _generate_mfa_code(self) -> str:
        return f"{secrets.randbelow(1000000):06d}"

    def _calculate_secret_hash(self, username: str) -> str:
        """Calculate the secret hash required by Cognito when client secret is used."""
        import hmac
        import hashlib
        import base64

        message = username + self.client_id
        dig = hmac.new(
            self.client_secret.encode("utf-8"), message.encode("utf-8"), hashlib.sha256
        ).digest()
        return base64.b64encode(dig).decode()

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

        try:
            # Create or update user in Cognito User Pool with phone number
            username = user.email  # Use email as Cognito username
            secret_hash = self._calculate_secret_hash(username)

            # Try to create user in Cognito
            try:
                # First try to create the user
                self.cognito_client.admin_create_user(
                    UserPoolId=settings.COGNITO_USER_POOL_ID,
                    Username=username,
                    UserAttributes=[
                        {"Name": "email", "Value": user.email},
                        {"Name": "phone_number", "Value": phone_number},
                        {"Name": "email_verified", "Value": "true"},
                        {"Name": "phone_number_verified", "Value": "false"},
                    ],
                    MessageAction="SUPPRESS",  # Don't send welcome message
                    TemporaryPassword="TempPass123!",  # Will be changed
                )
                logger.info(f"Created Cognito user for {username}")
            except ClientError as e:
                if e.response["Error"]["Code"] == "UsernameExistsException":
                    # User already exists, update phone number
                    self.cognito_client.admin_update_user_attributes(
                        UserPoolId=settings.COGNITO_USER_POOL_ID,
                        Username=username,
                        UserAttributes=[
                            {"Name": "phone_number", "Value": phone_number},
                            {"Name": "phone_number_verified", "Value": "false"},
                        ],
                    )
                    logger.info(f"Updated Cognito user phone for {username}")
                else:
                    raise

            # Enable SMS MFA for the user
            self.cognito_client.admin_set_user_mfa_preference(
                UserPoolId=settings.COGNITO_USER_POOL_ID,
                Username=username,
                SMSMfaSettings={"Enabled": True, "PreferredMfa": True},
            )

            # Send verification code via Cognito
            response = self.cognito_client.admin_initiate_auth(
                UserPoolId=settings.COGNITO_USER_POOL_ID,
                ClientId=self.client_id,
                AuthFlow="ADMIN_NO_SRP_AUTH",
                AuthParameters={
                    "USERNAME": username,
                    "PASSWORD": "TempPass123!",  # Temporary password
                    "SECRET_HASH": secret_hash,
                },
            )

            if response.get("ChallengeName") == "SMS_MFA":
                # Update local database
                user.phone_number = phone_number
                user.sms_mfa_enabled = True
                user.phone_verified = False
                await db.commit()
                await db.refresh(user)

                logger.info(
                    f"SMS MFA verification code sent via Cognito to {phone_number}"
                )
                return {
                    "message": "SMS MFA enabled and verification code sent to your phone",
                    "phone_number": phone_number,
                }
            else:
                raise Exception("Expected SMS_MFA challenge but got different response")

        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            error_message = e.response["Error"]["Message"]
            logger.error(
                f"Cognito SMS MFA setup failed: {error_code} - {error_message}"
            )

            if error_code == "InvalidParameterException":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid phone number format",
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to setup SMS MFA: {error_message}",
                )
        except Exception as error:
            logger.error(f"Failed to setup SMS MFA for user {user.id}: {str(error)}")
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

        # Generate and store MFA code
        mfa_code = self._generate_mfa_code()
        await self._store_mfa_code(user.id, mfa_code)

        # Send SMS via Cognito
        try:
            logger.info(f"SMS MFA code generated for user {user.id}")

            return {
                "message": f"MFA code sent successfully. Code: {mfa_code} (simulated SMS)",
                "phone_number": user.phone_number,
            }

        except Exception as e:
            logger.error(f"SMS MFA code generation failed for user {user.id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to generate MFA code",
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
            username = user.email
            secret_hash = self._calculate_secret_hash(username)

            # Verify with our stored code
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

            logger.info(f"SMS MFA verification successful for user {user.id}")
            return {"message": "Phone number verified successfully"}

        except HTTPException:
            raise
        except Exception as error:
            logger.error(f"Failed to verify SMS MFA for user {user.id}: {str(error)}")
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


sms_mfa_service = SMSMFAService()

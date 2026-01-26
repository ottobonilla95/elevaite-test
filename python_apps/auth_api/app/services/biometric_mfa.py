"""Biometric MFA service for WebAuthn authentication."""

import json
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from datetime import datetime, timezone

from app.db.models import User, BiometricDevice
from app.core.logging import logger


class BiometricMFAService:
    """Service for handling biometric MFA operations."""

    async def verify_biometric_assertion(
        self, user: User, assertion_response: str, session: AsyncSession
    ) -> bool:
        """Verify WebAuthn assertion for biometric MFA."""
        try:
            # Parse the assertion response (JSON string)
            assertion_data = json.loads(assertion_response)

            # Get user's active biometric devices
            result = await session.execute(
                select(BiometricDevice).where(
                    BiometricDevice.user_id == user.id, BiometricDevice.is_active
                )
            )
            devices = result.scalars().all()

            if not devices:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No biometric devices registered",
                )

            # Verify assertion against registered devices
            for device in devices:
                if await self._verify_assertion_against_device(assertion_data, device):
                    # Update device last used
                    device.last_used_at = datetime.now(timezone.utc)
                    await session.commit()

                    logger.info(
                        f"Biometric MFA verified for user {user.id} using device {device.id}"
                    )
                    return True

            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid biometric verification",
            )

        except json.JSONDecodeError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid biometric assertion format",
            )
        except Exception as e:
            logger.error(f"Biometric verification error for user {user.id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid MFA code"
            )

    async def _verify_assertion_against_device(
        self, assertion_data: dict, device: BiometricDevice
    ) -> bool:
        """Verify WebAuthn assertion against a specific device."""
        try:
            # Simplified verification - in production use proper WebAuthn library
            credential_id = assertion_data.get("id")
            if not credential_id:
                return False

            # Check if credential ID matches device fingerprint
            return credential_id == device.device_fingerprint

        except Exception as e:
            logger.error(f"Device verification error: {str(e)}")
            return False


# Global instance
biometric_mfa_service = BiometricMFAService()

from datetime import datetime, timedelta, timezone
from typing import Optional
from fastapi import Request
from sqlalchemy import and_, delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.device_fingerprint import (
    generate_device_fingerprint,
    get_device_info_for_logging,
)
from app.core.logging import logger
from app.db.models import MfaDeviceVerification, User


class MfaDeviceService:
    """Service for managing MFA device verifications and 24-hour bypass."""

    @staticmethod
    async def check_device_mfa_bypass(
        user: User, request: Request, session: AsyncSession
    ) -> bool:
        """
        Check if the current device has a valid MFA bypass (verified within 24 hours).

        Args:
            user: User object
            request: FastAPI request object
            session: Database session

        Returns:
            True if device has valid MFA bypass, False otherwise
        """
        try:
            # Generate device fingerprint
            device_fingerprint = generate_device_fingerprint(request, user.id)

            # Check for existing valid verification
            now = datetime.now(timezone.utc)

            result = await session.execute(
                select(MfaDeviceVerification).where(
                    and_(
                        MfaDeviceVerification.user_id == user.id,
                        MfaDeviceVerification.device_fingerprint == device_fingerprint,
                        MfaDeviceVerification.expires_at > now,
                    )
                )
            )

            verification = result.scalars().first()

            if verification:
                logger.info(
                    f"MFA bypass found for user {user.id} on device {device_fingerprint[:16]}... "
                    f"(expires: {verification.expires_at})"
                )
                return True

            logger.info(
                f"No valid MFA bypass found for user {user.id} on device {device_fingerprint[:16]}..."
            )
            return False

        except Exception as e:
            logger.error(
                f"Error checking MFA device bypass for user {user.id}: {str(e)}"
            )
            # Fail secure - require MFA if there's an error
            return False

    @staticmethod
    async def record_mfa_verification(
        user: User,
        request: Request,
        session: AsyncSession,
        mfa_method: str,
        bypass_duration_hours: Optional[int] = None,
    ) -> None:
        """
        Record a successful MFA verification for the current device.

        Args:
            user: User object
            request: FastAPI request object
            session: Database session
            mfa_method: MFA method used ('totp', 'sms', 'email')
            bypass_duration_hours: How long the bypass should last (uses config default if None)
        """
        try:
            # Get bypass duration from config if not specified
            if bypass_duration_hours is None:
                from app.core.config import settings

                bypass_duration_hours = settings.MFA_DEVICE_BYPASS_HOURS

            # Generate device fingerprint
            device_fingerprint = generate_device_fingerprint(request, user.id)
            device_info = get_device_info_for_logging(request)

            # Calculate expiration time
            now = datetime.now(timezone.utc)
            expires_at = now + timedelta(hours=bypass_duration_hours)

            # Clean up any existing verifications for this user/device
            await session.execute(
                delete(MfaDeviceVerification).where(
                    and_(
                        MfaDeviceVerification.user_id == user.id,
                        MfaDeviceVerification.device_fingerprint == device_fingerprint,
                    )
                )
            )

            # Create new verification record
            verification = MfaDeviceVerification(
                user_id=user.id,
                device_fingerprint=device_fingerprint,
                ip_address=device_info["ip_address"],
                user_agent=device_info["user_agent"],
                verified_at=now,
                expires_at=expires_at,
                mfa_method=mfa_method,
            )

            session.add(verification)
            await session.commit()

            logger.info(
                f"MFA verification recorded for user {user.id} using {mfa_method}. "
                f"Device {device_fingerprint[:16]}... bypass valid until {expires_at}"
            )

        except Exception as e:
            logger.error(
                f"Error recording MFA verification for user {user.id}: {str(e)}"
            )
            await session.rollback()
            raise

    @staticmethod
    async def cleanup_expired_verifications(session: AsyncSession) -> int:
        """
        Clean up expired MFA device verifications.

        Args:
            session: Database session

        Returns:
            Number of expired verifications removed
        """
        try:
            now = datetime.now(timezone.utc)

            # Delete expired verifications
            result = await session.execute(
                delete(MfaDeviceVerification).where(
                    MfaDeviceVerification.expires_at <= now
                )
            )

            deleted_count = result.rowcount
            await session.commit()

            if deleted_count > 0:
                logger.info(
                    f"Cleaned up {deleted_count} expired MFA device verifications"
                )

            return deleted_count

        except Exception as e:
            logger.error(f"Error cleaning up expired MFA verifications: {str(e)}")
            await session.rollback()
            return 0

    @staticmethod
    async def revoke_device_verification(
        user_id: int, device_fingerprint: str, session: AsyncSession
    ) -> bool:
        """
        Revoke MFA verification for a specific device.

        Args:
            user_id: User ID
            device_fingerprint: Device fingerprint to revoke
            session: Database session

        Returns:
            True if verification was revoked, False if not found
        """
        try:
            result = await session.execute(
                delete(MfaDeviceVerification).where(
                    and_(
                        MfaDeviceVerification.user_id == user_id,
                        MfaDeviceVerification.device_fingerprint == device_fingerprint,
                    )
                )
            )

            deleted_count = result.rowcount
            await session.commit()

            if deleted_count > 0:
                logger.info(
                    f"Revoked MFA device verification for user {user_id}, "
                    f"device {device_fingerprint[:16]}..."
                )
                return True

            return False

        except Exception as e:
            logger.error(
                f"Error revoking device verification for user {user_id}: {str(e)}"
            )
            await session.rollback()
            return False

    @staticmethod
    async def revoke_all_user_verifications(user_id: int, session: AsyncSession) -> int:
        """
        Revoke all MFA verifications for a user (useful for security incidents).

        Args:
            user_id: User ID
            session: Database session

        Returns:
            Number of verifications revoked
        """
        try:
            result = await session.execute(
                delete(MfaDeviceVerification).where(
                    MfaDeviceVerification.user_id == user_id
                )
            )

            deleted_count = result.rowcount
            await session.commit()

            logger.info(
                f"Revoked {deleted_count} MFA device verifications for user {user_id}"
            )

            return deleted_count

        except Exception as e:
            logger.error(
                f"Error revoking all device verifications for user {user_id}: {str(e)}"
            )
            await session.rollback()
            return 0

    @staticmethod
    async def get_user_device_verifications(
        user_id: int, session: AsyncSession
    ) -> list[MfaDeviceVerification]:
        """
        Get all active MFA device verifications for a user.

        Args:
            user_id: User ID
            session: Database session

        Returns:
            List of active MFA device verifications
        """
        try:
            now = datetime.now(timezone.utc)

            result = await session.execute(
                select(MfaDeviceVerification)
                .where(
                    and_(
                        MfaDeviceVerification.user_id == user_id,
                        MfaDeviceVerification.expires_at > now,
                    )
                )
                .order_by(MfaDeviceVerification.verified_at.desc())
            )

            return result.scalars().all()

        except Exception as e:
            logger.error(
                f"Error getting device verifications for user {user_id}: {str(e)}"
            )
            return []


# Create a singleton instance
mfa_device_service = MfaDeviceService()

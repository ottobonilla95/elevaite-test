import asyncio
from datetime import datetime, timezone

from app.core.logging import logger
from app.db.orm import get_async_session
from app.services.mfa_device_service import mfa_device_service
from app.db.models import Session
from sqlalchemy import delete


async def cleanup_expired_sessions():
    try:
        async for session in get_async_session():
            now = datetime.now(timezone.utc)

            result = await session.execute(
                delete(Session).where(Session.expires_at <= now)
            )

            deleted_count = result.rowcount
            await session.commit()

            if deleted_count > 0:
                logger.info(f"Cleaned up {deleted_count} expired sessions")

            break
    except Exception as e:
        logger.error(f"Error during session cleanup: {str(e)}")


async def cleanup_expired_mfa_verifications():
    """Clean up expired MFA device verifications."""
    try:
        async for session in get_async_session():
            deleted_count = await mfa_device_service.cleanup_expired_verifications(
                session
            )
            if deleted_count > 0:
                logger.info(
                    f"Cleaned up {deleted_count} expired MFA device verifications"
                )
            break  # Only need one session iteration
    except Exception as e:
        logger.error(f"Error during MFA verification cleanup: {str(e)}")


async def start_cleanup_tasks():
    """Start the background tasks for cleaning up expired data."""
    logger.info("Starting cleanup tasks (sessions and MFA verifications)")

    while True:
        try:
            # Run cleanup every hour
            await asyncio.sleep(3600)  # 1 hour

            logger.debug("Running scheduled cleanup tasks")
            await cleanup_expired_sessions()
            await cleanup_expired_mfa_verifications()

        except asyncio.CancelledError:
            logger.info("Cleanup tasks cancelled")
            break
        except Exception as e:
            logger.error(f"Unexpected error in cleanup tasks: {str(e)}")
            # Continue running even if there's an error
            await asyncio.sleep(60)  # Wait 1 minute before retrying

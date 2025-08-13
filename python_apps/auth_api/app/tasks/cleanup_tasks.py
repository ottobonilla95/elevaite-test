import asyncio

from app.core.logging import logger
from app.db.orm import get_async_session
from app.services.mfa_device_service import mfa_device_service


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


async def start_mfa_cleanup_task():
    """Start the background task for cleaning up expired MFA verifications."""
    logger.info("Starting MFA device verification cleanup task")

    while True:
        try:
            # Run cleanup every hour
            await asyncio.sleep(3600)  # 1 hour

            logger.debug("Running scheduled MFA device verification cleanup")
            await cleanup_expired_mfa_verifications()

        except asyncio.CancelledError:
            logger.info("MFA cleanup task cancelled")
            break
        except Exception as e:
            logger.error(f"Unexpected error in MFA cleanup task: {str(e)}")
            # Continue running even if there's an error
            await asyncio.sleep(60)  # Wait 1 minute before retrying

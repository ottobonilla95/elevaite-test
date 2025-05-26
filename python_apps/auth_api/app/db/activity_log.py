"""User activity logging utilities."""

from datetime import datetime, timezone
from typing import Any, Dict, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import logger
from app.db.models import UserActivity


# Helper functions
async def log_user_activity(
    session: AsyncSession,
    user_id: int,
    action: str,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
) -> None:
    """Log user activity for audit purposes."""
    # Check if session is None
    if session is None:
        print(
            f"WARNING: Session is None in log_user_activity for user ID {user_id}, action {action}"
        )
        return

    try:
        # Create a new UserActivity instance
        activity = UserActivity(
            user_id=user_id,
            action=action,
            ip_address=ip_address,
            user_agent=user_agent,
            timestamp=datetime.now(timezone.utc),
            details=details,
        )
    except Exception as e:
        print(f"Error creating UserActivity instance: {e}")

    # Add to session and commit
    try:
        await session.run_sync(lambda s: s.add(activity))
        await session.commit()
        logger.debug(
            f"Activity logged for user {user_id}: {action}",
            extra={
                "user_id": user_id,
                "action": action,
                "ip_address": ip_address,
                "timestamp": activity.timestamp.isoformat(),
            },
        )
    except Exception as e:
        logger.error(
            f"Failed to log user activity for user {user_id}: {str(e)}",
            extra={
                "user_id": user_id,
                "action": action,
                "error": str(e),
            },
        )

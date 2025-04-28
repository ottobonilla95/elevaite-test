"""User activity logging utilities."""

from datetime import datetime, timezone
from typing import Any, Dict, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import user_activity


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
    await session.execute(
        user_activity.insert().values(
            user_id=user_id,
            action=action,
            ip_address=ip_address,
            user_agent=user_agent,
            timestamp=datetime.now(timezone.utc),
            details=details,
        )
    )
    await session.commit()

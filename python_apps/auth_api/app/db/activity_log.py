"""User activity logging utilities."""

from datetime import datetime, timezone
from typing import Any, Dict, Optional

from sqlalchemy import Column, DateTime, Integer, JSON, String, Table
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.database import database
from app.db.orm_models import Base

# User activity logging table (for audit)
user_activity = Table(
    "user_activity",
    Base.metadata,
    Column("id", Integer, primary_key=True),
    Column("user_id", Integer, nullable=False),
    Column("action", String, nullable=False),
    Column("ip_address", String, nullable=True),
    Column("user_agent", String, nullable=True),
    Column("timestamp", DateTime, default=lambda: datetime.now(timezone.utc), nullable=False),
    Column("details", JSON, nullable=True),
)


# Helper functions
async def log_user_activity(
    user_id: int,
    action: str,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
) -> None:
    """Log user activity for audit purposes."""
    await database.execute(
        user_activity.insert().values(
            user_id=user_id,
            action=action,
            ip_address=ip_address,
            user_agent=user_agent,
            timestamp=datetime.now(timezone.utc),
            details=details,
        )
    )

"""Database connection and utilities."""

from datetime import datetime, timezone
from typing import Any, Dict, Optional

import sqlalchemy
from databases import Database
from sqlalchemy import Column, DateTime, MetaData, Table, create_engine
from sqlalchemy.ext.declarative import declarative_base

from app.core.config import settings

# SQLAlchemy database connection
database = Database(settings.DATABASE_URI)
metadata = MetaData()
Base = declarative_base(metadata=metadata)


# Base model with created_at and updated_at fields
class TimestampModel:
    """Base model with timestamp fields."""

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(
        DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False
    )


async def create_tables() -> None:
    """Create database tables."""
    engine = create_engine(str(settings.DATABASE_URI).replace("asyncpg", "psycopg2"))
    metadata.create_all(engine)
    await database.connect()


async def get_db() -> Database:
    """Get database connection."""
    return database


# User activity logging table (for audit)
user_activity = Table(
    "user_activity",
    metadata,
    Column("id", sqlalchemy.Integer, primary_key=True),
    Column("user_id", sqlalchemy.Integer, nullable=False),
    Column("action", sqlalchemy.String, nullable=False),
    Column("ip_address", sqlalchemy.String, nullable=True),
    Column("user_agent", sqlalchemy.String, nullable=True),
    Column("timestamp", sqlalchemy.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False),
    Column("details", sqlalchemy.JSON, nullable=True),
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

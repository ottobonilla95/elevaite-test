"""Database connection and utilities."""

from datetime import datetime, timezone
from typing import AsyncGenerator

import sqlalchemy
from sqlalchemy import Column, DateTime, MetaData, Table
from sqlalchemy.ext.asyncio import AsyncSession

from db_core import get_tenant_async_db

from app.core.multitenancy import multitenancy_settings

# SQLAlchemy metadata for tables
metadata = MetaData()


# Base model with created_at and updated_at fields
class TimestampModel:
    """Base model with timestamp fields."""

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(
        DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False
    )


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Get a tenant-aware database session."""
    async for session in get_tenant_async_db(multitenancy_settings):
        yield session


# User activity logging table (for audit)
user_activity = Table(
    "user_activity",
    metadata,
    Column("id", sqlalchemy.Integer, primary_key=True),
    Column("user_id", sqlalchemy.Integer, nullable=False),
    Column("action", sqlalchemy.String, nullable=False),
    Column("ip_address", sqlalchemy.String, nullable=True),
    Column("user_agent", sqlalchemy.String, nullable=True),
    Column("timestamp", sqlalchemy.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False),
    Column("details", sqlalchemy.JSON, nullable=True),
)


# Helper functions for user activity logging are now in app.db.activity_log

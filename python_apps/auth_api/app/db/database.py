"""Database connection and utilities."""

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from db_core import get_tenant_async_db

from app.core.multitenancy import multitenancy_settings


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Get a tenant-aware database session."""
    async for session in get_tenant_async_db(multitenancy_settings):
        yield session

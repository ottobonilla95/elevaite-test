"""Database initialization for ORM models."""

from sqlalchemy.ext.asyncio import create_async_engine

from app.core.config import settings
from .models import Base


async def create_tables() -> None:
    """Create database tables using ORM models."""
    engine = create_async_engine(settings.DATABASE_URI)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

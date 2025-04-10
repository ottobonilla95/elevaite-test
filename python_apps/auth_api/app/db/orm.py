"""SQLAlchemy ORM async session management."""

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.core.config import settings
from app.db.orm_models import Base

# Create async engine
async_engine = create_async_engine(
    settings.DATABASE_URI,
    echo=False,
    future=True,
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    async_engine,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_async_session():
    """Get an async database session."""
    session = AsyncSessionLocal()
    try:
        yield session
    finally:
        await session.close()

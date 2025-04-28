"""SQLAlchemy ORM async session management with tenant awareness."""

from typing import AsyncGenerator, cast

from sqlalchemy.ext.asyncio import AsyncSession

from db_core import get_tenant_async_db, get_current_tenant_id

from app.core.multitenancy import multitenancy_settings


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """Get a tenant-aware async database session."""
    # Get the current tenant ID from the request
    tenant_id = get_current_tenant_id()

    # Use a string tenant ID, not a Depends object
    if isinstance(tenant_id, str):
        async for session in get_tenant_async_db(multitenancy_settings, tenant_id):
            try:
                yield session
            finally:
                await session.close()
    else:
        # Fallback to default tenant if tenant_id is not a string
        default_tenant = cast(str, multitenancy_settings.default_tenant_id or "default")
        async for session in get_tenant_async_db(multitenancy_settings, default_tenant):
            try:
                yield session
            finally:
                await session.close()

"""Tenant-aware database connection and session management."""

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from db_core import (
    get_tenant_async_db,
    init_db,
    MultitenancySettings,
)
from db_core.middleware import get_current_tenant_id

from app.core.config import settings
from app.core.multitenancy import multitenancy_settings, DEFAULT_TENANTS
from .models import Base

# Update the multitenancy settings with the database URL from config
db_url = settings._database_env

multitenancy_settings.db_url = db_url


async def initialize_db():
    """Initialize the database with tenant schemas."""
    # Initialize the database with tenant schemas
    init_db(
        settings=multitenancy_settings,
        db_url=multitenancy_settings.db_url,
        create_schemas=True,
        base_model_class=Base,
        tenant_ids=DEFAULT_TENANTS,
        is_async=True,
    )


async def get_tenant_session(
    settings: MultitenancySettings = multitenancy_settings,
) -> AsyncGenerator[AsyncSession, None]:
    """Get a tenant-aware database session."""
    async for session in get_tenant_async_db(settings):
        yield session


# Current tenant ID dependency
def get_current_tenant():
    """Get the current tenant ID from the request context."""
    tenant_id = get_current_tenant_id()
    if tenant_id is None:
        # Default to 'default' tenant if none is set
        return multitenancy_settings.default_tenant_id
    return tenant_id

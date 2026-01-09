"""
Tenant administration for the Workflow Execution Engine.

Provides tenant initializer, admin router, and tenant validation callback.
"""

import asyncio
import logging
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from fastapi import Depends

from db_core import TenantRegistry, register_tenant_initializer, create_tenant_admin_router, get_tenant_cache
from db_core.utils import get_schema_name
from workflow_core_sdk.multitenancy import multitenancy_settings, DEFAULT_TENANTS
from workflow_core_sdk.db.database import DATABASE_URL
from workflow_core_sdk.db.models import *  # noqa: F401, F403 - register models
from workflow_core_sdk.db.migrations import run_migrations_for_tenant
from workflow_engine_poc.util import superadmin_guard

logger = logging.getLogger(__name__)
_async_engine = None
_async_session_factory = None


def _get_async_db_url() -> str:
    """Convert sync database URL to async format."""
    url = DATABASE_URL
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+asyncpg://", 1)
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+asyncpg://", 1)
    return url


def _ensure_async_engine():
    """Initialize async engine lazily."""
    global _async_engine, _async_session_factory
    if _async_engine is None:
        _async_engine = create_async_engine(_get_async_db_url(), echo=False)
        _async_session_factory = async_sessionmaker(_async_engine, class_=AsyncSession, expire_on_commit=False)


async def get_admin_session() -> AsyncGenerator[AsyncSession, None]:
    """Provide async session for tenant admin operations."""
    _ensure_async_engine()
    async with _async_session_factory() as session:
        yield session


def get_tenant_registry() -> TenantRegistry:
    """Provide tenant registry instance."""
    return TenantRegistry(multitenancy_settings)


# Register migration initializer FIRST (order matters!)
@register_tenant_initializer
async def init_workflow_tables(tenant_id: str, session: AsyncSession) -> None:
    """Create workflow tables in new tenant's schema using Alembic migrations."""
    schema_name = get_schema_name(tenant_id, multitenancy_settings)
    logger.info(f"Running Alembic migrations for tenant '{tenant_id}' in schema '{schema_name}'")

    # Run Alembic migrations in a thread pool since it uses sync database operations
    await asyncio.to_thread(run_migrations_for_tenant, schema_name, DATABASE_URL)

    logger.info(f"Migrations completed for tenant '{tenant_id}'")


# Import seeding module to register the seed_tenant_data initializer AFTER migrations
# This ensures the seeding initializer runs after tables are created
from workflow_engine_poc.seeding import seed_tenant_data  # noqa: F401, E402 - registers initializer


def validate_tenant_exists(tenant_id: str) -> bool:
    """Validate tenant exists and is active using cached lookup."""
    is_active = get_tenant_cache().is_active(tenant_id)
    if is_active is not None:
        return is_active
    # Fallback: allow default tenants when cache not initialized
    return tenant_id in DEFAULT_TENANTS


# Tenant admin router with superadmin security
tenant_admin_router = create_tenant_admin_router(
    get_session=get_admin_session,
    get_registry=get_tenant_registry,
    prefix="/tenants",
    tags=["admin"],
    dependencies=[Depends(superadmin_guard("manage_tenants"))],
)

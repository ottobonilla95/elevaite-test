"""
Tenant administration for the Workflow Execution Engine.

Provides tenant initializer, admin router, and tenant validation callback.
"""

import logging
from typing import AsyncGenerator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.schema import CreateTable
from sqlalchemy.dialects import postgresql
from sqlmodel import SQLModel
from fastapi import Depends

from db_core import TenantRegistry, register_tenant_initializer, create_tenant_admin_router, get_tenant_cache
from db_core.utils import get_schema_name
from workflow_core_sdk.multitenancy import multitenancy_settings, DEFAULT_TENANTS
from workflow_core_sdk.db.models import *  # noqa: F401, F403 - register models
from workflow_engine_poc.util import superadmin_guard

logger = logging.getLogger(__name__)
_async_engine = None
_async_session_factory = None


def _get_async_db_url() -> str:
    """Convert sync database URL to async format."""
    from workflow_core_sdk.db.database import DATABASE_URL

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


@register_tenant_initializer
async def init_workflow_tables(tenant_id: str, session: AsyncSession) -> None:
    """Create workflow tables in new tenant's schema."""
    schema_name = get_schema_name(tenant_id, multitenancy_settings)
    logger.info(f"Initializing tables for tenant '{tenant_id}' in schema '{schema_name}'")

    for table in SQLModel.metadata.tables.values():
        # Check if table exists
        result = await session.execute(
            text("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_schema = :schema AND table_name = :table)"),
            {"schema": schema_name, "table": table.name},
        )
        if not result.scalar():
            # Create table with schema-qualified name
            ddl = str(CreateTable(table).compile(dialect=postgresql.dialect()))
            ddl = ddl.replace(f'"{table.name}"', f'"{schema_name}"."{table.name}"')
            await session.execute(text(ddl))

    await session.commit()
    logger.info(f"Tables initialized for tenant '{tenant_id}'")


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

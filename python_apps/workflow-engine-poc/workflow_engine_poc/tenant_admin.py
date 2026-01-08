"""
Tenant administration for the Workflow Execution Engine.

This module provides:
- Tenant initializer callback for creating workflow-specific tables
- Dependencies for the tenant admin router
- Tenant admin router configuration
"""

import logging
from typing import AsyncGenerator

from sqlalchemy import text, MetaData
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlmodel import SQLModel

from fastapi import Depends

from db_core import (
    TenantRegistry,
    register_tenant_initializer,
    create_tenant_admin_router,
)
from db_core.utils import get_schema_name

from workflow_core_sdk.multitenancy import multitenancy_settings
from workflow_engine_poc.util import superadmin_guard

# Import models to ensure they're registered with SQLModel.metadata
# fmt: off
from workflow_core_sdk.db.models import (  # noqa: F401
    Workflow,
    WorkflowExecution,
    StepExecution,
    StepType,
    Agent,
    AgentToolBinding,
    AgentMessage,
    Prompt,
    Tool,
    ToolCategory,
    MCPServer,
    ApprovalRequest,
    A2AAgent,
    AgentExecutionMetrics,
    WorkflowMetrics,
)
# fmt: on

logger = logging.getLogger(__name__)

# Async engine and session factory for tenant admin operations
_async_engine = None
_async_session_factory = None


def _get_async_database_url() -> str:
    """Convert sync database URL to async format."""
    from workflow_core_sdk.db.database import DATABASE_URL

    url = DATABASE_URL
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
    elif url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+asyncpg://", 1)
    return url


def _ensure_async_engine():
    """Ensure the async engine and session factory are initialized."""
    global _async_engine, _async_session_factory

    if _async_engine is None:
        db_url = _get_async_database_url()
        _async_engine = create_async_engine(db_url, echo=False)
        _async_session_factory = async_sessionmaker(
            _async_engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )
        logger.info("Async database engine initialized for tenant admin")


async def get_admin_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency that provides an async session for tenant admin operations."""
    _ensure_async_engine()
    async with _async_session_factory() as session:
        yield session


def get_tenant_registry() -> TenantRegistry:
    """Dependency that provides the tenant registry."""
    return TenantRegistry(multitenancy_settings)


@register_tenant_initializer
async def init_workflow_tables(tenant_id: str, session: AsyncSession) -> None:
    """
    Initialize workflow-specific tables for a new tenant.

    This callback is invoked when a new tenant is created via the admin API.
    It creates all the workflow engine tables in the tenant's schema.

    Args:
        tenant_id: The tenant identifier
        session: Async database session
    """
    schema_name = get_schema_name(tenant_id, multitenancy_settings)

    logger.info(f"Initializing workflow tables for tenant '{tenant_id}' in schema '{schema_name}'")

    # Create all SQLModel tables in the tenant schema
    # We need to run raw DDL since SQLModel.metadata.create_all requires sync engine
    for table in SQLModel.metadata.tables.values():
        # Get the CREATE TABLE DDL
        table_name = table.name

        # Skip if table already exists in schema
        check_sql = text(f"""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = :schema 
                AND table_name = :table
            )
        """)
        result = await session.execute(check_sql, {"schema": schema_name, "table": table_name})
        exists = result.scalar()

        if not exists:
            # Create table using DDL compiled for PostgreSQL
            from sqlalchemy.schema import CreateTable
            from sqlalchemy.dialects import postgresql

            create_ddl = CreateTable(table).compile(dialect=postgresql.dialect())
            # Modify DDL to use the tenant schema
            ddl_str = str(create_ddl)
            ddl_str = ddl_str.replace(f'"{table_name}"', f'"{schema_name}"."{table_name}"')

            await session.execute(text(ddl_str))
            logger.debug(f"Created table '{schema_name}.{table_name}'")

    await session.commit()
    logger.info(f"Workflow tables initialized for tenant '{tenant_id}'")


# Create the tenant admin router with superadmin security
# Only organization-level superadmins can manage tenants
tenant_admin_router = create_tenant_admin_router(
    get_session=get_admin_session,
    get_registry=get_tenant_registry,
    prefix="/tenants",
    tags=["admin"],
    dependencies=[Depends(superadmin_guard("manage_tenants"))],
)

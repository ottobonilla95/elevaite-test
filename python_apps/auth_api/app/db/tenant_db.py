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
from app.core.logging import logger
from app.core.multitenancy import multitenancy_settings, DEFAULT_TENANTS
from .models import Base

# Update the multitenancy settings with the database URL from config
db_url = settings.DATABASE_URI

multitenancy_settings.db_url = db_url


async def initialize_db():
    """Initialize the database with tenant schemas."""
    logger.info(f"Initializing database with tenants: {DEFAULT_TENANTS}")
    try:
        # Initialize the database with tenant schemas
        db_info = init_db(
            settings=multitenancy_settings,
            db_url=multitenancy_settings.db_url,
            create_schemas=True,
            base_model_class=Base,
            tenant_ids=DEFAULT_TENANTS,
            is_async=True,
        )
        logger.info("Database initialization completed successfully")
    except Exception as e:
        logger.error(
            f"Database initialization failed: {str(e)}", extra={"error": str(e)}
        )

    # Get the engine from the returned info
    engine = db_info["engine"]

    # Create schemas for async connections
    from sqlalchemy import text
    from db_core.utils import (
        async_tenant_schema_exists,
        async_create_tenant_schema,
        get_schema_name,
    )

    for tenant_id in DEFAULT_TENANTS:
        schema_name = get_schema_name(tenant_id, multitenancy_settings)

        # Check if schema exists
        schema_exists = await async_tenant_schema_exists(engine, schema_name)

        if not schema_exists:
            # Create the schema
            success = await async_create_tenant_schema(engine, schema_name)
            if not success:
                raise RuntimeError(
                    f"Failed to create schema {schema_name} for tenant {tenant_id}"
                )

            # Create tables in the schema
            async with engine.begin() as conn:
                await conn.execute(text(f'SET search_path TO "{schema_name}", public'))
                await conn.run_sync(Base.metadata.create_all)

            print(
                f"Created schema {schema_name} for tenant {tenant_id} with all tables"
            )
        else:
            print(f"Schema {schema_name} for tenant {tenant_id} already exists")


async def get_tenant_session(
    settings: MultitenancySettings = multitenancy_settings,
) -> AsyncGenerator[AsyncSession, None]:
    """Get a tenant-aware database session."""
    tenant_id = get_current_tenant_id() or settings.default_tenant_id
    logger.debug(f"Getting database session for tenant: {tenant_id}")
    async for session in get_tenant_async_db(settings):
        yield session


# Current tenant ID dependency
def get_current_tenant():
    """Get the current tenant ID from the request context."""
    tenant_id = get_current_tenant_id()
    if tenant_id is None:
        # Default to 'default' tenant if none is set
        tenant_id = multitenancy_settings.default_tenant_id
        logger.debug(f"No tenant ID in context, using default: {tenant_id}")
    else:
        logger.debug(f"Using tenant ID from context: {tenant_id}")
    return tenant_id


async def create_tenant_schema_if_not_exists(tenant_id: str) -> bool:
    """
    Create a tenant schema if it doesn't exist.

    Args:
        tenant_id: The tenant ID to create a schema for

    Returns:
        True if the schema was created or already exists, False otherwise
    """
    from sqlalchemy.ext.asyncio import create_async_engine
    from sqlalchemy import text
    from db_core.utils import (
        async_tenant_schema_exists,
        async_create_tenant_schema,
        get_schema_name,
    )

    # Create engine
    db_url = multitenancy_settings.db_url
    if not db_url:
        raise ValueError("Database URL is not set in multitenancy settings")
    engine = create_async_engine(db_url)

    # Get schema name
    schema_name = get_schema_name(tenant_id, multitenancy_settings)

    try:
        # Check if schema exists
        schema_exists = await async_tenant_schema_exists(engine, schema_name)

        if not schema_exists:
            # Create the schema
            success = await async_create_tenant_schema(engine, schema_name)
            if not success:
                print(f"Failed to create schema {schema_name} for tenant {tenant_id}")
                return False

            # Create tables in the schema
            async with engine.begin() as conn:
                await conn.execute(text(f'SET search_path TO "{schema_name}", public'))
                await conn.run_sync(Base.metadata.create_all)

            print(
                f"Created schema {schema_name} for tenant {tenant_id} with all tables"
            )
        else:
            print(f"Schema {schema_name} for tenant {tenant_id} already exists")

        return True
    except Exception as e:
        print(f"Error creating schema for tenant {tenant_id}: {e}")
        return False
    finally:
        await engine.dispose()

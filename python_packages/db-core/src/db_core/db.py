"""
Database connection and session management with schema-based tenant awareness.
"""

import logging
from functools import wraps
from typing import Any, Dict, Optional

from sqlalchemy import create_engine, event
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker
from sqlalchemy.pool import NullPool

from db_core.config import MultitenancySettings
from db_core.middleware import get_current_tenant_id
from db_core.utils import (
    create_tenant_schema,
    get_schema_name,
    tenant_schema_exists,
)

logger = logging.getLogger(__name__)

# Base class for SQLAlchemy models
Base = declarative_base()

# Session factories
sync_session_factory: Optional[sessionmaker] = None
async_session_factory: Optional[async_sessionmaker] = None


def init_db(
    settings: MultitenancySettings,
    db_url: Optional[str] = None,
    create_schemas: bool = True,
    base_model_class: Any = Base,
    tenant_ids: Optional[list] = None,
    is_async: bool = False,
) -> Dict[str, Any]:
    """
    Initialize the database connections and session factories.

    Args:
        settings: The multitenancy settings
        db_url: Database URL (overrides settings.db_url)
        create_schemas: Whether to create tenant schemas
        base_model_class: The base model class for SQLAlchemy models
        tenant_ids: Optional list of tenant IDs to initialize schemas for
        is_async: Whether to use async database connections

    Returns:
        Dictionary with 'engine', 'session_factory', and other initialized objects
    """
    global sync_session_factory, async_session_factory

    db_url = db_url or settings.db_url
    if not db_url:
        raise ValueError("Database URL must be provided")

    # Create the main engine
    engine_kwargs = {
        "pool_size": settings.db_pool_size,
        "max_overflow": settings.db_max_overflow,
        "pool_timeout": settings.db_pool_timeout,
        "pool_recycle": settings.db_pool_recycle,
    }

    if is_async:
        # For async engines, adjust connection arguments
        engine = create_async_engine(
            db_url,
            poolclass=None if settings.db_pool_size > 0 else NullPool,
            **{k: v for k, v in engine_kwargs.items() if k not in ["pool_size"]},
        )
        # Create async session factory
        async_session_factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
        session_factory = async_session_factory
    else:
        # For sync engines
        engine = create_engine(db_url, **engine_kwargs)
        # Create session factory
        sync_session_factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        session_factory = sync_session_factory

    # Schema creation for schema-based multitenancy
    if create_schemas and tenant_ids:
        # Just log for async - actual creation will happen via startup event
        if is_async:
            logger.info(f"Async mode: Schemas for tenants {tenant_ids} will be created during app startup")
        else:
            # For sync connections, create the schemas immediately
            for tenant_id in tenant_ids:
                schema_name = get_schema_name(tenant_id, settings)
                if not tenant_schema_exists(engine, schema_name):
                    create_tenant_schema(engine, schema_name)

    # Add event listener for schema-based multitenancy for sync engines
    if not is_async:

        @event.listens_for(engine, "connect")
        def set_search_path(dbapi_connection, connection_record):
            tenant_id = get_current_tenant_id()
            if tenant_id:
                schema = get_schema_name(tenant_id, settings)
                cursor = dbapi_connection.cursor()
                cursor.execute(f'SET search_path TO "{schema}", public')
                cursor.close()

    # Create models in the public schema
    if not is_async:
        base_model_class.metadata.create_all(engine)

    return {
        "engine": engine,
        "session_factory": session_factory,
        "base_model_class": base_model_class,
    }


def get_tenant_session(settings: Optional[MultitenancySettings] = None) -> Session:
    """
    Get a database session for the current tenant.

    Args:
        settings: Optional multitenancy settings (if not provided, uses default settings)

    Returns:
        SQLAlchemy session with tenant context

    Raises:
        RuntimeError: If session factory is not initialized
    """
    if sync_session_factory is None:
        raise RuntimeError("Database not initialized. Call init_db() before using get_tenant_session().")

    session = sync_session_factory()

    # Set the search path for schema-based multitenancy
    if settings:
        tenant_id = get_current_tenant_id()
        if tenant_id:
            schema = get_schema_name(tenant_id, settings)
            session.execute(f'SET search_path TO "{schema}", public')

    return session


async def get_tenant_async_session(settings: Optional[MultitenancySettings] = None) -> AsyncSession:
    """
    Get an async database session for the current tenant.

    Args:
        settings: Optional multitenancy settings (if not provided, uses default settings)

    Returns:
        SQLAlchemy async session with tenant context

    Raises:
        RuntimeError: If session factory is not initialized
    """
    if async_session_factory is None:
        raise RuntimeError(
            "Async database not initialized. Call init_db(is_async=True) before using get_tenant_async_session()."
        )

    session = async_session_factory()

    # Set the search path for schema-based multitenancy
    if settings:
        tenant_id = get_current_tenant_id()
        if tenant_id:
            schema = get_schema_name(tenant_id, settings)
            await session.execute(f'SET search_path TO "{schema}", public')

    return session


def tenant_db_session(func):
    """
    Decorator for functions that need a tenant database session.

    Args:
        func: The function to decorate

    Returns:
        Decorated function with tenant session
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        if "db" not in kwargs:
            session = get_tenant_session()
            try:
                kwargs["db"] = session
                return func(*args, **kwargs)
            finally:
                session.close()
        else:
            return func(*args, **kwargs)

    return wrapper


def tenant_async_db_session(func):
    """
    Decorator for async functions that need a tenant database session.

    Args:
        func: The async function to decorate

    Returns:
        Decorated async function with tenant session
    """

    @wraps(func)
    async def wrapper(*args, **kwargs):
        if "db" not in kwargs:
            session = await get_tenant_async_session()
            try:
                kwargs["db"] = session
                return await func(*args, **kwargs)
            finally:
                await session.close()
        else:
            return await func(*args, **kwargs)

    return wrapper

"""
Database engine and session management using SQLModel

This module provides the database engine, session management, and
database initialization functionality for the workflow engine.

Supports schema-based multitenancy when enabled via db-core middleware.
"""

import os
import logging
from typing import Generator
from sqlmodel import SQLModel, create_engine, Session
from sqlalchemy import text, event
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor

logger = logging.getLogger(__name__)

# Database configuration
# Priority order:
# 1. SQLALCHEMY_DATABASE_URL (standard across all apps)
# 2. WORKFLOW_ENGINE_DATABASE_URL (workflow-engine-poc specific)
# 3. Default to agent_studio_sdk database
DATABASE_URL = os.getenv(
    "SQLALCHEMY_DATABASE_URL",
    os.getenv(
        "WORKFLOW_ENGINE_DATABASE_URL",
        "postgresql://elevaite:elevaite@localhost:5433/agent_studio_sdk",
    ),
)

# Pool tuning via env vars with sensible defaults
pool_size = int(
    os.getenv("WORKFLOW_ENGINE_DB_POOL_SIZE", os.getenv("DB_POOL_SIZE", "20"))
)
max_overflow = int(
    os.getenv("WORKFLOW_ENGINE_DB_MAX_OVERFLOW", os.getenv("DB_MAX_OVERFLOW", "50"))
)
pool_recycle = int(
    os.getenv("WORKFLOW_ENGINE_DB_POOL_RECYCLE", os.getenv("DB_POOL_RECYCLE", "1800"))
)  # seconds
pool_timeout = int(
    os.getenv("WORKFLOW_ENGINE_DB_POOL_TIMEOUT", os.getenv("DB_POOL_TIMEOUT", "30"))
)  # seconds

# Create PostgreSQL engine
# Note: Connection test removed - async engines can't be tested at module import time
engine = create_engine(
    DATABASE_URL,
    echo=os.getenv("SQL_ECHO", "false").lower() == "true",
    pool_size=pool_size,
    max_overflow=max_overflow,
    pool_recycle=pool_recycle,
    pool_timeout=pool_timeout,
)

SQLAlchemyInstrumentor().instrument(engine=engine)  # OTEL


def _apply_tenant_schema_on_checkout(
    dbapi_connection, connection_record, connection_proxy
):
    """
    Event listener that applies tenant schema on connection checkout.

    This is called every time a connection is checked out from the pool,
    ensuring ALL sessions automatically get the correct search_path based
    on the current tenant context, regardless of how they're created.
    """
    try:
        from db_core.middleware import get_current_tenant_id
        from workflow_core_sdk.multitenancy import multitenancy_settings

        tenant_id = get_current_tenant_id()
        if tenant_id:
            schema_name = f"{multitenancy_settings.schema_prefix}{tenant_id}"
            cursor = dbapi_connection.cursor()
            cursor.execute(f'SET search_path TO "{schema_name}", public')
            cursor.close()
            logger.info(f"Applied tenant schema on checkout: {schema_name}")
    except ImportError:
        # db_core not available, skip tenant isolation
        pass
    except Exception as e:
        logger.warning(f"Failed to apply tenant schema on checkout: {e}")


# Register the checkout event listener
event.listen(engine, "checkout", _apply_tenant_schema_on_checkout)


def create_db_and_tables():
    """Create database tables"""
    SQLModel.metadata.create_all(engine)


def _apply_tenant_schema(session: Session) -> None:
    """
    Apply tenant schema to session if tenant context is set.

    Checks db_core's context variable for current tenant ID and sets
    the PostgreSQL search_path accordingly.
    """
    try:
        from db_core.middleware import get_current_tenant_id
        from workflow_core_sdk.multitenancy import multitenancy_settings

        tenant_id = get_current_tenant_id()
        if tenant_id:
            schema_name = f"{multitenancy_settings.schema_prefix}{tenant_id}"
            session.execute(text(f'SET search_path TO "{schema_name}", public'))
            logger.debug(f"Applied tenant schema: {schema_name}")
    except ImportError:
        # db_core not available, skip tenant isolation
        pass
    except Exception as e:
        logger.warning(f"Failed to apply tenant schema: {e}")


def get_session() -> Generator[Session, None, None]:
    """
    Get database session with automatic tenant schema isolation.

    When a tenant context is set (via db_core's set_current_tenant_id or
    TenantMiddleware), the session automatically has its search_path set
    to the tenant's schema.

    This provides transparent data isolation without manual intervention.
    """
    with Session(engine) as session:
        _apply_tenant_schema(session)
        yield session


# Dependency for FastAPI
def get_db_session() -> Session:
    """
    FastAPI dependency for database session.

    Automatically applies tenant schema isolation when tenant context is set.

    Usage:
        @router.get("/items")
        def list_items(session: Session = Depends(get_db_session)):
            ...
    """
    session = Session(engine)
    _apply_tenant_schema(session)
    return session


# For backwards compatibility with existing code
async def get_database():
    """Legacy compatibility function"""
    from .service import DatabaseService

    return DatabaseService()

"""
Database engine and session management using SQLModel

This module provides the database engine, session management, and
database initialization functionality for the workflow engine.

Supports schema-based multitenancy when enabled via db-core middleware.
"""

import os
from typing import Generator
from sqlmodel import SQLModel, create_engine, Session
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor

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


def create_db_and_tables():
    """Create database tables"""
    SQLModel.metadata.create_all(engine)


def get_session() -> Generator[Session, None, None]:
    """
    Get database session with automatic tenant schema isolation.

    When multitenancy is enabled via initialize_tenant_db(), the db-core
    event listener automatically sets the PostgreSQL search_path to the
    tenant's schema based on the X-Tenant-ID request header.

    This provides transparent data isolation without manual intervention.
    """
    with Session(engine) as session:
        yield session


# Dependency for FastAPI
def get_db_session() -> Session:
    """
    FastAPI dependency for database session.

    Automatically applies tenant schema isolation when multitenancy is enabled.

    Usage:
        @router.get("/items")
        def list_items(session: Session = Depends(get_db_session)):
            ...
    """
    return next(get_session())


# For backwards compatibility with existing code
async def get_database():
    """Legacy compatibility function"""
    from .service import DatabaseService

    return DatabaseService()

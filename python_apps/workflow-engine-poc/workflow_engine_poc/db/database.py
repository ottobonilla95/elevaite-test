"""
Database engine and session management using SQLModel

This module provides the database engine, session management, and
database initialization functionality for the workflow engine.
"""

import os
from typing import Generator
from sqlmodel import SQLModel, create_engine, Session
from sqlalchemy.pool import StaticPool
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from contextlib import contextmanager

# Database configuration
DATABASE_URL = os.getenv(
    "WORKFLOW_ENGINE_DATABASE_URL",
    "postgresql://elevaite:elevaite@localhost:5433/workflow_engine",
)

# For development, fall back to SQLite if PostgreSQL is not available
SQLITE_DATABASE_URL = "sqlite:///./workflow_engine.db"

# Try PostgreSQL first, fall back to SQLite for development
try:
    # Test PostgreSQL connection
    test_engine = create_engine(DATABASE_URL, echo=False)
    with test_engine.connect():
        pass

    # PostgreSQL is available
    # Pool tuning via env vars with sensible defaults
    pool_size = int(os.getenv("WORKFLOW_ENGINE_DB_POOL_SIZE", os.getenv("DB_POOL_SIZE", "20")))
    max_overflow = int(os.getenv("WORKFLOW_ENGINE_DB_MAX_OVERFLOW", os.getenv("DB_MAX_OVERFLOW", "50")))
    pool_recycle = int(os.getenv("WORKFLOW_ENGINE_DB_POOL_RECYCLE", os.getenv("DB_POOL_RECYCLE", "1800")))  # seconds
    pool_timeout = int(os.getenv("WORKFLOW_ENGINE_DB_POOL_TIMEOUT", os.getenv("DB_POOL_TIMEOUT", "30")))  # seconds

    engine = create_engine(
        DATABASE_URL,
        echo=os.getenv("SQL_ECHO", "false").lower() == "true",
        pool_size=pool_size,
        max_overflow=max_overflow,
        pool_recycle=pool_recycle,
        pool_timeout=pool_timeout,
    )
    print(f"Connected to PostgreSQL: {DATABASE_URL}")

except Exception as e:
    # Fall back to SQLite for development
    print(f"PostgreSQL connection failed ({e}), falling back to SQLite")
    engine = create_engine(
        SQLITE_DATABASE_URL,
        echo=os.getenv("SQL_ECHO", "false").lower() == "true",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    print(f"Connected to SQLite: {SQLITE_DATABASE_URL}")

SQLAlchemyInstrumentor().instrument(engine=engine)  # OTEL


def create_db_and_tables():
    """Create database tables"""
    SQLModel.metadata.create_all(engine)


def get_session() -> Generator[Session, None, None]:
    """Get database session"""
    with Session(engine) as session:
        yield session


# Dependency for FastAPI
def get_db_session():
    """FastAPI dependency for database session"""
    return next(get_session())


# For backwards compatibility with existing code
async def get_database():
    """Legacy compatibility function"""
    from .service import DatabaseService

    return DatabaseService()

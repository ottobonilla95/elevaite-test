"""
Database configuration and session management.
"""

import os
from typing import Generator

from sqlmodel import Session, create_engine
from sqlalchemy.pool import NullPool

# Get database URL from environment
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/ingestion_db")

# Create engine with connection pooling disabled for DBOS compatibility
engine = create_engine(
    DATABASE_URL,
    echo=False,
    poolclass=NullPool,  # DBOS manages connections
)


def get_session() -> Generator[Session, None, None]:
    """Get a database session"""
    with Session(engine) as session:
        yield session


def init_db() -> None:
    """Initialize database tables"""
    from sqlmodel import SQLModel

    SQLModel.metadata.create_all(engine)


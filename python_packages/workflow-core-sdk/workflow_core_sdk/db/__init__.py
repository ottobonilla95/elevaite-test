"""
Database package for the Workflow Engine

This package contains all database-related functionality:
- SQLModel models for database tables
- Database engine and session management
- CRUD operations and services
- Tenant-aware database sessions for multitenancy
- Programmatic Alembic migrations for tenant schemas
"""

from .database import engine, get_session, create_db_and_tables
from .models import *
from .migrations import run_migrations_for_tenant, get_current_revision, stamp_revision

# Tenant-aware database (lazy import to avoid circular dependencies)
# Use: from workflow_core_sdk.db.tenant_db import get_tenant_db_session, initialize_tenant_db

__all__ = [
    "engine",
    "get_session",
    "create_db_and_tables",
    "run_migrations_for_tenant",
    "get_current_revision",
    "stamp_revision",
]

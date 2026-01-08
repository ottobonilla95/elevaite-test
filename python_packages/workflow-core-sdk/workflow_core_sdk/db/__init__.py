"""
Database package for the Workflow Engine

This package contains all database-related functionality:
- SQLModel models for database tables
- Database engine and session management
- CRUD operations and services
- Tenant-aware database sessions for multitenancy
"""

from .database import engine, get_session, create_db_and_tables
from .models import *

# Tenant-aware database (lazy import to avoid circular dependencies)
# Use: from workflow_core_sdk.db.tenant_db import get_tenant_db_session, initialize_tenant_db

__all__ = [
    "engine",
    "get_session",
    "create_db_and_tables",
]

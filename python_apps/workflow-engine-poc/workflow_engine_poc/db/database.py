"""
Database engine and session management - Re-exported from SDK

This module re-exports database functionality from workflow-core-sdk
to maintain backward compatibility with existing PoC code.

For main_sdk.py (SDK-only mode), this ensures a single database connection.
For main.py (legacy PoC mode), this still works but uses the SDK's database layer.
"""

# Re-export everything from the SDK's database module
from workflow_core_sdk.db.database import (
    DATABASE_URL,
    engine,
    create_db_and_tables,
    get_session,
    get_db_session,
)


# For backwards compatibility with existing code
async def get_database():
    """Legacy compatibility function"""
    from workflow_core_sdk.db.service import DatabaseService

    return DatabaseService()


__all__ = [
    "DATABASE_URL",
    "engine",
    "create_db_and_tables",
    "get_session",
    "get_db_session",
    "get_database",
]

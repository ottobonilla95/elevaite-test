"""
Database package for the Workflow Engine - Re-exported from SDK

This package re-exports database functionality from workflow-core-sdk
to maintain backward compatibility with existing PoC code.
"""

# Re-export from SDK via our database module (which itself re-exports from SDK)
from .database import engine, get_session, create_db_and_tables, DATABASE_URL
from .models import *

__all__ = [
    "engine",
    "get_session",
    "create_db_and_tables",
    "DATABASE_URL",
]

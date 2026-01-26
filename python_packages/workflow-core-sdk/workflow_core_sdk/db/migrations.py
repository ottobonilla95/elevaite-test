"""
Programmatic Alembic migration runner for multi-tenant schemas.

This module provides utilities to run Alembic migrations against specific
tenant schemas without needing to use the command line.
"""

import logging
import os
from pathlib import Path
from typing import Optional

from alembic import command
from alembic.config import Config

logger = logging.getLogger(__name__)

# Path to the alembic directory (relative to workflow-core-sdk package)
ALEMBIC_DIR = Path(__file__).parent.parent.parent / "alembic"
ALEMBIC_INI = ALEMBIC_DIR.parent / "alembic.ini"


def get_alembic_config(
    database_url: Optional[str] = None,
    tenant_schema: Optional[str] = None,
) -> Config:
    """
    Create an Alembic config for programmatic migrations.

    Args:
        database_url: Database URL (uses env var if not provided)
        tenant_schema: Target schema for multi-tenant migrations

    Returns:
        Configured Alembic Config object
    """
    config = Config(str(ALEMBIC_INI))
    config.set_main_option("script_location", str(ALEMBIC_DIR))

    if database_url:
        config.set_main_option("sqlalchemy.url", database_url)

    if tenant_schema:
        config.attributes["tenant_schema"] = tenant_schema

    return config


def run_migrations_for_tenant(
    tenant_schema: str,
    database_url: Optional[str] = None,
    revision: str = "head",
) -> None:
    """
    Run Alembic migrations for a specific tenant schema.

    Args:
        tenant_schema: The PostgreSQL schema to migrate
        database_url: Database URL (uses env var if not provided)
        revision: Target revision (default: "head" for latest)
    """
    logger.info(
        f"Running migrations for schema '{tenant_schema}' to revision '{revision}'"
    )

    config = get_alembic_config(database_url=database_url, tenant_schema=tenant_schema)
    command.upgrade(config, revision)

    logger.info(f"Migrations completed for schema '{tenant_schema}'")


def get_current_revision(
    tenant_schema: Optional[str] = None,
    database_url: Optional[str] = None,
) -> Optional[str]:
    """
    Get the current migration revision for a schema.

    Args:
        tenant_schema: The PostgreSQL schema to check
        database_url: Database URL (uses env var if not provided)

    Returns:
        Current revision string or None if no migrations applied
    """
    from alembic.runtime.migration import MigrationContext
    from sqlalchemy import create_engine, text

    db_url = database_url or os.getenv(
        "SQLALCHEMY_DATABASE_URL",
        os.getenv("WORKFLOW_ENGINE_DATABASE_URL"),
    )
    if not db_url:
        raise ValueError("No database URL provided")

    engine = create_engine(db_url)
    with engine.connect() as conn:
        if tenant_schema:
            conn.execute(text(f'SET search_path TO "{tenant_schema}", public'))

        context = MigrationContext.configure(
            conn,
            opts={"version_table_schema": tenant_schema} if tenant_schema else {},
        )
        return context.get_current_revision()


def stamp_revision(
    tenant_schema: str,
    revision: str = "head",
    database_url: Optional[str] = None,
) -> None:
    """
    Stamp a schema with a revision without running migrations.

    Useful for marking existing schemas as migrated.

    Args:
        tenant_schema: The PostgreSQL schema to stamp
        revision: Revision to stamp (default: "head")
        database_url: Database URL (uses env var if not provided)
    """
    logger.info(f"Stamping schema '{tenant_schema}' with revision '{revision}'")
    config = get_alembic_config(database_url=database_url, tenant_schema=tenant_schema)
    command.stamp(config, revision)
    logger.info(f"Schema '{tenant_schema}' stamped with revision '{revision}'")

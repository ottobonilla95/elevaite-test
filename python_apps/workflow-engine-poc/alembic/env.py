"""Alembic environment configuration for workflow-engine with multi-tenant support"""

from logging.config import fileConfig
import os
import sys
from sqlalchemy import engine_from_config, pool, text

from alembic import context

# Add the app directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Import models for autogenerate
from sqlmodel import SQLModel
from workflow_core_sdk.db.models import *  # noqa: F401, F403

target_metadata = SQLModel.metadata

# Tenant schema support:
# Set ALEMBIC_SCHEMA env var to run migrations in a specific schema
# Example: ALEMBIC_SCHEMA=workflow_default alembic upgrade head
target_schema = os.getenv("ALEMBIC_SCHEMA")

# Resolve the database URL used by Alembic in this order:
# 1) Value provided via Alembic Config (e.g., programmatic runs)
# 2) ALEMBIC_SQLALCHEMY_URL environment variable (for tests/CI)
# 3) DATABASE_URI or DATABASE_URL from environment
provided_url = config.get_main_option("sqlalchemy.url")
if provided_url:
    db_url = provided_url
else:
    override_url = os.getenv("ALEMBIC_SQLALCHEMY_URL")
    if override_url:
        db_url = override_url
    else:
        # Try both DATABASE_URI and DATABASE_URL for compatibility
        db_url = os.getenv("DATABASE_URI") or os.getenv("DATABASE_URL")

if not db_url:
    raise ValueError(
        "Database URL not provided. Set DATABASE_URI or DATABASE_URL environment variable."
    )

# Strip any accidental surrounding quotes from env files
db_url_clean = db_url.strip().strip('"').strip("'")

# Alembic requires synchronous database drivers
# Convert async URLs (postgresql+asyncpg://) to sync (postgresql://)
if "+asyncpg" in db_url_clean:
    db_url_clean = db_url_clean.replace("postgresql+asyncpg://", "postgresql://")

config.set_main_option("sqlalchemy.url", db_url_clean)


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    Supports tenant schema migrations via ALEMBIC_SCHEMA env var.
    """
    db_url = config.get_main_option("sqlalchemy.url")
    if db_url is None:
        raise Exception("DB URL not found")

    connectable = engine_from_config(
        {"sqlalchemy.url": db_url},
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        # Set search_path for tenant schema if specified
        if target_schema:
            connection.execute(text(f'SET search_path TO "{target_schema}", public'))
            connection.commit()
            print(f"Running migrations in schema: {target_schema}")

        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            version_table_schema=target_schema,  # Store alembic_version in tenant schema
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

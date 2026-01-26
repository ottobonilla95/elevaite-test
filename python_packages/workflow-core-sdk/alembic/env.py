import os
import sys
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool, text

from alembic import context

# Add the parent directory to the path so we can import workflow_core_sdk
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from workflow_core_sdk.db.models.base import BaseModel

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Database URL from environment or config
database_url = os.getenv(
    "SQLALCHEMY_DATABASE_URL",
    os.getenv(
        "WORKFLOW_ENGINE_DATABASE_URL",
        "postgresql://elevaite:elevaite@localhost:5433/agent_studio_2",
    ),
)
config.set_main_option("sqlalchemy.url", database_url)

# Target schema for multi-tenant migrations (None = public schema)
# Set via ALEMBIC_TENANT_SCHEMA env var or programmatically via config.attributes
target_schema = os.getenv("ALEMBIC_TENANT_SCHEMA") or config.attributes.get(
    "tenant_schema"
)

target_metadata = BaseModel.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
        version_table_schema=target_schema,
        include_schemas=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode with optional tenant schema support."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        # Set search_path to tenant schema if specified
        if target_schema:
            connection.execute(text(f'CREATE SCHEMA IF NOT EXISTS "{target_schema}"'))
            connection.execute(text(f'SET search_path TO "{target_schema}", public'))
            connection.commit()

        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
            version_table_schema=target_schema,
            include_schemas=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

"""Alembic environment configuration for toshiba_data database"""
from logging.config import fileConfig
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context
import os
import sys
import json

# Add the app directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# This is the Alembic Config object
config = context.config

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Load database URL from environment
def get_database_url():
    """Load database URL from OS env or local .env file"""
    conn_string = os.getenv("SR_ANALYTICS_DATABASE_URL")
    if not conn_string:
        raise ValueError(
            "Database URL not provided. Set SR_ANALYTICS_DATABASE_URL environment variable."
        )

    # Convert asyncpg to psycopg2 format if needed
    if 'postgresql+asyncpg://' in conn_string:
        conn_string = conn_string.replace('postgresql+asyncpg://', 'postgresql://')
        
    return conn_string
    
# Set the database URL
config.set_main_option('sqlalchemy.url', get_database_url())

# Add your model's MetaData object here for 'autogenerate' support
target_metadata = None

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
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
    """Run migrations in 'online' mode."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, 
            target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
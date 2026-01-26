"""
Tenant database initialization for the Workflow Engine.

This module provides schema initialization for multi-tenant deployments.
"""

import logging
from typing import Optional

from sqlalchemy import event, MetaData
from sqlmodel import SQLModel

from db_core import MultitenancySettings
from db_core.middleware import get_current_tenant_id
from db_core.utils import get_schema_name, tenant_schema_exists, create_tenant_schema

from workflow_core_sdk.multitenancy import multitenancy_settings, DEFAULT_TENANTS

# Import models to register with SQLModel.metadata
from workflow_core_sdk.db.models import *  # noqa: F401, F403

logger = logging.getLogger(__name__)
_event_listener_attached = False


def _attach_tenant_event_listener(engine, settings: MultitenancySettings):
    """Attach event listener to set search_path per connection checkout."""
    global _event_listener_attached
    if _event_listener_attached:
        return

    @event.listens_for(engine, "checkout")
    def set_search_path(dbapi_conn, conn_record, conn_proxy):
        tenant_id = get_current_tenant_id()
        schema = get_schema_name(tenant_id, settings) if tenant_id else "public"
        cursor = dbapi_conn.cursor()
        cursor.execute(f'SET search_path TO "{schema}", public')
        cursor.close()

    _event_listener_attached = True
    logger.info("Tenant event listener attached")


def initialize_tenant_db(
    settings: Optional[MultitenancySettings] = None,
    tenant_ids: Optional[list] = None,
    create_tables: bool = False,
) -> dict:
    """
    Initialize database with tenant schemas and optionally tables.

    Args:
        settings: Multitenancy settings (defaults to module settings)
        tenant_ids: Tenant IDs to create schemas for (defaults to DEFAULT_TENANTS)
        create_tables: Whether to create tables (default: False, tables should be created via migrations)

    Returns:
        Dictionary with engine info
    """
    from workflow_core_sdk.db.database import engine

    settings = settings or multitenancy_settings
    tenant_ids = tenant_ids or DEFAULT_TENANTS

    _attach_tenant_event_listener(engine, settings)

    for tenant_id in tenant_ids:
        schema_name = get_schema_name(tenant_id, settings)

        if not tenant_schema_exists(engine, schema_name):
            if not create_tenant_schema(engine, schema_name):
                raise RuntimeError(f"Failed to create schema {schema_name}")

            if create_tables:
                # Clone metadata with target schema and create tables
                target_metadata = MetaData(schema=schema_name)
                for table in SQLModel.metadata.tables.values():
                    table.to_metadata(target_metadata, schema=schema_name)
                target_metadata.create_all(engine)
                logger.info(f"Created schema {schema_name} with tables")
            else:
                logger.info(
                    f"Created schema {schema_name}. Tables should be created via migrations."
                )
        else:
            logger.debug(f"Schema {schema_name} already exists")

    return {"engine": engine}

"""
Tenant-aware database connection and session management for the Workflow Engine.

This module provides schema-based multitenancy support using db-core,
with sync SQLModel sessions for workflow data isolation per tenant.
"""

import logging
from typing import Generator, Optional

from sqlalchemy import event, text, MetaData
from sqlmodel import SQLModel, Session

from db_core import MultitenancySettings
from db_core.middleware import get_current_tenant_id
from db_core.utils import (
    get_schema_name,
    tenant_schema_exists,
    create_tenant_schema,
)

from workflow_core_sdk.multitenancy import multitenancy_settings, DEFAULT_TENANTS

# Import all models to ensure they are registered with SQLModel.metadata
# This is required for create_all() to create the tables
# fmt: off
from workflow_core_sdk.db.models import (  # noqa: F401
    Workflow,
    WorkflowExecution,
    StepExecution,
    StepType,
    Agent,
    AgentToolBinding,
    AgentMessage,
    Prompt,
    Tool,
    ToolCategory,
    MCPServer,
    ApprovalRequest,
    A2AAgent,
    AgentExecutionMetrics,
    WorkflowMetrics,
)
# fmt: on

logger = logging.getLogger(__name__)

# Track if event listener has been attached
_event_listener_attached = False


def _attach_tenant_event_listener(engine, settings: MultitenancySettings):
    """
    Attach SQLAlchemy event listener to set search_path on each connection checkout.

    This ensures every database connection automatically uses the correct
    tenant schema based on the X-Tenant-ID header in the request context.

    We use the 'checkout' event instead of 'connect' because:
    - 'connect' only fires when a new connection is created
    - 'checkout' fires every time a connection is checked out from the pool
    - This ensures per-request tenant isolation with connection pooling
    """
    global _event_listener_attached

    if _event_listener_attached:
        logger.debug("Tenant event listener already attached, skipping")
        return

    @event.listens_for(engine, "checkout")
    def set_search_path(dbapi_connection, connection_record, connection_proxy):
        """Set search_path when connection is checked out from pool."""
        tenant_id = get_current_tenant_id()
        if tenant_id:
            schema = get_schema_name(tenant_id, settings)
            cursor = dbapi_connection.cursor()
            cursor.execute(f'SET search_path TO "{schema}", public')
            cursor.close()
            logger.debug(f"Connection search_path set to: {schema}")
        else:
            # Reset to public schema when no tenant context
            cursor = dbapi_connection.cursor()
            cursor.execute("SET search_path TO public")
            cursor.close()
            logger.debug("Connection search_path reset to: public")

    _event_listener_attached = True
    logger.info("Tenant event listener attached to database engine")


def initialize_tenant_db(
    settings: Optional[MultitenancySettings] = None,
    tenant_ids: Optional[list] = None,
) -> dict:
    """
    Initialize the database with tenant schemas.

    This creates the necessary schemas for each tenant and attaches
    the event listener for automatic search_path switching.

    Args:
        settings: Multitenancy settings (defaults to module settings)
        tenant_ids: List of tenant IDs to create schemas for (defaults to DEFAULT_TENANTS)

    Returns:
        Dictionary with engine info
    """
    # Import here to avoid circular imports
    from workflow_core_sdk.db.database import engine

    settings = settings or multitenancy_settings
    tenant_ids = tenant_ids or DEFAULT_TENANTS

    logger.info(f"Initializing tenant database with tenants: {tenant_ids}")

    # Attach event listener to existing engine for automatic schema switching
    _attach_tenant_event_listener(engine, settings)

    # Create schemas and tables for each tenant
    for tenant_id in tenant_ids:
        schema_name = get_schema_name(tenant_id, settings)

        if not tenant_schema_exists(engine, schema_name):
            success = create_tenant_schema(engine, schema_name)
            if not success:
                raise RuntimeError(f"Failed to create schema {schema_name} for tenant {tenant_id}")

            # Create all SQLModel tables in the tenant schema
            # We need to clone the metadata with the target schema because
            # SQLAlchemy's create_all doesn't respect search_path for table creation
            target_metadata = MetaData(schema=schema_name)
            for table in SQLModel.metadata.tables.values():
                table.to_metadata(target_metadata, schema=schema_name)
            target_metadata.create_all(engine)

            logger.info(f"Created schema {schema_name} for tenant {tenant_id} with all tables")
        else:
            logger.info(f"Schema {schema_name} for tenant {tenant_id} already exists")

    logger.info("Tenant database initialization completed successfully")
    return {"engine": engine}


def get_tenant_session(
    settings: Optional[MultitenancySettings] = None,
    tenant_id: Optional[str] = None,
) -> Generator[Session, None, None]:
    """
    Get a tenant-aware database session with explicit schema setting.

    This is an alternative to the automatic event listener approach,
    useful when you need explicit control over the tenant context.

    Args:
        settings: Multitenancy settings (defaults to module settings)
        tenant_id: Explicit tenant ID (defaults to current context tenant)

    Yields:
        SQLModel Session with tenant schema context
    """
    from workflow_core_sdk.db.database import engine

    settings = settings or multitenancy_settings

    # Get tenant ID from context or use provided/default
    resolved_tenant_id = tenant_id or get_current_tenant_id() or settings.default_tenant_id

    if not resolved_tenant_id:
        raise ValueError("No tenant ID available. Provide tenant_id or set X-Tenant-ID header.")

    schema_name = get_schema_name(resolved_tenant_id, settings)

    with Session(engine) as session:
        # Explicitly set search path to tenant schema
        session.execute(text(f'SET search_path TO "{schema_name}", public'))
        yield session


def get_tenant_db_session(
    settings: Optional[MultitenancySettings] = None,
) -> Session:
    """
    FastAPI dependency for tenant-aware database session with explicit schema.

    Note: When using the standard get_db_session() from database.py, the tenant
    schema is set automatically via the event listener. This function is provided
    for cases where you need explicit tenant control.

    Usage:
        @router.get("/items")
        def list_items(session: Session = Depends(get_tenant_db_session)):
            ...

    Args:
        settings: Multitenancy settings (defaults to module settings)

    Returns:
        SQLModel Session with tenant schema context
    """
    return next(get_tenant_session(settings))


def get_current_tenant() -> str:
    """
    Get the current tenant ID from the request context.

    Returns:
        The current tenant ID, or the default tenant if none is set
    """
    tenant_id = get_current_tenant_id()
    if tenant_id is None:
        tenant_id = multitenancy_settings.default_tenant_id or "default"
        logger.debug(f"No tenant ID in context, using default: {tenant_id}")
    else:
        logger.debug(f"Using tenant ID from context: {tenant_id}")
    return tenant_id

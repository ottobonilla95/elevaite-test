"""
Utility functions for working with tenants.
"""

import logging
import re
from typing import List, Optional, Union

from sqlalchemy import text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncEngine

from db_core.config import MultitenancySettings
from db_core.exceptions import InvalidTenantIdError

logger = logging.getLogger(__name__)


def get_schema_name(tenant_id: str, settings: MultitenancySettings) -> str:
    """
    Generate the schema name for a tenant.

    Args:
        tenant_id: The tenant ID
        settings: The multitenancy settings

    Returns:
        The schema name
    """
    # Check if tenant_id is a string
    if not isinstance(tenant_id, str):
        raise TypeError(f"tenant_id must be a string, got {type(tenant_id).__name__}")

    # Normalize tenant ID if case sensitivity is not required
    if not settings.case_sensitive_tenant_id:
        tenant_id = tenant_id.lower()

    return f"{settings.schema_prefix}{tenant_id}"


def validate_tenant_id(tenant_id: str, settings: MultitenancySettings) -> bool:
    """
    Validate a tenant ID against the configured pattern.

    Args:
        tenant_id: The tenant ID to validate
        settings: The multitenancy settings

    Returns:
        True if the tenant ID is valid, False otherwise

    Raises:
        InvalidTenantIdError: If the tenant ID is invalid
    """
    if not tenant_id:
        return False

    if not re.match(settings.tenant_id_validation_pattern, tenant_id):
        raise InvalidTenantIdError(tenant_id, settings.tenant_id_validation_pattern)

    return True


def tenant_schema_exists(engine: Union[Engine, AsyncEngine], schema_name: str) -> bool:
    """
    Check if a tenant schema exists.

    Args:
        engine: SQLAlchemy engine (sync or async)
        schema_name: The schema name to check

    Returns:
        True if the schema exists, False otherwise
    """
    # Handle async engines differently
    is_async = isinstance(engine, AsyncEngine)

    if is_async:
        # For async engines, we need to delegate to a method that can be awaited
        # Since this function can't be async (used in both async and sync contexts),
        # we have to return a default value for async engines
        logger.warning(
            "tenant_schema_exists called with AsyncEngine. This function can't check "
            "schema existence with an async engine. Returning False."
        )
        return False

    # For synchronous engines, proceed as before
    try:
        with engine.connect() as conn:
            # Check if schema exists in PostgreSQL
            query = text("SELECT EXISTS(SELECT 1 FROM information_schema.schemata WHERE schema_name = :schema_name)")
            result = conn.execute(query, {"schema_name": schema_name})
            return bool(result.scalar())
    except SQLAlchemyError as e:
        logger.error(f"Error checking if schema {schema_name} exists: {e}")
        return False


async def async_tenant_schema_exists(engine: AsyncEngine, schema_name: str) -> bool:
    """
    Asynchronously check if a tenant schema exists.

    Args:
        engine: SQLAlchemy async engine
        schema_name: The schema name to check

    Returns:
        True if the schema exists, False otherwise
    """
    try:
        async with engine.connect() as conn:
            # Check if schema exists in PostgreSQL
            query = text("SELECT EXISTS(SELECT 1 FROM information_schema.schemata WHERE schema_name = :schema_name)")
            result = await conn.execute(query, {"schema_name": schema_name})
            return bool(result.scalar())
    except SQLAlchemyError as e:
        logger.error(f"Error checking if schema {schema_name} exists: {e}")
        return False


def create_tenant_schema(engine: Union[Engine, AsyncEngine], schema_name: str) -> bool:
    """
    Create a tenant schema if it doesn't exist.

    Args:
        engine: SQLAlchemy engine (sync or async)
        schema_name: The schema name to create

    Returns:
        True if successful, False otherwise
    """
    # Handle async engines differently
    is_async = isinstance(engine, AsyncEngine)

    if is_async:
        # For async engines, we can't proceed in a synchronous function
        logger.warning(
            "create_tenant_schema called with AsyncEngine. This function can't create "
            "a schema with an async engine. Use async_create_tenant_schema instead. Returning False."
        )
        return False

    # For synchronous engines
    if tenant_schema_exists(engine, schema_name):
        return True

    try:
        with engine.begin() as conn:
            # Create schema if it doesn't exist
            conn.execute(text(f'CREATE SCHEMA IF NOT EXISTS "{schema_name}"'))
        return True
    except SQLAlchemyError as e:
        logger.error(f"Error creating schema {schema_name}: {e}")
        return False


async def async_create_tenant_schema(engine: AsyncEngine, schema_name: str) -> bool:
    """
    Asynchronously create a tenant schema if it doesn't exist.

    Args:
        engine: SQLAlchemy async engine
        schema_name: The schema name to create

    Returns:
        True if successful, False otherwise
    """
    if await async_tenant_schema_exists(engine, schema_name):
        return True

    try:
        async with engine.begin() as conn:
            # Create schema if it doesn't exist
            await conn.execute(text(f'CREATE SCHEMA IF NOT EXISTS "{schema_name}"'))
        return True
    except SQLAlchemyError as e:
        logger.error(f"Error creating schema {schema_name}: {e}")
        return False


def list_tenant_schemas(engine: Union[Engine, AsyncEngine], schema_prefix: str) -> List[str]:
    """
    List all tenant schemas.

    Args:
        engine: SQLAlchemy engine (sync or async)
        schema_prefix: The prefix used for tenant schemas

    Returns:
        List of tenant schema names
    """
    # Handle async engines differently
    is_async = isinstance(engine, AsyncEngine)

    if is_async:
        # For async engines, we can't proceed in a synchronous function
        logger.warning(
            "list_tenant_schemas called with AsyncEngine. This function can't list "
            "schemas with an async engine. Use async_list_tenant_schemas instead. Returning empty list."
        )
        return []

    # For synchronous engines
    try:
        with engine.connect() as conn:
            query = text("SELECT schema_name FROM information_schema.schemata WHERE schema_name LIKE :prefix")
            result = conn.execute(query, {"prefix": f"{schema_prefix}%"})
            return [row[0] for row in result]
    except SQLAlchemyError as e:
        logger.error(f"Error listing tenant schemas: {e}")
        return []


async def async_list_tenant_schemas(engine: AsyncEngine, schema_prefix: str) -> List[str]:
    """
    Asynchronously list all tenant schemas.

    Args:
        engine: SQLAlchemy async engine
        schema_prefix: The prefix used for tenant schemas

    Returns:
        List of tenant schema names
    """
    try:
        async with engine.connect() as conn:
            query = text("SELECT schema_name FROM information_schema.schemata WHERE schema_name LIKE :prefix")
            result = await conn.execute(query, {"prefix": f"{schema_prefix}%"})
            return [row[0] for row in result]
    except SQLAlchemyError as e:
        logger.error(f"Error listing tenant schemas: {e}")
        return []


def get_tenant_id_from_schema(schema_name: str, schema_prefix: str) -> Optional[str]:
    """
    Extract tenant ID from schema name.

    Args:
        schema_name: The schema name
        schema_prefix: The prefix used for tenant schemas

    Returns:
        The tenant ID, or None if the schema name doesn't match the expected pattern
    """
    if schema_name.startswith(schema_prefix):
        return schema_name[len(schema_prefix) :]
    return None


def set_tenant_search_path(engine: Union[Engine, AsyncEngine], schema_name: str) -> bool:
    """
    Set the search path for a connection to include the tenant schema.

    Args:
        engine: SQLAlchemy engine (sync or async)
        schema_name: The schema name

    Returns:
        True if successful, False otherwise
    """
    # Handle async engines differently
    is_async = isinstance(engine, AsyncEngine)

    if is_async:
        # For async engines, we can't proceed in a synchronous function
        logger.warning(
            "set_tenant_search_path called with AsyncEngine. This function can't set search path "
            "with an async engine. Use async_set_tenant_search_path instead. Returning False."
        )
        return False

    # For synchronous engines
    try:
        # Create a connection and explicitly commit the change
        with engine.begin() as conn:
            conn.execute(text(f'SET search_path TO "{schema_name}", public'))

        # Verify the search path was set correctly
        with engine.connect() as conn:
            result = conn.execute(text("SHOW search_path"))
            logger.info(f"Set search path to: {result.scalar()}")

        return True
    except SQLAlchemyError as e:
        logger.error(f"Error setting search path to {schema_name}: {e}")
        return False


async def async_set_tenant_search_path(engine: AsyncEngine, schema_name: str) -> bool:
    """
    Asynchronously set the search path for a connection to include the tenant schema.

    Args:
        engine: SQLAlchemy async engine
        schema_name: The schema name

    Returns:
        True if successful, False otherwise
    """
    try:
        async with engine.connect() as conn:
            await conn.execute(text(f'SET search_path TO "{schema_name}", public'))
            return True
    except SQLAlchemyError as e:
        logger.error(f"Error setting search path to {schema_name}: {e}")
        return False

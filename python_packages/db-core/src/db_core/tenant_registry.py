"""
Tenant Registry for dynamic tenant provisioning.

This module provides a registry for managing tenants dynamically,
including creating, listing, and deactivating tenants at runtime.
"""

import logging
from typing import Any, Callable, Coroutine, Dict, List, Optional

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from db_core.config import MultitenancySettings
from db_core.models import Tenant, TenantStatus
from db_core.utils import get_schema_name

logger = logging.getLogger(__name__)

# Type for tenant initializer callbacks
TenantInitializer = Callable[[str, AsyncSession], Coroutine[Any, Any, None]]

# Global registry of tenant initializers
_tenant_initializers: List[TenantInitializer] = []


def register_tenant_initializer(initializer: TenantInitializer) -> TenantInitializer:
    """
    Register a callback to be invoked when a new tenant is created.

    This can be used as a decorator:

        @register_tenant_initializer
        async def init_my_service_tables(tenant_id: str, session: AsyncSession):
            # Create service-specific tables or seed data
            ...

    Args:
        initializer: Async function that takes tenant_id and session

    Returns:
        The same initializer function (for decorator usage)
    """
    _tenant_initializers.append(initializer)
    logger.info(f"Registered tenant initializer: {initializer.__name__}")
    return initializer


def get_tenant_initializers() -> List[TenantInitializer]:
    """Get all registered tenant initializers."""
    return _tenant_initializers.copy()


def clear_tenant_initializers() -> None:
    """Clear all registered tenant initializers. Useful for testing."""
    _tenant_initializers.clear()


class TenantRegistry:
    """
    Registry for managing tenants dynamically.

    This class provides methods for creating, listing, and managing tenants
    without requiring application restarts.
    """

    def __init__(self, settings: MultitenancySettings):
        """
        Initialize the tenant registry.

        Args:
            settings: Multitenancy configuration settings
        """
        self.settings = settings

    async def create_tenant(
        self,
        session: AsyncSession,
        tenant_id: str,
        name: str,
        description: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        run_initializers: bool = True,
    ) -> Tenant:
        """
        Create a new tenant with its schema.

        Args:
            session: Database session
            tenant_id: Unique tenant identifier
            name: Human-readable tenant name
            description: Optional description
            metadata: Optional JSON metadata
            run_initializers: Whether to run registered initializers

        Returns:
            The created Tenant object

        Raises:
            ValueError: If tenant already exists
        """
        # Check if tenant already exists
        existing = await self.get_tenant(session, tenant_id)
        if existing:
            raise ValueError(f"Tenant '{tenant_id}' already exists")

        # Calculate schema name
        schema_name = get_schema_name(tenant_id, self.settings)

        # Create the schema
        await session.execute(text(f'CREATE SCHEMA IF NOT EXISTS "{schema_name}"'))
        logger.info(f"Created schema '{schema_name}' for tenant '{tenant_id}'")

        # Create tenant record
        tenant = Tenant(
            tenant_id=tenant_id,
            name=name,
            description=description,
            schema_name=schema_name,
            metadata_=metadata,
            status=TenantStatus.ACTIVE.value,
            is_schema_initialized=False,
        )
        session.add(tenant)
        await session.flush()

        # Run tenant initializers
        if run_initializers:
            for initializer in _tenant_initializers:
                try:
                    await initializer(tenant_id, session)
                    logger.info(f"Ran initializer '{initializer.__name__}' for tenant '{tenant_id}'")
                except Exception as e:
                    logger.error(f"Initializer '{initializer.__name__}' failed for tenant '{tenant_id}': {e}")
                    raise

            tenant.is_schema_initialized = True

        await session.commit()
        await session.refresh(tenant)

        logger.info(f"Created tenant '{tenant_id}' with schema '{schema_name}'")
        return tenant

    async def get_tenant(self, session: AsyncSession, tenant_id: str) -> Optional[Tenant]:
        """
        Get a tenant by its ID.

        Args:
            session: Database session
            tenant_id: Tenant identifier

        Returns:
            Tenant object or None if not found
        """
        result = await session.execute(select(Tenant).where(Tenant.tenant_id == tenant_id))
        return result.scalar_one_or_none()

    async def list_tenants(
        self,
        session: AsyncSession,
        status: Optional[TenantStatus] = None,
        include_inactive: bool = False,
    ) -> List[Tenant]:
        """
        List all tenants.

        Args:
            session: Database session
            status: Optional filter by status
            include_inactive: Whether to include inactive tenants

        Returns:
            List of Tenant objects
        """
        query = select(Tenant)

        if status:
            query = query.where(Tenant.status == status.value)
        elif not include_inactive:
            query = query.where(Tenant.status != TenantStatus.INACTIVE.value)

        result = await session.execute(query.order_by(Tenant.created_at))
        return list(result.scalars().all())

    async def update_tenant(
        self,
        session: AsyncSession,
        tenant_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        status: Optional[TenantStatus] = None,
    ) -> Optional[Tenant]:
        """
        Update a tenant's metadata.

        Args:
            session: Database session
            tenant_id: Tenant identifier
            name: Optional new name
            description: Optional new description
            metadata: Optional new metadata (replaces existing)
            status: Optional new status

        Returns:
            Updated Tenant object or None if not found
        """
        tenant = await self.get_tenant(session, tenant_id)
        if not tenant:
            return None

        if name is not None:
            tenant.name = name
        if description is not None:
            tenant.description = description
        if metadata is not None:
            tenant.metadata_ = metadata
        if status is not None:
            tenant.status = status.value

        await session.commit()
        await session.refresh(tenant)

        logger.info(f"Updated tenant '{tenant_id}'")
        return tenant

    async def deactivate_tenant(
        self,
        session: AsyncSession,
        tenant_id: str,
    ) -> Optional[Tenant]:
        """
        Deactivate a tenant (soft delete).

        This sets the tenant status to INACTIVE but preserves the schema
        and data for potential recovery.

        Args:
            session: Database session
            tenant_id: Tenant identifier

        Returns:
            Updated Tenant object or None if not found
        """
        return await self.update_tenant(session, tenant_id, status=TenantStatus.INACTIVE)

    async def activate_tenant(
        self,
        session: AsyncSession,
        tenant_id: str,
    ) -> Optional[Tenant]:
        """
        Activate (or reactivate) a tenant.

        Args:
            session: Database session
            tenant_id: Tenant identifier

        Returns:
            Updated Tenant object or None if not found
        """
        return await self.update_tenant(session, tenant_id, status=TenantStatus.ACTIVE)

    async def delete_tenant(
        self,
        session: AsyncSession,
        tenant_id: str,
        drop_schema: bool = False,
    ) -> bool:
        """
        Delete a tenant permanently.

        WARNING: If drop_schema is True, this will permanently delete
        all data in the tenant's schema.

        Args:
            session: Database session
            tenant_id: Tenant identifier
            drop_schema: Whether to also drop the PostgreSQL schema

        Returns:
            True if deleted, False if not found
        """
        tenant = await self.get_tenant(session, tenant_id)
        if not tenant:
            return False

        schema_name = tenant.schema_name

        # Delete tenant record
        await session.delete(tenant)

        # Optionally drop the schema
        if drop_schema:
            await session.execute(text(f'DROP SCHEMA IF EXISTS "{schema_name}" CASCADE'))
            logger.warning(f"Dropped schema '{schema_name}' for tenant '{tenant_id}'")

        await session.commit()
        logger.info(f"Deleted tenant '{tenant_id}'")
        return True

    async def ensure_tenant_table(self, session: AsyncSession) -> None:
        """
        Ensure the _tenants table exists in the public schema.

        This should be called during application startup.

        Args:
            session: Database session
        """
        # Create the table using raw SQL for simplicity
        await session.execute(
            text("""
            CREATE TABLE IF NOT EXISTS public._tenants (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                tenant_id VARCHAR(100) UNIQUE NOT NULL,
                name VARCHAR(255) NOT NULL,
                description TEXT,
                status VARCHAR(20) NOT NULL DEFAULT 'active',
                schema_name VARCHAR(100) NOT NULL,
                metadata JSONB,
                is_schema_initialized BOOLEAN NOT NULL DEFAULT FALSE,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
        """)
        )
        await session.execute(
            text("""
            CREATE INDEX IF NOT EXISTS ix__tenants_tenant_id ON public._tenants(tenant_id)
        """)
        )
        await session.commit()
        logger.info("Ensured _tenants table exists")

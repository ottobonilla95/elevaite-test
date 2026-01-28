"""
Tenant Registry for dynamic tenant provisioning.
"""

import logging
import time
from threading import RLock
from typing import Any, Callable, Coroutine, Dict, List, Optional, Set

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from db_core.audit import (
    TenantAuditEvent,
    log_tenant_activated,
    log_tenant_created,
    log_tenant_deactivated,
    log_tenant_deleted,
    log_tenant_event,
    log_tenant_init_completed,
    log_tenant_init_failed,
    log_tenant_init_started,
    log_tenant_updated,
)
from db_core.config import MultitenancySettings
from db_core.models import Tenant, TenantStatus
from db_core.utils import get_schema_name

logger = logging.getLogger(__name__)


class TenantCache:
    """Thread-safe cache for active tenant IDs with TTL."""

    def __init__(self, ttl_seconds: int = 60):
        self._active_tenants: Set[str] = set()
        self._last_refresh: float = 0
        self._ttl_seconds = ttl_seconds
        self._lock = RLock()
        self._initialized = False

    def is_active(self, tenant_id: str) -> Optional[bool]:
        """Check if tenant is active. Returns None if cache needs refresh."""
        with self._lock:
            if (
                not self._initialized
                or time.time() - self._last_refresh > self._ttl_seconds
            ):
                return None
            return tenant_id in self._active_tenants

    def refresh(self, active_tenant_ids: Set[str]) -> None:
        """Refresh cache with active tenant IDs."""
        with self._lock:
            self._active_tenants = active_tenant_ids.copy()
            self._last_refresh = time.time()
            self._initialized = True

    def add_tenant(self, tenant_id: str) -> None:
        """Add tenant to cache."""
        with self._lock:
            self._active_tenants.add(tenant_id)

    def remove_tenant(self, tenant_id: str) -> None:
        """Remove tenant from cache."""
        with self._lock:
            self._active_tenants.discard(tenant_id)


_tenant_cache = TenantCache(ttl_seconds=60)


def get_tenant_cache() -> TenantCache:
    """Get global tenant cache instance."""
    return _tenant_cache


TenantInitializer = Callable[[str, AsyncSession], Coroutine[Any, Any, None]]
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
        log_tenant_event(
            TenantAuditEvent.TENANT_SCHEMA_CREATED,
            tenant_id,
            details={"schema_name": schema_name},
        )

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
            log_tenant_init_started(tenant_id, schema_name)
            for initializer in _tenant_initializers:
                try:
                    await initializer(tenant_id, session)
                    logger.info(
                        f"Ran initializer '{initializer.__name__}' for tenant '{tenant_id}'"
                    )
                except Exception as e:
                    log_tenant_init_failed(tenant_id, schema_name, str(e))
                    raise

            tenant.is_schema_initialized = True
            log_tenant_init_completed(tenant_id, schema_name)

        await session.commit()
        await session.refresh(tenant)

        # Update cache with new tenant
        _tenant_cache.add_tenant(tenant_id)

        log_tenant_created(tenant_id, display_name=name)
        return tenant

    async def get_tenant(
        self, session: AsyncSession, tenant_id: str
    ) -> Optional[Tenant]:
        """
        Get a tenant by its ID.

        Args:
            session: Database session
            tenant_id: Tenant identifier

        Returns:
            Tenant object or None if not found
        """
        result = await session.execute(
            select(Tenant).where(Tenant.tenant_id == tenant_id)
        )
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

    async def get_active_tenant_ids(self, session: AsyncSession) -> Set[str]:
        """
        Get all active tenant IDs.

        This is used to refresh the tenant cache.

        Args:
            session: Database session

        Returns:
            Set of active tenant IDs
        """
        query = select(Tenant.tenant_id).where(
            Tenant.status == TenantStatus.ACTIVE.value
        )
        result = await session.execute(query)
        return {row[0] for row in result.fetchall()}

    async def refresh_cache(self, session: AsyncSession) -> None:
        """
        Refresh the tenant cache with current active tenants from database.

        Args:
            session: Database session
        """
        active_tenant_ids = await self.get_active_tenant_ids(session)
        _tenant_cache.refresh(active_tenant_ids)
        logger.info(
            f"Refreshed tenant cache with {len(active_tenant_ids)} active tenants"
        )

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

        changes = {}
        if name is not None:
            changes["name"] = {"old": tenant.name, "new": name}
            tenant.name = name
        if description is not None:
            changes["description"] = {"old": tenant.description, "new": description}
            tenant.description = description
        if metadata is not None:
            changes["metadata"] = "updated"
            tenant.metadata_ = metadata
        if status is not None:
            changes["status"] = {"old": tenant.status, "new": status.value}
            tenant.status = status.value

        await session.commit()
        await session.refresh(tenant)

        if changes:
            log_tenant_updated(tenant_id, changes)
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
        result = await self.update_tenant(
            session, tenant_id, status=TenantStatus.INACTIVE
        )
        if result:
            _tenant_cache.remove_tenant(tenant_id)
            log_tenant_deactivated(tenant_id)
        return result

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
        result = await self.update_tenant(
            session, tenant_id, status=TenantStatus.ACTIVE
        )
        if result:
            _tenant_cache.add_tenant(tenant_id)
            log_tenant_activated(tenant_id)
        return result

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
            await session.execute(
                text(f'DROP SCHEMA IF EXISTS "{schema_name}" CASCADE')
            )
            log_tenant_event(
                TenantAuditEvent.TENANT_SCHEMA_DROPPED,
                tenant_id,
                details={"schema_name": schema_name},
            )

        await session.commit()

        # Remove from cache
        _tenant_cache.remove_tenant(tenant_id)

        log_tenant_deleted(tenant_id, drop_schema=drop_schema)
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

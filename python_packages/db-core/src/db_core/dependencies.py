"""
FastAPI dependencies for tenant-aware database sessions.
"""

from functools import lru_cache
from typing import AsyncGenerator, Callable, Generator, Optional

from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from db_core.config import MultitenancySettings
from db_core.db import get_tenant_async_session, get_tenant_session
from db_core.middleware import get_current_tenant_id


@lru_cache()
def get_multitenancy_settings() -> MultitenancySettings:
    """
    Get the multitenancy settings.

    Returns:
        The multitenancy settings
    """
    return MultitenancySettings()


# Define dependencies as constants to avoid function calls in default arguments
multitenancy_settings_dependency = Depends(get_multitenancy_settings)


def get_tenant_id(settings: MultitenancySettings = multitenancy_settings_dependency) -> str:
    """
    Get the current tenant ID from the context.

    Args:
        settings: The multitenancy settings

    Returns:
        The current tenant ID

    Raises:
        HTTPException: If no tenant ID is set
    """
    tenant_id = get_current_tenant_id()
    if tenant_id is None:
        if settings.default_tenant_id:
            return settings.default_tenant_id
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No tenant ID provided",
        )
    return tenant_id


# Define tenant_id dependency as a constant
tenant_id_dependency = Depends(get_tenant_id)


def get_tenant_db(
    settings: MultitenancySettings = multitenancy_settings_dependency,
    _: str = tenant_id_dependency,  # This ensures a valid tenant ID exists but we don't use the value
) -> Generator[Session, None, None]:
    """
    FastAPI dependency for getting a tenant-specific database session.

    Args:
        settings: The multitenancy settings
        tenant_id: The tenant ID

    Yields:
        SQLAlchemy session with tenant context
    """
    db = get_tenant_session(settings)
    try:
        yield db
    finally:
        db.close()


async def get_tenant_async_db(
    settings: MultitenancySettings = multitenancy_settings_dependency,
    _: str = tenant_id_dependency,  # This ensures a valid tenant ID exists but we don't use the value
) -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency for getting a tenant-specific async database session.

    Args:
        settings: The multitenancy settings
        tenant_id: The tenant ID

    Yields:
        SQLAlchemy async session with tenant context
    """
    db = await get_tenant_async_session(settings)
    try:
        yield db
    finally:
        await db.close()


class TenantValidator:
    """
    Dependency for validating tenant existence.
    """

    def __init__(
        self,
        tenant_callback: Callable[[str], bool],
        settings: Optional[MultitenancySettings] = None,
    ):
        """
        Initialize the tenant validator.

        Args:
            tenant_callback: Callback function to validate tenant existence
            settings: Optional multitenancy settings
        """
        self.tenant_callback = tenant_callback
        self.settings = settings or MultitenancySettings()

    def __call__(self, tenant_id: str = tenant_id_dependency) -> str:
        """
        Validate the tenant existence.

        Args:
            tenant_id: The tenant ID

        Returns:
            The validated tenant ID

        Raises:
            HTTPException: If the tenant doesn't exist
        """
        if not self.tenant_callback(tenant_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tenant not found: {tenant_id}",
            )
        return tenant_id


class AdminOnly:
    """
    Dependency for restricting access to admin tenant only.
    """

    def __init__(self, settings: Optional[MultitenancySettings] = None):
        """
        Initialize the admin-only dependency.

        Args:
            settings: Optional multitenancy settings
        """
        self.settings = settings or MultitenancySettings()

    def __call__(self, tenant_id: str = tenant_id_dependency) -> str:
        """
        Validate that the current tenant is the admin tenant.

        Args:
            tenant_id: The tenant ID

        Returns:
            The tenant ID

        Raises:
            HTTPException: If the tenant is not the admin tenant
        """
        if not self.settings.admin_tenant_id:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Admin tenant ID not configured",
            )

        if tenant_id != self.settings.admin_tenant_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin access required",
            )

        return tenant_id

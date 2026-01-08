"""
FastAPI router for tenant administration.

This router provides REST endpoints for managing tenants dynamically.
APIs can include this router to enable tenant provisioning.
"""

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from db_core.models import TenantStatus

logger = logging.getLogger(__name__)


# ============================================================================
# Request/Response Models
# ============================================================================


class TenantCreate(BaseModel):
    """Request model for creating a new tenant."""

    tenant_id: str = Field(
        ...,
        min_length=1,
        max_length=100,
        pattern=r"^[a-z][a-z0-9_]*$",
        description="Unique tenant identifier (lowercase alphanumeric with underscores)",
    )
    name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Human-readable tenant name",
    )
    description: Optional[str] = Field(
        None,
        description="Optional tenant description",
    )
    metadata: Optional[Dict[str, Any]] = Field(
        None,
        description="Optional JSON metadata",
    )


class TenantUpdate(BaseModel):
    """Request model for updating a tenant."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    status: Optional[TenantStatus] = None


class TenantResponse(BaseModel):
    """Response model for tenant data."""

    id: str
    tenant_id: str
    name: str
    description: Optional[str]
    status: str
    schema_name: str
    metadata: Optional[Dict[str, Any]]
    is_schema_initialized: bool
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class TenantListResponse(BaseModel):
    """Response model for listing tenants."""

    tenants: List[TenantResponse]
    total: int


class MessageResponse(BaseModel):
    """Simple message response."""

    message: str


# ============================================================================
# Router Factory
# ============================================================================


def create_tenant_admin_router(
    get_session: Any,
    get_registry: Any,
    prefix: str = "/tenants",
    tags: Optional[List[str]] = None,
    dependencies: Optional[List[Any]] = None,
) -> APIRouter:
    """
    Create a tenant administration router.

    This factory function creates a router with all tenant management endpoints.
    It requires dependency injection for the session and registry to work with
    different database configurations.

    Args:
        get_session: Dependency function that returns AsyncSession
        get_registry: Dependency function that returns TenantRegistry
        prefix: URL prefix for the router (default: "/tenants")
        tags: OpenAPI tags for the router
        dependencies: Optional list of FastAPI dependencies (e.g., security guards)

    Returns:
        Configured FastAPI router

    Example:
        from db_core.router import create_tenant_admin_router
        from db_core.tenant_registry import TenantRegistry

        async def get_session():
            async with async_session() as session:
                yield session

        def get_registry():
            return TenantRegistry(settings)

        router = create_tenant_admin_router(
            get_session=get_session,
            get_registry=get_registry,
            dependencies=[Depends(superadmin_guard("manage_tenants"))],
        )
        app.include_router(router, prefix="/admin")
    """
    router = APIRouter(
        prefix=prefix,
        tags=tags or ["tenants"],
        dependencies=dependencies or [],
    )

    @router.post(
        "",
        response_model=TenantResponse,
        status_code=status.HTTP_201_CREATED,
        summary="Create a new tenant",
        description="Provision a new tenant with its database schema",
    )
    async def create_tenant(
        request: TenantCreate,
        session: AsyncSession = Depends(get_session),
        registry=Depends(get_registry),
    ) -> TenantResponse:
        """Create a new tenant and initialize its schema."""
        try:
            tenant = await registry.create_tenant(
                session=session,
                tenant_id=request.tenant_id,
                name=request.name,
                description=request.description,
                metadata=request.metadata,
            )
            return _tenant_to_response(tenant)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=str(e),
            )
        except Exception as e:
            logger.error(f"Failed to create tenant: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create tenant: {str(e)}",
            )

    @router.get(
        "",
        response_model=TenantListResponse,
        summary="List all tenants",
        description="Get a list of all tenants in the system",
    )
    async def list_tenants(
        include_inactive: bool = False,
        session: AsyncSession = Depends(get_session),
        registry=Depends(get_registry),
    ) -> TenantListResponse:
        """List all tenants."""
        try:
            tenants = await registry.list_tenants(
                session=session,
                include_inactive=include_inactive,
            )
            return TenantListResponse(
                tenants=[_tenant_to_response(t) for t in tenants],
                total=len(tenants),
            )
        except Exception as e:
            logger.error(f"Failed to list tenants: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to list tenants: {str(e)}",
            )

    @router.get(
        "/{tenant_id}",
        response_model=TenantResponse,
        summary="Get tenant details",
        description="Get details of a specific tenant",
    )
    async def get_tenant(
        tenant_id: str,
        session: AsyncSession = Depends(get_session),
        registry=Depends(get_registry),
    ) -> TenantResponse:
        """Get a specific tenant by ID."""
        tenant = await registry.get_tenant(session, tenant_id)
        if not tenant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tenant '{tenant_id}' not found",
            )
        return _tenant_to_response(tenant)

    @router.patch(
        "/{tenant_id}",
        response_model=TenantResponse,
        summary="Update tenant",
        description="Update a tenant's metadata",
    )
    async def update_tenant(
        tenant_id: str,
        request: TenantUpdate,
        session: AsyncSession = Depends(get_session),
        registry=Depends(get_registry),
    ) -> TenantResponse:
        """Update a tenant's metadata."""
        tenant = await registry.update_tenant(
            session=session,
            tenant_id=tenant_id,
            name=request.name,
            description=request.description,
            metadata=request.metadata,
            status=request.status,
        )
        if not tenant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tenant '{tenant_id}' not found",
            )
        return _tenant_to_response(tenant)

    @router.post(
        "/{tenant_id}/deactivate",
        response_model=TenantResponse,
        summary="Deactivate tenant",
        description="Deactivate a tenant (soft delete)",
    )
    async def deactivate_tenant(
        tenant_id: str,
        session: AsyncSession = Depends(get_session),
        registry=Depends(get_registry),
    ) -> TenantResponse:
        """Deactivate a tenant."""
        tenant = await registry.deactivate_tenant(session, tenant_id)
        if not tenant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tenant '{tenant_id}' not found",
            )
        return _tenant_to_response(tenant)

    @router.post(
        "/{tenant_id}/activate",
        response_model=TenantResponse,
        summary="Activate tenant",
        description="Activate or reactivate a tenant",
    )
    async def activate_tenant(
        tenant_id: str,
        session: AsyncSession = Depends(get_session),
        registry=Depends(get_registry),
    ) -> TenantResponse:
        """Activate a tenant."""
        tenant = await registry.activate_tenant(session, tenant_id)
        if not tenant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tenant '{tenant_id}' not found",
            )
        return _tenant_to_response(tenant)

    @router.delete(
        "/{tenant_id}",
        response_model=MessageResponse,
        summary="Delete tenant",
        description="Permanently delete a tenant (use with caution)",
    )
    async def delete_tenant(
        tenant_id: str,
        drop_schema: bool = False,
        session: AsyncSession = Depends(get_session),
        registry=Depends(get_registry),
    ) -> MessageResponse:
        """Delete a tenant permanently."""
        deleted = await registry.delete_tenant(
            session=session,
            tenant_id=tenant_id,
            drop_schema=drop_schema,
        )
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tenant '{tenant_id}' not found",
            )
        message = f"Tenant '{tenant_id}' deleted"
        if drop_schema:
            message += " (schema dropped)"
        return MessageResponse(message=message)

    return router


def _tenant_to_response(tenant) -> TenantResponse:
    """Convert a Tenant model to TenantResponse."""
    return TenantResponse(
        id=str(tenant.id),
        tenant_id=tenant.tenant_id,
        name=tenant.name,
        description=tenant.description,
        status=tenant.status,
        schema_name=tenant.schema_name,
        metadata=tenant.metadata_,
        is_schema_initialized=tenant.is_schema_initialized,
        created_at=tenant.created_at.isoformat(),
        updated_at=tenant.updated_at.isoformat(),
    )

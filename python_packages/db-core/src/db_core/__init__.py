"""
DB-Core - A package for implementing schema-based multitenancy in FastAPI applications.

This package provides utilities for implementing database multitenancy in FastAPI
applications using SQLAlchemy, PostgreSQL and schema-based tenant separation.
"""

from db_core.config import MultitenancySettings
from db_core.db import Base, get_tenant_async_session, get_tenant_session, init_db, tenant_async_db_session, tenant_db_session
from db_core.dependencies import get_tenant_async_db, get_tenant_db
from db_core.middleware import TenantMiddleware, get_current_tenant_id
from db_core.models import Tenant, TenantStatus
from db_core.tenant_registry import (
    TenantRegistry,
    register_tenant_initializer,
    get_tenant_initializers,
    clear_tenant_initializers,
)
from db_core.router import (
    create_tenant_admin_router,
    TenantCreate,
    TenantUpdate,
    TenantResponse,
    TenantListResponse,
)

__version__ = "0.1.0"
__all__ = [
    # Middleware and context
    "TenantMiddleware",
    "get_current_tenant_id",
    # Database sessions
    "get_tenant_db",
    "get_tenant_async_db",
    "get_tenant_session",
    "get_tenant_async_session",
    "init_db",
    "Base",
    "tenant_db_session",
    "tenant_async_db_session",
    # Settings
    "MultitenancySettings",
    # Tenant models
    "Tenant",
    "TenantStatus",
    # Tenant registry
    "TenantRegistry",
    "register_tenant_initializer",
    "get_tenant_initializers",
    "clear_tenant_initializers",
    # Router
    "create_tenant_admin_router",
    "TenantCreate",
    "TenantUpdate",
    "TenantResponse",
    "TenantListResponse",
]

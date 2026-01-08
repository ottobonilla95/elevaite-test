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
    TenantCache,
    register_tenant_initializer,
    get_tenant_initializers,
    clear_tenant_initializers,
    get_tenant_cache,
)
from db_core.router import (
    create_tenant_admin_router,
    TenantCreate,
    TenantUpdate,
    TenantResponse,
    TenantListResponse,
)
from db_core.audit import (
    TenantAuditEvent,
    log_tenant_event,
    log_tenant_created,
    log_tenant_updated,
    log_tenant_activated,
    log_tenant_deactivated,
    log_tenant_deleted,
    get_audit_logger,
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
    # Tenant registry and cache
    "TenantRegistry",
    "TenantCache",
    "register_tenant_initializer",
    "get_tenant_initializers",
    "clear_tenant_initializers",
    "get_tenant_cache",
    # Router
    "create_tenant_admin_router",
    "TenantCreate",
    "TenantUpdate",
    "TenantResponse",
    "TenantListResponse",
    # Audit logging
    "TenantAuditEvent",
    "log_tenant_event",
    "log_tenant_created",
    "log_tenant_updated",
    "log_tenant_activated",
    "log_tenant_deactivated",
    "log_tenant_deleted",
    "get_audit_logger",
]

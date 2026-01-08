"""
Audit logging for tenant operations.

Provides structured logging for tenant lifecycle events (create, update, delete)
using the elevaite_logger package for consolidated logging.
"""

import json
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

from fastapi_logger import ElevaiteLogger

# Singleton audit logger instance
_audit_logger: Optional[ElevaiteLogger] = None


class TenantAuditEvent(str, Enum):
    """Tenant lifecycle audit events."""

    TENANT_CREATED = "tenant.created"
    TENANT_UPDATED = "tenant.updated"
    TENANT_ACTIVATED = "tenant.activated"
    TENANT_DEACTIVATED = "tenant.deactivated"
    TENANT_DELETED = "tenant.deleted"
    TENANT_SCHEMA_CREATED = "tenant.schema.created"
    TENANT_SCHEMA_DROPPED = "tenant.schema.dropped"
    TENANT_INIT_STARTED = "tenant.init.started"
    TENANT_INIT_COMPLETED = "tenant.init.completed"
    TENANT_INIT_FAILED = "tenant.init.failed"


def get_audit_logger() -> ElevaiteLogger:
    """Get or create the singleton audit logger."""
    global _audit_logger
    if _audit_logger is None:
        _audit_logger = ElevaiteLogger(
            name="db_core.audit",
            cloudwatch_enabled=False,  # Can be enabled via env vars
        )
    return _audit_logger


def _build_audit_entry(
    event: TenantAuditEvent,
    tenant_id: str,
    actor: Optional[str] = None,
    details: Optional[dict[str, Any]] = None,
    error: Optional[str] = None,
) -> dict[str, Any]:
    """Build a structured audit log entry."""
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event": event.value,
        "tenant_id": tenant_id,
        "component": "db_core.tenant_registry",
    }
    if actor:
        entry["actor"] = actor
    if details:
        entry["details"] = details
    if error:
        entry["error"] = error
    return entry


def log_tenant_event(
    event: TenantAuditEvent,
    tenant_id: str,
    actor: Optional[str] = None,
    details: Optional[dict[str, Any]] = None,
    error: Optional[str] = None,
) -> None:
    """
    Log a tenant audit event.

    Args:
        event: The type of tenant event
        tenant_id: The tenant identifier
        actor: Optional identifier of the user/system performing the action
        details: Optional additional context about the event
        error: Optional error message if the operation failed
    """
    logger = get_audit_logger().get_logger()
    entry = _build_audit_entry(event, tenant_id, actor, details, error)
    log_message = f"[TENANT_AUDIT] {json.dumps(entry)}"

    if error:
        logger.error(log_message)
    else:
        logger.info(log_message)


def log_tenant_created(
    tenant_id: str,
    display_name: Optional[str] = None,
    actor: Optional[str] = None,
) -> None:
    """Log tenant creation event."""
    log_tenant_event(
        TenantAuditEvent.TENANT_CREATED,
        tenant_id,
        actor=actor,
        details={"display_name": display_name} if display_name else None,
    )


def log_tenant_updated(
    tenant_id: str,
    changes: dict[str, Any],
    actor: Optional[str] = None,
) -> None:
    """Log tenant update event."""
    log_tenant_event(
        TenantAuditEvent.TENANT_UPDATED,
        tenant_id,
        actor=actor,
        details={"changes": changes},
    )


def log_tenant_activated(tenant_id: str, actor: Optional[str] = None) -> None:
    """Log tenant activation event."""
    log_tenant_event(TenantAuditEvent.TENANT_ACTIVATED, tenant_id, actor=actor)


def log_tenant_deactivated(tenant_id: str, actor: Optional[str] = None) -> None:
    """Log tenant deactivation event."""
    log_tenant_event(TenantAuditEvent.TENANT_DEACTIVATED, tenant_id, actor=actor)


def log_tenant_deleted(
    tenant_id: str,
    drop_schema: bool = False,
    actor: Optional[str] = None,
) -> None:
    """Log tenant deletion event."""
    log_tenant_event(
        TenantAuditEvent.TENANT_DELETED,
        tenant_id,
        actor=actor,
        details={"drop_schema": drop_schema},
    )


def log_tenant_init_started(tenant_id: str, schema_name: str) -> None:
    """Log tenant initialization started."""
    log_tenant_event(
        TenantAuditEvent.TENANT_INIT_STARTED,
        tenant_id,
        details={"schema_name": schema_name},
    )


def log_tenant_init_completed(tenant_id: str, schema_name: str) -> None:
    """Log tenant initialization completed."""
    log_tenant_event(
        TenantAuditEvent.TENANT_INIT_COMPLETED,
        tenant_id,
        details={"schema_name": schema_name},
    )


def log_tenant_init_failed(tenant_id: str, schema_name: str, error: str) -> None:
    """Log tenant initialization failure."""
    log_tenant_event(
        TenantAuditEvent.TENANT_INIT_FAILED,
        tenant_id,
        details={"schema_name": schema_name},
        error=error,
    )


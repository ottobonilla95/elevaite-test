"""
Database models for db-core tenant management.

These models are stored in the public schema and manage tenant metadata.
"""

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from sqlalchemy import JSON, Boolean, DateTime, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from db_core.db import Base


def utcnow() -> datetime:
    """Return the current UTC datetime with timezone info."""
    return datetime.now(timezone.utc)


class TenantStatus(str, Enum):
    """Tenant status enum."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING = "pending"


class Tenant(Base):
    """
    Tenant model for storing tenant metadata.

    This table is stored in the public schema and tracks all tenants
    in the system along with their status and configuration.
    """

    __tablename__ = "_tenants"
    __table_args__ = {"schema": "public"}

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    tenant_id: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
        comment="Unique tenant identifier used in schema names and headers",
    )
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Human-readable tenant name",
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Optional description of the tenant",
    )
    status: Mapped[str] = mapped_column(
        String(20),
        default=TenantStatus.ACTIVE.value,
        nullable=False,
        comment="Tenant status: active, inactive, suspended, pending",
    )
    schema_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="PostgreSQL schema name for this tenant",
    )
    metadata_: Mapped[Optional[dict]] = mapped_column(
        "metadata",
        JSON,
        nullable=True,
        comment="Additional tenant metadata as JSON",
    )
    is_schema_initialized: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="Whether the tenant schema has been initialized with tables",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utcnow,
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utcnow,
        onupdate=utcnow,
        nullable=False,
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<Tenant {self.tenant_id} ({self.status})>"

"""SQLAlchemy ORM models for RBAC (Role-Based Access Control)."""

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import ForeignKey, String, DateTime, CheckConstraint, text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column
from typing import Dict, List, Any

from app.db.models import Base


def utcnow() -> datetime:
    """Return the current UTC datetime with timezone info."""
    return datetime.now(timezone.utc)


class Organization(Base):
    """Organization model - top level of RBAC hierarchy."""

    __tablename__ = "organizations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=text("uuid_generate_v4()"))
    name: Mapped[str] = mapped_column(String(), unique=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow, onupdate=utcnow)

    def __repr__(self) -> str:
        """String representation."""
        return f"<Organization {self.name}>"


class Account(Base):
    """Account model - belongs to an organization."""

    __tablename__ = "accounts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=text("uuid_generate_v4()"))
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow, onupdate=utcnow)

    def __repr__(self) -> str:
        """String representation."""
        return f"<Account {self.name}>"


class Project(Base):
    """Project model - belongs to an account."""

    __tablename__ = "projects"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=text("uuid_generate_v4()"))
    account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("accounts.id", ondelete="CASCADE"),
        nullable=False,
    )
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow, onupdate=utcnow)

    def __repr__(self) -> str:
        """String representation."""
        return f"<Project {self.name}>"


class UserRoleAssignment(Base):
    """
    User role assignment model - maps users to roles on resources.

    This is the core of RBAC - it defines what role a user has on a specific resource.
    Resources can be organizations, accounts, or projects.

    Roles:
    - superadmin: Organization-level admin (full access to everything in the org)
    - admin: Account-level admin (full access to account and its projects)
    - editor: Project-level editor (can edit and view project)
    - viewer: Project-level viewer (can only view project)
    """

    __tablename__ = "user_role_assignments"

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
    )
    resource_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, nullable=False)
    role: Mapped[str] = mapped_column(String(), nullable=False)
    resource_type: Mapped[str] = mapped_column(String(), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)

    __table_args__ = (
        CheckConstraint(
            "role IN ('superadmin', 'admin', 'editor', 'viewer')",
            name="ck_user_role_assignments_role",
        ),
        CheckConstraint(
            "resource_type IN ('organization', 'account', 'project')",
            name="ck_user_role_assignments_resource_type",
        ),
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<UserRoleAssignment user={self.user_id} role={self.role} resource={self.resource_type}:{self.resource_id}>"


class PermissionOverride(Base):
    """
    Permission override model - allows fine-grained permission control.

    Overrides allow granting or denying specific permissions to users on resources,
    independent of their role. This enables exceptions to role-based permissions.

    Example use cases:
    - Grant a viewer permission to edit a specific project
    - Deny an editor permission to delete a specific project
    - Grant temporary access to specific actions

    Deny takes precedence over allow (security best practice).
    """

    __tablename__ = "permission_overrides"

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
    )
    resource_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, nullable=False)
    resource_type: Mapped[str] = mapped_column(String(), nullable=False)
    allow_actions: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True, default=list)
    deny_actions: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow, onupdate=utcnow)

    __table_args__ = (
        CheckConstraint(
            "resource_type IN ('organization', 'account', 'project')",
            name="ck_permission_overrides_resource_type",
        ),
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<PermissionOverride user={self.user_id} resource={self.resource_type}:{self.resource_id}>"

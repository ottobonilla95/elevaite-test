"""SQLAlchemy ORM models for RBAC (Role-Based Access Control)."""

import uuid
from datetime import datetime, timezone
from typing import Optional, List

from sqlalchemy import (
    ForeignKey,
    String,
    DateTime,
    CheckConstraint,
    Boolean,
    Index,
    text,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.models import Base


def utcnow() -> datetime:
    """Return the current UTC datetime with timezone info."""
    return datetime.now(timezone.utc)


# =============================================================================
# ROLE MODELS
# =============================================================================


class Role(Base):
    """
    Role model - defines available roles in the system.

    Roles are the primary permission sets assigned to users on resources.
    System roles (is_system=True) are predefined and cannot be deleted.

    Base types define inherited permission levels:
    - superadmin: Full access to everything in scope
    - admin: Full access to account and its projects
    - editor: Can create, edit, view, execute (no delete)
    - viewer: Read-only access
    """

    __tablename__ = "roles"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("uuid_generate_v4()")
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    base_type: Mapped[str] = mapped_column(String(50), nullable=False)
    scope_type: Mapped[str] = mapped_column(String(50), nullable=False)
    is_system: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow, onupdate=utcnow
    )

    # Relationships
    permissions: Mapped[List["RolePermission"]] = relationship(
        "RolePermission",
        back_populates="role",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    user_assignments: Mapped[List["UserRoleAssignment"]] = relationship(
        "UserRoleAssignment", back_populates="role_ref", cascade="all, delete-orphan"
    )

    __table_args__ = (
        CheckConstraint(
            "base_type IN ('superadmin', 'admin', 'editor', 'viewer')",
            name="ck_roles_base_type",
        ),
        CheckConstraint(
            "scope_type IN ('organization', 'account', 'project')",
            name="ck_roles_scope_type",
        ),
        Index("idx_roles_name", "name"),
        Index("idx_roles_is_system", "is_system"),
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<Role {self.name} ({self.base_type})>"


class RolePermission(Base):
    """
    Role permission model - defines allowed actions per service for a role.

    Each role can have different permissions for different services
    (workflow_engine, governance_studio, agent_studio, etc.)
    """

    __tablename__ = "role_permissions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("uuid_generate_v4()")
    )
    role_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("roles.id", ondelete="CASCADE"),
        nullable=False,
    )
    service_name: Mapped[str] = mapped_column(String(100), nullable=False)
    allowed_actions: Mapped[List[str]] = mapped_column(
        JSONB, nullable=False, default=list
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow, onupdate=utcnow
    )

    # Relationships
    role: Mapped["Role"] = relationship("Role", back_populates="permissions")

    __table_args__ = (
        Index("idx_role_permissions_role_id", "role_id"),
        Index("idx_role_permissions_service", "service_name"),
        Index(
            "idx_role_permissions_role_service", "role_id", "service_name", unique=True
        ),
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<RolePermission role={self.role_id} service={self.service_name}>"


# =============================================================================
# GROUP MODELS
# =============================================================================


class Group(Base):
    """
    Group model - organization-defined permission groups.

    Groups act as "tags" that can be assigned to users to grant or deny
    additional permissions on top of their role. Users can be in multiple groups.
    Groups are created and managed by organization admins.
    """

    __tablename__ = "groups"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("uuid_generate_v4()")
    )
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow, onupdate=utcnow
    )

    # Relationships
    organization: Mapped["Organization"] = relationship(
        "Organization", back_populates="groups"
    )
    permissions: Mapped[List["GroupPermission"]] = relationship(
        "GroupPermission",
        back_populates="group",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    memberships: Mapped[List["UserGroupMembership"]] = relationship(
        "UserGroupMembership", back_populates="group", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("idx_groups_organization_id", "organization_id"),
        Index("idx_groups_name", "name"),
        Index("idx_groups_org_name", "organization_id", "name", unique=True),
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<Group {self.name}>"


class GroupPermission(Base):
    """
    Group permission model - defines allow/deny actions per service for a group.

    Groups can both grant additional permissions (allow_actions) and
    revoke permissions (deny_actions). Deny always takes precedence.
    """

    __tablename__ = "group_permissions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("uuid_generate_v4()")
    )
    group_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("groups.id", ondelete="CASCADE"),
        nullable=False,
    )
    service_name: Mapped[str] = mapped_column(String(100), nullable=False)
    allow_actions: Mapped[List[str]] = mapped_column(
        JSONB, nullable=False, default=list
    )
    deny_actions: Mapped[List[str]] = mapped_column(JSONB, nullable=False, default=list)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow, onupdate=utcnow
    )

    # Relationships
    group: Mapped["Group"] = relationship("Group", back_populates="permissions")

    __table_args__ = (
        Index("idx_group_permissions_group_id", "group_id"),
        Index("idx_group_permissions_service", "service_name"),
        Index(
            "idx_group_permissions_group_service",
            "group_id",
            "service_name",
            unique=True,
        ),
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<GroupPermission group={self.group_id} service={self.service_name}>"


class UserGroupMembership(Base):
    """
    User group membership model - assigns users to groups on specific resources.

    Users can be members of multiple groups. Group membership is scoped to
    a specific resource (organization, account, or project).
    """

    __tablename__ = "user_group_memberships"

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
    )
    group_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("groups.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
    )
    resource_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, nullable=False
    )
    resource_type: Mapped[str] = mapped_column(String(50), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow
    )

    # Relationships
    group: Mapped["Group"] = relationship("Group", back_populates="memberships")

    __table_args__ = (
        CheckConstraint(
            "resource_type IN ('organization', 'account', 'project')",
            name="ck_user_group_memberships_resource_type",
        ),
        Index("idx_user_group_memberships_user_id", "user_id"),
        Index("idx_user_group_memberships_group_id", "group_id"),
        Index("idx_user_group_memberships_resource", "resource_type", "resource_id"),
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<UserGroupMembership user={self.user_id} group={self.group_id} resource={self.resource_type}:{self.resource_id}>"


# =============================================================================
# EXISTING MODELS (Updated)
# =============================================================================


class Organization(Base):
    """Organization model - top level of RBAC hierarchy."""

    __tablename__ = "organizations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("uuid_generate_v4()")
    )
    name: Mapped[str] = mapped_column(String(), unique=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow, onupdate=utcnow
    )

    # Relationships
    groups: Mapped[List["Group"]] = relationship(
        "Group", back_populates="organization", cascade="all, delete-orphan"
    )
    accounts: Mapped[List["Account"]] = relationship(
        "Account", back_populates="organization", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<Organization {self.name}>"


class Account(Base):
    """Account model - belongs to an organization."""

    __tablename__ = "accounts"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("uuid_generate_v4()")
    )
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow, onupdate=utcnow
    )

    # Relationships
    organization: Mapped["Organization"] = relationship(
        "Organization", back_populates="accounts"
    )
    projects: Mapped[List["Project"]] = relationship(
        "Project", back_populates="account", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<Account {self.name}>"


class Project(Base):
    """Project model - belongs to an account."""

    __tablename__ = "projects"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("uuid_generate_v4()")
    )
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
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow, onupdate=utcnow
    )

    # Relationships
    account: Mapped["Account"] = relationship("Account", back_populates="projects")

    def __repr__(self) -> str:
        """String representation."""
        return f"<Project {self.name}>"


class UserRoleAssignment(Base):
    """
    User role assignment model - maps users to roles on resources.

    This is the core of RBAC - it defines what role a user has on a specific resource.
    Resources can be organizations, accounts, or projects.

    The role_id references the Role table which contains the full role definition
    and its associated permissions.
    """

    __tablename__ = "user_role_assignments"

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
    )
    resource_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, nullable=False
    )
    # New: FK to roles table (nullable during migration, will become NOT NULL)
    role_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("roles.id", ondelete="CASCADE"),
        nullable=True,  # Nullable for backward compatibility during migration
    )
    # Legacy: Keep for backward compatibility, will be removed after migration
    role: Mapped[Optional[str]] = mapped_column(String(), nullable=True)
    resource_type: Mapped[str] = mapped_column(String(), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow
    )

    # Relationships
    role_ref: Mapped[Optional["Role"]] = relationship(
        "Role", back_populates="user_assignments"
    )

    __table_args__ = (
        CheckConstraint(
            "resource_type IN ('organization', 'account', 'project')",
            name="ck_user_role_assignments_resource_type",
        ),
        Index("idx_user_role_assignments_user_id", "user_id"),
        Index("idx_user_role_assignments_role_id", "role_id"),
        Index("idx_user_role_assignments_resource", "resource_type", "resource_id"),
    )

    def __repr__(self) -> str:
        """String representation."""
        role_name = self.role_ref.name if self.role_ref else self.role
        return f"<UserRoleAssignment user={self.user_id} role={role_name} resource={self.resource_type}:{self.resource_id}>"


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
    resource_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, nullable=False
    )
    resource_type: Mapped[str] = mapped_column(String(), nullable=False)
    allow_actions: Mapped[List[str]] = mapped_column(
        JSONB, nullable=False, default=list
    )
    deny_actions: Mapped[List[str]] = mapped_column(JSONB, nullable=False, default=list)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow, onupdate=utcnow
    )

    __table_args__ = (
        CheckConstraint(
            "resource_type IN ('organization', 'account', 'project')",
            name="ck_permission_overrides_resource_type",
        ),
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<PermissionOverride user={self.user_id} resource={self.resource_type}:{self.resource_id}>"

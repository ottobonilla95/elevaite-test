"""Pydantic schemas for RBAC (Role-Based Access Control)."""

from datetime import datetime
from enum import Enum
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class RoleType(str, Enum):
    """Role types in the RBAC system."""

    SUPERADMIN = "superadmin"
    ADMIN = "admin"
    EDITOR = "editor"
    VIEWER = "viewer"


class ResourceType(str, Enum):
    """Resource types in the RBAC system."""

    ORGANIZATION = "organization"
    ACCOUNT = "account"
    PROJECT = "project"


# Organization schemas
class OrganizationCreate(BaseModel):
    """Schema for creating an organization."""

    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None


class OrganizationResponse(BaseModel):
    """Schema for organization response."""

    id: UUID
    name: str
    description: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Account schemas
class AccountCreate(BaseModel):
    """Schema for creating an account."""

    organization_id: UUID
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None


class AccountResponse(BaseModel):
    """Schema for account response."""

    id: UUID
    organization_id: UUID
    name: str
    description: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Project schemas
class ProjectCreate(BaseModel):
    """Schema for creating a project."""

    account_id: UUID
    organization_id: UUID
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None


class ProjectResponse(BaseModel):
    """Schema for project response."""

    id: UUID
    account_id: UUID
    organization_id: UUID
    name: str
    description: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# User role assignment schemas
class UserRoleAssignmentCreate(BaseModel):
    """Schema for creating a user role assignment."""

    user_id: int
    role: RoleType
    resource_type: ResourceType
    resource_id: UUID


class UserRoleAssignmentResponse(BaseModel):
    """Schema for user role assignment response."""

    user_id: int
    role: str
    resource_type: str
    resource_id: UUID
    created_at: datetime

    class Config:
        from_attributes = True


# Authorization check schemas
class ResourceInfo(BaseModel):
    """Schema for resource information in authorization checks."""

    type: str = Field(..., description="Resource type (organization, account, project)")
    id: UUID = Field(..., description="Resource ID")
    organization_id: UUID = Field(..., description="Organization ID")
    account_id: Optional[UUID] = Field(None, description="Account ID (for projects)")


class AccessCheckRequest(BaseModel):
    """Schema for access check request."""

    user_id: int = Field(..., description="User ID to check access for")
    action: str = Field(..., description="Action to perform (e.g., view_project, edit_project)")
    resource: ResourceInfo = Field(..., description="Resource being accessed")


class AccessCheckResponse(BaseModel):
    """Schema for access check response."""

    allowed: bool = Field(..., description="Whether access is allowed")
    deny_reason: Optional[str] = Field(None, description="Reason for denial if not allowed")
    user_status: str = Field(..., description="User status at time of check")


# List responses
class OrganizationListResponse(BaseModel):
    """Schema for list of organizations."""

    organizations: List[OrganizationResponse]
    total: int | None


class AccountListResponse(BaseModel):
    """Schema for list of accounts."""

    accounts: List[AccountResponse]
    total: int | None


class ProjectListResponse(BaseModel):
    """Schema for list of projects."""

    projects: List[ProjectResponse]
    total: int | None


class UserRoleAssignmentListResponse(BaseModel):
    """Schema for list of user role assignments."""

    assignments: List[UserRoleAssignmentResponse]
    total: int | None


# Permission override schemas
class PermissionOverrideCreate(BaseModel):
    """Schema for creating a permission override."""

    user_id: int = Field(..., description="User ID to apply overrides to")
    resource_type: ResourceType = Field(..., description="Type of resource")
    resource_id: UUID = Field(..., description="Resource ID")
    allow_actions: Optional[List[str]] = Field(
        None, description="List of actions to explicitly allow (e.g., ['edit_project', 'delete_workflow'])"
    )
    deny_actions: Optional[List[str]] = Field(
        None, description="List of actions to explicitly deny. Deny takes precedence over allow."
    )


class PermissionOverrideUpdate(BaseModel):
    """Schema for updating a permission override."""

    allow_actions: Optional[List[str]] = Field(
        None, description="List of actions to explicitly allow. Set to empty list to clear."
    )
    deny_actions: Optional[List[str]] = Field(
        None, description="List of actions to explicitly deny. Set to empty list to clear."
    )


class PermissionOverrideResponse(BaseModel):
    """Schema for permission override response."""

    user_id: int
    resource_type: str
    resource_id: UUID
    allow_actions: Optional[List[str]]
    deny_actions: Optional[List[str]]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PermissionOverrideListResponse(BaseModel):
    """Schema for list of permission overrides."""

    overrides: List[PermissionOverrideResponse]
    total: int | None


# ============================================================================
# Role schemas (system-defined and custom roles)
# ============================================================================


class RolePermissionResponse(BaseModel):
    """Schema for role permission response."""

    id: UUID
    role_id: UUID
    service_name: str
    allowed_actions: List[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class RoleResponse(BaseModel):
    """Schema for role response."""

    id: UUID
    name: str
    description: Optional[str]
    base_type: str
    scope_type: str
    is_system: bool
    created_at: datetime
    updated_at: datetime
    permissions: Optional[List[RolePermissionResponse]] = None

    class Config:
        from_attributes = True


class RoleListResponse(BaseModel):
    """Schema for list of roles."""

    roles: List[RoleResponse]
    total: int | None


class RoleCreate(BaseModel):
    """Schema for creating a custom role."""

    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    base_type: RoleType = Field(..., description="Base permission type")
    scope_type: ResourceType = Field(..., description="Scope level for this role")


class RolePermissionCreate(BaseModel):
    """Schema for adding permissions to a role."""

    service_name: str = Field(..., min_length=1, max_length=100)
    allowed_actions: List[str] = Field(..., description="List of allowed actions for this service")


# ============================================================================
# Group schemas (organization-defined permission groups)
# ============================================================================


class GroupPermissionResponse(BaseModel):
    """Schema for group permission response."""

    id: UUID
    group_id: UUID
    service_name: str
    allow_actions: List[str]
    deny_actions: List[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class GroupResponse(BaseModel):
    """Schema for group response."""

    id: UUID
    organization_id: UUID
    name: str
    description: Optional[str]
    created_at: datetime
    updated_at: datetime
    permissions: Optional[List[GroupPermissionResponse]] = None

    class Config:
        from_attributes = True


class GroupListResponse(BaseModel):
    """Schema for list of groups."""

    groups: List[GroupResponse]
    total: int | None


class GroupCreate(BaseModel):
    """Schema for creating a group."""

    organization_id: UUID = Field(..., description="Organization this group belongs to")
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)


class GroupUpdate(BaseModel):
    """Schema for updating a group."""

    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)


class GroupPermissionCreate(BaseModel):
    """Schema for adding permissions to a group."""

    service_name: str = Field(..., min_length=1, max_length=100)
    allow_actions: List[str] = Field(default_factory=list, description="Actions allowed by this group")
    deny_actions: List[str] = Field(default_factory=list, description="Actions denied by this group (restricts role)")


class GroupPermissionUpdate(BaseModel):
    """Schema for updating group permissions."""

    allow_actions: Optional[List[str]] = None
    deny_actions: Optional[List[str]] = None


# ============================================================================
# User Group Membership schemas
# ============================================================================


class UserGroupMembershipResponse(BaseModel):
    """Schema for user group membership response."""

    user_id: int
    group_id: UUID
    resource_id: UUID
    resource_type: str
    created_at: datetime
    group: Optional[GroupResponse] = None

    class Config:
        from_attributes = True


class UserGroupMembershipListResponse(BaseModel):
    """Schema for list of user group memberships."""

    memberships: List[UserGroupMembershipResponse]
    total: int | None


class UserGroupMembershipCreate(BaseModel):
    """Schema for adding a user to a group."""

    user_id: int = Field(..., description="User ID to add to group")
    resource_id: UUID = Field(..., description="Resource ID where this membership applies")
    resource_type: ResourceType = Field(..., description="Type of resource")


# ============================================================================
# Current User RBAC Response (for /me/rbac endpoint)
# ============================================================================


class UserRbacResponse(BaseModel):
    """Complete RBAC information for the current user."""

    user_id: int = Field(..., description="User ID")
    is_superuser: bool = Field(..., description="Whether user is a superuser")
    role_assignments: List[UserRoleAssignmentResponse] = Field(
        default_factory=list, description="User's role assignments across resources"
    )
    group_memberships: List[UserGroupMembershipResponse] = Field(default_factory=list, description="User's group memberships")
    permission_overrides: List[PermissionOverrideResponse] = Field(
        default_factory=list, description="User's permission overrides"
    )

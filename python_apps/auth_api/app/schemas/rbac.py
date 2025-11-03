"""Pydantic schemas for RBAC (Role-Based Access Control)."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
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

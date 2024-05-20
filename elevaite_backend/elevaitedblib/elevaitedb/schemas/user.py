# app/schemas/user_schemas.py
from pydantic import BaseModel, EmailStr, Field, Extra, root_validator, validator
from typing import Optional, List, Literal, Dict, Any
from uuid import UUID
from datetime import datetime
from .role import (
    RoleResponseDTO,
    RoleSummaryDTO,
)
from ...elevaitelib.schemas.permission import ProjectScopedRBACPermission
from .common import StatusUpdateAction


class UserPatchRequestDTO(BaseModel):
    firstname: Optional[str] = Field(
        None, max_length=60, description="First name of user"
    )
    lastname: Optional[str] = Field(
        None, max_length=60, description="Last name of user"
    )

    class Config:
        extra = Extra.forbid

    @root_validator(pre=True)
    @classmethod
    def check_not_all_none(cls, values):
        # Check if all values are None
        if all(value is None for value in values.values()):
            print(
                f"Inside PATCH /users/user_id - UserPatchRequestDTO schema validation"
            )
            raise ValueError("At least one field must be provided in payload")
        return values


class UserListDTO(BaseModel):
    user_ids: List[UUID] = Field(..., description="The IDs of the users in a list")

    class Config:
        extra = Extra.forbid

    @validator("user_ids")
    @classmethod
    def validate_user_ids(cls, v: List[UUID]) -> List[UUID]:
        # Ensure uniqueness
        if len(v) != len(set(v)):
            print(f"Inside UserListDTO schema validation")
            raise ValueError("Duplicate user IDs are not allowed")
        # Check length constraint
        if len(v) < 1 or len(v) > 50:
            print(f"Inside UserListDTO schema validation")
            raise ValueError(
                "The list of user IDs must have length between 1 and 50 (inclusive)"
            )
        return v


class UserAccountMembershipInfo(BaseModel):
    account_id: UUID = Field(..., description="The ID of the account")
    account_name: str = Field(..., description="The name of the account")
    is_admin: bool = Field(
        ..., description="Whether the user is an admin in this account"
    )
    roles: List[RoleSummaryDTO] = Field(
        ..., description="The roles of the user within this account"
    )

    # model_config = {
    #      "json_schema_extra" : {
    #          "example": {
    #              "roleIds": ["123e4567-e89b-12d3-a456-426614174002", "123e4567-e89b-12d3-a456-426614174003"]
    #          }
    #      }
    # }


# class UserPatchOverridingRoleRequestDTO(BaseModel): # to be used by superadmin in separate endpoints for updating user_account, user_project or user overriding role id's
#     overridingRoleId: UUID = Field(..., examples=["123e4567-e89b-12d3-a456-426614174002"])

#  model_config = {
#      "json_schema_extra" : {
#          "example": {
#              "overridingRoleId": "123e4567-e89b-12d3-a456-426614174002"
#          }
#      }
#  }


class UserProfileDTO(BaseModel):
    id: UUID = Field(...)
    organization_id: UUID = Field(
        ..., description="The ID of the org to be assigned to the user"
    )
    firstname: Optional[str] = Field(None)
    lastname: Optional[str] = Field(None)
    email: EmailStr = Field(...)
    is_superadmin: bool = Field(...)
    created_at: datetime = Field(...)
    updated_at: datetime = Field(...)
    account_memberships: List[UserAccountMembershipInfo] = Field(
        ...,
        description="List of accounts the user is part of and their roles within those accounts",
    )

    class Config:
        extra = Extra.forbid
        schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "organization_id": "123e4567-e89b-12d3-a456-426614174000",
                "firstname": "John",
                "lastname": "Doe",
                "email": "john.doe@example.com",
                "is_superadmin": False,
                "created_at": "2022-01-01T00:00:00Z",
                "updated_at": "2022-01-02T00:00:00Z",
                "account_memberships": [],
            }
        }


class OrgUserListItemDTO(BaseModel):
    id: UUID = Field(...)
    organization_id: UUID = Field(
        ..., description="The ID of the org to be assigned to the user"
    )
    firstname: Optional[str] = Field(None)
    lastname: Optional[str] = Field(None)
    email: EmailStr = Field(...)
    is_superadmin: bool = Field(...)
    created_at: datetime = Field(...)
    updated_at: datetime = Field(...)

    class Config:
        orm_mode = True
        schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "organization_id": "123e4567-e89b-12d3-a456-426614174000",
                "firstname": "John",
                "lastname": "Doe",
                "email": "john.doe@example.com",
                "is_superadmin": False,
                "created_at": "2022-01-01T00:00:00Z",
                "updated_at": "2022-01-02T00:00:00Z",
            }
        }


class AccountUserListItemDTO(OrgUserListItemDTO):
    is_account_admin: bool = Field(...)
    roles: List[RoleSummaryDTO] = Field(
        ..., description="List of RoleSummaryDTO objects scoped to account"
    )


class AccountUserProfileDTO(OrgUserListItemDTO):
    is_account_admin: bool = Field(...)
    roles: List[RoleResponseDTO] = Field(
        ..., description="List of RoleResponseDTO objects scoped to account"
    )


class ProjectUserListItemDTO(AccountUserListItemDTO):
    is_project_admin: bool = Field(...)


class ProjectUserProfileDTO(AccountUserProfileDTO):
    permission_overrides: ProjectScopedRBACPermission


class SuperadminStatusUpdateDTO(StatusUpdateAction):
    pass


# class UpdateUserProjectPermissionOverrides(BaseModel):
#    permission_overrides: ProjectScopedRBACPermission = Field(...)

#    # @validator('permission_overrides', pre=True)
#    # def validate_permission_overrides(cls, v, values, **kwargs):
#    #    try:
#    #       validated_permission_overrides = ProjectScopedRBACPermission.parse_obj(v)
#    #       return v # return the raw object after validation
#    #    except Exception as e:
#    #       raise e

#    class Config:
#       extra = Extra.forbid

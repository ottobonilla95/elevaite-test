from pydantic import BaseModel, Field, Extra, root_validator, validator
from typing import Optional, Literal, List
from uuid import UUID
from datetime import datetime
import json
import os
# ActionEnumType Model : Defines possible enum values for an action on resource type
class ActionEnumType(BaseModel):
   action: Literal["Allow", "Deny"] = Field(default="Deny")
   class Config:
      extra = Extra.forbid
# # Permission type for Organization resource type in create/patch role request
# class OrganizationPermissionRequestType(BaseModel):
#     READ: ActionEnumType

# Permission type for Organization resource type in role response
# class OrganizationPermissionResponseType(BaseModel):
#     CREATE: ActionEnumType
#     READ: ActionEnumType
#     UPDATE: ActionEnumType

# Permission type for Account resource type in role create/patch request
# class AccountPermissionRequestType(BaseModel):
#     READ: ActionEnumType

# # Permission type for Account resource type in role response
# class AccountPermissionResponseType(BaseModel):
#     CREATE: ActionEnumType
#     READ: ActionEnumType
#     UPDATE: ActionEnumType
#     ARCHIVE: ActionEnumType

# Permission type for Project resource type in role create/patch request
class ProjectPermissionType(BaseModel):
   CREATE: ActionEnumType = Field(default_factory=ActionEnumType)
   READ: ActionEnumType = Field(default_factory=ActionEnumType)
   class Config:
      extra = Extra.forbid
# # Permission type for Project resource type in role response
# class ProjectPermissionResponseType(BaseModel):
#     CREATE: ActionEnumType
#     READ: ActionEnumType

# Permission type for User resource type in role create/patch request
# class UserPermissionType(BaseModel):
#     CREATE: ActionEnumType = Field(default_factory=ActionEnumType)

# Permission type for User resource type in role response
# class UserPermissionResponseType(BaseModel):
#     CREATE: ActionEnumType
#     READ: ActionEnumType
#     UPDATE : ActionEnumType
#     ARCHIVE: ActionEnumType

# Permission type for Configure action on a particular resource type, in role create/patch request
class ConfigurePermissionType(BaseModel):
   READ: ActionEnumType = Field(default_factory=ActionEnumType)
   CREATE: ActionEnumType = Field(default_factory=ActionEnumType)
   RUN: ActionEnumType = Field(default_factory=ActionEnumType)
   class Config:
      extra = Extra.forbid
# Permission type for Configure action on a particular resource type, in role response
# class ConfigurePermissionResponseType(BaseModel):
#     READ: ActionEnumType
#     CREATE: ActionEnumType
#     RUN: ActionEnumType
#     UPDATE: ActionEnumType
#     ARCHIVE: ActionEnumType

# Permission type for Schedule action on a particular resource type, in role create/patch request
class SchedulePermissionType(BaseModel):
   READ: ActionEnumType = Field(default_factory=ActionEnumType)
   CREATE: ActionEnumType = Field(default_factory=ActionEnumType)
   class Config:
      extra = Extra.forbid
# Permission type for Schedule action on a particular resource type, in role response
# class SchedulePermissionResponseType(BaseModel):
#     READ: ActionEnumType
#     CREATE: ActionEnumType
#     UPDATE: ActionEnumType
#     ARCHIVE: ActionEnumType
# Permission type for EnableWebHooks action on a particular resource type in role create/patch request
class EnableWebHooksPermissionType(BaseModel):
   READ: ActionEnumType = Field(default_factory=ActionEnumType)
   CREATE: ActionEnumType = Field(default_factory=ActionEnumType)
   class Config:
      extra = Extra.forbid
# Permission type for EnableWebHooks action on a particular resource type in role response
# class EnableWebHooksPermissionResponseType(BaseModel):
#     READ: ActionEnumType
#     CREATE: ActionEnumType
#     UPDATE: ActionEnumType
#     ARCHIVE: ActionEnumType

# Permission type for ingest action on a particular resource type in role create/patch request
class IngestPermissionType(BaseModel):
   CONFIGURE: ConfigurePermissionType = Field(default_factory=ConfigurePermissionType)
   SCHEDULE: SchedulePermissionType = Field(default_factory=SchedulePermissionType)
   ENABLE_WEBHOOKS: EnableWebHooksPermissionType = Field(default_factory=EnableWebHooksPermissionType)
   READ: ActionEnumType = Field(default_factory=ActionEnumType)
   class Config:
      extra = Extra.forbid

# Permission type for ingest action on a particular resource type in role create/patch request
# class IngestPermissionResponseType(BaseModel):
#     CONFIGURE: ConfigurePermissionResponseType
#     SCHEDULE: SchedulePermissionResponseType
#     ENABLE_WEBHOOKS: EnableWebHooksPermissionResponseType
#     READ: ActionEnumType

# PreprocessPermissionType follows the same structure as IngestPermissionType
class PreprocessPermissionType(IngestPermissionType):
   pass
# class PreprocessPermissionResponseType(IngestPermissionResponseType):
#     pass

# DownloadPermissionType Model (similar to ConfigurePermissionType for Train)
class DownloadPermissionType(ConfigurePermissionType):
   pass
# class DownloadPermissionResponseType(ConfigurePermissionResponseType):
#     pass

# EvaluatePermissionType Model (similar to ConfigurePermissionType for Train)
class EvaluatePermissionType(ConfigurePermissionType):
   pass
# class EvaluatePermissionResponseType(ConfigurePermissionResponseType):
#     pass

# FineTuningPermissionType Model (similar to EnableWebHooksPermissionType for Train)
class FineTuningPermissionType(EnableWebHooksPermissionType):
   pass
# class FineTuningPermissionResponseType(EnableWebHooksPermissionResponseType):
#     pass

# Permission type for Train action
class TrainPermissionType(BaseModel):
   READ: ActionEnumType = Field(default_factory=ActionEnumType)
   DOWNLOAD: DownloadPermissionType = Field(default_factory=DownloadPermissionType)
   EVALUATE: EvaluatePermissionType = Field(default_factory=EvaluatePermissionType)
   FINE_TUNING: FineTuningPermissionType = Field(default_factory=FineTuningPermissionType)
   class Config:
      extra = Extra.forbid

# class TrainPermissionResponseType(BaseModel):
#     DOWNLOAD: DownloadPermissionResponseType
#     EVALUATE: EvaluatePermissionResponseType
#     FINE_TUNING: FineTuningPermissionResponseType

# permission type for deploy action
class DeployPermissionType(BaseModel):
   READ: ActionEnumType = Field(default_factory=ActionEnumType)
   CREATE: ActionEnumType = Field(default_factory=ActionEnumType)
   RUN: ActionEnumType = Field(default_factory=ActionEnumType)
   ENABLE_WEBHOOKS: EnableWebHooksPermissionType = Field(default_factory=EnableWebHooksPermissionType)
   SCHEDULE: SchedulePermissionType = Field(default_factory=SchedulePermissionType)
   CONFIGURE: ConfigurePermissionType = Field(default_factory=ConfigurePermissionType)
   class Config:
      extra = Extra.forbid
# class DeployPermissionResponseType(BaseModel):
#     READ: ActionEnumType
#     CREATE: ActionEnumType
#     RUN: ActionEnumType
#     ENABLE_WEBHOOKS: EnableWebHooksPermissionResponseType
#     SCHEDULE: SchedulePermissionResponseType
#     CONFIGURE: ConfigurePermissionResponseType

# 'Dataset' and 'Model' are artifacts
class ArtifactPermissionType(BaseModel):
   READ: ActionEnumType = Field(default_factory=ActionEnumType)
   TAG: ActionEnumType = Field(default_factory=ActionEnumType)
   class Config:
      extra = Extra.forbid

class ModelPermissionType(ArtifactPermissionType):
   pass

class DatasetPermissionType(ArtifactPermissionType):
   pass

class ApplicationPermissionType(BaseModel):
   READ: ActionEnumType = Field(default_factory=ActionEnumType)
   CONFIGURE: ConfigurePermissionType = Field(default_factory=ConfigurePermissionType)
   RUN : ActionEnumType = Field(default_factory=ActionEnumType)
   class Config:
      extra = Extra.forbid
# class ApplicationPermissionResponseType(BaseModel):
#     READ: ActionEnumType
#     CONFIGURE: ConfigurePermissionResponseType
#     RUN : ActionEnumType

class APIKeyPermissionType(BaseModel):
   CREATE: ActionEnumType = Field(default_factory=ActionEnumType)
   class Config:
      extra = Extra.forbid

# class APIKeyPermissionResponseType(BaseModel):
#     CREATE: ActionEnumType
#     READ: ActionEnumType
#     ARCHIVE: ActionEnumType

# class RolePermissionType:
#     READ: ActionEnumType
# class RolePermissionResponseType:
#     CREATE: ActionEnumType
#     READ: ActionEnumType
#     UPDATE: ActionEnumType
#     ARCHIVE: ActionEnumType

class AccountScopedPermissions(BaseModel):
   Project: ProjectPermissionType = Field(default_factory=ProjectPermissionType)
   # User: UserPermissionType = Field(default_factory=UserPermissionType)
   Ingest: IngestPermissionType = Field(default_factory=IngestPermissionType)
   Preprocess: PreprocessPermissionType = Field(default_factory=PreprocessPermissionType)
   Train: TrainPermissionType = Field(default_factory=TrainPermissionType)
   Deploy: DeployPermissionType = Field(default_factory=DeployPermissionType)
   Model: ModelPermissionType = Field(default_factory=ModelPermissionType)
   Dataset: DatasetPermissionType = Field(default_factory=DatasetPermissionType)
   Application: ApplicationPermissionType = Field(default_factory=ApplicationPermissionType)
   ApiKey: APIKeyPermissionType = Field(default_factory=APIKeyPermissionType)
   class Config:
      extra = Extra.forbid
      orm_mode = True

class ProjectScopedPermissions(BaseModel):
   Project: ProjectPermissionType = Field(default_factory=ProjectPermissionType)
   Ingest: IngestPermissionType = Field(default_factory=IngestPermissionType)
   Preprocess: PreprocessPermissionType = Field(default_factory=PreprocessPermissionType)
   Train: TrainPermissionType = Field(default_factory=TrainPermissionType)
   Deploy: DeployPermissionType = Field(default_factory=DeployPermissionType)
   Model: ModelPermissionType = Field(default_factory=ModelPermissionType)
   Dataset: DatasetPermissionType = Field(default_factory=DatasetPermissionType)
   class Config:
      extra = Extra.forbid
      orm_mode = True
# class permissionsResponseType(BaseModel):
#     Organizaiton: OrganizationPermissionResponseType
#     Account: AccountPermissionResponseType
#     Project: ProjectPermissionResponseType
#     User: UserPermissionResponseType
#     Ingest: IngestPermissionResponseType
#     Preprocess: PreprocessPermissionResponseType
#     Train: TrainPermissionResponseType
#     Deploy: DeployPermissionResponseType
#     Model: ModelPermissionType
#     Dataset: DatasetPermissionType
#     Application: ApplicationPermissionResponseType
#     ApiKey: APIKeyPermissionResponseType
#     Role: RolePermissionResponseType
   

# RoleCreationRequestDTO: Defines the structure for creating a new role with detailed permissions
class RoleCreationRequestDTO(BaseModel):
   name: str = Field(...)
   permissions: AccountScopedPermissions = Field(...)
   
   class Config:
      extra = Extra.forbid
   
# RoleUpdateRequestDTO: Defines the structure for updating an existing role's permissions
class RoleUpdateRequestDTO(BaseModel):
   name: Optional[str] = Field(None)
   permissions: Optional[AccountScopedPermissions] = Field(None)
    
   class Config:
      extra = Extra.forbid

   @root_validator(pre=True)
   @classmethod
   def check_not_all_none(cls, values):
      # Check if all values are None
      if all(value is None for value in values.values()):
         print(f"Inside PATCH /roles/role_id - RoleUpdateRequestDTO schema validation")
         raise ValueError("At least one field must be provided in payload")
      return values
   

class RoleResponseDTO(BaseModel):
   id: UUID = Field(...)
   name: str = Field(...)
   permissions: AccountScopedPermissions = Field(...)
   created_at: datetime = Field(...)
   updated_at: datetime = Field(...)
   
   class Config:
      extra = Extra.forbid
      orm_mode = True
    

class RoleListDTO(BaseModel):
   role_ids: List[UUID] = Field(..., description="The IDs of the roles in a list to be assigned to a user")
   action: Literal["Add", "Remove"] = Field(..., description = "The action to be performed with the roles")

   @validator('role_ids')
   @classmethod
   def validate_role_ids(cls, v : List[UUID]) -> List[UUID]:
      # Ensure uniqueness
      if len(v) != len(set(v)):
         print(f"Inside PATCH /users/user_id/accounts/account_id/roles - RoleListDTO schema validation")
         raise ValueError('Duplicate role IDs are not allowed')
      # Check length constraint
      if len(v) < 1 or len(v) > 10:
         print(f"Inside PATCH /users/user_id/accounts/account_id/roles - RoleListDTO schema validation")
         raise ValueError('The list of role IDs must have length between 1 and 10 (inclusive)')
      return v
   
   class Config:
      extra = Extra.forbid
      schema_extra = {
            "example": {
                "role_ids": [
                    "11111111-1111-1111-1111-111111111111",
                    "22222222-2222-2222-2222-222222222222",
                    "33333333-3333-3333-3333-333333333333"
                ],
                "action": "Add"
            }
        }
class RoleSummaryDTO(BaseModel):
   id: UUID = Field(..., description="ID of role")
   name: str = Field(..., description = "The name of the role")
   
   class Config:
      extra = Extra.forbid
      orm_mode = True
      schema_extra = {
            "example": {
                "id": "11111111-1111-1111-1111-111111111111",
                "name": "Data Scientist"
            }
        }
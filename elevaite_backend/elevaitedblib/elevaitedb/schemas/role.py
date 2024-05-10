from pydantic import BaseModel, Field, Extra, root_validator, validator
from typing import Optional, Literal, List
from uuid import UUID
from datetime import datetime

# 'Dataset' and 'Model' are artifacts
class ArtifactPermission(BaseModel):
   ACTION_READ: Literal["Allow", "Deny"] = Field(default="Deny")
   ACTION_TAG: Literal["Allow", "Deny"] = Field(default="Deny")

   @classmethod
   def create(cls, default_action:Literal["Allow", "Deny"] = "Deny"):
      return cls(ACTION_READ=default_action, ACTION_TAG=default_action)
   
   class Config:
      extra = Extra.forbid

class ModelPermission(ArtifactPermission):
   pass

class DatasetPermission(ArtifactPermission):
   pass

class CollectionPermission(BaseModel):
   ACTION_CREATE: Literal["Allow", "Deny"] = Field(default="Deny")
   ACTION_READ: Literal["Allow", "Deny"] = Field(default="Deny")

   @classmethod
   def create(cls, default_action:Literal["Allow", "Deny"] = "Deny"):
      return cls(ACTION_CREATE=default_action, ACTION_READ=default_action)
   
   class Config:
      extra = Extra.forbid

# Permission type for AccountScoped Project resource type
class AccountScopedProjectPermission(BaseModel):
   ACTION_CREATE: Literal["Allow", "Deny"] = Field(default="Deny")
   ACTION_READ: Literal["Allow", "Deny"] = Field(default="Deny")
   ENTITY_Dataset: DatasetPermission = Field(default_factory=DatasetPermission)
   ENTITY_Collection: CollectionPermission = Field(default_factory=CollectionPermission)
   class Config:
      extra = Extra.forbid

# Permission type for ProjectScoped Project resource type
class ProjectScopedProjectPermission(BaseModel):
   ACTION_CREATE: Literal["Allow", "Deny"] = Field(default="Allow")
   ENTITY_Dataset: DatasetPermission = Field(default_factory=lambda: DatasetPermission.create("Allow"))
   ENTITY_Collection: CollectionPermission = Field(default_factory=lambda: CollectionPermission.create("Allow"))
   class Config:
      extra = Extra.forbid

class ApplicationConfigurationPermission(BaseModel):
   ACTION_READ: Literal["Allow", "Deny"] = Field(default="Deny")
   ACTION_CREATE: Literal["Allow", "Deny"] = Field(default="Deny")
   ACTION_UPDATE: Literal["Allow", "Deny"] = Field(default="Deny")
   class Config:
      extra = Extra.forbid

class InstanceConfigurationPermission(BaseModel):
   ACTION_READ: Literal["Allow", "Deny"] = Field(default="Deny")
   class Config:
      extra = Extra.forbid

   @classmethod
   def create(cls, default_action:Literal["Allow", "Deny"] = "Deny"):
      return cls(ACTION_READ=default_action)
   
class ApplicationInstancePermission(BaseModel):
   ACTION_READ: Literal["Allow", "Deny"] = Field(default="Deny")
   ACTION_CREATE: Literal["Allow", "Deny"] = Field(default="Deny")
   ACTION_CONFIGURATION: InstanceConfigurationPermission = Field(default_factory=InstanceConfigurationPermission)
   
   class Config:
      extra = Extra.forbid

   @classmethod
   def create(cls, default_action:Literal["Allow", "Deny"] = "Deny"):
      return cls(ACTION_READ=default_action, ACTION_CREATE=default_action,ACTION_CONFIGURATION=InstanceConfigurationPermission.create(default_action))

# Account Scoped Permission type for ingest connector 
class AccountScopedApplicationIngestPermission(BaseModel):
   ENTITY_Configuration: ApplicationConfigurationPermission = Field(default_factory=ApplicationConfigurationPermission)
   ENTITY_Instance: ApplicationInstancePermission = Field(default_factory=ApplicationInstancePermission)
   ACTION_READ: Literal["Allow", "Deny"] = Field(default="Deny")
   class Config:
      extra = Extra.forbid


# Account Scoped Permission type for ingest connector 
class ProjectScopedApplicationIngestPermission(BaseModel):
   ENTITY_Instance: ApplicationInstancePermission = Field(default_factory=lambda: ApplicationInstancePermission.create("Allow"))

   class Config:
      extra = Extra.forbid

# PreprocessPermissionType follows the same structure as IngestPermissionType
class AccountScopedApplicationPreprocessPermission(AccountScopedApplicationIngestPermission):
   pass

class ProjectScopedApplicationPreprocessPermission(ProjectScopedApplicationIngestPermission):
   pass

# if generic entity had more than one branching type like 'type1' and 'type2';
# and each of them have 2 possible values like 'type1value1','type1value2', 'type2value1', 'type2value2',
# then the values of this class will consider all 4 combinations : ('type1value1', 'type2value1'), ('type1value1', 'type2value2'), ('type1value2', 'type2value1'), ('type1value2', 'type2value2')
# so the naming convention will be TYPEVALUES_<type1value1>__<type2value1>__... (delimitter between values has 2 underscores)
# in this case there is only 1 branching type with 2 values, resulting in 2 attributes.
class AccountScopedApplicationTypeValues(BaseModel): 
   TYPEVALUES_ingest: AccountScopedApplicationIngestPermission = Field(default_factory=AccountScopedApplicationIngestPermission)
   TYPEVALUES_preprocess: AccountScopedApplicationPreprocessPermission = Field(default_factory=AccountScopedApplicationPreprocessPermission)

   class Config:
      extra = Extra.forbid


# this class considers all branching type attribute names for entity: TYPENAMES_<type1name>__<type2name>__...
class AccountScopedApplicationTypeNames(BaseModel):
   TYPENAMES_applicationType: AccountScopedApplicationTypeValues = Field(default_factory=AccountScopedApplicationTypeValues)
   class Config:
      extra = Extra.forbid


# if generic entity had more than one branching type like 'type1' and 'type2';
# and each of them have 2 possible values like 'type1value1','type1value2', 'type2value1', 'type2value2',
# then the values of this class will consider all 4 combinations : ('type1value1', 'type2value1'), ('type1value1', 'type2value2'), ('type1value2', 'type2value1'), ('type1value2', 'type2value2')
# so the naming convention will be TYPEVALUES_<type1value1>__<type2value1>__... (delimitter between values has 2 underscores)
# in this case there is only 1 branching type with 2 values, resulting in 2 attributes
class ProjectScopedApplicationTypeValues(BaseModel):
   TYPEVALUES_ingest: ProjectScopedApplicationIngestPermission = Field(default_factory=ProjectScopedApplicationIngestPermission)
   TYPEVALUES_preprocess: ProjectScopedApplicationPreprocessPermission = Field(default_factory=ProjectScopedApplicationPreprocessPermission)

   class Config:
      extra = Extra.forbid

# this class considers all branching type attribute names for entity: TYPENAMES_<type1name>__<type2name>__...
class ProjectScopedApplicationTypeNames(BaseModel):
   TYPENAMES_applicationType: ProjectScopedApplicationTypeValues = Field(default_factory=ProjectScopedApplicationTypeValues)
   class Config:
      extra = Extra.forbid

class APIKeyPermission(BaseModel):
   ACTION_CREATE: Literal["Allow", "Deny"] = Field(default="Deny")
   class Config:
      extra = Extra.forbid

class AccountScopedPermission(BaseModel):
   ENTITY_Project: AccountScopedProjectPermission = Field(default_factory=AccountScopedProjectPermission)
   ENTITY_Application: AccountScopedApplicationTypeNames = Field(default_factory=AccountScopedApplicationTypeNames)
   
   class Config:
      extra = Extra.forbid
      orm_mode = True

class ProjectScopedPermission(BaseModel):
   ENTITY_Project: ProjectScopedProjectPermission = Field(default_factory=ProjectScopedProjectPermission)
   ENTITY_Application: ProjectScopedApplicationTypeNames = Field(default_factory=ProjectScopedApplicationTypeNames)
   class Config:
      extra = Extra.forbid
      orm_mode = True

# RoleCreationRequestDTO: Defines the structure for creating a new role with detailed permissions
class RoleCreationRequestDTO(BaseModel):
   name: str = Field(...)
   permissions: AccountScopedPermission = Field(...)
   
   class Config:
      extra = Extra.forbid
   
# RoleUpdateRequestDTO: Defines the structure for updating an existing role's permissions
class RoleUpdateRequestDTO(BaseModel):
   name: Optional[str] = Field(None)
   permissions: Optional[AccountScopedPermission] = Field(None)
    
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
   permissions: AccountScopedPermission = Field(...)
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
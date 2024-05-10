from pydantic import BaseModel, Field, Extra, root_validator
from typing import Optional, Literal, Union
from uuid import UUID
from enum import Enum

class RegisterUserRequestDTO(BaseModel):
   firstname: Optional[str] = Field(None, max_length=60, description="First name of user")
   lastname: Optional[str] = Field(None, max_length=60, description="Last name of user")
   
   class Config:
      extra = Extra.forbid
      schema_extra = {
         "example": {
               "firstname": "First name",
               "lastname": "Last name"
         }
      }

class BaseParamsWithoutAccountAndProject(BaseModel):
   class Config:
      extra = Extra.forbid

class ApplicationDependencyParam(BaseParamsWithoutAccountAndProject):
   application_id: int = Field(..., description = "ID of the application")

class RBACPermissionScope(str, Enum):
   ACCOUNT_SCOPE = "ACCOUNT_SCOPE"
   PROJECT_SCOPE = "PROJECT_SCOPE"

class PermissionsValidationRequest(BaseModel): # the payload for the fields directly corresponds to the path params excluding account/project. The final path param for READ/UPDATE is skipped (for example instance_id is not passed for INSTANCE_READ, collection_id is skipped for COLLECTION_READ etc), since these are permissions which are not specific to a target entity id.
   IS_ACCOUNT_ADMIN: Optional[BaseParamsWithoutAccountAndProject]
   IS_PROJECT_ADMIN: Optional[BaseParamsWithoutAccountAndProject]
   PROJECT_READ: Optional[BaseParamsWithoutAccountAndProject]
   PROJECT_CREATE: Optional[BaseParamsWithoutAccountAndProject]
   DATASET_READ: Optional[BaseParamsWithoutAccountAndProject]
   DATASET_TAG: Optional[BaseParamsWithoutAccountAndProject]
   COLLECTION_READ: Optional[BaseParamsWithoutAccountAndProject]
   COLLECTION_CREATE: Optional[BaseParamsWithoutAccountAndProject]
   CONFIGURATION_READ: Optional[ApplicationDependencyParam] # this directly corresponds to the path params needed 
   CONFIGURATION_CREATE: Optional[ApplicationDependencyParam] 
   CONFIGURATION_UPDATE: Optional[ApplicationDependencyParam] 
   INSTANCE_READ: Optional[ApplicationDependencyParam] 
   INSTANCE_CREATE: Optional[ApplicationDependencyParam] 
   INSTANCE_CONFIGURATION_READ: Optional[ApplicationDependencyParam] 

   class Config:
      extra = Extra.forbid

   @root_validator(pre=True)
   @classmethod
   def check_not_all_none(cls, values):
      # Check if all values are None
      if all(value is None for value in values.values()):
         print(f"Inside POST /auth/rbac-permissions - PermissionsValidationRequest root validator")
         raise ValueError("At least one field must be provided in payload")
      return values
   
   @staticmethod
   def parse_model_type_and_action_sequence(field_name: str) -> tuple[str, tuple[str, ...]]:
      parts = field_name.split('_')
      model_class_str = parts[0]
      action_sequence = tuple(parts[1:])
      return model_class_str, action_sequence
   
   @staticmethod
   def validate_permission_scope(field_name: str, rbac_permission_scope: RBACPermissionScope) -> bool:
      match field_name:
         case "PROJECT_READ":
            return rbac_permission_scope == RBACPermissionScope.ACCOUNT_SCOPE
         case "PROJECT_CREATE":
            return rbac_permission_scope == RBACPermissionScope.ACCOUNT_SCOPE or rbac_permission_scope == RBACPermissionScope.PROJECT_SCOPE # can be both account (when project created at topmost account level) and project scoped (when created inside a project)
         case "DATASET_READ":
            return rbac_permission_scope == RBACPermissionScope.PROJECT_SCOPE
         case "DATASET_TAG":
            return rbac_permission_scope == RBACPermissionScope.PROJECT_SCOPE
         case "COLLECTION_READ":
            return rbac_permission_scope == RBACPermissionScope.PROJECT_SCOPE
         case "COLLECTION_CREATE":
            return rbac_permission_scope == RBACPermissionScope.PROJECT_SCOPE
         case "CONFIGURATION_READ":
            return rbac_permission_scope == RBACPermissionScope.ACCOUNT_SCOPE
         case "CONFIGURATION_CREATE":
            return rbac_permission_scope == RBACPermissionScope.ACCOUNT_SCOPE
         case "CONFIGURATION_UPDATE":
            return rbac_permission_scope == RBACPermissionScope.ACCOUNT_SCOPE
         case "INSTANCE_READ":
            return rbac_permission_scope == RBACPermissionScope.PROJECT_SCOPE
         case "INSTANCE_CREATE":
            return rbac_permission_scope == RBACPermissionScope.PROJECT_SCOPE
         case "INSTANCE_CONFIGURATION_READ":
            return rbac_permission_scope == RBACPermissionScope.PROJECT_SCOPE
         case _:
            return False

class PermissionsValidationResponse(BaseModel):
   IS_ACCOUNT_ADMIN: Union[bool, Literal['NOT_EVALUATED']] = Field(default='NOT_EVALUATED')
   IS_PROJECT_ADMIN: Union[bool, Literal['NOT_EVALUATED']] = Field(default='NOT_EVALUATED')
   PROJECT_READ: Union[bool, Literal['NOT_EVALUATED']] = Field(default='NOT_EVALUATED')
   PROJECT_CREATE: Union[bool, Literal['NOT_EVALUATED']] = Field(default='NOT_EVALUATED')
   DATASET_READ: Union[bool, Literal['NOT_EVALUATED']] = Field(default='NOT_EVALUATED')
   DATASET_TAG: Union[bool, Literal['NOT_EVALUATED']] = Field(default='NOT_EVALUATED')
   COLLECTION_READ: Union[bool, Literal['NOT_EVALUATED']] = Field(default='NOT_EVALUATED')
   COLLECTION_CREATE: Union[bool, Literal['NOT_EVALUATED']] = Field(default='NOT_EVALUATED')
   CONFIGURATION_READ: Union[bool, Literal['NOT_EVALUATED']] = Field(default='NOT_EVALUATED')
   CONFIGURATION_CREATE: Union[bool, Literal['NOT_EVALUATED']] = Field(default='NOT_EVALUATED')
   CONFIGURATION_UPDATE: Union[bool, Literal['NOT_EVALUATED']] = Field(default='NOT_EVALUATED')
   INSTANCE_READ: Union[bool, Literal['NOT_EVALUATED']] = Field(default='NOT_EVALUATED')
   INSTANCE_CREATE: Union[bool, Literal['NOT_EVALUATED']] = Field(default='NOT_EVALUATED')
   INSTANCE_CONFIGURATION_READ: Union[bool, Literal['NOT_EVALUATED']] = Field(default='NOT_EVALUATED')

   class Config:
      extra = Extra.forbid
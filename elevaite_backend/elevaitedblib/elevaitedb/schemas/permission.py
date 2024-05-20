from pydantic import BaseModel, Field, Extra
from typing import Optional, Literal, List, Any
from uuid import UUID
from datetime import datetime
from enum import Enum
# define nested structure for AccountScopedRBACPermission which goes into Role.permissions
# define nested structure for ProjectScopedRBACPermission which goes into User_Project.permission_overrides
# define nested structure for ApikeyScopedRBACPermission which goes into Apikey.permissions

class RBACPermissionScope(str, Enum):
   ACCOUNT_SCOPE = "ACCOUNT_SCOPE"
   PROJECT_SCOPE = "PROJECT_SCOPE"
   APIKEY_SCOPE = "APIKEY_SCOPE"
# 'Dataset' and 'Model' are artifacts
class ArtifactPermission(BaseModel):
   ACTION_READ: Literal["Allow", "Deny"] = Field(...)
   ACTION_TAG: Literal["Allow", "Deny"] = Field(...)
   
   class Config:
      extra = Extra.forbid

   @classmethod
   def create(cls, default_action:Literal["Allow", "Deny"] = "Deny"):
      return cls(ACTION_READ=default_action, ACTION_TAG=default_action)

class ModelPermission(ArtifactPermission):
   pass

class DatasetPermission(ArtifactPermission):
   pass

class CollectionPermission(BaseModel):
   ACTION_CREATE: Literal["Allow", "Deny"] = Field(...)
   ACTION_READ: Literal["Allow", "Deny"] = Field(...)

   class Config:
      extra = Extra.forbid

   @classmethod
   def create(cls, default_action:Literal["Allow", "Deny"] = "Deny"):
      return cls(ACTION_CREATE=default_action, ACTION_READ=default_action)
   
class ApikeyPermission(BaseModel):
   ACTION_READ: Literal["Allow", "Deny"] = Field(...)
   ACTION_CREATE: Literal["Allow", "Deny"] = Field(...)
   class Config:
      extra = Extra.forbid

   @classmethod
   def create(cls, default_action:Literal["Allow", "Deny"] = "Deny"): 
      return cls(ACTION_READ=default_action, ACTION_CREATE=default_action)

class ServicenowTicketIngestPermission(BaseModel):
   ACTION_INGEST: Literal["Allow", "Deny"] = Field(...)
   class Config:
      extra = Extra.forbid

   @classmethod
   def create(cls, default_action:Literal["Allow", "Deny"] = "Deny"):
      return cls(ACTION_INGEST=default_action)
   
class ServicenowTicketPermission(BaseModel):
   ACTION_TICKET: ServicenowTicketIngestPermission = Field(...)
   class Config:
      extra = Extra.forbid

   @classmethod
   def create(cls, default_action:Literal["Allow", "Deny"] = "Deny"):
      return cls(ACTION_TICKET=ServicenowTicketIngestPermission.create(default_action))

# Permission type for AccountScoped Project resource type
class AccountScopedProjectPermission(BaseModel):
   ACTION_CREATE: Literal["Allow", "Deny"] = Field(...)
   ACTION_READ: Literal["Allow", "Deny"] = Field(...)
   ACTION_SERVICENOW: ServicenowTicketPermission = Field(...)
   ENTITY_Dataset: DatasetPermission = Field(...)
   ENTITY_Collection: CollectionPermission = Field(...)
   ENTITY_Apikey : ApikeyPermission = Field(...)
   class Config:
      extra = Extra.forbid

   @classmethod
   def create(cls, default_action: Literal["Allow", "Deny"] = "Deny"):
      return cls(
         ACTION_READ=default_action,
         ACTION_CREATE=default_action,
         ACTION_SERVICENOW=ServicenowTicketPermission.create(default_action),
         ENTITY_Dataset=DatasetPermission.create(default_action),
         ENTITY_Collection=CollectionPermission.create(default_action),
         ENTITY_Apikey=ApikeyPermission.create(default_action)
      )
   
# Permission type for ProjectScoped Project resource type
class ProjectScopedProjectPermission(BaseModel):
   ACTION_CREATE: Literal["Allow", "Deny"] = Field(...)
   ACTION_SERVICENOW: ServicenowTicketPermission = Field(...)
   ENTITY_Dataset: DatasetPermission = Field(...)
   ENTITY_Collection: CollectionPermission = Field(...)
   ENTITY_Apikey : ApikeyPermission = Field(...)
   class Config:
      extra = Extra.forbid

   @classmethod
   def create(cls, default_action: Literal["Allow", "Deny"] = "Deny"):
      return cls(
         ACTION_CREATE=default_action,
         ACTION_SERVICENOW=ServicenowTicketPermission.create(default_action),
         ENTITY_Dataset=DatasetPermission.create(default_action),
         ENTITY_Collection=CollectionPermission.create(default_action),
         ENTITY_Apikey=ApikeyPermission.create(default_action)
      )

# Permission type for ApikeyScoped Project resource type
class ApikeyScopedProjectPermission(BaseModel):
   ACTION_SERVICENOW: ServicenowTicketPermission = Field(...)
   ENTITY_Dataset: DatasetPermission = Field(...)
   ENTITY_Collection: CollectionPermission = Field(...)
   class Config:
      extra = Extra.forbid

   @classmethod
   def create(cls, default_action: Literal["Allow", "Deny"] = "Deny"):
      return cls(
         ACTION_SERVICENOW=ServicenowTicketPermission.create(default_action),
         ENTITY_Dataset=DatasetPermission.create(default_action),
         ENTITY_Collection=CollectionPermission.create(default_action),
      )
   
class ApplicationConfigurationPermission(BaseModel):
   ACTION_READ: Literal["Allow", "Deny"] = Field(...)
   ACTION_CREATE: Literal["Allow", "Deny"] = Field(...)
   ACTION_UPDATE: Literal["Allow", "Deny"] = Field(...)
   class Config:
      extra = Extra.forbid

   @classmethod
   def create(cls, default_action: Literal["Allow", "Deny"] = "Deny"):
      return cls(
         ACTION_READ=default_action,
         ACTION_CREATE=default_action,
         ACTION_UPDATE=default_action
      )
   
class InstanceConfigurationPermission(BaseModel):
   ACTION_READ: Literal["Allow", "Deny"] = Field(...)
   class Config:
      extra = Extra.forbid

   @classmethod
   def create(cls, default_action:Literal["Allow", "Deny"] = "Deny"):
      return cls(ACTION_READ=default_action)
   
class ApplicationInstancePermission(BaseModel):
   ACTION_READ: Literal["Allow", "Deny"] = Field(...)
   ACTION_CREATE: Literal["Allow", "Deny"] = Field(...)
   ACTION_CONFIGURATION: InstanceConfigurationPermission = Field(...)
   
   class Config:
      extra = Extra.forbid

   @classmethod
   def create(cls, default_action:Literal["Allow", "Deny"] = "Deny"):
      return cls(
         ACTION_READ=default_action,
         ACTION_CREATE=default_action,
         ACTION_CONFIGURATION=InstanceConfigurationPermission.create(default_action)
      )

# Account Scoped Permission type for ingest connector 
class AccountScopedApplicationIngestPermission(BaseModel):
   ENTITY_Configuration: ApplicationConfigurationPermission = Field(...)
   ENTITY_Instance: ApplicationInstancePermission = Field(...)
   ACTION_READ: Literal["Allow", "Deny"] = Field(...)
   class Config:
      extra = Extra.forbid

   @classmethod
   def create(cls, default_action: Literal["Allow", "Deny"] = "Deny"):
      return cls(
         ENTITY_Configuration=ApplicationConfigurationPermission.create(default_action),
         ENTITY_Instance=ApplicationInstancePermission.create(default_action),
         ACTION_READ=default_action
      )

# Project Scoped Permission type for ingest connector 
class ProjectScopedApplicationIngestPermission(BaseModel):
   ENTITY_Instance: ApplicationInstancePermission = Field(...)

   class Config:
      extra = Extra.forbid

   @classmethod
   def create(cls, default_action:Literal["Allow", "Deny"] = "Deny"):
      return cls(ENTITY_Instance=ApplicationInstancePermission.create(default_action))
   
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
   TYPEVALUES_ingest: AccountScopedApplicationIngestPermission = Field(...)
   TYPEVALUES_preprocess: AccountScopedApplicationPreprocessPermission = Field(...)

   class Config:
      extra = Extra.forbid

   @classmethod
   def create(cls, default_action:Literal["Allow", "Deny"] = "Deny"):
      return cls(
         TYPEVALUES_ingest=AccountScopedApplicationIngestPermission.create(default_action),
         TYPEVALUES_preprocess=AccountScopedApplicationPreprocessPermission.create(default_action)
      )

# this class considers all branching type attribute names for entity: TYPENAMES_<type1name>__<type2name>__...
class AccountScopedApplicationTypeNames(BaseModel):
   TYPENAMES_applicationType: AccountScopedApplicationTypeValues = Field(...)
   class Config:
      extra = Extra.forbid

   @classmethod
   def create(cls, default_action:Literal["Allow", "Deny"] = "Deny"):
      return cls(TYPENAMES_applicationType=AccountScopedApplicationTypeValues.create(default_action))
   
# if generic entity had more than one branching type like 'type1' and 'type2';
# and each of them have 2 possible values like 'type1value1','type1value2', 'type2value1', 'type2value2',
# then the values of this class will consider all 4 combinations : ('type1value1', 'type2value1'), ('type1value1', 'type2value2'), ('type1value2', 'type2value1'), ('type1value2', 'type2value2')
# so the naming convention will be TYPEVALUES_<type1value1>__<type2value1>__... (delimitter between values has 2 underscores)
# in this case there is only 1 branching type with 2 values, resulting in 2 attributes
class ProjectScopedApplicationTypeValues(BaseModel):
   TYPEVALUES_ingest: ProjectScopedApplicationIngestPermission = Field(...)
   TYPEVALUES_preprocess: ProjectScopedApplicationPreprocessPermission = Field(...)

   class Config:
      extra = Extra.forbid

   @classmethod
   def create(cls, default_action:Literal["Allow", "Deny"] = "Deny"):
      return cls(
         TYPEVALUES_ingest=ProjectScopedApplicationIngestPermission.create(default_action),
         TYPEVALUES_preprocess=ProjectScopedApplicationPreprocessPermission.create(default_action)
      )
   
# this class considers all branching type attribute names for entity: TYPENAMES_<type1name>__<type2name>__...
class ProjectScopedApplicationTypeNames(BaseModel):
   TYPENAMES_applicationType: ProjectScopedApplicationTypeValues = Field(...)
   class Config:
      extra = Extra.forbid

   @classmethod
   def create(cls, default_action:Literal["Allow", "Deny"] = "Deny"):
      return cls(TYPENAMES_applicationType=ProjectScopedApplicationTypeValues.create(default_action))
   
class AccountScopedRBACPermission(BaseModel):
   ENTITY_Project: AccountScopedProjectPermission = Field(...)
   ENTITY_Application: AccountScopedApplicationTypeNames = Field(...)

   class Config:
      extra = Extra.forbid
      orm_mode = True

   @classmethod
   def create(cls, default_action:Literal["Allow", "Deny"] = "Deny"):
      return cls(
         ENTITY_Project=AccountScopedProjectPermission.create(default_action),
         ENTITY_Application=AccountScopedApplicationTypeNames.create(default_action)
      )
   
   
class ProjectScopedRBACPermission(BaseModel):
   ENTITY_Project: ProjectScopedProjectPermission = Field(...)
   ENTITY_Application: ProjectScopedApplicationTypeNames = Field(...)
   
   class Config:
      extra = Extra.forbid
      orm_mode = True

   @classmethod
   def create(cls, default_action:Literal["Allow", "Deny"] = "Deny"):
      return cls(
         ENTITY_Project=ProjectScopedProjectPermission.create(default_action),
         ENTITY_Application=ProjectScopedApplicationTypeNames.create(default_action)
      )

class ApikeyScopedRBACPermission(BaseModel):
   ENTITY_Project: ApikeyScopedProjectPermission = Field(...) 
   ENTITY_Application: ProjectScopedApplicationTypeNames = Field(...)
   
   class Config:
      extra = Extra.forbid
      orm_mode = True

   @classmethod
   def create(cls, default_action:Literal["Allow", "Deny"] = "Deny"):
      return cls(
         ENTITY_Project=ApikeyScopedProjectPermission.create(default_action),
         ENTITY_Application=ProjectScopedApplicationTypeNames.create(default_action)
      )
   
   @classmethod
   def map_to_apikey_scoped_permissions(cls, rbac_permissions: dict[str, Any], rbac_permission_scope: RBACPermissionScope) -> dict[str, Any]:
      if rbac_permission_scope is RBACPermissionScope.ACCOUNT_SCOPE:
         # validate permissions against permission_scope
         try:
            validated_account_scoped_rbac_permissions = AccountScopedRBACPermission.parse_obj(rbac_permissions).dict()
         except Exception as e:
               print(f'error in map_to_apikey_scoped_permissions: malformed rbac account-scoped permissions object - {rbac_permissions}')
         # remove excessive fields 
         validated_account_scoped_rbac_permissions.pop("ENTITY_Application", None)
         validated_account_scoped_rbac_permissions["ENTITY_Project"].pop("ENTITY_Apikey", None)
         validated_account_scoped_rbac_permissions["ENTITY_Project"].pop("ACTION_CREATE", None)
         validated_account_scoped_rbac_permissions["ENTITY_Project"].pop("ENTITY_Apikey", None)
         # return permissions object which conforms to apikey scoped permissions
         return ApikeyScopedRBACPermission.parse_obj(validated_account_scoped_rbac_permissions).dict()
      elif rbac_permission_scope is RBACPermissionScope.PROJECT_SCOPE:
         # validate permissions against permission_scope
         try:
            validated_project_scoped_rbac_permissions = ProjectScopedRBACPermission.parse_obj(rbac_permissions).dict()
         except Exception as e:
               print(f'error in map_to_apikey_scoped_permissions: malformed project-scoped rbac permissions object - {rbac_permissions}')
         # remove excessive fields 
         validated_project_scoped_rbac_permissions["ENTITY_Project"].pop("ACTION_CREATE", None)
         validated_project_scoped_rbac_permissions["ENTITY_Project"].pop("ENTITY_Apikey", None)

         # return permissions object which conforms to apikey scoped permissions
         return ApikeyScopedRBACPermission.parse_obj(validated_project_scoped_rbac_permissions).dict()
      else:
         raise ValueError(f"Mapping business logic for permission scope - {rbac_permission_scope} - not implemented")

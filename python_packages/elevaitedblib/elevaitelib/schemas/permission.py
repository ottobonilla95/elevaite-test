from pydantic import BaseModel, Field, Extra, root_validator
from typing import Optional, Literal, Any
from enum import Enum

# define nested structure for AccountScopedRBACPermission which goes into Role.permissions
# define nested structure for ProjectScopedRBACPermission which goes into User_Project.permission_overrides
# define nested structure for ApikeyScopedRBACPermission which goes into Apikey.permissions


class RBACPermissionScope(str, Enum):
    ACCOUNT_SCOPE = "ACCOUNT_SCOPE"
    PROJECT_SCOPE = "PROJECT_SCOPE"
    APIKEY_SCOPE = "APIKEY_SCOPE"


# 'Dataset' and 'Model' are artifacts
class AccountScopedArtifactPermission(BaseModel):
    ACTION_READ: Optional[Literal["Allow"]] = Field(None)
    ACTION_TAG: Optional[Literal["Allow"]] = Field(None)

    @root_validator(pre=True)
    @classmethod
    def check_not_all_none(cls, values):
        # Check if all values are None
        if all(value is None for value in values.values()):
            raise ValueError(
                "At least one field - 'ACTION_READ' or 'ACTION_TAG' must be provided"
            )
        return values

    class Config:
        extra = Extra.forbid

    @classmethod
    def create(cls):
        return cls(ACTION_READ="Allow", ACTION_TAG="Allow")


class ProjectScopedArtifactPermission(BaseModel):
    ACTION_READ: Optional[Literal["Deny"]] = Field(None)
    ACTION_TAG: Optional[Literal["Deny"]] = Field(None)

    @root_validator(pre=True)
    @classmethod
    def check_not_all_none(cls, values):
        # Check if all values are None
        if all(value is None for value in values.values()):
            raise ValueError(
                "At least one field - 'ACTION_READ' or 'ACTION_TAG' must be provided"
            )
        return values

    class Config:
        extra = Extra.forbid

    @classmethod
    def create(cls):
        return cls(ACTION_READ="Deny", ACTION_TAG="Deny")


class AccountScopedModelPermission(AccountScopedArtifactPermission):
    pass


class ProjectScopedModelPermission(ProjectScopedArtifactPermission):
    pass


class AccountScopedDatasetPermission(AccountScopedArtifactPermission):
    pass


class ProjectScopedDatasetPermission(ProjectScopedArtifactPermission):
    pass


class AccountScopedCollectionPermission(BaseModel):
    ACTION_CREATE: Optional[Literal["Allow"]] = Field(None)
    ACTION_READ: Optional[Literal["Allow"]] = Field(None)

    @root_validator(pre=True)
    @classmethod
    def check_not_all_none(cls, values):
        # Check if all values are None
        if all(value is None for value in values.values()):
            raise ValueError(
                "At least one field - 'ACTION_READ' or 'ACTION_CREATE' must be provided"
            )
        return values

    class Config:
        extra = Extra.forbid

    @classmethod
    def create(cls):
        return cls(ACTION_CREATE="Allow", ACTION_READ="Allow")


class ProjectScopedCollectionPermission(BaseModel):
    ACTION_CREATE: Optional[Literal["Deny"]] = Field(None)
    ACTION_READ: Optional[Literal["Deny"]] = Field(None)

    @root_validator(pre=True)
    @classmethod
    def check_not_all_none(cls, values):
        # Check if all values are None
        if all(value is None for value in values.values()):
            raise ValueError(
                "At least one field - 'ACTION_READ' or 'ACTION_CREATE' must be provided"
            )
        return values

    class Config:
        extra = Extra.forbid

    @classmethod
    def create(cls):
        return cls(ACTION_CREATE="Deny", ACTION_READ="Deny")


class AccountScopedApikeyPermission(BaseModel):
    ACTION_READ: Optional[Literal["Allow"]] = Field(None)
    ACTION_CREATE: Optional[Literal["Allow"]] = Field(None)

    class Config:
        extra = Extra.forbid

    @root_validator(pre=True)
    @classmethod
    def check_not_all_none(cls, values):
        # Check if all values are None
        if all(value is None for value in values.values()):
            raise ValueError(
                "At least one field - 'ACTION_READ' or 'ACTION_CREATE' must be provided"
            )
        return values

    @classmethod
    def create(cls):
        return cls(ACTION_READ="Allow", ACTION_CREATE="Allow")


class ProjectScopedApikeyPermission(BaseModel):
    ACTION_READ: Optional[Literal["Deny"]] = Field(None)
    ACTION_CREATE: Optional[Literal["Deny"]] = Field(None)

    @root_validator(pre=True)
    @classmethod
    def check_not_all_none(cls, values):
        # Check if all values are None
        if all(value is None for value in values.values()):
            raise ValueError(
                "At least one field - 'ACTION_READ' or 'ACTION_CREATE' must be provided"
            )
        return values

    class Config:
        extra = Extra.forbid

    @classmethod
    def create(cls):
        return cls(ACTION_READ="Deny", ACTION_CREATE="Deny")


class AccountScopedServicenowTicketIngestPermission(BaseModel):
    ACTION_INGEST: Literal["Allow"] = Field(...)

    class Config:
        extra = Extra.forbid

    @classmethod
    def create(cls):
        return cls(ACTION_INGEST="Allow")


class ProjectScopedServicenowTicketIngestPermission(BaseModel):
    ACTION_INGEST: Literal["Deny"] = Field(...)

    class Config:
        extra = Extra.forbid

    @classmethod
    def create(cls):
        return cls(ACTION_INGEST="Deny")


class AccountScopedServicenowTicketPermission(BaseModel):
    ACTION_TICKET: AccountScopedServicenowTicketIngestPermission = Field(...)

    class Config:
        extra = Extra.forbid

    @classmethod
    def create(cls):
        return cls(ACTION_TICKET=AccountScopedServicenowTicketIngestPermission.create())


class ProjectScopedServicenowTicketPermission(BaseModel):
    ACTION_TICKET: ProjectScopedServicenowTicketIngestPermission = Field(...)

    class Config:
        extra = Extra.forbid

    @classmethod
    def create(cls):
        return cls(ACTION_TICKET=ProjectScopedServicenowTicketIngestPermission.create())


# Permission type for AccountScoped Project resource type
class AccountScopedProjectPermission(BaseModel):
    ACTION_CREATE: Optional[Literal["Allow"]] = Field(None)
    ACTION_READ: Optional[Literal["Allow"]] = Field(None)
    ACTION_SERVICENOW: Optional[AccountScopedServicenowTicketPermission] = Field(None)
    ENTITY_Dataset: Optional[AccountScopedDatasetPermission] = Field(None)
    ENTITY_Collection: Optional[AccountScopedCollectionPermission] = Field(None)
    ENTITY_Apikey: Optional[AccountScopedApikeyPermission] = Field(None)

    @root_validator(pre=True)
    @classmethod
    def check_not_all_none(cls, values):
        # Check if all values are None
        if all(value is None for value in values.values()):
            raise ValueError(
                "At least one field from - 'ACTION_READ', 'ACTION_CREATE', 'ACTION_SERVICENOW', 'ENTITY_Dataset', 'ENTITY_Collection', 'ENTITY_Apikey' must be provided"
            )
        return values

    class Config:
        extra = Extra.forbid

    @classmethod
    def create(cls):
        return cls(
            ACTION_READ="Allow",
            ACTION_CREATE="Allow",
            ACTION_SERVICENOW=AccountScopedServicenowTicketPermission.create(),
            ENTITY_Dataset=AccountScopedDatasetPermission.create(),
            ENTITY_Collection=AccountScopedCollectionPermission.create(),
            ENTITY_Apikey=AccountScopedApikeyPermission.create(),
        )


class ProjectScopedProjectPermission(BaseModel):
    ACTION_CREATE: Optional[Literal["Deny"]] = Field(None)
    ACTION_SERVICENOW: Optional[ProjectScopedServicenowTicketPermission] = Field(None)
    ENTITY_Dataset: Optional[ProjectScopedDatasetPermission] = Field(None)
    ENTITY_Collection: Optional[ProjectScopedCollectionPermission] = Field(None)
    ENTITY_Apikey: Optional[ProjectScopedApikeyPermission] = Field(None)

    @root_validator(pre=True)
    @classmethod
    def check_not_all_none(cls, values):
        # Check if all values are None
        if all(value is None for value in values.values()):
            raise ValueError(
                "At least one field from - 'ACTION_CREATE', 'ACTION_SERVICENOW', 'ENTITY_Dataset', 'ENTITY_Collection', 'ENTITY_Apikey' must be provided"
            )
        return values

    class Config:
        extra = Extra.forbid

    @classmethod
    def create(cls):
        return cls(
            ACTION_CREATE="Deny",
            ACTION_SERVICENOW=ProjectScopedServicenowTicketPermission.create(),
            ENTITY_Dataset=ProjectScopedDatasetPermission.create(),
            ENTITY_Collection=ProjectScopedCollectionPermission.create(),
            ENTITY_Apikey=ProjectScopedApikeyPermission.create(),
        )


# Permission type for ProjectScoped Project resource type


# Permission type for ApikeyScoped Project resource type
class ApikeyScopedProjectPermission(BaseModel):
    ACTION_SERVICENOW: Optional[AccountScopedServicenowTicketPermission] = Field(None)
    ENTITY_Dataset: Optional[AccountScopedDatasetPermission] = Field(None)
    ENTITY_Collection: Optional[AccountScopedCollectionPermission] = Field(None)

    @root_validator(pre=True)
    @classmethod
    def check_not_all_none(cls, values):
        # Check if all values are None
        if all(value is None for value in values.values()):
            raise ValueError(
                "At least one field from - 'ACTION_SERVICENOW', 'ENTITY_Dataset', 'ENTITY_Collection' must be provided"
            )
        return values

    class Config:
        extra = Extra.forbid

    @classmethod
    def create(cls):
        return cls(
            ACTION_SERVICENOW=AccountScopedServicenowTicketPermission.create(),
            ENTITY_Dataset=AccountScopedDatasetPermission.create(),
            ENTITY_Collection=AccountScopedCollectionPermission.create(),
        )


class ApplicationConfigurationPermission(BaseModel):
    ACTION_READ: Optional[Literal["Allow"]] = Field(None)
    ACTION_CREATE: Optional[Literal["Allow"]] = Field(None)
    ACTION_UPDATE: Optional[Literal["Allow"]] = Field(None)

    @root_validator(pre=True)
    @classmethod
    def check_not_all_none(cls, values):
        # Check if all values are None
        if all(value is None for value in values.values()):
            raise ValueError(
                "At least one field from - 'ACTION_READ', 'ACTION_CREATE', 'ACTION_UPDATE' must be provided"
            )
        return values

    class Config:
        extra = Extra.forbid

    @classmethod
    def create(cls):
        return cls(ACTION_READ="Allow", ACTION_CREATE="Allow", ACTION_UPDATE="Allow")


class AccountScopedInstanceConfigurationPermission(BaseModel):
    ACTION_READ: Literal["Allow"] = Field(...)

    class Config:
        extra = Extra.forbid

    @classmethod
    def create(cls):
        return cls(ACTION_READ="Allow")


class ProjectScopedInstanceConfigurationPermission(BaseModel):
    ACTION_READ: Literal["Deny"] = Field(...)

    class Config:
        extra = Extra.forbid

    @classmethod
    def create(cls):
        return cls(ACTION_READ="Deny")


class AccountScopedApplicationInstancePermission(BaseModel):
    ACTION_READ: Optional[Literal["Allow"]] = Field(None)
    ACTION_CREATE: Optional[Literal["Allow"]] = Field(None)
    ACTION_CONFIGURATION: Optional[AccountScopedInstanceConfigurationPermission] = (
        Field(None)
    )

    @root_validator(pre=True)
    @classmethod
    def check_not_all_none(cls, values):
        # Check if all values are None
        if all(value is None for value in values.values()):
            raise ValueError(
                "At least one field from - 'ACTION_READ', 'ACTION_CREATE', 'ACTION_CONFIGURATION' must be provided"
            )
        return values

    class Config:
        extra = Extra.forbid

    @classmethod
    def create(cls):
        return cls(
            ACTION_READ="Allow",
            ACTION_CREATE="Allow",
            ACTION_CONFIGURATION=AccountScopedInstanceConfigurationPermission.create(),
        )


class ProjectScopedApplicationInstancePermission(BaseModel):
    ACTION_READ: Optional[Literal["Deny"]] = Field(None)
    ACTION_CREATE: Optional[Literal["Deny"]] = Field(None)
    ACTION_CONFIGURATION: Optional[ProjectScopedInstanceConfigurationPermission] = (
        Field(None)
    )

    @root_validator(pre=True)
    @classmethod
    def check_not_all_none(cls, values):
        # Check if all values are None
        if all(value is None for value in values.values()):
            raise ValueError(
                "At least one field from - 'ACTION_READ', 'ACTION_CREATE', 'ACTION_CONFIGURATION' must be provided"
            )
        return values

    class Config:
        extra = Extra.forbid

    @classmethod
    def create(cls):
        return cls(
            ACTION_READ="Deny",
            ACTION_CREATE="Deny",
            ACTION_CONFIGURATION=ProjectScopedInstanceConfigurationPermission.create(),
        )


class ApikeyScopedApplicationInstancePermission(
    AccountScopedApplicationInstancePermission
):  # just for the Allow values
    pass


# Account Scoped Permission type for ingest connector
class AccountScopedApplicationIngestPermission(BaseModel):
    ENTITY_Configuration: Optional[ApplicationConfigurationPermission] = Field(None)
    ENTITY_Instance: Optional[AccountScopedApplicationInstancePermission] = Field(None)
    ACTION_READ: Optional[Literal["Allow"]] = Field(None)

    @root_validator(pre=True)
    @classmethod
    def check_not_all_none(cls, values):
        # Check if all values are None
        if all(value is None for value in values.values()):
            raise ValueError(
                "At least one field from - 'ENTITY_Configuration', 'ENTITY_Instance', 'ACTION_READ' must be provided"
            )
        return values

    class Config:
        extra = Extra.forbid

    @classmethod
    def create(cls):
        return cls(
            ENTITY_Configuration=ApplicationConfigurationPermission.create(),
            ENTITY_Instance=AccountScopedApplicationInstancePermission.create(),
            ACTION_READ="Allow",
        )


# Project Scoped Permission type for ingest connector
class ProjectScopedApplicationIngestPermission(BaseModel):
    ENTITY_Instance: ProjectScopedApplicationInstancePermission = Field(...)

    class Config:
        extra = Extra.forbid

    @classmethod
    def create(cls):
        return cls(ENTITY_Instance=ProjectScopedApplicationInstancePermission.create())


class ApikeyScopedApplicationIngestPermission(BaseModel):
    ENTITY_Instance: ApikeyScopedApplicationInstancePermission = Field(...)

    class Config:
        extra = Extra.forbid

    @classmethod
    def create(cls):
        return cls(ENTITY_Instance=ApikeyScopedApplicationInstancePermission.create())


# PreprocessPermissionType follows the same structure as IngestPermissionType
class AccountScopedApplicationPreprocessPermission(
    AccountScopedApplicationIngestPermission
):
    pass


class ProjectScopedApplicationPreprocessPermission(
    ProjectScopedApplicationIngestPermission
):
    pass


class ApikeyScopedApplicationPreprocessPermission(
    ApikeyScopedApplicationIngestPermission
):
    pass


# if generic entity had more than one branching type like 'type1' and 'type2';
# and each of them have 2 possible values like 'type1value1','type1value2', 'type2value1', 'type2value2',
# then the values of this class will consider all 4 combinations : ('type1value1', 'type2value1'), ('type1value1', 'type2value2'), ('type1value2', 'type2value1'), ('type1value2', 'type2value2')
# so the naming convention will be TYPEVALUES_<type1value1>__<type2value1>__... (delimitter between values has 2 underscores)
# in this case there is only 1 branching type with 2 values, resulting in 2 attributes.
class AccountScopedApplicationTypeValues(BaseModel):
    TYPEVALUES_ingest: Optional[AccountScopedApplicationIngestPermission] = Field(None)
    TYPEVALUES_preprocess: Optional[AccountScopedApplicationPreprocessPermission] = (
        Field(None)
    )

    @root_validator(pre=True)
    @classmethod
    def check_not_all_none(cls, values):
        # Check if all values are None
        if all(value is None for value in values.values()):
            raise ValueError(
                "At least one field from - 'TYPEVALUES_ingest', 'TYPEVALUES_preprocess' must be provided"
            )
        return values

    class Config:
        extra = Extra.forbid

    @classmethod
    def create(cls):
        return cls(
            TYPEVALUES_ingest=AccountScopedApplicationIngestPermission.create(),
            TYPEVALUES_preprocess=AccountScopedApplicationPreprocessPermission.create(),
        )


# this class considers all branching type attribute names for entity: TYPENAMES_<type1name>__<type2name>__...
class AccountScopedApplicationTypeNames(BaseModel):
    TYPENAMES_applicationType: AccountScopedApplicationTypeValues = Field(...)

    class Config:
        extra = Extra.forbid

    @classmethod
    def create(cls):
        return cls(
            TYPENAMES_applicationType=AccountScopedApplicationTypeValues.create()
        )


# if generic entity had more than one branching type like 'type1' and 'type2';
# and each of them have 2 possible values like 'type1value1','type1value2', 'type2value1', 'type2value2',
# then the values of this class will consider all 4 combinations : ('type1value1', 'type2value1'), ('type1value1', 'type2value2'), ('type1value2', 'type2value1'), ('type1value2', 'type2value2')
# so the naming convention will be TYPEVALUES_<type1value1>__<type2value1>__... (delimitter between values has 2 underscores)
# in this case there is only 1 branching type with 2 values, resulting in 2 attributes
class ProjectScopedApplicationTypeValues(BaseModel):
    TYPEVALUES_ingest: Optional[ProjectScopedApplicationIngestPermission] = Field(None)
    TYPEVALUES_preprocess: Optional[ProjectScopedApplicationPreprocessPermission] = (
        Field(None)
    )

    @root_validator(pre=True)
    @classmethod
    def check_not_all_none(cls, values):
        # Check if all values are None
        if all(value is None for value in values.values()):
            raise ValueError(
                "At least one field from - 'TYPEVALUES_ingest', 'TYPEVALUES_preprocess' must be provided"
            )
        return values

    class Config:
        extra = Extra.forbid

    @classmethod
    def create(cls):
        return cls(
            TYPEVALUES_ingest=ProjectScopedApplicationIngestPermission.create(),
            TYPEVALUES_preprocess=ProjectScopedApplicationPreprocessPermission.create(),
        )


# this class considers all branching type attribute names for entity: TYPENAMES_<type1name>__<type2name>__...
class ProjectScopedApplicationTypeNames(BaseModel):
    TYPENAMES_applicationType: ProjectScopedApplicationTypeValues = Field(...)

    class Config:
        extra = Extra.forbid

    @classmethod
    def create(cls):
        return cls(
            TYPENAMES_applicationType=ProjectScopedApplicationTypeValues.create()
        )


class ApikeyScopedApplicationTypeValues(BaseModel):
    TYPEVALUES_ingest: Optional[ApikeyScopedApplicationIngestPermission] = Field(None)
    TYPEVALUES_preprocess: Optional[ApikeyScopedApplicationPreprocessPermission] = (
        Field(None)
    )

    @root_validator(pre=True)
    @classmethod
    def check_not_all_none(cls, values):
        # Check if all values are None
        if all(value is None for value in values.values()):
            raise ValueError(
                "At least one field from - 'TYPEVALUES_ingest', 'TYPEVALUES_preprocess' must be provided"
            )
        return values

    class Config:
        extra = Extra.forbid

    @classmethod
    def create(cls):
        return cls(
            TYPEVALUES_ingest=ApikeyScopedApplicationIngestPermission.create(),
            TYPEVALUES_preprocess=ApikeyScopedApplicationPreprocessPermission.create(),
        )


class ApikeyScopedApplicationTypeNames(BaseModel):
    TYPENAMES_applicationType: ApikeyScopedApplicationTypeValues = Field(...)

    class Config:
        extra = Extra.forbid

    @classmethod
    def create(cls):
        return cls(TYPENAMES_applicationType=ApikeyScopedApplicationTypeValues.create())


class AccountScopedRBACPermission(BaseModel):
    ENTITY_Project: Optional[AccountScopedProjectPermission] = Field(None)
    ENTITY_Application: Optional[AccountScopedApplicationTypeNames] = Field(None)

    # @root_validator(pre=True)
    # @classmethod
    # def check_not_all_none(cls, values):
    #    # Check if all values are None
    #    if all(value is None for value in values.values()):
    #       raise ValueError("At least one field from - 'ENTITY_Project', 'ENTITY_Application' must be provided")
    #    return values
    class Config:
        extra = Extra.forbid
        orm_mode = True

    @classmethod
    def create(cls):
        return cls(
            ENTITY_Project=AccountScopedProjectPermission.create(),
            ENTITY_Application=AccountScopedApplicationTypeNames.create(),
        )


class ProjectScopedRBACPermission(BaseModel):
    ENTITY_Project: Optional[ProjectScopedProjectPermission] = Field(None)
    ENTITY_Application: Optional[ProjectScopedApplicationTypeNames] = Field(None)

    # @root_validator(pre=True)
    # @classmethod
    # def check_not_all_none(cls, values):
    #    # Check if all values are None
    #    if all(value is None for value in values.values()):
    #       raise ValueError("At least one field from - 'ENTITY_Project', 'ENTITY_Application' must be provided")
    #    return values

    class Config:
        extra = Extra.forbid
        orm_mode = True

    @classmethod
    def create(cls):
        return cls(
            ENTITY_Project=ProjectScopedProjectPermission.create(),
            ENTITY_Application=ProjectScopedApplicationTypeNames.create(),
        )


class ApikeyScopedRBACPermission(BaseModel):
    ENTITY_Project: Optional[ApikeyScopedProjectPermission] = Field(None)
    ENTITY_Application: Optional[ApikeyScopedApplicationTypeNames] = Field(None)

    # @root_validator(pre=True)
    # @classmethod
    # def check_not_all_none(cls, values):
    #    # Check if all values are None
    #    if all(value is None for value in values.values()):
    #       raise ValueError("At least one field from - 'ENTITY_Project', 'ENTITY_Application' must be provided")
    #    return values

    class Config:
        extra = Extra.forbid
        orm_mode = True

    @classmethod
    def create(cls):
        return cls(
            ENTITY_Project=ApikeyScopedProjectPermission.create(),
            ENTITY_Application=ApikeyScopedApplicationTypeNames.create(),
        )

    @classmethod
    def map_to_apikey_scoped_permissions(
        cls,
        rbac_permissions: dict[str, Any],
        rbac_permission_scope: RBACPermissionScope,
    ) -> dict[str, Any]:
        if rbac_permission_scope is RBACPermissionScope.PROJECT_SCOPE:
            # validate permissions against permission_scope
            try:
                ProjectScopedRBACPermission.parse_obj(rbac_permissions).dict()
            except Exception:
                print(
                    f"error in map_to_apikey_scoped_permissions: malformed project-scoped rbac permissions object - {rbac_permissions}"
                )
            # remove excessive fields
            if "ENTITY_Project" in rbac_permissions:
                rbac_permissions["ENTITY_Project"].pop("ACTION_CREATE", None)
                rbac_permissions["ENTITY_Project"].pop("ENTITY_Apikey", None)

            # return permissions object which conforms to apikey scoped permissions
            return rbac_permissions
        else:
            raise ValueError(
                f"Mapping business logic for permission scope - {rbac_permission_scope} - not implemented"
            )

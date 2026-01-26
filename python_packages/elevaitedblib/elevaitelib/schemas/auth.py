from pydantic import BaseModel, Field, Extra, root_validator
from typing import Optional, Literal, Union
from enum import Enum
from .permission import (
    RBACPermissionScope,
)


class RegisterUserRequestDTO(BaseModel):
    firstname: Optional[str] = Field(
        None, max_length=60, description="First name of user"
    )
    lastname: Optional[str] = Field(
        None, max_length=60, description="Last name of user"
    )

    class Config:
        extra = Extra.forbid
        schema_extra = {"example": {"firstname": "First name", "lastname": "Last name"}}


class ExcludeAccountAndProjectParams(BaseModel):
    class Config:
        extra = Extra.forbid

    @root_validator(pre=True)
    def check_forbidden_fields(cls, values):
        forbidden_fields = {"account_id", "project_id"}
        for field in forbidden_fields:
            if field in values:
                raise ValueError(f"Field '{field}' is not allowed.")
        return values


class IsAccountAdminPermissionEvaluationRequest(ExcludeAccountAndProjectParams):
    pass


class IsProjectAdminPermissionEvaluationRequest(ExcludeAccountAndProjectParams):
    pass


# All route params below exclude account_id and project_id, and are for the general target resource rather than a particular target resource
# class GetApplicationsRouteParams(ExcludeAccountAndProjectParams):  # /application
#     pass


class GetProjectsRouteParams(ExcludeAccountAndProjectParams):  # /projects
    pass


class CreateProjectRouteParams(ExcludeAccountAndProjectParams):  # /projects
    pass


class IngestServicenowTicketsRouteParams(
    ExcludeAccountAndProjectParams
):  # /servicenow/ingest
    pass


class GetApiKeysRouteParams(
    ExcludeAccountAndProjectParams
):  # /projects/{project_id}/apikeys
    pass


class CreateApiKeyRouteParams(
    ExcludeAccountAndProjectParams
):  # /projects/{project_id}/apikeys
    pass


class GetDatasetsRouteParams(
    ExcludeAccountAndProjectParams
):  # /projects/{project_id}/datasets
    pass


class TagDatasetRouteParams(
    ExcludeAccountAndProjectParams
):  # /projects/{project_id}/datasets -> not considering specfic dataset for tag permissions on general dataset resources
    pass


class GetCollectionsRouteParams(
    ExcludeAccountAndProjectParams
):  # /projects/{project_id}/collection
    pass


class CreateCollectionRouteParams(
    ExcludeAccountAndProjectParams
):  # /projects/{project_id}/collection
    pass


class GetApplicationConfigurationsRouteParams(
    ExcludeAccountAndProjectParams
):  # /application/{application_id}/configuration
    application_id: int = Field(..., description="ID of the application")


class CreateApplicationConfigurationRouteParams(
    ExcludeAccountAndProjectParams
):  # /projects/{project_id}/configuration
    application_id: int = Field(..., description="ID of the application")


class UpdateApplicationConfigurationRouteParams(
    ExcludeAccountAndProjectParams
):  # /projects/{project_id}/configuration -> not considering specfic configuration for update permissions on general configuration resources
    application_id: int = Field(..., description="ID of the application")


class GetApplicationInstanceRouteParams(
    ExcludeAccountAndProjectParams
):  # /application/{application_id}/instance
    application_id: int = Field(..., description="ID of the application")


class CreateApplicationInstanceRouteParams(
    ExcludeAccountAndProjectParams
):  # /application/{application_id}/instance
    application_id: int = Field(..., description="ID of the application")


class UpdateApplicationInstanceRouteParams(
    ExcludeAccountAndProjectParams
):  # /application/{application_id}/instance -> not considering specfic instance for update permissions on general instance resources
    application_id: int = Field(..., description="ID of the application")


class GetApplicationInstanceConfigurationsRouteParams(
    ExcludeAccountAndProjectParams
):  # /application/{application_id}/instance -> not considering specfic instance for configuration read permissions on general instance resources
    application_id: int = Field(..., description="ID of the application")


class PermissionsEvaluationRequest(
    BaseModel
):  # the payload for the fields directly corresponds to the path params/header params for the GET ALL version of the endpoints (in other words, exclude target model id) without account/project in any order; this is because these are not exclusive to the target model id, and account/project is skipped because it is evaluated once in the endpoint for all the fields in payload for POST /auth/rbac-permissions
    IS_ACCOUNT_ADMIN: Optional[IsAccountAdminPermissionEvaluationRequest]
    IS_PROJECT_ADMIN: Optional[IsProjectAdminPermissionEvaluationRequest]
    # APPLICATION_READ: Optional[GetApplicationsRouteParams]
    PROJECT_READ: Optional[GetProjectsRouteParams]
    PROJECT_CREATE: Optional[CreateProjectRouteParams]
    PROJECT_SERVICENOW_TICKET_INGEST: Optional[IngestServicenowTicketsRouteParams]
    APIKEY_READ: Optional[GetApiKeysRouteParams]
    APIKEY_CREATE: Optional[CreateApiKeyRouteParams]
    DATASET_READ: Optional[GetDatasetsRouteParams]
    DATASET_TAG: Optional[TagDatasetRouteParams]
    COLLECTION_READ: Optional[GetCollectionsRouteParams]
    COLLECTION_CREATE: Optional[CreateCollectionRouteParams]
    CONFIGURATION_READ: Optional[GetApplicationConfigurationsRouteParams]
    CONFIGURATION_CREATE: Optional[CreateApplicationConfigurationRouteParams]
    CONFIGURATION_UPDATE: Optional[UpdateApplicationConfigurationRouteParams]
    INSTANCE_READ: Optional[GetApplicationInstanceRouteParams]
    INSTANCE_CREATE: Optional[CreateApplicationInstanceRouteParams]
    INSTANCE_CONFIGURATION_READ: Optional[
        GetApplicationInstanceConfigurationsRouteParams
    ]

    class Config:
        extra = Extra.forbid

    @root_validator(pre=True)
    @classmethod
    def check_not_all_none(cls, values):
        # Check if all values are None
        if all(value is None for value in values.values()):
            print(
                "Inside POST /auth/rbac-permissions - PermissionsEvaluationRequest root validator"
            )
            raise ValueError("At least one field must be provided in payload")
        return values

    @staticmethod
    def parse_model_type_and_action_sequence(
        field_name: str,
    ) -> tuple[str, tuple[str, ...]]:
        parts = field_name.split("_")
        model_class_str = parts[0]
        action_sequence = tuple(parts[1:])
        return model_class_str, action_sequence

    @staticmethod
    def validate_permission_scope(
        field_name: str, rbac_permission_scope: RBACPermissionScope
    ) -> bool:
        match field_name:
            case "APPLICATION_READ":
                return rbac_permission_scope == RBACPermissionScope.ACCOUNT_SCOPE
            case "PROJECT_READ":
                return rbac_permission_scope == RBACPermissionScope.ACCOUNT_SCOPE
            case "PROJECT_CREATE":
                return (
                    rbac_permission_scope == RBACPermissionScope.ACCOUNT_SCOPE
                    or rbac_permission_scope == RBACPermissionScope.PROJECT_SCOPE
                )  # can be both account (when project created at topmost account level) and project scoped (when created inside a project)
            case "PROJECT_SERVICENOW_TICKET_INGEST":
                return rbac_permission_scope == RBACPermissionScope.PROJECT_SCOPE
            case "APIKEY_READ":
                return rbac_permission_scope == RBACPermissionScope.PROJECT_SCOPE
            case "APIKEY_CREATE":
                return rbac_permission_scope == RBACPermissionScope.PROJECT_SCOPE
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


class EvaluatedPermission(BaseModel):
    OVERALL_PERMISSIONS: bool

    class Config:
        extra = Extra.forbid

    @classmethod
    def create(cls, overall_permissions: bool):
        return cls(OVERALL_PERMISSIONS=overall_permissions)


class IsAccountAdminEvaluatedPermission(EvaluatedPermission):
    pass


class IsProjectAdminEvaluatedPermission(EvaluatedPermission):
    pass


# When 'Application' entity is the target entity, since it has  has 1 typename - 'applicationType' - and 2 possible typevalues - 'ingest' and 'preprocess',
# its READ request will have to consider specific permissions for these types as well and may look something like:
# {
#   applicationType: {
#       ingest: false
#       preprocess: true
#   }
# }

# suppose later there is a target entity which has 2 typenames - 'typename1' and 'typename2'
# and 'typename1' can have 2 values - 'type1value1' and 'type1value2'
# and 'typename2' can have 2 values - 'type2value1' and type2value2'
# then to consider all possibilities, the example response will look like :

# {
#   typename1_typename2: {
#       type1value1_type2value1: false,
#       type1value1_type2value2: true,
#       type1value2_type2value1: false,
#       type1value2_type2value2: false,
#   }
# }

# NOTES:

# The outer key 'typename1_typename2' represents the possible typenames for the entities delimited by underscore. Their order determines typevalue (inner keys) mapping to the typenames
# The inner keys represent the possible typevalue combinations for the entities delimited by underscore. typename-typevalue can be determined based on the order of listing


class ApplicationEntityTypeValues(BaseModel):
    preprocess: bool
    ingest: bool

    @classmethod
    def create(cls, all_permissions: bool):
        return cls(preprocess=all_permissions, ingest=all_permissions)


class ApplicationEntityTypeNames(BaseModel):
    applicationType: ApplicationEntityTypeValues

    @classmethod
    def create(cls, all_permissions: bool):
        return cls(applicationType=ApplicationEntityTypeValues.create(all_permissions))


class GetApplicationsEvaluatedPermission(EvaluatedPermission):
    SPECIFIC_PERMISSIONS: ApplicationEntityTypeNames

    @classmethod
    def create(cls, all_permissions: bool):
        return cls(
            SPECIFIC_PERMISSIONS=ApplicationEntityTypeNames.create(all_permissions),
            OVERALL_PERMISSIONS=all_permissions,
        )


class GetProjectsEvaluatedPermission(EvaluatedPermission):
    pass


class CreateProjectEvaluatedPermission(EvaluatedPermission):
    pass


class IngestServicenowTicketsEvaluatedPermission(EvaluatedPermission):
    pass


class GetApiKeysEvaluatedPermission(EvaluatedPermission):
    pass


class CreateApiKeyEvaluatedPermission(EvaluatedPermission):
    pass


class GetDatasetsEvaluatedPermission(EvaluatedPermission):
    pass


class TagDatasetEvaluatedPermission(EvaluatedPermission):
    pass


class GetCollectionsEvaluatedPermission(EvaluatedPermission):
    pass


class CreateCollectionEvaluatedPermission(EvaluatedPermission):
    pass


class GetApplicationConfigurationsEvaluatedPermission(EvaluatedPermission):
    pass


class CreateApplicationConfigurationEvaluatedPermission(EvaluatedPermission):
    pass


class UpdateApplicationConfigurationEvaluatedPermission(EvaluatedPermission):
    pass


class GetApplicationInstanceEvaluatedPermission(EvaluatedPermission):
    pass


class CreateApplicationInstanceEvaluatedPermission(EvaluatedPermission):
    pass


class GetApplicationInstanceConfigurationsEvaluatedPermission(EvaluatedPermission):
    pass


class EvaluatedPermissionsFactory:
    @staticmethod
    def get_evaluated_permission(
        all_permissions: bool, permission_field
    ) -> EvaluatedPermission:
        match permission_field:
            case "APPLICATION_READ":
                return GetApplicationsEvaluatedPermission.create(all_permissions)
            case "PROJECT_READ":
                return GetProjectsEvaluatedPermission.create(all_permissions)
            case "PROJECT_CREATE":
                return CreateProjectEvaluatedPermission.create(all_permissions)
            case "PROJECT_SERVICENOW_TICKET_INGEST":
                return IngestServicenowTicketsEvaluatedPermission.create(
                    all_permissions
                )
            case "APIKEY_READ":
                return GetApiKeysEvaluatedPermission.create(all_permissions)
            case "APIKEY_CREATE":
                return CreateApiKeyEvaluatedPermission.create(all_permissions)
            case "DATASET_READ":
                return GetDatasetsEvaluatedPermission.create(all_permissions)
            case "DATASET_TAG":
                return TagDatasetEvaluatedPermission.create(all_permissions)
            case "COLLECTION_READ":
                return GetCollectionsEvaluatedPermission.create(all_permissions)
            case "COLLECTION_CREATE":
                return CreateCollectionEvaluatedPermission.create(all_permissions)
            case "CONFIGURATION_READ":
                return GetApplicationConfigurationsEvaluatedPermission.create(
                    all_permissions
                )
            case "CONFIGURATION_CREATE":
                return CreateApplicationConfigurationEvaluatedPermission.create(
                    all_permissions
                )
            case "CONFIGURATION_UPDATE":
                return UpdateApplicationConfigurationEvaluatedPermission.create(
                    all_permissions
                )
            case "INSTANCE_READ":
                return GetApplicationInstanceEvaluatedPermission.create(all_permissions)
            case "INSTANCE_CREATE":
                return CreateApplicationInstanceEvaluatedPermission.create(
                    all_permissions
                )
            case "INSTANCE_CONFIGURATION_READ":
                return GetApplicationInstanceConfigurationsEvaluatedPermission.create(
                    all_permissions
                )
            case _:
                raise ValueError(f"Unsupported permission field: {permission_field}")


class PermissionsEvaluationResponse(BaseModel):
    IS_ACCOUNT_ADMIN: Union[
        IsAccountAdminEvaluatedPermission, Literal["NOT_EVALUATED"]
    ] = Field(default="NOT_EVALUATED")
    IS_PROJECT_ADMIN: Union[
        IsProjectAdminEvaluatedPermission, Literal["NOT_EVALUATED"]
    ] = Field(default="NOT_EVALUATED")
    APPLICATION_READ: Union[
        GetApplicationsEvaluatedPermission, Literal["NOT_EVALUATED"]
    ] = Field(default="NOT_EVALUATED")
    PROJECT_READ: Union[GetProjectsEvaluatedPermission, Literal["NOT_EVALUATED"]] = (
        Field(default="NOT_EVALUATED")
    )
    PROJECT_CREATE: Union[
        CreateProjectEvaluatedPermission, Literal["NOT_EVALUATED"]
    ] = Field(default="NOT_EVALUATED")
    PROJECT_SERVICENOW_TICKET_INGEST: Union[
        IngestServicenowTicketsEvaluatedPermission, Literal["NOT_EVALUATED"]
    ] = Field(default="NOT_EVALUATED")
    APIKEY_READ: Union[GetApiKeysEvaluatedPermission, Literal["NOT_EVALUATED"]] = Field(
        default="NOT_EVALUATED"
    )
    APIKEY_CREATE: Union[CreateApiKeyEvaluatedPermission, Literal["NOT_EVALUATED"]] = (
        Field(default="NOT_EVALUATED")
    )
    DATASET_READ: Union[GetDatasetsEvaluatedPermission, Literal["NOT_EVALUATED"]] = (
        Field(default="NOT_EVALUATED")
    )
    DATASET_TAG: Union[TagDatasetEvaluatedPermission, Literal["NOT_EVALUATED"]] = Field(
        default="NOT_EVALUATED"
    )
    COLLECTION_READ: Union[
        GetCollectionsEvaluatedPermission, Literal["NOT_EVALUATED"]
    ] = Field(default="NOT_EVALUATED")
    COLLECTION_CREATE: Union[
        CreateCollectionEvaluatedPermission, Literal["NOT_EVALUATED"]
    ] = Field(default="NOT_EVALUATED")
    CONFIGURATION_READ: Union[
        GetApplicationConfigurationsEvaluatedPermission, Literal["NOT_EVALUATED"]
    ] = Field(default="NOT_EVALUATED")
    CONFIGURATION_CREATE: Union[
        CreateApplicationConfigurationEvaluatedPermission, Literal["NOT_EVALUATED"]
    ] = Field(default="NOT_EVALUATED")
    CONFIGURATION_UPDATE: Union[
        UpdateApplicationConfigurationEvaluatedPermission, Literal["NOT_EVALUATED"]
    ] = Field(default="NOT_EVALUATED")
    INSTANCE_READ: Union[
        GetApplicationInstanceEvaluatedPermission, Literal["NOT_EVALUATED"]
    ] = Field(default="NOT_EVALUATED")
    INSTANCE_CREATE: Union[
        CreateApplicationInstanceEvaluatedPermission, Literal["NOT_EVALUATED"]
    ] = Field(default="NOT_EVALUATED")
    INSTANCE_CONFIGURATION_READ: Union[
        GetApplicationInstanceConfigurationsEvaluatedPermission,
        Literal["NOT_EVALUATED"],
    ] = Field(default="NOT_EVALUATED")

    class Config:
        extra = Extra.forbid


class iDPType(str, Enum):
    GOOGLE = "google"
    CREDENTIALS = "credentials"


class AuthType(str, Enum):
    ACCESS_TOKEN = "access_token"
    API_KEY = "api_key"
    ACCESS_TOKEN_OR_API_KEY = "access_token_or_api_key"


from . import (
   entities as entity_validators,
   auth as auth_validators,
   servicenow as servicenow_validators
)
from elevaitedb.db import models
from elevaitedb.schemas import (
   api as api_schemas,
)
route_validator_map = {
   (api_schemas.APINamespace.RBAC_API, "register_user"): auth_validators.register.validate_register_user,   
   (api_schemas.APINamespace.RBAC_API, "evaluate_rbac_permissions"): auth_validators.rbac_permissions.validate_evaluate_rbac_permissions, 

   (api_schemas.APINamespace.RBAC_API, "patch_organization"): entity_validators.organization.validate_patch_organization,
   (api_schemas.APINamespace.RBAC_API, "get_organization"): entity_validators.organization.validate_get_organization,
   (api_schemas.APINamespace.RBAC_API, "get_org_users"): entity_validators.organization.validate_get_org_users,

   (api_schemas.APINamespace.RBAC_API, "create_account"): entity_validators.account.validate_post_account,
   (api_schemas.APINamespace.RBAC_API, "patch_account"): entity_validators.account.validate_patch_account,
   (api_schemas.APINamespace.RBAC_API, "get_accounts"): entity_validators.account.validate_get_accounts,
   (api_schemas.APINamespace.RBAC_API, "get_account"): entity_validators.account.validate_get_account,
   (api_schemas.APINamespace.RBAC_API, "get_account_user_list"): entity_validators.account.validate_get_account_user_list,
   (api_schemas.APINamespace.RBAC_API, "assign_users_to_account"): entity_validators.account.validate_assign_users_to_account,
   (api_schemas.APINamespace.RBAC_API, "deassign_user_from_account"): entity_validators.account.validate_deassign_user_from_account,
   (api_schemas.APINamespace.RBAC_API, "patch_user_account_admin_status"): entity_validators.account.validate_patch_account_admin_status,

   (api_schemas.APINamespace.RBAC_API, "create_project"): entity_validators.project.validate_post_project_factory(models.Project, ("CREATE",)),
   (api_schemas.APINamespace.RBAC_API, "patch_project"): entity_validators.project.validate_patch_project_factory(models.Project, ("READ",)),
   (api_schemas.APINamespace.RBAC_API, "get_project"): entity_validators.project.validate_get_project_factory(models.Project, ("READ",)), 
   (api_schemas.APINamespace.RBAC_API, "get_projects"): entity_validators.project.validate_get_projects_factory(models.Project, ("READ",)),
   (api_schemas.APINamespace.RBAC_API, "get_project_user_list"): entity_validators.project.validate_get_project_user_list_factory(models.Project, ("READ",)),
   (api_schemas.APINamespace.RBAC_API, "deassign_user_from_project"): entity_validators.project.validate_deassign_user_from_project_factory(models.Project, ("READ",)),
   (api_schemas.APINamespace.RBAC_API, "assign_users_to_project"): entity_validators.project.validate_assign_users_to_project_factory(models.Project, ("READ",)),
   (api_schemas.APINamespace.RBAC_API, "patch_user_project_admin_status"): entity_validators.project.validate_update_user_project_admin_status_factory(models.Project, ("READ",)),

   (api_schemas.APINamespace.RBAC_API, "get_apikey"): entity_validators.apikey.validate_get_apikey_factory(models.Apikey, ("READ",)),
   (api_schemas.APINamespace.RBAC_API, "get_apikeys"): entity_validators.apikey.validate_get_apikeys_factory(models.Apikey, ("READ",)),
   (api_schemas.APINamespace.RBAC_API, "create_apikey"): entity_validators.apikey.validate_create_apikey_factory(models.Apikey, ("CREATE",)),
   (api_schemas.APINamespace.RBAC_API, "delete_apikey"): entity_validators.apikey.validate_delete_apikey_factory(models.Apikey, ("READ",)),
   
   (api_schemas.APINamespace.RBAC_API, "create_role"): entity_validators.role.validate_post_roles,
   (api_schemas.APINamespace.RBAC_API, "get_role"): entity_validators.role.validate_get_role,
   (api_schemas.APINamespace.RBAC_API, "get_roles"): entity_validators.role.validate_get_roles,
   (api_schemas.APINamespace.RBAC_API, "patch_role"): entity_validators.role.validate_patch_roles,
   (api_schemas.APINamespace.RBAC_API, "delete_role"): entity_validators.role.validate_delete_roles,

   (api_schemas.APINamespace.RBAC_API, "patch_user"): entity_validators.user.validate_patch_user,
   (api_schemas.APINamespace.RBAC_API, "get_user_profile"): entity_validators.user.validate_get_user_profile,
   (api_schemas.APINamespace.RBAC_API, "patch_user_account_roles"): entity_validators.user.validate_patch_user_account_roles,
   (api_schemas.APINamespace.RBAC_API, "update_user_project_permission_overrides"): entity_validators.user.validate_update_project_permission_overrides_factory(models.Project, ("READ", )),
   (api_schemas.APINamespace.RBAC_API, "get_user_project_permission_overrides"): entity_validators.user.validate_get_project_permission_overrides_factory(models.Project, ("READ", )),
   (api_schemas.APINamespace.RBAC_API, "patch_user_superadmin_status"): entity_validators.user.validate_patch_user_superadmin_status,

   (api_schemas.APINamespace.ETL_API, "getApplicationList"): entity_validators.application.validate_get_applications_factory(models.Application, ("READ", )),
   (api_schemas.APINamespace.ETL_API, "getApplicationById"): entity_validators.application.validate_get_application_factory(models.Application, ("READ", )),
   (api_schemas.APINamespace.ETL_API, "getApplicationPipelines"): entity_validators.application.validate_get_application_pipelines_factory(models.Application, ("READ", )),

   (api_schemas.APINamespace.ETL_API, "getCollectionsOfProject"): entity_validators.collection.validate_get_project_collections_factory(models.Collection, ("READ", )),
   (api_schemas.APINamespace.ETL_API, "getCollectionById"): entity_validators.collection.validate_get_project_collection_factory(models.Collection, ("READ", )),
   (api_schemas.APINamespace.ETL_API, "createCollection"): entity_validators.collection.validate_create_project_collection_factory(models.Collection, ("CREATE", )),
   (api_schemas.APINamespace.ETL_API, "getCollectionScroll"): entity_validators.collection.validate_get_project_collection_scroll_factory(models.Collection, ("READ", )), 

   (api_schemas.APINamespace.ETL_API, "getApplicationConfigurations"): entity_validators.configuration.validate_get_application_configurations_factory(models.Configuration, ("READ", )),
   (api_schemas.APINamespace.ETL_API, "getApplicationConfiguration"): entity_validators.configuration.validate_get_application_configuration_factory(models.Configuration, ("READ", )),
   (api_schemas.APINamespace.ETL_API, "createConfiguration"): entity_validators.configuration.validate_create_application_configuration_factory(models.Configuration, ("CREATE", )),
   (api_schemas.APINamespace.ETL_API, "updateConfiguration"): entity_validators.configuration.validate_update_application_configuration_factory(models.Configuration, ("UPDATE", )),

   (api_schemas.APINamespace.ETL_API, "getProjectDatasets"): entity_validators.dataset.validate_get_project_datasets_factory(models.Dataset, ("READ", )),
   (api_schemas.APINamespace.ETL_API, "getDatasetById"): entity_validators.dataset.validate_get_project_dataset_factory(models.Dataset, ("READ", )),
   (api_schemas.APINamespace.ETL_API, "addTagToDataset"): entity_validators.dataset.validate_add_tag_to_dataset_factory(models.Dataset, ("TAG", )),

   (api_schemas.APINamespace.ETL_API, "getApplicationInstances"): entity_validators.instance.validate_get_application_instances_factory(models.Instance, ("READ", )),
   (api_schemas.APINamespace.ETL_API, "getApplicationInstanceById"): entity_validators.instance.validate_get_application_instance_factory(models.Instance, ("READ", )),
   (api_schemas.APINamespace.ETL_API, "getApplicationInstanceChart"): entity_validators.instance.validate_get_application_instance_chart_factory(models.Instance, ("READ", )),
   (api_schemas.APINamespace.ETL_API, "getApplicationInstanceConfiguration"): entity_validators.instance.validate_get_application_instance_configuration_factory(models.Instance, ("CONFIGURATION", "READ",)),
   (api_schemas.APINamespace.ETL_API, "getApplicationInstanceLogs"): entity_validators.instance.validate_get_application_instance_logs_factory(models.Instance, ("READ", )),
   (api_schemas.APINamespace.ETL_API, "createApplicationInstance"): entity_validators.instance.validate_create_application_instance_factory(models.Instance, ("CREATE", )),

   (api_schemas.APINamespace.ETL_API, "ingestServiceNowTickets"): servicenow_validators.ingest.validate_servicenow_tickets_ingest_factory(models.Project, ("SERVICENOW", "TICKET", "INGEST",)), 
}



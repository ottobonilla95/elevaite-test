
from . import (
   entities as entity_validators,
   auth as auth_validators,
   servicenow as servicenow_validators
)
from elevaitedb.db import models

routes_to_middleware_imple_map = {
   "register_user": auth_validators.register.validate_register_user,   
   "evaluate_rbac_permissions": auth_validators.rbac_permissions.validate_evaluate_rbac_permissions, 

   "patch_organization": entity_validators.organization.validate_patch_organization,
   "get_organization": entity_validators.organization.validate_get_organization,
   "get_org_users": entity_validators.organization.validate_get_org_users,

   "create_account": entity_validators.account.validate_post_account,
   "patch_account": entity_validators.account.validate_patch_account,
   "get_accounts": entity_validators.account.validate_get_accounts,
   "get_account": entity_validators.account.validate_get_account,
   "get_account_user_list": entity_validators.account.validate_get_account_user_list,
   "assign_users_to_account": entity_validators.account.validate_assign_users_to_account,
   "deassign_user_from_account": entity_validators.account.validate_deassign_user_from_account,
   "patch_user_account_admin_status": entity_validators.account.validate_patch_account_admin_status,

   "create_project": entity_validators.project.validate_post_project_factory(models.Project, ("CREATE",)),
   "patch_project": entity_validators.project.validate_patch_project_factory(models.Project, ("READ",)),
   "get_project": entity_validators.project.validate_get_project_factory(models.Project, ("READ",)), 
   "get_projects": entity_validators.project.validate_get_projects_factory(models.Project, ("READ",)),
   "get_project_user_list": entity_validators.project.validate_get_project_user_list_factory(models.Project, ("READ",)),
   "deassign_user_from_project": entity_validators.project.validate_deassign_user_from_project_factory(models.Project, ("READ",)),
   "assign_users_to_project": entity_validators.project.validate_assign_users_to_project_factory(models.Project, ("READ",)),
   "patch_user_project_admin_status": entity_validators.project.validate_update_user_project_admin_status_factory(models.Project, ("READ",)),

   "get_apikey": entity_validators.apikey.validate_get_apikey_factory(models.Apikey, ("READ",)),
   "get_apikeys": entity_validators.apikey.validate_get_apikeys_factory(models.Apikey, ("READ",)),
   "create_apikey": entity_validators.apikey.validate_create_apikey_factory(models.Apikey, ("CREATE",)),
   "delete_apikey": entity_validators.apikey.validate_delete_apikey_factory(models.Apikey, ("READ",)),
   
   "create_role": entity_validators.role.validate_post_roles,
   "get_role": entity_validators.role.validate_get_role,
   "get_roles": entity_validators.role.validate_get_roles,
   "patch_role": entity_validators.role.validate_patch_roles,
   "delete_role": entity_validators.role.validate_delete_roles,

   "patch_user": entity_validators.user.validate_patch_user,
   "get_user_profile": entity_validators.user.validate_get_user_profile,
   "patch_user_account_roles": entity_validators.user.validate_patch_user_account_roles,
   "update_user_project_permission_overrides": entity_validators.user.validate_update_project_permission_overrides_factory(models.Project, ("READ", )),
   "get_user_project_permission_overrides": entity_validators.user.validate_get_project_permission_overrides_factory(models.Project, ("READ", )),
   "patch_user_superadmin_status": entity_validators.user.validate_patch_user_superadmin_status,

   "getApplicationList": entity_validators.application.validate_get_applications_factory(models.Application, ("READ", )),
   "getApplicationById": entity_validators.application.validate_get_application_factory(models.Application, ("READ", )),
   "getApplicationPipelines": entity_validators.application.validate_get_application_pipelines_factory(models.Application, ("READ", )),

   "getCollectionsOfProject": entity_validators.collection.validate_get_project_collections_factory(models.Collection, ("READ", )),
   "getCollectionById": entity_validators.collection.validate_get_project_collection_factory(models.Collection, ("READ", )),
   "createCollection": entity_validators.collection.validate_create_project_collection_factory(models.Collection, ("CREATE", )),
   "getCollectionScroll": entity_validators.collection.validate_get_project_collection_scroll_factory(models.Collection, ("READ", )), 

   "getApplicationConfigurations": entity_validators.configuration.validate_get_application_configurations_factory(models.Configuration, ("READ", )),
   "getApplicationConfiguration": entity_validators.configuration.validate_get_application_configuration_factory(models.Configuration, ("READ", )),
   "createConfiguration": entity_validators.configuration.validate_create_application_configuration_factory(models.Configuration, ("CREATE", )),
   "updateConfiguration": entity_validators.configuration.validate_update_application_configuration_factory(models.Configuration, ("UPDATE", )),

   "getProjectDatasets": entity_validators.dataset.validate_get_project_datasets_factory(models.Dataset, ("READ", )),
   "getDatasetById": entity_validators.dataset.validate_get_project_dataset_factory(models.Dataset, ("READ", )),
   "addTagToDataset": entity_validators.dataset.validate_add_tag_to_dataset_factory(models.Dataset, ("TAG", )),

   "getApplicationInstances": entity_validators.instance.validate_get_application_instances_factory(models.Instance, ("READ", )),
   "getApplicationInstanceById": entity_validators.instance.validate_get_application_instance_factory(models.Instance, ("READ", )),
   "getApplicationInstanceChart": entity_validators.instance.validate_get_application_instance_chart_factory(models.Instance, ("READ", )),
   "getApplicationInstanceConfiguration": entity_validators.instance.validate_get_application_instance_configuration_factory(models.Instance, ("CONFIGURATION", "READ",)),
   "getApplicationInstanceLogs": entity_validators.instance.validate_get_application_instance_logs_factory(models.Instance, ("READ", )),
   "createApplicationInstance": entity_validators.instance.validate_create_application_instance_factory(models.Instance, ("CREATE", )),

   "ingestServiceNowTickets": servicenow_validators.ingest.validate_servicenow_tickets_ingest_factory(models.Project, ("SERVICENOW", "TICKET", "INGEST",)), 
}




from . import (
   entities as entity_middlewares,
   auth as auth_middlewares,
   servicenow as servicenow_middlewares
)
from elevaitedb.db import models

routes_to_middleware_imple_map = {
   "register_user": auth_middlewares.register.validate_register_user,  
   "evaluate_rbac_permissions": auth_middlewares.rbac_permissions.validate_evaluate_rbac_permissions,

   "patch_organization": entity_middlewares.organization.validate_patch_organization,
   "get_organization": entity_middlewares.organization.validate_get_organization,
   "get_org_users": entity_middlewares.organization.validate_get_org_users,

   "create_account": entity_middlewares.account.validate_post_account,
   "patch_account": entity_middlewares.account.validate_patch_account,
   "get_accounts": entity_middlewares.account.validate_get_accounts,
   "get_account": entity_middlewares.account.validate_get_account,
   "get_account_user_list": entity_middlewares.account.validate_get_account_user_list,
   "assign_users_to_account": entity_middlewares.account.validate_assign_users_to_account,
   "deassign_user_from_account": entity_middlewares.account.validate_deassign_user_from_account,
   "patch_user_account_admin_status": entity_middlewares.account.validate_patch_account_admin_status,

   "create_project": entity_middlewares.project.validate_post_project_factory(models.Project, ("CREATE",)),
   "patch_project": entity_middlewares.project.validate_patch_project_factory(models.Project, ("READ",)),
   "get_project": entity_middlewares.project.validate_get_project_factory(models.Project, ("READ",)), 
   "get_projects": entity_middlewares.project.validate_get_projects_factory(models.Project, ("READ",)),
   "get_project_user_list": entity_middlewares.project.validate_get_project_user_list_factory(models.Project, ("READ",)),
   "deassign_user_from_project": entity_middlewares.project.validate_deassign_user_from_project_factory(models.Project, ("READ",)),
   "assign_users_to_project": entity_middlewares.project.validate_assign_users_to_project_factory(models.Project, ("READ",)),
   "patch_user_project_admin_status": entity_middlewares.project.validate_update_user_project_admin_status_factory(models.Project, ("READ",)),

   "get_apikey": entity_middlewares.apikey.validate_get_apikey_factory(models.Apikey, ("READ",)),
   "get_apikeys": entity_middlewares.apikey.validate_get_apikeys_factory(models.Apikey, ("READ",)),
   "create_apikey": entity_middlewares.apikey.validate_create_apikey_factory(models.Apikey, ("CREATE",)),
   "delete_apikey": entity_middlewares.apikey.validate_delete_apikey_factory(models.Apikey, ("READ",)),
   
   "create_role": entity_middlewares.role.validate_post_roles,
   "get_role": entity_middlewares.role.validate_get_role,
   "get_roles": entity_middlewares.role.validate_get_roles,
   "patch_role": entity_middlewares.role.validate_patch_roles,
   "delete_role": entity_middlewares.role.validate_delete_roles,

   "patch_user": entity_middlewares.user.validate_patch_user,
   "get_user_profile": entity_middlewares.user.validate_get_user_profile,
   "patch_user_account_roles": entity_middlewares.user.validate_patch_user_account_roles,
   "update_user_project_permission_overrides": entity_middlewares.user.validate_update_project_permission_overrides_factory(models.Project, ("READ", )),
   "get_user_project_permission_overrides": entity_middlewares.user.validate_get_project_permission_overrides_factory(models.Project, ("READ", )),
   "patch_user_superadmin_status": entity_middlewares.user.validate_patch_user_superadmin_status,

   "getApplicationList": entity_middlewares.application.validate_get_applications_factory(models.Application, ("READ", )),
   "getApplicationById": entity_middlewares.application.validate_get_application_factory(models.Application, ("READ", )),
   "getApplicationPipelines": entity_middlewares.application.validate_get_application_pipelines_factory(models.Application, ("READ", )),

   "getCollectionsOfProject": entity_middlewares.collection.validate_get_project_collections_factory(models.Collection, ("READ", )),
   "getCollectionById": entity_middlewares.collection.validate_get_project_collection_factory(models.Collection, ("READ", )),
   "createCollection": entity_middlewares.collection.validate_create_project_collection_factory(models.Collection, ("CREATE", )),
   "getCollectionScroll": entity_middlewares.collection.validate_get_project_collection_scroll_factory(models.Collection, ("READ", )),

   "getApplicationConfigurations": entity_middlewares.configuration.validate_get_application_configurations_factory(models.Configuration, ("READ", )),
   "getApplicationConfiguration": entity_middlewares.configuration.validate_get_application_configuration_factory(models.Configuration, ("READ", )),
   "createConfiguration": entity_middlewares.configuration.validate_create_application_configuration_factory(models.Configuration, ("CREATE", )),
   "updateConfiguration": entity_middlewares.configuration.validate_update_application_configuration_factory(models.Configuration, ("UPDATE", )),

   "getProjectDatasets": entity_middlewares.dataset.validate_get_project_datasets_factory(models.Dataset, ("READ", )),
   "getDatasetById": entity_middlewares.dataset.validate_get_project_dataset_factory(models.Dataset, ("READ", )),
   "addTagToDataset": entity_middlewares.dataset.validate_add_tag_to_dataset_factory(models.Dataset, ("TAG", )),

   "getApplicationInstances": entity_middlewares.instance.validate_get_application_instances_factory(models.Instance, ("READ", )),
   "getApplicationInstanceById": entity_middlewares.instance.validate_get_application_instance_factory(models.Instance, ("READ", )),
   "getApplicationInstanceChart": entity_middlewares.instance.validate_get_application_instance_chart_factory(models.Instance, ("READ", )),
   "getApplicationInstanceConfiguration": entity_middlewares.instance.validate_get_application_instance_configuration_factory(models.Instance, ("CONFIGURATION", "READ",)),
   "getApplicationInstanceLogs": entity_middlewares.instance.validate_get_application_instance_logs_factory(models.Instance, ("READ", )),
   "createApplicationInstance": entity_middlewares.instance.validate_create_application_instance_factory(models.Instance, ("CREATE", )),

   "ingestServiceNowTickets": servicenow_middlewares.ingest.validate_servicenow_tickets_ingest_factory(models.Project, ("SERVICENOW", "TICKET", "INGEST",)), 
}



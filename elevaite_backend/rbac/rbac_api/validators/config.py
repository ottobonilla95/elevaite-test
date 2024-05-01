from elevaitedb.db import models
from .schemas.permissions import account_scoped_permissions as rbac_schema

model_classStr_to_class = {
   "Account": models.Account,
   "Project": models.Project,
   "User": models.User,
   "Application": models.Application,
   "Instance": models.Instance,
   "Configuration": models.Configuration,
   "Dataset": models.Dataset,
   "Collection": models.Collection,
}

validation_precedence_order = [models.Project, models.Application, models.Configuration, models.Instance, models.Dataset, models.Collection] # order of validating associations and role based permissions for models 

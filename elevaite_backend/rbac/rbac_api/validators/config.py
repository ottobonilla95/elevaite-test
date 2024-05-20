from elevaitedb.db import models

# include all models in routes here
model_classStr_to_class = {
   "Account": models.Account,
   "Project": models.Project,
   "User": models.User,
   "Application": models.Application,
   "Instance": models.Instance,
   "Configuration": models.Configuration,
   "Dataset": models.Dataset,
   "Collection": models.Collection,
   "Apikey": models.Apikey
}

# validation_precedence_order : dictates order of account-scoped and project-scoped role evaluation
# include all models (ENTITY's) present in role_schemas.AccountScopedRBACPermission here 
# left-to-right order generally follows path param order of outer entity to inner entity
# Project should be placed first in this order, and then the general left-to-right order follows path param order of outer entity to inner entity
# It is only important that for entities involved in a certain endpoint, the inner entities should be to the right of the inner entities
validation_precedence_order = [models.Project, models.Application, models.Configuration, models.Instance, models.Dataset, models.Collection, models.Apikey]

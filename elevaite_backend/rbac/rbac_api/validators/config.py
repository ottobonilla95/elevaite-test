from elevaitedb.db import models
from typing import Optional, Type

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

validation_precedence_order = [models.Account, models.Project, models.Application, models.Configuration, models.Instance, models.Dataset, models.Collection] # order of validating associations and role based permissions for models 

rbac_schema =  {
   "ENTITY_Account": {
      "ACTION_READ": "Allow"
   },
   "ENTITY_Project": {
      "ACTION_READ": "Allow",
      "ACTION_CREATE": "Allow",
      "ENTITY_Dataset": {
         "ACTION_READ" : "Allow",
         "ACTION_TAG": "Allow"
      },
      "ENTITY_Collection": {
         "ACTION_READ" : "Allow",
         "ACTION_CREATE": "Allow"
      }
   },
   "ENTITY_Application": {
      "TYPENAMES_applicationType": {
         "TYPEVALUES_ingest":{
            "ENTITY_Configuration": {
               "ACTION_READ": "Allow",
               "ACTION_CREATE": "Allow",
               "ACTION_UPDATE": "Allow"
            },
            "ENTITY_Instance": {
               "ACTION_READ": "Allow",
               "ACTION_CREATE": "Allow",
               "ACTION_CONFIGURATION": {
                  "ACTION_READ": "Allow"
               }
            },
            "ACTION_READ": "Allow"
         },
         "TYPEVALUES_preprocess": {
            "ENTITY_Configuration": {
               "ACTION_READ": "Allow",
               "ACTION_CREATE": "Allow",
               "ACTION_UPDATE": "Allow"
            },
            "ENTITY_Instance": {
               "ACTION_READ": "Allow",
               "ACTION_CREATE": "Allow",
               "ACTION_CONFIGURATION": {
                  "ACTION_READ": "Allow"
               }
            },
            "ACTION_READ": "Allow"
         }
      }
   }
}

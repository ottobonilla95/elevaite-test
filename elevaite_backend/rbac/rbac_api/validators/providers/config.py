from elevaitedb.db import models
from elevaitelib.schemas import permission as permission_schemas

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
    "Apikey": models.Apikey,
}

# validation_precedence_order : dictates order of account-scoped and project-scoped role evaluation
# include all models (ENTITY's) present in role_schemas.AccountScopedRBACPermission here
# left-to-right order generally follows path param order of outer entity to inner entity
# Project should be placed first in this order, and then the general left-to-right order follows path param order of outer entity to inner entity
# It is only important that for entities involved in a certain endpoint, the inner entities should be to the right of the inner entities
validation_precedence_order = [
    models.Project,
    models.Application,
    models.Configuration,
    models.Instance,
    models.Dataset,
    models.Collection,
    models.Apikey,
]


# X ----------------------------------- PERMISSION SCHEMAS ---------------------------------------------------

# The value 'Allow/Deny' has no meaning other than for schema validation against the pydantic class - 'AccountScopedRBACPermission'
# The actual values will be determined at the time of role creation/updation

# The nested structure of the schema reflects the nested structure of the endpoints:

# ENDPOINTS : /projects/
#             /projects/<...>/datasets
#             /projects/<...>/collections
#             /projects/<...>/apikeys
#             /application/<...>/configuration
#             /application/<...>/instance
#             /servicenow/ingest
# Account, User, Role resources only have rbac decided by superadmin/account-admin/project-admin status and hence are not part of the schema

# Resources are prefixed by 'ENTITY_', actions on these entities are prefixed by 'ACTION_' (actions can be a leaf action, or have other nested actions)
# If an entity has 1 or more types, the types which require rbac validation are considered 'branching types'.
# If entities have 1 or more branching types, for example the 'Application' entity has the typename - 'applicationType' column with 2 possible type values - 'preprocess' and 'ingest' (as defined by enum), where both of these are considered branching since they require rbac validation
# then the entities must list the branching types with the following syntax:  TYPENAMES_<type1name>__<type2name>__... (double underscore as delimiter between typenames)

# if generic entity had more than one branching type like 'type1' and 'type2';
# and each of them have 2 possible values like 'type1value1','type1value2', 'type2value1', 'type2value2',
# then the 4 value combinations are : ('type1value1', 'type2value1'), ('type1value1', 'type2value2'), ('type1value2', 'type2value1'), ('type1value2', 'type2value2')
# so the value listing will be of the format:
#                              TYPEVALUES_type1value1__type2value1
#                              TYPEVALUES_type1value1__type2value2
#                              TYPEVALUES_type1value2__type2value1
#                              TYPEVALUES_type1value2__type2value2

# so the naming convention will be TYPEVALUES_<type1value1>__<type2value1>__... (delimitter between values has 2 underscores)
# in the case of the 'Application  case there is only 1 branching type with 2 values, resulting in:
# TYPEVALUES_ingest
# TYPEVALUES_preprocess

# The nested contents must be listed inside each branching type value. This way the schema can be parsed for validation in a generic way.

# This is the Role.permissions schema which reflect AccountScopedRBACPermissions since role permissions are account scoped
# Is not taken into consideration for users with elevated status of superadmin (User.is_superadmin)/account-admin(User_Account.is_admin)
account_scoped_permissions = permission_schemas.AccountScopedRBACPermission.create(
    "Allow"
).dict()
# {
#    "ENTITY_Project": {
#       "ACTION_READ": "Allow",
#       "ACTION_CREATE": "Allow",
#       "ACTION_SERVICENOW": {
#          "ACTION_TICKET" : {
#            "ACTION_INGEST" : "Allow"
#           }
#       },
#       "ENTITY_Dataset": {
#          "ACTION_READ" : "Allow",
#          "ACTION_TAG": "Allow"
#       },
#       "ENTITY_Collection": {
#          "ACTION_READ" : "Allow",
#          "ACTION_CREATE": "Allow"
#       },
#       "ENTITY_Apikey":{
#          "ACTION_READ": "Allow",
#          "ACTION_CREATE": "Allow"
#       }
#    },
#    "ENTITY_Application": {
#       "TYPENAMES_applicationType": {
#          "TYPEVALUES_ingest":{
#             "ENTITY_Configuration": {
#                "ACTION_READ": "Allow",
#                "ACTION_CREATE": "Allow",
#                "ACTION_UPDATE": "Allow"
#             },
#             "ENTITY_Instance": {
#                "ACTION_READ": "Allow",
#                "ACTION_CREATE": "Allow",
#                "ACTION_CONFIGURATION": {
#                   "ACTION_READ": "Allow"
#                }
#             },
#             "ACTION_READ": "Allow"
#          },
#          "TYPEVALUES_preprocess": {
#             "ENTITY_Configuration": {
#                "ACTION_READ": "Allow",
#                "ACTION_CREATE": "Allow",
#                "ACTION_UPDATE": "Allow"
#             },
#             "ENTITY_Instance": {
#                "ACTION_READ": "Allow",
#                "ACTION_CREATE": "Allow",
#                "ACTION_CONFIGURATION": {
#                   "ACTION_READ": "Allow"
#                }
#             },
#             "ACTION_READ": "Allow"
#          }
#       }
#    }
# }

# An example of how schema can be modified to include validations when  entities have more than 1 type:
# When modifying this schema, the pydantic class for AccountScopedRBACPermission must also be updated to reflect the new schema.

# In this case, 'Application' entity has two type columns - 'applicationType' and 'applicationTypeX' with the following possible value combinations :
# COLUMN NAME :      'applicationType'          'applicationTypeX'
# COLUMN VALUES : ('ingest', 'preprocess')       ('ingest', 'preprocess')
#
# 'Instance' entity has 1 type column - 'instanceTypeX' - with the following possible value combinations:
# COLUMN NAME :      'instanceTypeX'
# COLUMN VALUE :           'Type1'


# {
#    "ENTITY_Account": {
#       "ACTION_READ": "Allow"
#    },
#    "ENTITY_Project": {
#       "ACTION_READ": "Allow",
#       "ACTION_CREATE": "Allow",
#       "ACTION_SERVICENOW": {
#          "ACTION_TICKET" : {
#            "ACTION_INGEST" : "Allow"
#           }
#       },
#       "ENTITY_Apikey":{
#          "ACTION_READ": "Allow",
#          "ACTION_CREATE": "Allow"
#       },
#       "ENTITY_Dataset": {
#          "ACTION_READ" : "Allow",
#          "ACTION_TAG": "Allow"
#       },
#       "ENTITY_Collection": {
#          "ACTION_READ" : "Allow",
#          "ACTION_CREATE": "Allow"
#       }
#    },
#    "ENTITY_Application": {
#       "TYPENAMES_applicationType__applicationTypeX": {
#          "TYPEVALUES_ingest__ingest":{
#             "ENTITY_Configuration": {
#                "ACTION_READ": "Allow",
#                "ACTION_CREATE": "Allow",
#                "ACTION_UPDATE": "Allow"
#             },
#             "ENTITY_Instance": {
#                "TYPENAMES_instanceTypeX": {
#                   "TYPEVALUES_Type1":{
#                      "ACTION_READ": "Allow",
#                      "ACTION_CREATE": "Allow",
#                      "ACTION_CONFIGURATION": {
#                         "ACTION_READ": "Allow"
#                      }
#                   }
#                }
#             },
#             "ACTION_READ": "Allow"
#          },
#          "TYPEVALUES_ingest__preprocess":{
#             "ENTITY_Configuration": {
#                "ACTION_READ": "Allow",
#                "ACTION_CREATE": "Allow",
#                "ACTION_UPDATE": "Allow"
#             },
#             "ENTITY_Instance": {
#                "TYPENAMES_instanceTypeX": {
#                   "TYPEVALUES_Type1":{
#                      "ACTION_READ": "Allow",
#                      "ACTION_CREATE": "Allow",
#                      "ACTION_CONFIGURATION": {
#                         "ACTION_READ": "Allow"
#                      }
#                   }
#                }
#             },
#             "ACTION_READ": "Allow"
#          },
#          "TYPEVALUES_preprocess__ingest":{
#             "ENTITY_Configuration": {
#                "ACTION_READ": "Allow",
#                "ACTION_CREATE": "Allow",
#                "ACTION_UPDATE": "Allow"
#             },
#             "ENTITY_Instance": {
#                "TYPENAMES_instanceTypeX": {
#                   "TYPEVALUES_Type1":{
#                      "ACTION_READ": "Allow",
#                      "ACTION_CREATE": "Allow",
#                      "ACTION_CONFIGURATION": {
#                         "ACTION_READ": "Allow"
#                      }
#                   }
#                }
#             },
#             "ACTION_READ": "Allow"
#          },
#          "TYPEVALUES_preprocess__preprocess": {
#             "ENTITY_Configuration": {
#                "ACTION_READ": "Allow",
#                "ACTION_CREATE": "Allow",
#                "ACTION_UPDATE": "Allow"
#             },
#             "ENTITY_Instance": {
#                "TYPENAMES_instanceTypeX": {
#                   "TYPEVALUES_Type1":{
#                      "ACTION_READ": "Allow",
#                      "ACTION_CREATE": "Allow",
#                      "ACTION_CONFIGURATION": {
#                         "ACTION_READ": "Allow"
#                      }
#                   }
#                }
#             },
#             "ACTION_READ": "Allow"
#          }
#       }
#    }
# }


# This is the schema for User_Project.permission_overrides used for checking project permission overrides for a user in a project;
# Only meaningful if user has account-scoped permission for the resource first.
#  'Deny' value for a field means that the user who has account-scoped permission for that field, will be denied due to project-based permission overrides for that field.
# there is a It only contains permissions applicable at the project level; Project ENTITY's READ action, Configuration ENTITY and Application ENTITY's READ action permissions are omitted since they are account level actions and resources.
project_scoped_permissions = permission_schemas.ProjectScopedRBACPermission.create(
    "Allow"
).dict()
# {
#   "ENTITY_Project": {
#       "ACTION_CREATE": "Allow",
#       "ACTION_SERVICENOW": {
#          "ACTION_TICKET" : {
#            "ACTION_INGEST" : "Allow"
#           }
#       },
#       "ENTITY_Dataset": {
#          "ACTION_TAG": "Allow",
#          "ACTION_READ": "Allow"
#       },
#       "ENTITY_Collection": {
#          "ACTION_READ": "Allow",
#          "ACTION_CREATE": "Allow"
#       },
#       "ENTITY_Apikey":{
#          "ACTION_READ": "Allow",
#          "ACTION_CREATE": "Allow"
#       }
#   },
#   "ENTITY_Application": {
#       "TYPENAMES_applicationType": {
#          "TYPEVALUES_ingest": {
#             "ENTITY_Instance": {
#                "ACTION_READ": "Allow",
#                "ACTION_CREATE": "Allow",
#                "ACTION_CONFIGURATION": {
#                   "ACTION_READ": "Allow"
#                }
#             }
#          },
#          "TYPEVALUES_preprocess": {
#          "ENTITY_Instance": {
#                "ACTION_READ": "Allow",
#                "ACTION_CREATE": "Allow",
#                "ACTION_CONFIGURATION": {
#                   "ACTION_READ": "Allow"
#                }
#             }
#          }
#       }
#    }
# }

# This is the schema used for Apikey (Apikey.permissions) It only contains permissions scoped to the APikey, which is scoped to the project, and hence has a subset of the project's permissions.
# does not contain Project-CREATE,Apikey-CREATE, Apikey-READ
apikey_scoped_permissions = permission_schemas.ApikeyScopedRBACPermission.create(
    "Allow"
).dict()
# {
#   "ENTITY_Project": {
#       "ACTION_SERVICENOW": {
#          "ACTION_TICKET" : {
#            "ACTION_INGEST" : "Allow"
#           }
#       },
#       "ENTITY_Dataset": {
#          "ACTION_TAG": "Allow",
#          "ACTION_READ": "Allow"
#       },
#       "ENTITY_Collection": {
#          "ACTION_READ": "Allow",
#          "ACTION_CREATE": "Allow"
#       }
#   },
#   "ENTITY_Application": {
#       "TYPENAMES_applicationType": {
#          "TYPEVALUES_ingest": {
#             "ENTITY_Instance": {
#                "ACTION_READ": "Allow",
#                "ACTION_CREATE": "Allow",
#                "ACTION_CONFIGURATION": {
#                   "ACTION_READ": "Allow"
#                }
#             }
#          },
#          "TYPEVALUES_preprocess": {
#          "ENTITY_Instance": {
#                "ACTION_READ": "Allow",
#                "ACTION_CREATE": "Allow",
#                "ACTION_CONFIGURATION": {
#                   "ACTION_READ": "Allow"
#                }
#             }
#          }
#       }
#    }
# }

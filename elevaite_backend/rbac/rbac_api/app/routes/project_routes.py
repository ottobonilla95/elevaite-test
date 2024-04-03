from fastapi import APIRouter, Path, Body, status, Depends, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import List, Optional, Any
from uuid import UUID

from elevaitedb.schemas import (
     project_schemas,
     user_schemas,
)
from elevaitedb.db import models

from rbac_api.validators import (
   extract_and_validate_post_project_data,
   validate_get_project,
   validate_get_projects,
   validate_get_project_user_list,
   validate_patch_project,
   # validate_assign_self_to_project,
   validate_deassign_self_from_project,
   validate_assign_or_deassign_users_in_project,
   # validate_patch_project_status
)

from ..services import project_service as service
from .utils.helpers import load_schema

project_router = APIRouter(prefix="/projects", tags=["projects"])

@project_router.post("/", status_code=status.HTTP_201_CREATED, responses={
   status.HTTP_201_CREATED: {
      "description": "Project successfully created",
      "model": project_schemas.ProjectResponseDTO
   },
   status.HTTP_401_UNAUTHORIZED: {
      "description": "invalid, expired or no access token",
      "content": {
         "application/json": {
            "examples": load_schema('common/unauthorized_examples.json')
            }
         },
   },
   status.HTTP_403_FORBIDDEN: {
      "description": "User does not have permission to create project",
      "content": {
         "application/json": {
            "examples": load_schema('projects/post_project/forbidden_examples.json')
            }
         },
   },
   status.HTTP_404_NOT_FOUND: {
      "description": "account or parent project not found",
      "content": {
         "application/json": {
            "examples": load_schema('projects/post_project/notfound_examples.json')
            }
         },
   },
   status.HTTP_409_CONFLICT: {
      "description": "Project with same name already exists in account",
      "content": {
         "application/json": {
            "examples": load_schema('projects/post_project/conflict_examples.json')
            }
         },
   },
   status.HTTP_422_UNPROCESSABLE_ENTITY: {
      "description": "Payload validation error",
      "content": {
         "application/json": {
            "examples": load_schema('projects/post_project/validationerror_examples.json')
            }
         },
   },
   status.HTTP_503_SERVICE_UNAVAILABLE: {
      "description": "The server is currently unable to handle the request due to a server-side error, temporary overloading, or maintenance of the server",
      "content": {
         "application/json": {
            "examples": load_schema('common/serviceunavailable_examples.json')
            }
         },
   }
})
async def create_project(
   project_creation_payload: project_schemas.ProjectCreationRequestDTO = Body(..., description="project creation payload"),
   validation_info: dict[str, Any]= Depends(extract_and_validate_post_project_data)
) -> project_schemas.ProjectResponseDTO:
   db: Session = validation_info.get("db", None)
   logged_in_user_id: UUID = validation_info.get("logged_in_user_id", None)
   return service.create_project(project_creation_payload, db, logged_in_user_id)
   
@project_router.patch("/{project_id}", status_code=status.HTTP_200_OK, responses={
   status.HTTP_200_OK: {
      "description": "Project successfully patched",
      "content": {
         "application/json": {
            "examples": load_schema('projects/patch_project/ok_examples.json')
         }
      },
   },
   status.HTTP_401_UNAUTHORIZED: {
      "description": "invalid, expired or no access token",
      "content": {
         "application/json": {
            "examples": load_schema('common/unauthorized_examples.json')
         }
      },
   },
   status.HTTP_403_FORBIDDEN: {
      "description": "User does not have permission to patch project",
      "content": {
         "application/json": {
            "examples": load_schema('projects/patch_project/forbidden_examples.json')
         }
      },
   },
   status.HTTP_404_NOT_FOUND: {
      "description": "account or parent project not found",
      "content": {
         "application/json": {
            "examples": load_schema('projects/patch_project/notfound_examples.json')
         }
      },
   },
   status.HTTP_422_UNPROCESSABLE_ENTITY: {
      "description": "Payload validation error",
      "content": {
         "application/json": {
            "examples": load_schema('projects/patch_project/validationerror_examples.json')
         }
      },
   },
   status.HTTP_503_SERVICE_UNAVAILABLE: {
      "description": "The server is currently unable to handle the request due to a server-side error, temporary overloading, or maintenance of the server",
      "content": {
         "application/json": {
            "examples": load_schema('common/serviceunavailable_examples.json')
         }
      },
   }
})
async def patch_project(
   project_patch_payload: project_schemas.ProjectPatchRequestDTO = Body(...),
   validation_info: dict[str, Any] = Depends(validate_patch_project) # Assuming the dependency function extracts the user ID from the access token, and performs all required validations.
   ) -> project_schemas.ProjectResponseDTO: 
      project_to_patch: models.Project = validation_info.get("project_to_patch", None)
      db: Session = validation_info.get("db", None)
      return service.patch_project(project_to_patch, project_patch_payload, db)

@project_router.get("/{project_id}", status_code=status.HTTP_200_OK, responses={
   status.HTTP_200_OK: {
      "description": "Project successfully retrieved",
      "model": project_schemas.ProjectResponseDTO
   },
   status.HTTP_401_UNAUTHORIZED: {
      "description": "invalid, expired or no access token",
      "content": {
         "application/json": {
            "examples": load_schema('common/unauthorized_examples.json')
         }
      },
   },
   status.HTTP_403_FORBIDDEN: {
      "description": "logged-in user is not assigned to account or project or account is disabled",
      "content": {
         "application/json": {
            "examples": load_schema('projects/get_project/forbidden_examples.json')
         }
      },
   },
   status.HTTP_404_NOT_FOUND: {
      "description": "account or project not found",
      "content": {
         "application/json": {
            "examples": load_schema('projects/get_project/notfound_examples.json')
         }
      },
   },
   status.HTTP_422_UNPROCESSABLE_ENTITY: {
      "description": "Payload validation error",
      "content": {
         "application/json": {
            "examples": load_schema('projects/get_project/validationerror_examples.json')
         }
      },
   },
   status.HTTP_503_SERVICE_UNAVAILABLE: {
      "description": "The server is currently unable to handle the request due to a server-side error, temporary overloading, or maintenance of the server",
      "content": {
         "application/json": {
            "examples": load_schema('common/serviceunavailable_examples.json')
         }
      },
   }
})
async def get_project(
   validation_info: dict[str, Any] = Depends(validate_get_project) # Assuming the dependency function extracts the user ID from the access token, and performs all required validations.
   ) -> project_schemas.ProjectResponseDTO: 
      project: models.Project = validation_info.get("project", None)
      return project

@project_router.get("/", status_code=status.HTTP_200_OK, responses={
   status.HTTP_200_OK: {
      "description": "List of projects successfully retrieved",
      "model": List[project_schemas.ProjectResponseDTO]
   },
   status.HTTP_401_UNAUTHORIZED: {
      "description": "invalid, expired or no access token",
      "content": {
         "application/json": {
            "examples": load_schema('common/unauthorized_examples.json')
         }
      },
   },
   status.HTTP_403_FORBIDDEN: {
      "description": "User does not have permission to read projects",
      "content": {
         "application/json": {
            "examples": load_schema('projects/get_projects/forbidden_examples.json')
         }
      },
   },
   status.HTTP_404_NOT_FOUND: {
      "description": "Parent project or account not found",
      "content": {
         "application/json": {
            "examples": load_schema('projects/get_projects/notfound_examples.json')
         }
      },
   },
   status.HTTP_422_UNPROCESSABLE_ENTITY: {
      "description": "Payload validation error",
      "content": {
         "application/json": {
            "examples": load_schema('projects/get_projects/validationerror_examples.json')
            }
         },
   },
   status.HTTP_503_SERVICE_UNAVAILABLE: {
      "description": "The server is currently unable to handle the request due to a temporary overloading or maintenance of the server",
      "content": {
         "application/json": {
            "examples": load_schema('common/serviceunavailable_examples.json')
         }
      }
   }
}) 
async def get_projects( 
   validation_info: dict[str,Any] = Depends(validate_get_projects), # = Depends(validate_project_get) - Assuming the dependency that extracts the user ID from the access token, and performs all required validations including accessibility check into parent_project. This dependency will have signature that has req:Request, account_id: UUID = Query(..., description="Account ID") to make sure account id is mandatory query param for validation
   account_id: UUID = Query(..., description = "account id to which the project belongs to"),
   view: Optional[project_schemas.ProjectView] = Query(None, description = "View mode, either - 'Flat' or 'Hierarchical'; default value is 'Flat'. When set to 'Flat', parent_project_id will not be considered"),
   parent_project_id: Optional[UUID] = Query(None, description = "parent project id under which projects are queried; if not provided, refers to top level projects under account"),
   type: Optional[project_schemas.ProjectType] = Query(None, description = "Optional filter for querying projects based on ownership, either - 'My_Projects' or 'Shared_With_Me'; if not provided then this will assume both types (all projects for superadmin/admins)"),
   project_owner_email: Optional[str] = Query(None, description = "Optional filter for querying projects based on project_owner_email"),
   name: Optional[str] = Query(None, description = "Optional filter for querying projects based on project name"),
) -> List[project_schemas.ProjectResponseDTO]:
   """
    Retrieves a list of projects based on the provided criteria. This endpoint supports fetching both top-level projects and subprojects within a specific account, differentiated by the existence of parent_project_id (exists for sub-projects and doesn't exist for top-level projects), and filters of sharing status.

    Parameters:
    - account_id (int): Mandatory. The ID of the account to filter projects by.
    - view (Literal["Flat", Hierarchical], optional): Optional. Determines the view mode of projects to return. Can be 'Hierarchical' to show parent-child view where parent_project_id will be considered (null value for parent_project_id indicates top level projects in account), or 'Flat' which ignores parent_project_id value and lists all projects that user is associated with.
    - parent_project_id (int, optional): Optional. Specifies the ID of a parent project to fetch its subprojects. When omitted, top-level projects are returned; Only considered when 'view' is set to 'Hierarchical'.
    - type (Literal["My_Projects", "Shared_With_Me"], optional): Optional. Determines the type of projects to return. Can be 'My_Projects' for projects created by the logged-in user, or 'shared_with_me' for projects that the logged-in user has access to but did not create. When omitted, behavior defaults to returning all projects accessible to the user.

    Returns:
    - A list of projects or subprojects matching the specified criteria. The structure of the returned projects is defined by the application model.
   """
   db: Session = validation_info.get("db", None)
   logged_in_user_id = validation_info["logged_in_user_id"]
   logged_in_user_is_superadmin = validation_info.get("logged_in_user_is_superadmin", False)
   logged_in_user_is_admin = validation_info.get("logged_in_user_is_admin", False)
   return service.get_projects(logged_in_user_id,
                                 logged_in_user_is_superadmin,
                                 logged_in_user_is_admin,
                                 account_id,
                                 parent_project_id,
                                 project_owner_email,
                                 name,
                                 db,
                                 type,
                                 view)

@project_router.get("/{project_id}/users", status_code=status.HTTP_200_OK, responses={
   status.HTTP_200_OK: {
      "description": "Successfully retrieved project users list",
      "content": {
         "application/json": {
            "examples": load_schema('projects/get_project_user_list/ok_examples.json')
         }
      },
   },
   status.HTTP_401_UNAUTHORIZED: {
      "description": "invalid, expired or no access token",
      "content": {
         "application/json": {
            "examples": load_schema('common/unauthorized_examples.json')
         }
      },
   },
   status.HTTP_403_FORBIDDEN: {
      "description": "User does not have permission to read project user list",
      "content": {
         "application/json": {
            "examples": load_schema('projects/get_project_user_list/forbidden_examples.json')
         }
      },
   },
   status.HTTP_404_NOT_FOUND: {
      "description": "project or account not found",
      "content": {
         "application/json": {
            "examples": load_schema('projects/get_project_user_list/notfound_examples.json')
         }
      },
   },
   status.HTTP_422_UNPROCESSABLE_ENTITY: {
      "description": "Payload validation error",
      "content": {
         "application/json": {
            "examples": load_schema('projects/get_project_user_list/validationerror_examples.json')
            }
         },
   },
   status.HTTP_503_SERVICE_UNAVAILABLE: {
      "description": "The server is currently unable to handle the request due to a temporary overloading or maintenance of the server",
      "content": {
         "application/json": {
            "examples": load_schema('common/serviceunavailable_examples.json')
         }
      }
   }
})
async def get_project_user_list(
   validation_info: dict[str, Any] = Depends(validate_get_project_user_list), # Needs to return validation_info: dict[str, Any] containing whatever service needs like account_id 
   project_id: UUID = Path(..., description="Project id under which users are queried"), # when not provided, its only valid for admins and superadmins. 
   firstname: Optional[str] = Query(None, description="Filter users by first name"),
   lastname: Optional[str] = Query(None, description="Filter users by last name"),
   email: Optional[str] = Query(None, description="Filter users by email")
) -> List[user_schemas.ProjectUserListItemDTO]:
   account_id: UUID = validation_info.get("account_id", None)
   db: Session = validation_info.get("db", None)
   return service.get_project_user_list(db, project_id, account_id, firstname, lastname, email)
   
# @project_router.post("/{project_id}/users/self", status_code=status.HTTP_200_OK, responses={
#    status.HTTP_200_OK: {
#       "description": "successfully assigned self to project",
#       "content": {
#          "application/json": {
#             "examples": load_schema('projects/assign_self_to_project/ok_examples.json')
#          }
#       }
#    },
#    status.HTTP_401_UNAUTHORIZED: {
#       "description": "invalid, expired or no access token",
#       "content": {
#          "application/json": {
#             "examples": load_schema('common/unauthorized_examples.json')
#          }
#       },
#    },
#    status.HTTP_403_FORBIDDEN: {
#       "description": "user does not have superadmin/admin privileges to assign self to project",
#       "content": {
#          "application/json": {
#             "examples": load_schema('projects/assign_self_to_project/forbidden_examples.json')
#          }
#       },
#    },
#    status.HTTP_404_NOT_FOUND: {
#       "description": "Project not found",
#       "content": {
#          "application/json": {
#             "examples": load_schema('projects/assign_self_to_project/notfound_examples.json')
#          }
#       },
#    },
#    status.HTTP_409_CONFLICT: {
#       "description": "User is already assigned to project",
#       "content": {
#          "application/json": {
#             "examples": load_schema('projects/assign_self_to_project/conflict_examples.json')
#          }
#       },
#    },
#    status.HTTP_422_UNPROCESSABLE_ENTITY: {
#       "description": "Payload validation error",
#       "content": {
#          "application/json": {
#             "examples": load_schema('projects/assign_self_to_project/validationerror_examples.json')
#          }
#       },
#    },
#    status.HTTP_503_SERVICE_UNAVAILABLE: {
#       "description": "The server is currently unable to handle the request due to a temporary overloading or maintenance of the server",
#       "content": {
#          "application/json": {
#             "examples": load_schema('common/serviceunavailable_examples.json')
#          }
#       },
#    }
# })
# async def assign_self_to_project(
#    project_id: UUID = Path(..., description = "Project ID to deassign self from"),
#    validation_info: dict[str, Any] = Depends(validate_assign_self_to_project)
# ) -> JSONResponse:
#       logged_in_user_id : UUID = validation_info.get("logged_in_user_id", None)
#       db: Session = validation_info.get("db", None)
#       project_exists: bool = validation_info.get("project_exists", None)
      
#       return service.assign_self_to_project(logged_in_user_id,
#                                              project_exists,
#                                              project_id,
#                                              db)

@project_router.delete("/{project_id}/users/self", status_code=status.HTTP_200_OK, responses={
   status.HTTP_200_OK: {
      "description": "successfully deassigned self from project",
      "content": {
         "application/json": {
            "examples": load_schema('projects/deassign_self_from_project/ok_examples.json')
         }
      }
   },
   status.HTTP_401_UNAUTHORIZED: {
      "description": "invalid, expired or no access token",
      "content": {
         "application/json": {
            "examples": load_schema('common/unauthorized_examples.json')
         }
      },
   },
   status.HTTP_403_FORBIDDEN: {
      "description": "user is not assigned to project",
      "content": {
         "application/json": {
            "examples": load_schema('projects/deassign_self_from_project/forbidden_examples.json')
         }
      },
   },
   status.HTTP_404_NOT_FOUND: {
      "description": "Project not found",
      "content": {
         "application/json": {
            "examples": load_schema('projects/deassign_self_from_project/notfound_examples.json')
         }
      },
   },
   status.HTTP_422_UNPROCESSABLE_ENTITY: {
      "description": "Payload validation error",
      "content": {
         "application/json": {
            "examples": load_schema('projects/deassign_self_from_project/validationerror_examples.json')
         }
      },
   },
   status.HTTP_503_SERVICE_UNAVAILABLE: {
      "description": "The server is currently unable to handle the request due to a temporary overloading or maintenance of the server",
      "content": {
         "application/json": {
            "examples": load_schema('common/serviceunavailable_examples.json')
         }
      },
   }
})
async def deassign_self_from_project(
   project_id: UUID = Path(..., description = "Project ID to deassign self from"),
   validation_info: dict[str, Any] = Depends(validate_deassign_self_from_project)
) -> JSONResponse:
      db: Session = validation_info.get("db", None)
      logged_in_user_id: UUID = validation_info.get("logged_in_user_id", None)
      return service.deassign_self_from_project(db =db, 
                                                project_id=project_id,
                                                logged_in_user_id=logged_in_user_id,
                                                )

@project_router.post("/{project_id}/users", status_code=status.HTTP_200_OK, responses={
   status.HTTP_200_OK: {
      "description": "Users successfully assigned to project",
      "content": {
         "application/json": {
            "examples": load_schema('projects/assign_or_deassign_users_in_project/ok_examples.json')
         }
      }
   },
   status.HTTP_401_UNAUTHORIZED: {
      "description": "invalid, expired or no access token",
      "content": {
         "application/json": {
            "examples": load_schema('common/unauthorized_examples.json')
         }
      },
   },
   status.HTTP_403_FORBIDDEN: {
      "description": "User does not have permissions to this resource",
      "content": {
         "application/json": {
            "examples": load_schema('projects/assign_or_deassign_users_in_project/forbidden_examples.json')
         }
      },
   },
   status.HTTP_404_NOT_FOUND: {
      "description": "Resource not found",
      "content": {
         "application/json": {
            "examples": load_schema('projects/assign_or_deassign_users_in_project/notfound_examples.json')
         }
      },
   },
   status.HTTP_409_CONFLICT: {
      "description": "User-Project association already exists",
      "content": {
         "application/json": {
            "examples": load_schema('projects/assign_or_deassign_users_in_project/conflict_examples.json')
         }
      },
   },
   status.HTTP_422_UNPROCESSABLE_ENTITY: {
      "description": "Payload validation error",
      "content": {
         "application/json": {
            "examples": load_schema('projects/assign_or_deassign_users_in_project/validationerror_examples.json')
         }
      },
   },
   status.HTTP_503_SERVICE_UNAVAILABLE: {
      "description": "The server is currently unable to handle the request due to a temporary overloading or maintenance of the server",
      "content": {
         "application/json": {
            "examples": load_schema('common/serviceunavailable_examples.json')
         }
      },
   }
})
async def assign_or_deassign_users_in_project(
   user_list_dto: user_schemas.UserListDTO = Body(description = "payload containing user_id's to assign/deassign to/from project"),
   validation_info: dict[str, Any] = Depends(validate_assign_or_deassign_users_in_project)
) -> JSONResponse:
      project : models.Project = validation_info.get("project", None)
      logged_in_user_id: UUID = validation_info.get("logged_in_user_id", None)
      logged_in_user_is_superadmin: bool = validation_info.get("logged_in_user_is_superadmin", False)
      logged_in_user_is_admin: bool = validation_info.get("logged_in_user_is_admin", False)
      db: Session = validation_info.get("db", None)
      return service.assign_or_deassign_users_in_project(user_list_dto,
                                                         db,
                                                         project,
                                                         logged_in_user_id,
                                                         logged_in_user_is_superadmin,
                                                         logged_in_user_is_admin)
   

# @project_router.patch("/{project_id}/status", status_code=status.HTTP_200_OK, responses={
#    status.HTTP_200_OK: {
#       "description": "Successfully enabled/disabled the project",
#       "content": {
#          "application/json": {
#             "examples": {
#                "enable_success": {
#                   "summary": "Project enabled",
#                   "value": {
#                      "message": "Successfully enabled project"
#                   },
#                },
#                "disable_success": {
#                   "summary": "Project disabled",
#                   "value": {
#                         "message": "Successfully disabled project"
#                   },
#                }
#             }
#          }
#       },
#    },
#    status.HTTP_401_UNAUTHORIZED: {
#       "description": "No access token or invalid access token"
#    },
#    status.HTTP_403_FORBIDDEN: {
#       "description": "User does not have permissions to perform this action"
#    },
#    status.HTTP_404_NOT_FOUND: {
#       "description": "Not found - Resource not found"
#    },
#    status.HTTP_422_UNPROCESSABLE_ENTITY: {
#       "description": "Payload validation error"
#    },
#    status.HTTP_503_SERVICE_UNAVAILABLE: {
#       "description": "The server is currently unable to handle the request due to a server-side error, temporary overloading, or maintenance of the server"
#    }
# })
# async def update_project_status(
#    project_id: UUID = Path(..., description="The ID of the project"),
#    project_status_update_dto: ResourceStatusUpdateDTO = Body(...),
#    db: Session = Depends(get_db),
#    _= Depends(validate_patch_project_status)  
# )-> JSONResponse:
#    return service.patch_project_status(project_id, project_status_update_dto, db)
   
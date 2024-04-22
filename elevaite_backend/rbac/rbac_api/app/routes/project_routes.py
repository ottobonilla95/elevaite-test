from fastapi import APIRouter, Path, Body, status, Depends, Query, Header
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import List, Optional, Any
from uuid import UUID
from pydantic import EmailStr

from elevaitedb.schemas import (
     project_schemas,
     user_schemas,
)
from elevaitedb.db import models
from rbac_api import validators

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
   project_id: Optional[UUID] = Header(None, alias = "X-elevAIte-ProjectId", description="The ID of the parent project to post under"),
   account_id: UUID = Header(..., alias = "X-elevAIte-AccountId", description="account_id in which project is posted"),
   validation_info: dict[str, Any]= Depends(validators.validate_post_project_factory(models.Project, ("CREATE",)))
) -> project_schemas.ProjectResponseDTO:
   db: Session = validation_info.get("db", None)
   logged_in_user = validation_info.get("logged_in_user", None)
   
   return service.create_project(
         account_id=account_id,
         parent_project_id=project_id,
         project_creation_payload=project_creation_payload,
         db=db,
         logged_in_user_id = logged_in_user.id,
         logged_in_user_email=logged_in_user.email
         )
   
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
   validation_info: dict[str, Any] = Depends(validators.validate_patch_project_factory(models.Project, ("READ",)))
   ) -> project_schemas.ProjectResponseDTO: 
      project_to_patch: models.Project = validation_info.get("Project", None)
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
      "description": "logged-in user is not assigned to account",
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
   validation_info: dict[str, Any] = Depends(validators.validate_get_project_factory(models.Project, ("READ",))) 
   ) -> project_schemas.ProjectResponseDTO: 
      project: models.Project = validation_info.get("Project", None)
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
   validation_info: dict[str,Any] = Depends(validators.validate_get_projects_factory(models.Project, ("READ",))),
   view: Optional[project_schemas.ProjectView] = Query(None, description = "View mode, either - 'Flat' or 'Hierarchical'; default value is 'Flat'. When set to 'Flat', parent_project_id will not be considered"),
   type: Optional[project_schemas.ProjectType] = Query(None, description = "Optional filter for querying projects based on ownership, either - 'My_Projects' or 'Shared_With_Me'; if not provided then this will assume both types (all projects for superadmin/account-admins)"),
   project_creator_email: Optional[str] = Query(None, description = "Optional filter for querying projects based on project_creator_email"),
   name: Optional[str] = Query(None, description = "Optional filter for querying projects based on project name"),
) -> List[project_schemas.ProjectResponseDTO]:
   """
    Retrieves a list of projects based on the provided criteria.

    Parameters:
    - account_id (UUID): Mandatory. The ID of the account to filter projects by.
    - project_id (UUID, optional): The parent project under which projects are queried.
    - view (Literal["Flat", Hierarchical], optional): Optional. When view is set to 'Hierarchical', immediate children projects corresponding to parent project id from header will be displayed (null value for project_id header represents top-level projects in account). When view is set to 'Flat', parent_project_id value from header is ignored and all user associated projects in account are displayed.
    - type (Literal["My_Projects", "Shared_With_Me", "All"], optional): Optional. Determines the type of projects to return. Can be 'My_Projects' for projects created by the logged-in user, or 'shared_with_me' for projects that the logged-in user has access to but did not create. When omitted, behavior defaults to returning 'All' projects accessible to the user; superadmins/admins can see all projects in account when 'All' is selected

    Returns:
    - A list of projects or subprojects matching the specified criteria. The structure of the returned projects is defined by the application model.
   """
   db: Session = validation_info.get("db", None)
   logged_in_user = validation_info.get("logged_in_user", None)
   logged_in_user_account_association = validation_info.get("logged_in_user_account_association", None)
   parent_project = validation_info.get("logged_in_user_project_association", None)
   account = validation_info.get("Account", None)
   
   return service.get_projects(logged_in_user_id=logged_in_user.id,
                                 logged_in_user_is_superadmin=logged_in_user.is_superadmin,
                                 logged_in_user_is_admin=logged_in_user_account_association.is_admin if logged_in_user_account_association else False,
                                 logged_in_user_email=logged_in_user.email,
                                 account_id=account.id,
                                 parent_project_id=parent_project.id if parent_project else None,
                                 project_creator_email=project_creator_email,
                                 name=name,
                                 db=db,
                                 type=type,
                                 view=view)

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
   validation_info: dict[str, Any] = Depends(validators.validate_get_project_user_list_factory(models.Project, ("READ",))),
   project_id: UUID = Path(..., description="Project id under which users are queried"),  
   account_id: UUID = Header(..., alias = "X-elevAIte-AccountId", description="account_id under which project users are queried"),
   firstname: Optional[str] = Query(None, description="Filter users by first name"),
   lastname: Optional[str] = Query(None, description="Filter users by last name"),
   email: Optional[str] = Query(None, description="Filter users by email")
) -> List[user_schemas.ProjectUserListItemDTO]:
   db: Session = validation_info.get("db", None)
   return service.get_project_user_list(
            db=db,
            project_id=project_id,
            account_id=account_id,
            firstname=firstname,
            lastname=lastname,
            email=email)

@project_router.delete("/{project_id}/users/{user_id}", status_code=status.HTTP_200_OK, responses={
   status.HTTP_200_OK: {
      "description": "successfully deassigned user from project",
      "content": {
         "application/json": {
            "examples": load_schema('projects/deassign_user_from_project/ok_examples.json')
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
            "examples": load_schema('projects/deassign_user_from_project/forbidden_examples.json')
         }
      },
   },
   status.HTTP_404_NOT_FOUND: {
      "description": "Project not found",
      "content": {
         "application/json": {
            "examples": load_schema('projects/deassign_user_from_project/notfound_examples.json')
         }
      },
   },
   status.HTTP_422_UNPROCESSABLE_ENTITY: {
      "description": "Payload validation error",
      "content": {
         "application/json": {
            "examples": load_schema('projects/deassign_user_from_project/validationerror_examples.json')
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
async def deassign_user_from_project(
   user_id: UUID = Path(..., description = "The ID of the user to deassign from project"),
   validation_info: dict[str, Any] = Depends(validators.validate_deassign_user_from_project_factory(models.Project, ("READ",)))
) -> JSONResponse:
      db: Session = validation_info.get("db", None)
      project = validation_info.get("Project", None)
      return service.deassign_user_from_project(user_id=user_id, db=db, project=project)

@project_router.post("/{project_id}/users", status_code=status.HTTP_200_OK, responses={
   status.HTTP_200_OK: {
      "description": "Users successfully assigned to project",
      "content": {
         "application/json": {
            "examples": load_schema('projects/assign_users_to_project/ok_examples.json')
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
            "examples": load_schema('projects/assign_users_to_project/forbidden_examples.json')
         }
      },
   },
   status.HTTP_404_NOT_FOUND: {
      "description": "Resource not found",
      "content": {
         "application/json": {
            "examples": load_schema('projects/assign_users_to_project/notfound_examples.json')
         }
      },
   },
   status.HTTP_409_CONFLICT: {
      "description": "User-Project association already exists",
      "content": {
         "application/json": {
            "examples": load_schema('projects/assign_users_to_project/conflict_examples.json')
         }
      },
   },
   status.HTTP_422_UNPROCESSABLE_ENTITY: {
      "description": "Payload validation error",
      "content": {
         "application/json": {
            "examples": load_schema('projects/assign_users_to_project/validationerror_examples.json')
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
async def assign_users_to_project(
   user_list_dto: user_schemas.UserListDTO = Body(description = "payload containing user_id's to assign to project"),
   validation_info: dict[str, Any] = Depends(validators.validate_assign_users_to_project_factory(models.Project, ("READ",)))
) -> JSONResponse:
      project : models.Project = validation_info.get("Project", None)
      db: Session = validation_info.get("db", None)
      return service.assign_users_to_project(user_list_dto,db,project)

@project_router.patch("/{project_id}/users/{user_id}/admin", status_code=status.HTTP_200_OK, responses={
   status.HTTP_200_OK: {
      "description": "Successfully patched the project admin status for user",
      "content": {
         "application/json": {
            "examples": load_schema('projects/patch_user_project_admin_status/ok_examples.json')
         }
      }
   },
   status.HTTP_401_UNAUTHORIZED: {
     "description": "Invalid, expired or no access token",
     "content": {
         "application/json": {
            "examples": load_schema('common/unauthorized_examples.json')
         }
      }
   },
   status.HTTP_403_FORBIDDEN: {
      "description": "User does not have permissions to this resource",
      "content": {
         "application/json": {
            "examples": load_schema('projects/patch_user_project_admin_status/forbidden_examples.json')
         }
      }
   },
   status.HTTP_404_NOT_FOUND: {
      "description": "Not found - account_id/user_id/project_id not found",
      "content": {
         "application/json": {
            "examples": load_schema('projects/patch_user_project_admin_status/notfound_examples.json')
         }
      }
   },
   status.HTTP_422_UNPROCESSABLE_ENTITY: {
      "description": "Payload validation error",
      "content": {
         "application/json": {
            "examples": load_schema('projects/patch_user_project_admin_status/validationerror_examples.json')
         }
      }
   },
   status.HTTP_503_SERVICE_UNAVAILABLE: {
      "description": "The server is currently unable to handle the request due to a server-side error, temporary overloading, or maintenance of the server",
      "content": {
         "application/json": {
            "examples": load_schema('common/serviceunavailable_examples.json')
         }
      }
   }
})
async def patch_user_project_admin_status(
   account_id: UUID = Header(..., alias = "X-elevAIte-AccountId", description="The ID of the account"),
   project_id: UUID = Path(..., description = "The ID of the project"),
   user_id: UUID = Path(..., description="ID of user"),
   project_admin_status_update_dto: project_schemas.ProjectAdminStatusUpdateDTO = Body(...),
   validation_info:dict[str, Any] = Depends(validators.validate_update_user_project_admin_status_factory(models.Project, ("READ",)))  
) -> JSONResponse:
   db: Session = validation_info.get("db", None)
   return service.patch_user_project_admin_status(user_id=user_id,
                                                   project_id=project_id,
                                                   account_id=account_id,
                                                   project_admin_status_update_dto=project_admin_status_update_dto,
                                                   db=db)


   
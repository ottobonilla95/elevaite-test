from fastapi import APIRouter, Path, Body, status, Depends, Query, Header
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import List, Optional, Any
from uuid import UUID
from pydantic import EmailStr

from elevaitedb.schemas import (
   project as project_schemas,
   user as user_schemas,
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
   """
   Create a Project resource

   Parameters:
      - Authorization Header (Bearer Token): Mandatory. Google access token containing user profile and email scope.
      - account_id (UUID) : Mandatory. id of account in which project is to be created
      - project_id( UUID) : Optional. id of parent project under which project is to be created
      - project_creation_payload : payload containing project creation details
      
   Returns: 
      - ProjectResponseDTO : Project response object 
   
   Notes:
      - When 'X-elevAIte-ProjectId' is not provided, the created project is a top level project in the account with parent_project_id = null
      - Creating a project makes the creator a project admin for that project
      - superadmin users can create projects in any account and under any parent project
      - users who are only account-admins can create projects under their admin accounts under any parent project
      - users who are only project-admins can create projects under their admin projects, if they are also associated to all projects in the parent project hierarchy of the admin project - 'X-elevAIte-ProjectId'(inclusive of 'X-elevAIte-ProjectId') - to be able to create a project under 'X-elevAIte-ProjectId'
      - Users who are not superadmin and not account-admin and not project-admin must have Project - 'READ' and 'CREATE' permission in any of their account-scoped roles under the account where project is created, (with no project permission overrides denying Project - 'READ' and 'CREATE' in case action performed inside a parent project) to create a project
      - Users who are not superadmin and not account-admin and not project-admin, who have the necessary permissions to create a project, must also be associated to all projects in the parent project hierarchy of 'X-elevAIte-ProjectId' (inclusive of 'X-elevAIte-ProjectId') to be able to create a project under 'X-elevAIte-ProjectId'
   """
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
   """
   Patch a Project resource

   Parameters:
      - Authorization Header (Bearer Token): Mandatory. Google access token containing user profile and email scope.
      - project_id( UUID) : Path variable. id of project to patch
      - project_patch_payload : payload containing project patch details; atleast 1 field must be provided
      
   Returns: 
      - ProjectResponseDTO : Patched Project response object 
   
   Notes:
      - Authorized for use only for superadmin/account-admin/project-admin users 
      - superadmin users can patch any project
      - users who are only account-admins can patch any project in their admin accounts
      - users who are only project-admins must also have Project - 'READ' permissions in any of their account-scoped roles under the account containing the project, and must be be associated to all projects in the parent project hierarchy of the admin project (inclusive of admin project) to be patched in order to patch the project
   """
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
   """
   Retrieve a Project resource

   Parameters:
      - Authorization Header (Bearer Token): Mandatory. Google access token containing user profile and email scope.
      - project_id( UUID) : Path variable. id of project to retrieve
      
   Returns: 
      - ProjectResponseDTO : Retrieved Project response object 
   
   Notes:
      - superadmin users can retrieve any project
      - users who are only account-admins can retrieve any project under their admin accounts
      - users who are not superadmin and not account-admin must have Project - 'READ' permissions in any of their account-scoped roles under the account where project is to be retrieved, and must be be associated to all projects in the parent project hierarchy of the project to be retrieved (invlusive of project to be retrieved) in order to retrieve the project
   """
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
    Retrieves a list of Project resources based on the provided criteria.

    Parameters:
      - X-elevAIte-AccountId (UUID): Mandatory. The ID of the account to filter projects by.
      - X-elevAIte-ProjectId (UUID, optional): The parent project under which projects are queried.
      - view (Literal["Flat", Hierarchical], optional): Optional. When view is set to 'Hierarchical', immediate children projects corresponding to parent project id from header will be displayed (null value for project_id header represents top-level projects in account). When view is set to 'Flat', parent_project_id value from header is ignored and all user associated projects in account are displayed.
      - type (Literal["My_Projects", "Shared_With_Me", "All"], optional): Optional. Determines the type of projects to return. Can be 'My_Projects' for projects created by the logged-in user, or 'Shared_With_Me' for projects that the logged-in user has access to but did not create. When omitted, behavior defaults to returning 'All' projects accessible to the user; superadmins/admins can see all projects in account when 'All' is selected

    Returns:
      - List[ProjectResponseDTO] - A list of Project resources matching the specified criteria

    Notes:
      - superadmin users can retrieve projects in any account under any parent project
      - users who are only account-admins can retrieve projects in their admin accounts under any parent project 
      - users who are not superadmin and account admin 
      - users who are not superadmin and not account-admin must have Project - 'READ' permissions in any of their account-scoped roles under the account where projects are to be retrieved, and must be be associated to all projects in the parent project hierarchy of 'X-elevAIte-ProjectId' (inclusive of 'X-elevAIte-ProjectId') if provided, in order to retrieve projects under 'X-elevAIte-ProjectId'
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
   # account_id: UUID = Header(..., alias = "X-elevAIte-AccountId", description="account_id under which project users are queried"),
   firstname: Optional[str] = Query(None, description="Filter users by first name"),
   lastname: Optional[str] = Query(None, description="Filter users by last name"),
   email: Optional[str] = Query(None, description="Filter users by email")
) -> List[user_schemas.ProjectUserListItemDTO]:
   """
   Retrieve Project resource's user list

   Parameters:
      - Authorization Header (Bearer Token): Mandatory. Google access token containing user profile and email scope.
      - project_id (UUID) : Path variable. id of project under which users are queried
      - firstname (str): Optional filter query param for user firstname with case-insensitive pattern matching
      - lastname (str): Optional filter query param for user lastname with case-insensitive pattern matching
      - email (str): Optional filter query param for user email with case-insensitive pattern matching
      
   Returns: 
      - List[ProjectResponseDTO] : Retrieved Project user list response objects 
   
   Notes:
      - superadmin users can retrieve any project's user list regardless of project assignment
      - users who are only account-admins users can retrieve any project's user list under their admin accounts regardless of project assignment
      - users who are not superadmin and not account-admin must have Project - 'READ' permissions in any of their account-scoped roles under the account where project's user list is to be retrieved, and must be be associated to all projects in the parent project hierarchy of the project (inclusive of project) in order to retrieve the project's user list
      - Each list item displays User resource information along with account-admin, project-admin status and account-scoped roles
      - superadmin/account-admin users will always display an empty list for their account-scoped roles 
   """
   db: Session = validation_info.get("db", None)
   account: models.Account = validation_info.get('Account', None)
   return service.get_project_user_list(
            db=db,
            project_id=project_id,
            account_id=account.id,
            firstname=firstname,
            lastname=lastname,
            email=email
         )

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
   """
   Deassign User resource from Project resource

   Parameters:
      - Authorization Header (Bearer Token): Mandatory. Google access token containing user profile and email scope.
      - project_id (UUID) : Path variable. id of project from which user is to be deassigned
      - user_id (UUID): Path variable. id of user who is to be deassigned from project
      
   Returns: 
      - JSONResponse : 200 success message for successful user deassignment from project
   
   Notes:
      - superadmin users can deassign any user from any project
      - users who are only account-admins can deassign any user from any project within admin account
      - users who are only project-admins can deassign any user from admin project if they have Project - 'READ' permissions in any of their account-scoped roles under the account containing the project, and must be be associated to all projects in the parent project hierarchy of the project (inclusive of project) in order to deassign user from the project
      - users who are not superadmin and not account-admin and not project-admin can only deassign self from project if they have Project - 'READ' permissions in any of their account-scoped roles under the account containing the project, and must be be associated to all projects in the parent project hierarchy of the project (inclusive of project) in order to deassign self from the project
      - project deassignment results in deassociation from all subproject associations of the project as well for deassigned user
   """
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
   """
   Assign User resources to Project resource

   Parameters:
      - Authorization Header (Bearer Token): Mandatory. Google access token containing user profile and email scope.
      - project_id (UUID) : Path variable. id of project to which users are assigned
      - user_list_dto (UUID): List of user id's to assign to project
      
   Returns: 
      - JSONResponse : 200 success message for successful assignment of users to project
   
   Notes
      - Authorized for use by superadmin/account-admin/project-admin users
      - all of the users to be assigned must be associated to parent project of assigning project (if it exists)
      - superadmins can assign users to any project
      - users who are only account-admins can assign users to any project within admin accounts
      - users who are only project-admins can assign any user from account containing admin projects if they have Project - 'READ' permissions in any of their account-scoped roles under the account containing the project, and must be associated to all projects in the parent project hierarchy of the project (inclusive of project) in order to assign users to project
   """
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
   # account_id: UUID = Header(..., alias = "X-elevAIte-AccountId", description="The ID of the account"),
   project_id: UUID = Path(..., description = "The ID of the project"),
   user_id: UUID = Path(..., description="ID of user"),
   project_admin_status_update_dto: project_schemas.ProjectAdminStatusUpdateDTO = Body(...),
   validation_info:dict[str, Any] = Depends(validators.validate_update_user_project_admin_status_factory(models.Project, ("READ",)))  
) -> JSONResponse:
   """
   Patch project admin status of user

   Parameters:
      - Authorization Header (Bearer Token): Mandatory. Google access token containing user profile and email scope.
      - project_id (UUID) : Path variable. id of project in which user's admin status is modified
      - user_id (UUID) : ID of user to modify project admin status
      - project_admin_status_update_dto: req body containing action - 'Grant', 'Revoke' - to perform on user's project admin status
      
   Returns: 
      - JSONResponse : A JSON with 200 success message for the user project admin status update. 
   
   Notes:
      - only authorized for use by superadmin/account-admin/project-admin users
      - superadmin users can update project admin status of any user in any project
      - users who are only account-admins can update project admin status of any user in any project within admin accounts
      - users who are only project-admins can update project admin status of any user in admin projects if they have Project - 'READ' permissions in any of their account-scoped roles under the account containing the project, and must be associated to all projects in the parent project hierarchy of the project (inclusive of project) in order to modify user project admin status
   """
   db: Session = validation_info.get("db", None)
   account: models.Account = validation_info.get("Account", None)
   return service.patch_user_project_admin_status(user_id=user_id,
                                                   project_id=project_id,
                                                   account_id=account.id,
                                                   project_admin_status_update_dto=project_admin_status_update_dto,
                                                   db=db)


   
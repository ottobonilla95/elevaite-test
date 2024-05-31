from fastapi import APIRouter, Path, Body, status, Depends, Query, Header, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import List, Optional, Any
from uuid import UUID

from elevaitedb.schemas import (
   project as project_schemas,
   user as user_schemas,
   api as api_schemas,
)
from elevaitedb.db import models
from rbac_api import route_validator_map

from ..services import project as service
from .utils.helpers import load_schema
from ...audit import AuditorProvider
auditor = AuditorProvider.get_instance()
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
            "examples": load_schema(
               'common/unauthorized_accesstoken_examples.json'
            )
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
@auditor.audit(api_namespace=api_schemas.APINamespace.RBAC_API)
async def create_project(
   request: Request,
   project_creation_payload: project_schemas.ProjectCreationRequestDTO = Body(..., description="project creation payload"),
   project_id: Optional[UUID] = Header(None, alias = "X-elevAIte-ProjectId", description="The ID of the parent project to post under"),
   account_id: UUID = Header(..., alias = "X-elevAIte-AccountId", description="account_id in which project is posted"),
   validation_info: dict[str, Any]= Depends(route_validator_map[(api_schemas.APINamespace.RBAC_API, 'create_project')]),
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
      - Creating a project makes the creator a project admin for that project, with no project-permission overrides (empty object)
      - superadmin users can create projects in any account and under any parent project
      - users who are only account-admins can create projects under their admin accounts under any parent project
      - users who are not superadmins and not account admins can create projects if they have Project - 'READ' and 'CREATE' permission in any of their account-scoped roles under the account where project is created, and if 'X-elevAIte-ProjectId' is provided, users must also be assigned to all projects in the parent project hierarchy of - 'X-elevAIte-ProjectId' (inclusive of 'X-elevAIte-ProjectId'). If user is not a project-admin, user must also not have denied permissions on 'Project' - 'CREATE' in project permission overrides
   """
   db: Session = request.state.db
   authenticated_entity = validation_info.get("authenticated_entity", None)
   
   return service.create_project(
      request,
      account_id=account_id,
      parent_project_id=project_id,
      project_creation_payload=project_creation_payload,
      db=db,
      logged_in_user_id = authenticated_entity.id,
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
            "examples": load_schema('common/unauthorized_accesstoken_examples.json')
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
@auditor.audit(api_namespace=api_schemas.APINamespace.RBAC_API)
async def patch_project(
   request: Request,
   project_patch_payload: project_schemas.ProjectPatchRequestDTO = Body(...),
   validation_info: dict[str, Any] = Depends(route_validator_map[(api_schemas.APINamespace.RBAC_API, 'patch_project')]),
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
      - users who are only project-admins must also have Project - 'READ' permissions in any of their account-scoped roles under the account containing the project, and must be be assigned to all projects in the parent project hierarchy of the project to be patched (inclusive of project to be patched) to patch the project
   """
   project_to_patch: models.Project = validation_info.get("Project", None)
   db: Session = request.state.db
   return service.patch_project(request, project_to_patch, project_patch_payload, db)


@project_router.get("/{project_id}", status_code=status.HTTP_200_OK, responses={
   status.HTTP_200_OK: {
      "description": "Project successfully retrieved",
      "model": project_schemas.ProjectResponseDTO
   },
   status.HTTP_401_UNAUTHORIZED: {
      "description": "invalid, expired or no access token",
      "content": {
         "application/json": {
            "examples": load_schema('common/unauthorized_accesstoken_examples.json')
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
@auditor.audit(api_namespace=api_schemas.APINamespace.RBAC_API)
async def get_project( 
   request: Request,
   validation_info: dict[str, Any] = Depends(route_validator_map[(api_schemas.APINamespace.RBAC_API, 'get_project')]),
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
      - users who are not superadmin and not account-admin must have Project - 'READ' permissions in any of their account-scoped roles under the account where project is to be retrieved, and must be be assigned to all projects in the parent project hierarchy of the project to be retrieved (invlusive of project to be retrieved) in order to retrieve the project
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
            "examples": load_schema(
               'common/unauthorized_accesstoken_examples.json'
            )
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
@auditor.audit(api_namespace=api_schemas.APINamespace.RBAC_API)
async def get_projects(  
   request: Request,
   validation_info: dict[str,Any] = Depends(route_validator_map[(api_schemas.APINamespace.RBAC_API, 'get_projects')]),
   view: Optional[project_schemas.ProjectView] = Query(project_schemas.ProjectView.Flat, description = "View mode, either - 'Flat' or 'Hierarchical'; default value is 'Flat'. When set to 'Flat', parent_project_id will not be considered"),
   type: Optional[project_schemas.ProjectType] = Query(project_schemas.ProjectType.All, description = "Optional filter for querying projects based on ownership, either - 'My_Projects' or 'Shared_With_Me'; if not provided then this will assume both types (all projects for superadmin/account-admins)"),
   name: Optional[str] = Query(None, description = "Optional filter for querying projects based on project name"),
) -> List[project_schemas.ProjectResponseDTO]:
   """
    Retrieves a list of Project resources based on the provided criteria.

    Parameters:
      - X-elevAIte-AccountId (UUID): Mandatory. The ID of the account to filter projects by.
      - X-elevAIte-ProjectId (UUID, optional): The parent project under which projects are queried.
      - view (Literal["Flat", Hierarchical], optional): Optional. When view is set to 'Hierarchical', immediate children projects corresponding to parent project id from header will be displayed (null value for project_id header represents top-level projects in account). When view is set to 'Flat', parent_project_id value from header is ignored and all projects to which user is assigned in account are displayed.
      - type (Literal["My_Projects", "Shared_With_Me", "All"], optional): Optional. Determines the type of projects to return. Can be 'My_Projects' for projects created by the logged-in user, or 'Shared_With_Me' for projects that the logged-in user has access to but did not create. When omitted, behavior defaults to returning 'All' projects accessible to the user; superadmins/admins can see all projects in account when 'All' is selected

    Returns:
      - List[ProjectResponseDTO] - A list of Project resources matching the specified criteria

    Notes:
      - superadmin users can retrieve all projects in any account under any parent project regardless of assignment
      - users who are only account-admins can retrieve all projects in their admin accounts under any parent project regardless of assignment 
      - users who are not superadmin and not account-admin must have Project - 'READ' permissions in any of their account-scoped roles under the account where projects are to be retrieved, and if 'X-elevAIte-ProjectId' is provided, user must be be assigned to all projects in the parent project hierarchy of 'X-elevAIte-ProjectId' (inclusive of 'X-elevAIte-ProjectId')
   """
   db: Session = request.state.db
   logged_in_user = validation_info.get("authenticated_entity", None)
   logged_in_user_account_association = validation_info.get("logged_in_entity_account_association", None)
   parent_project = validation_info.get("logged_in_entity_project_association", None)
   account = validation_info.get("Account", None)
   
   return service.get_projects(request=request,
                              logged_in_user_id=logged_in_user.id,
                              logged_in_user_is_superadmin=logged_in_user.is_superadmin,
                              logged_in_user_is_admin=logged_in_user_account_association.is_admin if logged_in_user_account_association else False,
                              account_id=account.id,
                              parent_project_id=parent_project.id if parent_project else None,
                              name=name,
                              db=db,
                              type=type,
                              view=view
                              )


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
            "examples": load_schema(
               'common/unauthorized_accesstoken_examples.json'
            )
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
@auditor.audit(api_namespace=api_schemas.APINamespace.RBAC_API)
async def get_project_user_list(
   request: Request,
   validation_info: dict[str, Any] = Depends(route_validator_map[(api_schemas.APINamespace.RBAC_API, 'get_project_user_list')]),
   project_id: UUID = Path(..., description="Project id under which users are queried"),  
   firstname: Optional[str] = Query(None, description="Filter users by first name"),
   lastname: Optional[str] = Query(None, description="Filter users by last name"),
   email: Optional[str] = Query(None, description="Filter users by email"),
   child_project_id: UUID = Query(None, description="Optional param to filter project user's by their assignment to immediate child project"),
   assigned: Optional[bool] = Query(True, description="Optional query param denoting project assignment status to child project"),
) -> List[user_schemas.ProjectUserListItemDTO]:
   """
   Retrieve Project resource's user list

   Parameters:
      - Authorization Header (Bearer Token): Mandatory. Google access token containing user profile and email scope.
      - project_id (UUID) : Path variable. id of project under which users are queried
      - firstname (str): Optional filter query param for user firstname with case-insensitive pattern matching
      - lastname (str): Optional filter query param for user lastname with case-insensitive pattern matching
      - email (str): Optional filter query param for user email with case-insensitive pattern matching
      - child_project_id (UUID): Optional filter query param to filter project users by their assignment to child project - 'child_project_id' 
      - assigned (bool): Optional filter query param to denote project users' assignment status to child project - 'child_project_id'; when child_project_id not provided, this value is ignored. Defaults to True.

   Returns: 
      - List[ProjectResponseDTO] : Retrieved Project user list response objects 
   
   Notes:
      - child_project_id optional query parameter is only authorized for use by superadmins/account-admins and project-admins (corresponding to param child_project_id), and it must be associated to parent project - 'project_id'  
      - superadmin users can retrieve any project's user list regardless of project assignment
      - users who are only account-admins can retrieve any project's user list under their admin accounts regardless of project assignment
      - users who are not superadmin and not account-admin must have Project - 'READ' permissions in any of their account-scoped roles under the account where project's user list is to be retrieved, and must be be assigned to all projects in the parent project hierarchy of the project (inclusive of project) in order to retrieve the project's user list
      - Each list item displays User resource information along with account-admin, project-admin status and account-scoped roles
      - superadmin/account-admin users will always display an empty list for their account-scoped roles 
   """
   db: Session = request.state.db
   account: models.Account = validation_info.get('Account', None)
   return service.get_project_user_list(
            request=request,
            db=db,
            project_id=project_id,
            account_id=account.id,
            firstname=firstname,
            lastname=lastname,
            email=email,
            child_project_id=child_project_id,
            assigned=assigned
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
            "examples": load_schema('common/unauthorized_accesstoken_examples.json')
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
@auditor.audit(api_namespace=api_schemas.APINamespace.RBAC_API)
async def deassign_user_from_project(
   request: Request,
   user_id: UUID = Path(..., description = "The ID of the user to deassign from project"),
   validation_info: dict[str, Any] = Depends(route_validator_map[(api_schemas.APINamespace.RBAC_API, 'deassign_user_from_project')]),
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
      - users who are only project-admins can deassign any user from the project if the project-admin user has Project - 'READ' permissions in any of their account-scoped roles under the account containing the project, and must be be assigned to all projects in the parent project hierarchy of the project (inclusive of project) in order to deassign user from the project
      - users who are not superadmin and not account-admin and not project-admin can only deassign self from project if they have Project - 'READ' permissions in any of their account-scoped roles under the account containing the project, and must be be assigned to all projects in the parent project hierarchy of the project (inclusive of project) in order to deassign self from the project
      - project deassignment results in deassignment from all subproject assignments within the project as well for deassigned user
   """
   db: Session = request.state.db
   project = validation_info.get("Project", None)
   return service.deassign_user_from_project(request=request, user_id=user_id, db=db, project=project)

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
            "examples": load_schema('common/unauthorized_accesstoken_examples.json')
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
@auditor.audit(api_namespace=api_schemas.APINamespace.RBAC_API)
async def assign_users_to_project(
   request: Request,
   project_assignee_list_dto: project_schemas.ProjectAssigneeListDTO = Body(description = "payload containing project assignees along with optional project permission overrides (default = no project permission overrides)"),
   validation_info: dict[str, Any] = Depends(route_validator_map[(api_schemas.APINamespace.RBAC_API, 'assign_users_to_project')]),
) -> JSONResponse:
   """
   Assign User resources to Project resource

   Parameters:
      - Authorization Header (Bearer Token): Mandatory. Google access token containing user profile and email scope.
      - project_id (UUID) : Path variable. id of project to which users are assigned
      - project_assignee_list_dto (UUID): List of user id's along with their optional project permission overrides to assign to project
      
   Returns: 
      - JSONResponse : 200 success message for successful assignment of users to project
   
   Notes
      - Authorized for use only by superadmin/account-admin/project-admin users
      - all of the users to be assigned must be assigned to parent project of assigning project (if it exists)
      - superadmins can assign users to any project
      - users who are only account-admins can assign users to any project within admin accounts
      - users who are only project-admins can assign any user from account containing the project if the project-admin user has Project - 'READ' permissions in any of their account-scoped roles under the account containing the project, and project-admin user must be assigned to all projects in the parent project hierarchy of the project (inclusive of project)
   """
   project : models.Project = validation_info.get("Project", None)
   db: Session = request.state.db
   return service.assign_users_to_project(request, project_assignee_list_dto,db,project)


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
            "examples": load_schema('common/unauthorized_accesstoken_examples.json')
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
@auditor.audit(api_namespace=api_schemas.APINamespace.RBAC_API)
async def patch_user_project_admin_status(
   request: Request,
   project_id: UUID = Path(..., description = "The ID of the project"),
   user_id: UUID = Path(..., description="ID of user"),
   project_admin_status_update_dto: project_schemas.ProjectAdminStatusUpdateDTO = Body(...),
   validation_info:dict[str, Any] = Depends(route_validator_map[(api_schemas.APINamespace.RBAC_API, 'patch_user_project_admin_status')]),
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
      - users who are only project-admins can update project admin status of any user in the project if the project-admin user has Project - 'READ' permissions in any of their account-scoped roles under the account containing the project, and must be assigned to all projects in the parent project hierarchy of the project (inclusive of project)
   """
   db: Session = request.state.db
   account: models.Account = validation_info.get("Account", None)
   return service.patch_user_project_admin_status(request=request,
                                                  user_id=user_id,
                                                   project_id=project_id,
                                                   account_id=account.id,
                                                   project_admin_status_update_dto=project_admin_status_update_dto,
                                                   db=db)


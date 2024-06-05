from fastapi import APIRouter, Path, Body, status, Depends, Query, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import List, Optional, Any
from uuid import UUID

from elevaitedb.schemas import (
   account as account_schemas,
   user as user_schemas,
   api as api_schemas,
)
from elevaitedb.db import models 
from rbac_api import (
   route_validator_map
)
from ..services import account as service
from .utils.helpers import load_schema
from ...audit import AuditorProvider
auditor = AuditorProvider.get_instance()

account_router = APIRouter(prefix="/accounts", tags=["accounts"]) 

@account_router.post("/", status_code=status.HTTP_201_CREATED, responses={
   status.HTTP_201_CREATED: {
      "description": "Account successfully created",
      "model" : account_schemas.AccountResponseDTO
   },
   status.HTTP_401_UNAUTHORIZED: {
      "description": "Invalid, expired or no access token",
      "content": {
         "application/json": {
            "examples": load_schema("common/unauthorized_accesstoken_examples.json")
         }
      },
   },
   status.HTTP_403_FORBIDDEN: {
      "description": "User does not have superadmin privileges to create accounts",
      "content": {
         "application/json": {
            "examples": load_schema('accounts/post_account/forbidden_examples.json')
         }
      },
   },
   status.HTTP_404_NOT_FOUND: {
      "description": "Not found - The org with the specified ID was not found",
      "content": {
         "application/json": {
            "examples": load_schema('accounts/post_account/notfound_examples.json')
         }
      },
   },
   status.HTTP_409_CONFLICT: {
      "description": "Conflict - An account with same name already exists in organization",
      "content": {
         "application/json": {
            "examples": load_schema('accounts/post_account/conflict_examples.json')
         }
      },
   },
   status.HTTP_422_UNPROCESSABLE_ENTITY: {
      "description": "Payload validation error",
      "content": {
         "application/json": {
            "examples": load_schema('accounts/post_account/validationerror_examples.json')
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
async def create_account(
   request: Request,
   account_creation_payload: account_schemas.AccountCreationRequestDTO = Body(..., description = "account creation request payload"),
   validation_info: dict[str, Any] = Depends(route_validator_map[(api_schemas.APINamespace.RBAC_API, 'create_account')]),
) -> account_schemas.AccountResponseDTO: 
   """
   Create an Account resource based on given body param.

   Parameters:
      - account_creation_payload (AccountCreationRequestDTO): The payload containing details of 'organization_id', 'name' and optionally 'description' for account creation
      - Authorization Header (Bearer Token): Mandatory. Google access token containing user profile and email scope.

   Returns: 
      - AccountResponseDTO : The response containing created AccountResponseDTO object. 
   
   Notes:
      - only authorized for use by superadmin users. 
      - creating an account assigns the creator to the account
   """
   logged_in_user: models.User = validation_info.get( "authenticated_entity", None)
   db: Session = request.state.db
   return service.create_account(request,account_creation_payload, db, logged_in_user.id)
  
   
@account_router.patch("/{account_id}", responses={
   status.HTTP_200_OK: {
      "description": "Account successfully patched",
      "content": {
         "application/json": {
            "examples": load_schema("accounts/patch_account/ok_examples.json")
         }
      },
   },
   status.HTTP_401_UNAUTHORIZED: {
      "description": "Invalid, expired or no access token",
      "content": {
         "application/json": {
            "examples": load_schema("common/unauthorized_accesstoken_examples.json")
         }
      },
   },
   status.HTTP_403_FORBIDDEN: {
      "description": "User does not have permission to patch account",
      "content": {
         "application/json": {
            "examples": load_schema('accounts/patch_account/forbidden_examples.json')
         }
      },
   },
   status.HTTP_404_NOT_FOUND: {
      "description": "Not found - The account with the specified ID was not found",
      "content": {
         "application/json": {
            "examples": load_schema('accounts/patch_account/notfound_examples.json')
         }
      },
   },
   status.HTTP_409_CONFLICT: {
      "description": "Account with same name already exists",
      "content": {
         "application/json": {
            "examples": load_schema('accounts/patch_account/conflict_examples.json')
            }
         },
   },
   status.HTTP_422_UNPROCESSABLE_ENTITY: {
      "description": "Payload validation error",
      "content": {
         "application/json": {
            "examples": load_schema('accounts/patch_account/validationerror_examples.json')
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
async def patch_account(
   request: Request,
   account_patch_req_payload: account_schemas.AccountPatchRequestDTO = Body(...),
   validation_info: dict[str, Any] = Depends(route_validator_map[(api_schemas.APINamespace.RBAC_API, 'patch_account')]) ,
) -> account_schemas.AccountResponseDTO: 
   """
   Patch an Account resource based on given body param.

   Parameters:
      - account_patch_req_payload (AccountPatchRequestDTO): The payload containing account patch details; atleast 1 field from 'name', 'description' must be provided
      - Authorization Header (Bearer Token): Mandatory. Google access token containing user profile and email scope.

   Returns: 
     - AccountResponseDTO : The response containing patched AccountResponseDTO object. 
   
   Notes:
      - only authorized for use by superadmin/account-admin users. 
   """
   account_to_patch: models.Account = validation_info.get("Account", None)
   db: Session = request.state.db
   return service.patch_account(request, account_to_patch, account_patch_req_payload, db)
   
@account_router.get("/", responses={
   status.HTTP_200_OK: {
      "description": "Successfully retrieved list of accounts",
      "content": {
         "application/json": {
            "examples": load_schema('accounts/get_accounts/ok_examples.json')
         }
      },
   },
   status.HTTP_401_UNAUTHORIZED: {
      "description": "Invalid, expired or no access token",
      "content": {
         "application/json": {
            "examples": load_schema('common/unauthorized_accesstoken_examples.json')
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
async def get_accounts(
   request: Request,
   validation_info: dict[str, Any] = Depends(route_validator_map[(api_schemas.APINamespace.RBAC_API, 'get_accounts')]), 
   name: Optional[str] = Query(None, description="Filter accounts by account name"),
) -> List[account_schemas.AccountResponseDTO]:
   """
   Retrieve Account resources accessible by user.

   Parameters:
      - Authorization Header (Bearer Token): Mandatory. Google access token containing user profile and email scope.
      - name (query param): case-insensitive pattern match for account name

   Returns: 
      - List[AccountResponseDTO] : The response containing list of accounts that are accessible by user. 
   
   Notes:
      - superadmin users can retrieve all organization accounts regardless of assignment. 
      - non-superadmin users can only retrieve accounts to which they are assigned. 
   """
   logged_in_user: models.User  = validation_info.get( "authenticated_entity", None)
   db: Session = request.state.db
   return service.get_accounts(request, logged_in_user.id,logged_in_user.is_superadmin, name, db)

@account_router.get("/{account_id}", responses={
   status.HTTP_200_OK: {
      "description": "Successfully retrieved account by id",
      "model": account_schemas.AccountResponseDTO
   },
   status.HTTP_401_UNAUTHORIZED: {
      "description": "Invalid, expired or no access token",
      "content": {
         "application/json": {
            "examples": load_schema('common/unauthorized_accesstoken_examples.json')
         }
      },
   },
   status.HTTP_403_FORBIDDEN: {
      "description": "User does not have privileges to read account in unassigned organization/account",
      "content": {
         "application/json": {
            "examples": load_schema('accounts/get_account/forbidden_examples.json')
         }
      },
   },
   status.HTTP_404_NOT_FOUND: {
      "description": "Not found - The org/account with the specified ID was not found",
      "content": {
         "application/json": {
            "examples": load_schema('accounts/get_account/notfound_examples.json')
         }
      },
   },
   status.HTTP_422_UNPROCESSABLE_ENTITY: {
      "description": "Payload validation error",
      "content": {
         "application/json": {
            "examples": load_schema('accounts/get_account/validationerror_examples.json')
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
async def get_account( 
   request: Request,
   validation_info: dict[str, Any] = Depends(route_validator_map[(api_schemas.APINamespace.RBAC_API, 'get_account')]),
) -> account_schemas.AccountResponseDTO:
   """
   Retrieve Account resource

   Parameters:
      - Authorization Header (Bearer Token): Mandatory. Google access token containing user profile and email scope.
      - account_id (UUID) : Path variable. id of account to be queried
   
   Returns: 
      - AccountResponseDTO : The response containing AccountResponseDTO object specified by account_id. 
   
   Notes:
      - superadmin users can retrieve any organization account regardless of assignment
      - non-superadmin users can only retrieve the account if assigned to account
   """
   account: models.Account = validation_info.get("Account", None)
   return account

@account_router.get("/{account_id}/users", response_model=List[user_schemas.AccountUserListItemDTO], status_code=status.HTTP_200_OK, responses={
   status.HTTP_200_OK: {
      "description": "Successfully retrieved account user list",
      "content": {
         "application/json": {
            "examples": load_schema('accounts/get_account_user_list/ok_examples.json')
         }
      },
   },
   status.HTTP_401_UNAUTHORIZED: {
      "description": "Invalid, expired or no access token",
      "content": {
         "application/json": {
            "examples": load_schema('common/unauthorized_accesstoken_examples.json')
         }
      },
   },
   status.HTTP_403_FORBIDDEN: {
      "description": "User does not have permission to get account profile",
      "content": {
         "application/json": {
            "examples": load_schema('accounts/get_account_user_list/forbidden_examples.json')
         }
      },
   },
   status.HTTP_404_NOT_FOUND: {
      "description": "Account not found",
      "content": {
         "application/json": {
            "examples": load_schema('accounts/get_account_user_list/notfound_examples.json')
         }
      },
   },
   status.HTTP_422_UNPROCESSABLE_ENTITY: {
      "description": "Payload validation error",
      "content": {
         "application/json": {
            "examples": load_schema('accounts/get_account_user_list/validationerror_examples.json')
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
async def get_account_user_list(
   request: Request,
   validation_info: dict[str, Any] = Depends(route_validator_map[(api_schemas.APINamespace.RBAC_API, 'get_account_user_list')]),
   account_id: UUID = Path(..., description="Account id under which users are queried"),  
   firstname: Optional[str] = Query(None, description="Filter users by first name"),
   lastname: Optional[str] = Query(None, description="Filter users by last name"),
   email: Optional[str] = Query(None, description="Filter users by email"),
   project_id: Optional[UUID] = Query(None, description="Optional query param to filter account user's by their assignment to account-level project"),
   assigned: Optional[bool] = Query(True, description="Optional query param denoting project assignment status to account-level project"),
) -> List[user_schemas.AccountUserListItemDTO]:
   """
   Retrieve Account resource's user list

   Parameters:
      - Authorization Header (Bearer Token): Mandatory. Google access token containing user profile and email scope.
      - account_id (UUID) : Path variable. id of account under which users are queried
      - firstname (str): Optional filter query param for user firstname with case-insensitive pattern matching
      - lastname (str): Optional filter query param for user lastname with case-insensitive pattern matching
      - email (str): Optional filter query param for user email with case-insensitive pattern matching
      - project_id (UUID): Optional filter query param to filter account users by their assignment to account-level project - 'project_id' 
      - assigned (bool): Optional filter query param to denote account users' assignment status to account-level project - 'project_id'; when project_id not provided, this value is ignored. Defaults to True.

   Returns: 
      - List[AccountUserListItemDTO] : The response containing AccountUserListItemDTO objects under account specified by account_id. 

   Notes:
      - project_id optional query parameter is only authorized for use by superadmins/account-admins and project-admins (corresponding to param project_id), and it must be associated to account with null parent_project_id 
      - superadmin users can retrieve any account user list regardless of account assignment
      - non-superadmin users can only retrieve the account user list if assigned to account
      - Each list item displays User resource information along with account-admin status and account-scoped roles
      - superadmin/account-admin users will always display an empty list for their account-scoped roles 
   """
   db: Session = request.state.db
   return service.get_account_user_list(request, db,account_id, firstname, lastname, email, project_id, assigned)
   

@account_router.post("/{account_id}/users", status_code=status.HTTP_200_OK, responses={
   status.HTTP_200_OK: {
      "description": "Users successfully assigned to account",
      "content": {
         "application/json": {
            "examples": load_schema('accounts/assign_users_to_account/ok_examples.json')
            }
         },
   },
   status.HTTP_401_UNAUTHORIZED: {
      "description": "Invalid, expired or no access token",
      "content": {
         "application/json": {
            "examples": load_schema('common/unauthorized_accesstoken_examples.json')
         }
      },
   },
   status.HTTP_403_FORBIDDEN: {
      "description": "User does not have permissions to assign users in list",
      "content": {
         "application/json": {
            "examples": load_schema('accounts/assign_users_to_account/forbidden_examples.json')
         }
      },
   },
   status.HTTP_404_NOT_FOUND: {
      "description": "Not found - account or user resources not found",
      "content": {
         "application/json": {
            "examples": load_schema('accounts/assign_users_to_account/notfound_examples.json')
         }
      },
   },
   status.HTTP_409_CONFLICT: {
        "description": "User-Account association already exists when trying to assign users to account",
        "content": {
         "application/json": {
            "examples": load_schema('accounts/assign_users_to_account/conflict_examples.json')
         }
      },
   },
   status.HTTP_422_UNPROCESSABLE_ENTITY: {
      "description": "Payload validation error",
      "content": {
         "application/json": {
            "examples": load_schema('accounts/assign_users_to_account/validationerror_examples.json')
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
async def assign_users_to_account(
   request: Request,
   account_id: UUID = Path(..., description="The ID of the account"),
   user_list_dto: user_schemas.UserListDTO = Body(description = "payload containing user_id's to assign to account"),
   validation_info: dict[str, Any] = Depends(route_validator_map[(api_schemas.APINamespace.RBAC_API, 'assign_users_to_account')]),
) -> JSONResponse:
   """
   Assign list of User resources to an Account resource

   Parameters:
      - Authorization Header (Bearer Token): Mandatory. Google access token containing user profile and email scope.
      - account_id (UUID) : Path variable. id of account to which users are assigned
      - user_list_dto  : List of user id's specifying users to assign to account
      
   Returns: 
      - JSONResponse : A JSON with 200 success message for the user list assignment to account. 
   
   Notes:
      - only authorized for use by superadmin/account-admin users
   """
   db: Session = request.state.db
   return service.assign_users_to_account(request, account_id, user_list_dto, db)

@account_router.delete("/{account_id}/users/{user_id}", status_code=status.HTTP_200_OK, responses={
   status.HTTP_200_OK: {
      "description": "user successfully deassigned from account",
      "content": {
         "application/json": {
            "examples": load_schema('accounts/deassign_user_from_account/ok_examples.json')
            }
         },
   },
   status.HTTP_401_UNAUTHORIZED: {
      "description": "Invalid, expired or no access token",
      "content": {
         "application/json": {
            "examples": load_schema('common/unauthorized_accesstoken_examples.json')
         }
      },
   },
   status.HTTP_403_FORBIDDEN: {
      "description": "User does not have permissions to deassign user",
      "content": {
         "application/json": {
            "examples": load_schema('accounts/deassign_user_from_account/forbidden_examples.json')
         }
      },
   },
   status.HTTP_404_NOT_FOUND: {
      "description": "Not found - account or user resource not found",
      "content": {
         "application/json": {
            "examples": load_schema('accounts/deassign_user_from_account/notfound_examples.json')
         }
      },
   },
   status.HTTP_422_UNPROCESSABLE_ENTITY: {
      "description": "Payload validation error",
      "content": {
         "application/json": {
            "examples": load_schema('accounts/deassign_user_from_account/validationerror_examples.json')
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
async def deassign_user_from_account(
   request: Request,
   account_id: UUID = Path(..., description="The ID of the account"),
   user_id:UUID = Path(..., description = "user id to deassign from account"),
   validation_info: dict[str, Any] = Depends(route_validator_map[(api_schemas.APINamespace.RBAC_API, 'deassign_user_from_account')]),
) -> JSONResponse:
   """
   Deassign User resource from Account resource

   Parameters:
      - Authorization Header (Bearer Token): Mandatory. Google access token containing user profile and email scope.
      - account_id (UUID) : Path variable. id of account from which user is to be deassigned
      - user_id (UUID) : ID of user to deassign
      
   Returns: 
      - JSONResponse : A JSON with 200 success message for the user deassignment from account. 
   
   Notes:
      - only authorized for use by superadmin/account-admin users
      - users who are only account-admins cannot deassign themselves from account
      - superadmin users can only be deassigned from account by root superadmin user or by themselves
      - deassignment from account also results in user getting deassigned from all assigned projects within that account
   """
   db: Session = request.state.db
   logged_in_user = validation_info.get('authenticated_entity', None)
   return service.deassign_user_from_account(request, account_id, user_id, logged_in_user, db)


   
@account_router.patch("/{account_id}/users/{user_id}/admin", status_code=status.HTTP_200_OK, responses={
   status.HTTP_200_OK: {
      "description": "Successfully patched the account admin status for user",
      "content": {
         "application/json": {
            "examples": load_schema('accounts/patch_user_account_admin_status/ok_examples.json')
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
            "examples": load_schema('accounts/patch_user_account_admin_status/forbidden_examples.json')
         }
      }
   },
   status.HTTP_404_NOT_FOUND: {
      "description": "Not found - user_id or account_id not found",
      "content": {
         "application/json": {
            "examples": load_schema('accounts/patch_user_account_admin_status/notfound_examples.json')
         }
      }
   },
   status.HTTP_422_UNPROCESSABLE_ENTITY: {
      "description": "Payload validation error",
      "content": {
         "application/json": {
            "examples": load_schema('accounts/patch_user_account_admin_status/validationerror_examples.json')
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
async def patch_user_account_admin_status(
   request: Request,
   account_id: UUID = Path(..., description="The ID of the account"),
   user_id: UUID = Path(..., description="ID of user"),
   account_admin_status_update_dto: account_schemas.AccountAdminStatusUpdateDTO = Body(...),
   validation_info:dict[str, Any] = Depends(route_validator_map[(api_schemas.APINamespace.RBAC_API, 'patch_user_account_admin_status')]),
) -> JSONResponse:
   """
   Patch User resources' account admin status

   Parameters:
      - Authorization Header (Bearer Token): Mandatory. Google access token containing user profile and email scope.
      - account_id (UUID) : Path variable. id of account in which user admin status is patched
      - user_id (UUID) : ID of user to modify account admin status
      - account_admin_status_update_dto: req body containing action - 'Grant', 'Revoke' - to perform on user's account admin status
      
   Returns: 
      - JSONResponse : A JSON with 200 success message for the user account admin status update. 
   
   Notes:
      - only authorized for use by superadmin/account-admin users
      - users who are only account-admins cannot modify account admin status of self
      - revoking account admin status of non-superadmin user also results in deassignment of the user from all of the account's projects where the user is not also assigned to all projects in the respective projects' parent project hierarchy up until the account's top level project (where parent_project_id is null) 
   """
   logged_in_user = validation_info.get("authenticated_entity", None)
   db: Session = request.state.db
   return service.patch_user_account_admin_status(request,
                                                   account_id,  
                                                   user_id,
                                                   logged_in_user.is_superadmin,
                                                   account_admin_status_update_dto,
                                                   db,
                                                   logged_in_user.id)

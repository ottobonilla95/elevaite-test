from fastapi import APIRouter, Path, Body, status, Depends, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import List, Optional, Any
from uuid import UUID

from elevaitedb.schemas import (
   account as account_schemas,
   user as user_schemas,
)
from elevaitedb.db import models 
from rbac_api import validators 
from ..services import account_service as service
from .utils.helpers import load_schema

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
            "examples": load_schema("common/unauthorized_examples.json")
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
async def create_account(
   account_creation_payload: account_schemas.AccountCreationRequestDTO = Body(..., description = "account creation request payload"),
   validation_info: dict[str, Any] = Depends(validators.validate_post_account) # Assuming the dependency function extracts the user ID from the access token, and performs all required validations.
   ) -> account_schemas.AccountResponseDTO: 
      logged_in_user: models.User = validation_info.get("logged_in_user", None)
      db: Session = validation_info.get("db", None)
      return service.create_account(account_creation_payload, db, logged_in_user.id)
  
   
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
            "examples": load_schema("common/unauthorized_examples.json")
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
async def patch_account(
   account_patch_req_payload: account_schemas.AccountPatchRequestDTO = Body(...),
   validation_info: dict[str, Any] = Depends(validators.validate_patch_account) # Assuming the dependency function extracts the user ID from the access token, and performs all required validations.
   ) -> account_schemas.AccountResponseDTO: 
      account_to_patch: models.Account = validation_info.get("Account", None)
      db: Session = validation_info.get("db", None)
      return service.patch_account(account_to_patch, account_patch_req_payload, db)
   
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
            "examples": load_schema('common/unauthorized_examples.json')
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
async def get_accounts(  
   validation_info: dict[str, Any] = Depends(validators.validate_get_accounts), 
   name: Optional[str] = Query(None, description="Filter accounts by account name"),
) -> List[account_schemas.AccountResponseDTO]:
      logged_in_user: models.User  = validation_info.get("logged_in_user", None)
      db: Session = validation_info.get("db", None)
      return service.get_accounts(logged_in_user.id,logged_in_user.is_superadmin, name, db)

@account_router.get("/{account_id}", responses={
   status.HTTP_200_OK: {
      "description": "Successfully retrieved account by id",
      "model": account_schemas.AccountResponseDTO
   },
   status.HTTP_401_UNAUTHORIZED: {
      "description": "Invalid, expired or no access token",
      "content": {
         "application/json": {
            "examples": load_schema('common/unauthorized_examples.json')
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
async def get_account( 
   validation_info: dict[str, Any] = Depends(validators.validate_get_account), 
) -> account_schemas.AccountResponseDTO:
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
            "examples": load_schema('common/unauthorized_examples.json')
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
async def get_account_user_list(
   validation_info: dict[str, Any] = Depends(validators.validate_get_account_user_list),
   account_id: UUID = Path(..., description="Account id under which users are queried"), # when not provided, its only valid for admins and superadmins. 
   firstname: Optional[str] = Query(None, description="Filter users by first name"),
   lastname: Optional[str] = Query(None, description="Filter users by last name"),
   email: Optional[str] = Query(None, description="Filter users by email")
) -> List[user_schemas.AccountUserListItemDTO]:
   db: Session = validation_info.get("db", None)
   return service.get_account_user_list(db,account_id, firstname, lastname, email)
   

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
            "examples": load_schema('common/unauthorized_examples.json')
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
async def assign_users_to_account(
   account_id: UUID = Path(..., description="The ID of the account"),
   user_list_dto: user_schemas.UserListDTO = Body(description = "payload containing user_id's to assign to account"),
   validation_info: dict[str, Any] = Depends(validators.validate_assign_users_to_account)
) -> JSONResponse:
   db: Session = validation_info.get("db", None)
   return service.assign_users_to_account(account_id, user_list_dto, db)

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
            "examples": load_schema('common/unauthorized_examples.json')
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
async def deassign_user_from_account(
   account_id: UUID = Path(..., description="The ID of the account"),
   user_id:UUID = Path(..., description = "user id to deassign from account"),
   validation_info: dict[str, Any] = Depends(validators.validate_deassign_user_from_account)
) -> JSONResponse:
   db: Session = validation_info.get("db", None)
   logged_in_user = validation_info.get('logged_in_user', None)
   return service.deassign_user_from_account(account_id, user_id, logged_in_user, db)


   
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
            "examples": load_schema('common/unauthorized_examples.json')
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
async def patch_user_account_admin_status(
   account_id: UUID = Path(..., description="The ID of the account"),
   user_id: UUID = Path(..., description="ID of user"),
   account_admin_status_update_dto: account_schemas.AccountAdminStatusUpdateDTO = Body(...),
   validation_info:dict[str, Any] = Depends(validators.validate_patch_account_admin_status)  
) -> JSONResponse:
   logged_in_user = validation_info.get("logged_in_user", None)
   db: Session = validation_info.get("db", None)
   return service.patch_user_account_admin_status(account_id,  
                                                  user_id,
                                                   logged_in_user.is_superadmin,
                                                   account_admin_status_update_dto,
                                                   db,
                                                   logged_in_user.id)

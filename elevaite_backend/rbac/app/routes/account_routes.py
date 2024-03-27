from fastapi import APIRouter, Path, Body, status, Depends, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import List, Optional, Any
from uuid import UUID
from .utils.helpers import load_schema

from elevaitedb.schemas.account_schemas import (
   AccountCreationRequestDTO,
   AccountResponseDTO,
   AccountPatchRequestDTO,
   AccountAdminStatusUpdateDTO
)

from elevaitedb.schemas.user_schemas import (
   UserListDTO,
   AccountUserListItemDTO,
   AccountUserProfileDTO
)
from elevaitedb.schemas.common_schemas import (
   ResourceStatusUpdateDTO
)
from elevaitedb.db.models import (
    User,
    Account,
    User_Account
)
from validators import (
   validate_post_account,
   validate_patch_account,
   validate_get_account,
   validate_get_accounts,
   validate_get_account_user_list_or_profile,
   validate_assign_or_deassign_users_in_account,
   validate_patch_account_admin_status,
   validate_patch_account_status
)

from app.services import account_service as service
account_router = APIRouter(prefix="/accounts", tags=["accounts"])

    
@account_router.post("/", status_code=status.HTTP_201_CREATED, responses={
   status.HTTP_201_CREATED: {
      "description": "Account successfully created",
      "model" : AccountResponseDTO
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
   account_creation_payload: AccountCreationRequestDTO = Body(..., description = "account creation request payload"),
   validation_info: dict[str, Any] = Depends(validate_post_account) # Assuming the dependency function extracts the user ID from the access token, and performs all required validations.
   ) -> AccountResponseDTO: 
      logged_in_user_id: UUID = validation_info.get("logged_in_user_id", None)
      db: Session = validation_info.get("db", None)
      return service.create_account(account_creation_payload, db, logged_in_user_id)
  
   
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
   account_patch_req_payload: AccountPatchRequestDTO = Body(...),
   validation_info: dict[str, Any] = Depends(validate_patch_account) # Assuming the dependency function extracts the user ID from the access token, and performs all required validations.
   ) -> AccountResponseDTO: 
      account_to_patch: Account = validation_info.get("account_to_patch", None)
      db: Session = validation_info.get("db", None)
      return service.patch_account(account_to_patch, account_patch_req_payload, db)
  
# no use case
# @account_router.get("/{account_id}", response_model=AccountResponseDTO, status_code=status.HTTP_200_OK, tags=["Account"], responses={
#    status.HTTP_401_UNAUTHORIZED: {"description": "No access token or invalid access token"},
#    status.HTTP_403_FORBIDDEN: {"description": "User does not have permissions to this resource"},
#    status.HTTP_404_NOT_FOUND: {"description": "Not found - The account with the specified ID was not found"},
#    status.HTTP_503_SERVICE_UNAVAILABLE: {"description": "The server is currently unable to handle the request due to a temporary overloading or maintenance of the server"}
# })
# async def get_account( # Need to add validation dependency for get_account in signature; not role-based, just User_Account check
#    account_id: UUID = Path(..., description="The ID of the account to retrieve"),
#    db: Session = Depends(get_db),
#    _= Depends(validate_get_account) # Assuming the dependency function extracts the user ID from the access token, and performs all required validations.
# ) -> AccountResponseDTO:
#    try:
#       db_account = db.query(Account).filter(Account.id == account_id).first()
#       if not db_account:
#          pprint(f'in GET /accounts/{account_id} - Account not found')
#          raise ApiError.notfound("Account not found")
#       return AccountResponseDTO.model_validate(db_account)
#       # return AccountResponseDTO.model_validate(db_account)
#    except SQLAlchemyError as e: # group db side error as 503 to not expose actual error to client
#       db.rollback()
#       pprint(f'Error in GET /accounts/{account_id} : {e}')
#       raise ApiError.serviceunavailable("The database is currently unavailable, please try again later.")
   
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
   status.HTTP_403_FORBIDDEN: {
      "description": "User does not have privileges to read accounts in unassigned organizations",
      "content": {
         "application/json": {
            "examples": load_schema('accounts/get_accounts/forbidden_examples.json')
         }
      },
   },
   status.HTTP_404_NOT_FOUND: {
      "description": "Not found - The org with the specified ID was not found",
      "content": {
         "application/json": {
            "examples": load_schema('accounts/get_accounts/notfound_examples.json')
         }
      },
   },
   status.HTTP_422_UNPROCESSABLE_ENTITY: {
      "description": "Payload validation error",
      "content": {
         "application/json": {
            "examples": load_schema('accounts/get_accounts/validationerror_examples.json')
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
   validation_info: dict[str, Any] = Depends(validate_get_accounts), 
   org_id: UUID = Query(description = "org_id under which accounts are queried"),
   name: Optional[str] = Query(None, description="Filter accounts by account name"),
) -> List[AccountResponseDTO]:
      logged_in_user_id: UUID  = validation_info.get("logged_in_user_id", None)
      logged_in_user_is_superadmin: bool = validation_info.get("logged_in_user_is_superadmin", False)
      db: Session = validation_info.get("db", None)
      return service.get_accounts(logged_in_user_id,logged_in_user_is_superadmin, org_id, name, db)

@account_router.get("/{account_id}", responses={
   status.HTTP_200_OK: {
      "description": "Successfully retrieved account by id",
      "model": AccountResponseDTO
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
   validation_info: dict[str, Any] = Depends(validate_get_account), 
) -> AccountResponseDTO:
      account: Account = validation_info.get("account", Account)
      return account

@account_router.get("/{account_id}/profile", status_code=status.HTTP_200_OK, responses={
    status.HTTP_200_OK: {
      "description": "Successfully retrieved account user profile",
      "content": {
         "application/json": {
            "examples": load_schema('accounts/get_account_user_profile/ok_examples.json')
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
      "description": "User does not have permissions to this resource",
      "content": {
         "application/json": {
            "examples": load_schema('accounts/get_account_user_profile/forbidden_examples.json')
         }
      },
   },
   status.HTTP_404_NOT_FOUND: {
      "description": "Account not found",
      "content": {
         "application/json": {
            "examples": load_schema('accounts/get_account_user_profile/notfound_examples.json')
         }
      },
   },
   status.HTTP_422_UNPROCESSABLE_ENTITY: {
      "description": "Payload validation error",
      "content": {
         "application/json": {
            "examples": load_schema('accounts/get_account_user_profile/validationerror_examples.json')
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
async def get_account_user_profile(
   account_id: UUID = Path(..., description="Account id under which user is queried"),
   validation_info: dict[str,Any] = Depends(validate_get_account_user_list_or_profile),
) -> AccountUserProfileDTO:
   logged_in_user: User = validation_info.get("logged_in_user", None)
   db: Session = validation_info.get("db", None)
   user_account_association: User_Account = validation_info.get("user_account_association", None)
   return service.get_account_user_profile(db,
                                          account_id,
                                          logged_in_user,
                                          user_account_association)

@account_router.get("/{account_id}/users", response_model=List[AccountUserListItemDTO], status_code=status.HTTP_200_OK, responses={
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
   validation_info: dict[str, Any] = Depends(validate_get_account_user_list_or_profile),
   account_id: UUID = Path(..., description="Account id under which users are queried"), # when not provided, its only valid for admins and superadmins. 
   firstname: Optional[str] = Query(None, description="Filter users by first name"),
   lastname: Optional[str] = Query(None, description="Filter users by last name"),
   email: Optional[str] = Query(None, description="Filter users by email")
) -> List[AccountUserListItemDTO]:
   db: Session = validation_info.get("db", None)
   return service.get_account_user_list(db,account_id, firstname, lastname, email)
   

@account_router.post("/{account_id}/users", status_code=status.HTTP_200_OK, responses={
   status.HTTP_200_OK: {
      "description": "Users successfully assigned/deassigned to/from account",
      "content": {
         "application/json": {
            "examples": load_schema('accounts/assign_or_deassign_users_in_account/ok_examples.json')
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
      "description": "User does not have permissions to assign/deassign users in list",
      "content": {
         "application/json": {
            "examples": load_schema('accounts/assign_or_deassign_users_in_account/forbidden_examples.json')
         }
      },
   },
   status.HTTP_404_NOT_FOUND: {
      "description": "Not found - account or user resources not found",
      "content": {
         "application/json": {
            "examples": load_schema('accounts/assign_or_deassign_users_in_account/notfound_examples.json')
         }
      },
   },
   status.HTTP_409_CONFLICT: {
        "description": "User-Account association already exists when trying to assign users to account",
        "content": {
         "application/json": {
            "examples": load_schema('accounts/assign_or_deassign_users_in_account/conflict_examples.json')
         }
      },
   },
   status.HTTP_422_UNPROCESSABLE_ENTITY: {
      "description": "Payload validation error",
      "content": {
         "application/json": {
            "examples": load_schema('accounts/assign_or_deassign_users_in_account/validationerror_examples.json')
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
async def assign_or_deassign_users_in_account(
   account_id: UUID = Path(..., description="The ID of the account"),
   user_list_dto: UserListDTO = Body(description = "payload containing user_id's to assign/deassign to/from account"),
   validation_info: dict[str, Any] = Depends(validate_assign_or_deassign_users_in_account)
) -> JSONResponse:
   logged_in_user_id: UUID = validation_info.get("logged_in_user_id", None)
   logged_in_user_is_superadmin: bool = validation_info.get("logged_in_user_is_superadmin", None)
   db: Session = validation_info.get("db", None)
   return service.assign_or_deassign_users_in_account(account_id,
                                                      user_list_dto,
                                                      db,
                                                      logged_in_user_id,
                                                      logged_in_user_is_superadmin)
   
@account_router.patch("/{account_id}/admin", status_code=status.HTTP_200_OK, responses={
   status.HTTP_200_OK: {
      "description": "Successfully patched the account admin status for user",
      "content": {
         "application/json": {
            "examples": load_schema('accounts/patch_account_user_admin_status/ok_examples.json')
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
            "examples": load_schema('accounts/patch_account_user_admin_status/forbidden_examples.json')
         }
      }
   },
   status.HTTP_404_NOT_FOUND: {
      "description": "Not found - user_id or account_id not found",
      "content": {
         "application/json": {
            "examples": load_schema('accounts/patch_account_user_admin_status/notfound_examples.json')
         }
      }
   },
   status.HTTP_409_CONFLICT: {
      "description": "user is already an admin of account",
      "content": {
         "application/json": {
            "examples": load_schema('accounts/patch_account_user_admin_status/conflict_examples.json')
         }
      }
   },
   status.HTTP_422_UNPROCESSABLE_ENTITY: {
      "description": "Payload validation error",
      "content": {
         "application/json": {
            "examples": load_schema('accounts/patch_account_user_admin_status/validationerror_examples.json')
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
async def patch_account_user_admin_status(
   account_id: UUID = Path(..., description="The ID of the account"),
   account_admin_status_update_dto: AccountAdminStatusUpdateDTO = Body(...),
   validation_info:dict[str, Any] = Depends(validate_patch_account_admin_status)  
) -> JSONResponse:
   logged_in_user_id = validation_info.get("logged_in_user_id", None)
   logged_in_user_is_superadmin = validation_info.get("logged_in_user_is_superadmin", False)
   db: Session = validation_info.get("db", None)
   # user_account_association: User_Account = validation_info.get("user_account_association", None)
   return service.patch_account_user_admin_status(account_id, 
                                                   logged_in_user_is_superadmin,
                                                   account_admin_status_update_dto,
                                                   db,
                                                   logged_in_user_id)

@account_router.patch("/{account_id}/status", status_code=status.HTTP_200_OK, responses={
   status.HTTP_200_OK: {
      "description": "Successfully enabled/disabled the account",
      "content": {
         "application/json": {
            "examples": load_schema('accounts/patch_account_status/ok_examples.json')
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
      "description": "User does not have permissions to this resource",
      "content": {
         "application/json": {
            "examples": load_schema('accounts/patch_account_status/forbidden_examples.json')
            }
         },
   },
   status.HTTP_404_NOT_FOUND: {
      "description": "Not found - account resource not found",
      "content": {
         "application/json": {
            "examples": load_schema('accounts/patch_account_status/notfound_examples.json')
            }
         },
   },
   status.HTTP_422_UNPROCESSABLE_ENTITY: {
      "description": "Payload validation error",
      "content": {
         "application/json": {
            "examples": load_schema('accounts/patch_account_status/validationerror_examples.json')
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
async def patch_account_status(
   account_disabled_status_update_dto: ResourceStatusUpdateDTO = Body(...),
   validation_info: dict[str, Any] = Depends(validate_patch_account_status)  
)-> JSONResponse:
   account: Account = validation_info.get("account", None)
   db: Session = validation_info.get("db", None)
   return service.patch_account_status(account, account_disabled_status_update_dto, db) 
  
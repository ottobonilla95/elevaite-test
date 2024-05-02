from fastapi import APIRouter, Body, Depends, Path, Header, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import Any, Optional
from uuid import UUID

from elevaitedb.schemas import (
   user as user_schemas,
   role as role_schemas
)
from elevaitedb.db import models
from rbac_api import validators

from ..services import user_service as service
from .utils.helpers import load_schema

user_router = APIRouter(prefix="/users", tags=["users"]) 

@user_router.patch("/{user_id}", status_code=status.HTTP_200_OK, responses={
   status.HTTP_200_OK: {
      "description": "Successfully patched user resource",
      "content": {
         "application/json": {
            "examples": load_schema('users/patch_user/ok_examples.json')
            }
         },
   },
   status.HTTP_401_UNAUTHORIZED: {
      "description": "No access token or invalid access token",
      "content": {
         "application/json": {
            "examples": load_schema('common/unauthorized_examples.json')
            }
         },
   },
   status.HTTP_403_FORBIDDEN: {
      "description": "User does not have superadmin/account-admin privileges to update other users",
      "content": {
         "application/json": {
            "examples": load_schema('users/patch_user/forbidden_examples.json')
         }
      },
   },
   status.HTTP_404_NOT_FOUND: {
      "description": "user not found",
      "content": {
         "application/json": {
            "examples": load_schema('users/patch_user/notfound_examples.json')
         }
      },
   },
   status.HTTP_422_UNPROCESSABLE_ENTITY: {
      "description": "Validation error",
      "content": {
         "application/json": {
            "examples": load_schema('users/patch_user/validationerror_examples.json')
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
async def patch_user(
   user_patch_payload: user_schemas.UserPatchRequestDTO = Body(description= "User patch payload"),
   validation_info: dict[str, Any] = Depends(validators.validate_patch_user)
) -> user_schemas.OrgUserListItemDTO:
   """
   Patch User resource

   Parameters:
      - Authorization Header (Bearer Token): Mandatory. Google access token containing user profile and email scope.
      - user_patch_payload (UUID) : payload containing atleast 1 of user firstname/lastname information for update

   Returns: 
      -OrgUserListItemDTO : Patched User resource response object
   
   Notes:
      - superadmin users can patch any user
      - non-superadmin users can only patch self
   """
   user_to_patch: models.User = validation_info.get("User", None)
   db: Session = validation_info.get("db", None)
   return service.patch_user(user_to_patch, user_patch_payload, db)

@user_router.get("/{user_id}/profile", status_code=status.HTTP_200_OK, responses={
   status.HTTP_200_OK: {
      "description": "Successfully retrieved user profile object",
      "content": {
         "application/json": {
            "examples": load_schema('users/get_user_profile/ok_examples.json')
            }
         },
   },
   status.HTTP_401_UNAUTHORIZED: {
      "description": "No access token or invalid access token",
      "content": {
         "application/json": {
            "examples": load_schema('common/unauthorized_examples.json')
            }
         },
   },
   status.HTTP_403_FORBIDDEN: {
      "description": "User does not have permissions to read user profile",
      "content": {
         "application/json": {
            "examples": load_schema('users/get_user_profile/forbidden_examples.json')
         }
      },
   },
   status.HTTP_404_NOT_FOUND: {
      "description": "user, account, or user in account not found",
      "content": {
         "application/json": {
            "examples": load_schema('users/get_user_profile/notfound_examples.json')
         }
      },
   },
   status.HTTP_422_UNPROCESSABLE_ENTITY: {
      "description": "Validation error",
      "content": {
         "application/json": {
            "examples": load_schema('users/get_user_profile/validationerror_examples.json')
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
async def get_user_profile(
   account_id: Optional[UUID] = Header(None, alias = "X-elevAIte-AccountId", description="optional account_id under which user profile is queried; required by non-superadmins"),
   validation_info: dict[str, Any] = Depends(validators.validate_get_user_profile),
) -> user_schemas.UserProfileDTO:
   """
   Retrieve User profile with mutual account membership information

   Parameters:
      - X-elevAIte-AccountId (UUID): The ID of the account in which user is being profiled; mandatory parameter for non-superadmin users
      - user_id (UUID): ID of user being profiled.

   Returns:
      - UserProfileDTO: User profile containing user information along with account membership information
   
   Notes:
      - superadmin users can see all account-memberships of user 
      - non-superadmin users can see only mutual account membership information
   """
   user_to_profile = validation_info.get("User", None)
   logged_in_user = validation_info.get("logged_in_user", None)
   db: Session = validation_info.get("db", None)
   return service.get_user_profile(user_to_profile, logged_in_user, account_id, db)
   
@user_router.patch("/{user_id}/accounts/{account_id}/roles", responses={
   status.HTTP_200_OK: {
      "description": "User roles successfully updated",
      "content": {
         "application/json": {
            "examples": load_schema('users/patch_user_account_roles/ok_examples.json')
         }
      }
   },
   status.HTTP_401_UNAUTHORIZED: {
      "description": "No access token or invalid access token",
      "content": {
         "application/json": {
            "examples": load_schema('common/unauthorized_examples.json')
            }
         },
   },
   status.HTTP_403_FORBIDDEN: {
      "description": "logged-in user does not have permissions to patch user account roles",
      "content": {
         "application/json": {
            "examples": load_schema('users/patch_user_account_roles/forbidden_examples.json')
         }
      },
   },
   status.HTTP_404_NOT_FOUND: {
      "description": "user,account or roles not found",
      "content": {
         "application/json": {
            "examples": load_schema('users/patch_user_account_roles/notfound_examples.json')
         }
      },
   },
   status.HTTP_422_UNPROCESSABLE_ENTITY: {
      "description": "Validation error",
      "content": {
         "application/json": {
            "examples": load_schema('users/patch_user_account_roles/validationerror_examples.json')
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
async def patch_user_account_roles(
   account_id: UUID = Path(..., description="The ID of the account to scope the user roles to"),
   role_list_dto: role_schemas.RoleListDTO = Body(description = "payload containing account-scoped role_id's and action to patch user"),
   validation_info:dict[str,Any] = Depends(validators.validate_patch_user_account_roles)
) -> JSONResponse:
   """
   Patch user's account scoped roles

   Parameters:
      - account_id (UUID): The ID of the account in which user's account scoped roles are being updated
      - role_list_dto: payload containing list of role_id's and action - 'Add' or 'Remove'

   Returns:
      - JSONResponse: 200 success message for successfull addition or removal of account-scoped roles for user
   
   Notes:
      - Authorized for use only by superadmin/account-admin users
      - cannot patch account-scoped roles of superadmin/account-admin users
   """
   db: Session = validation_info.get("db", None)
   user_to_patch: models.User = validation_info["User"]

   return service.patch_user_account_roles(user_to_patch=user_to_patch,
                                             account_id=account_id,
                                             db = db,
                                             role_list_dto= role_list_dto)

@user_router.put("/{user_id}/projects/{project_id}/permission-overrides", status_code=status.HTTP_200_OK, responses={
   status.HTTP_200_OK: {
      "description": "Project permission overrides successfully updated for user",
      "content": {
         "application/json": {
            "example": {"message": "Project permission overrides successfully updated for user"}
         }
      }
   },
   status.HTTP_401_UNAUTHORIZED: {
      "description": "No access token or invalid access token",
      "content": {
         "application/json": {
            "examples": load_schema('common/unauthorized_examples.json')
            }
         },
   },
   status.HTTP_403_FORBIDDEN: {
      "description": "logged-in user does not have permissions to read project permission overrides of user",
      "content": {
         "application/json": {
            "examples": load_schema('users/update_user_project_permission_overrides/forbidden_examples.json')
         }
      },
   },
   status.HTTP_404_NOT_FOUND: {
      "description": "project or account not found",
      "content": {
         "application/json": {
            "examples": load_schema('users/update_user_project_permission_overrides/notfound_examples.json')
         }
      },
   },
   status.HTTP_422_UNPROCESSABLE_ENTITY: {
      "description": "Validation error",
      "content": {
         "application/json": {
            "examples": load_schema('users/update_user_project_permission_overrides/validationerror_examples.json')
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
async def update_user_project_permission_overrides(
   user_id: UUID = Path(..., description="The ID of the user"),
   # account_id: UUID = Header(..., alias = "X-elevAIte-AccountId", description="The ID of the account that contains the project"),
   project_id: UUID = Path(..., description="The ID of the project"),
   permission_overrides_payload: role_schemas.ProjectScopedPermission = Body(...),
   validation_info: dict[str, Any] = Depends(validators.validate_update_project_permission_overrides_factory(models.Project, ("READ", )))
) -> JSONResponse:
   """
   Update user's project permission overrides 

   Parameters:
      - project_id (UUID): The ID of the project in which user's project permission overrides are being updated
      - user_id (UUID): The ID of the user whose project permission overrides are being updated
      - permission_overrides_payload: payload containing ProjectScopedPermission JSON with 'Allow' and 'Deny' values against resource actions 

   Returns:
      - JSONResponse: 200 success message for successful updation of user's project permission overrides
   
   Notes:
      - Authorized for use only by superadmin/account-admin/project-admin users
      - cannot patch project permission overrides for superadmin/account-admin/project-admin users
      - users who are only project-admins can patch project permission overrides for other regular users if they have Project - 'READ' permissions in any of their account-scoped roles under the account containing the project, and must be associated to all projects in the parent project hierarchy of the project (inclusive of project)
   """
   db: Session = validation_info.get("db", None)
   user_to_patch = validation_info.get("User", None)
   account = validation_info.get("Account", None)
   return service.update_user_project_permission_overrides(user_id, user_to_patch, account.id, project_id, permission_overrides_payload, db)

@user_router.get("/{user_id}/projects/{project_id}/permission-overrides", status_code=status.HTTP_200_OK, responses={
   status.HTTP_200_OK: {
      "description": "Project permission overrides successfully retrieved for user",
      "content": {
         "application/json": {
            "examples": load_schema('users/get_user_project_permission_overrides/ok_examples.json')
         }
      }
   },
   status.HTTP_401_UNAUTHORIZED: {
      "description": "No access token or invalid access token",
      "content": {
         "application/json": {
            "examples": load_schema('common/unauthorized_examples.json')
            }
         },
   },
   status.HTTP_403_FORBIDDEN: {
      "description": "User does not have permissions to read user profile",
      "content": {
         "application/json": {
            "examples": load_schema('users/get_user_project_permission_overrides/forbidden_examples.json')
         }
      },
   },
   status.HTTP_404_NOT_FOUND: {
      "description": "user, account, or user in account not found",
      "content": {
         "application/json": {
            "examples": load_schema('users/get_user_project_permission_overrides/notfound_examples.json')
         }
      },
   },
   status.HTTP_422_UNPROCESSABLE_ENTITY: {
      "description": "Validation error",
      "content": {
         "application/json": {
            "examples": load_schema('users/get_user_project_permission_overrides/validationerror_examples.json')
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
async def get_user_project_permission_overrides(
   user_id: UUID = Path(..., description="The ID of the user"),
   # account_id: UUID = Header(..., alias = "X-elevAIte-AccountId", description="The ID of the account that contains the project"),
   project_id: UUID = Path(..., description="The ID of the project"),
   validation_info: dict[str, Any] = Depends(validators.validate_get_project_permission_overrides_factory(models.Project, ("READ", )))
) -> role_schemas.ProjectScopedPermission:
   """
   Get user's project permission overrides 

   Parameters:
      - project_id (UUID): The ID of the project in which user's project permission overrides are being retrieved
      - user_id (UUID): The ID of the user whose project permission overrides are being retrieved
      
   Returns:
      - ProjectScopedPermission:  user's project permission overrides
   
   Notes:
      - Authorized for use only by superadmin/account-admin/project-admin users, or by regular users only for their own project permission overrides
      - cannot retrieve project permission overrides for superadmin/account-admin/project-admin users
      - users who are only project-admins can retrieve project permission overrides for other regular users if they have Project - 'READ' permissions in any of their account-scoped roles under the account containing the project, and must be associated to all projects in the parent project hierarchy of the project (inclusive of project)
   """
   db: Session = validation_info.get("db", None)
   user_to_patch = validation_info.get("User", None)
   account = validation_info.get("Account", None)
   user_project_association: models.User_Account = validation_info.get("user_project_association", None)
   return service.get_user_project_permission_overrides(user_to_patch, user_id, account.id, project_id, db, user_project_association)

@user_router.patch("/{user_id}/superadmin", status_code=status.HTTP_200_OK, responses={
   status.HTTP_200_OK: {
      "description": "Superadmin status successfully updated",
      "content": {
         "application/json": {
            "examples": load_schema('users/patch_user_superadmin_status/ok_examples.json')
         }
      }
   },
   status.HTTP_401_UNAUTHORIZED: {
      "description": "No access token or invalid access token",
      "content": {
         "application/json": {
            "examples": load_schema('common/unauthorized_examples.json')
            }
         },
   },
   status.HTTP_403_FORBIDDEN: {
      "description": "User does not have permissions to read user profile",
      "content": {
         "application/json": {
            "examples": load_schema('users/patch_user_superadmin_status/forbidden_examples.json')
         }
      },
   },
   status.HTTP_404_NOT_FOUND: {
      "description": "user, account, or user in account not found",
      "content": {
         "application/json": {
            "examples": load_schema('users/patch_user_superadmin_status/notfound_examples.json')
         }
      },
   },
   status.HTTP_422_UNPROCESSABLE_ENTITY: {
      "description": "Validation error",
      "content": {
         "application/json": {
            "examples": load_schema('users/patch_user_superadmin_status/validationerror_examples.json')
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
async def patch_user_superadmin_status(
   user_id: UUID = Path(..., description="The ID of the user"),
   superadmin_status_update_dto: user_schemas.SuperadminStatusUpdateDTO = Body(...),
   validation_info: dict[str, Any] = Depends(validators.validate_patch_user_superadmin_status)
) -> JSONResponse:
   """
   Update user's superadmin status

   Parameters:
      - user_id (UUID): The ID of the user whose project permission overrides are being updated
      - superadmin_status_update_dto: payload containing action with 'Grant' or 'Revoke' values for superadmin status update of user

   Returns:
      - JSONResponse: 200 success message for successful superadmin status update of user
   
   Notes:
      - Authorized for use only by superadmin users
      - Cannot modify superadmin status of self
      - Cannot modify superadmin status of root superadmin user
      - Revoking superadmin status will result in dissociation of user from all projects in non-admin accounts which are not connected to their respective account's top level projects through associations 
   """
   db: Session = validation_info.get("db", None)
   logged_in_user = validation_info.get("logged_in_user", None)
   return service.patch_user_superadmin_status(db=db,
                                                logged_in_user_id=logged_in_user.id,
                                                user_id=user_id,
                                                superadmin_status_update_dto=superadmin_status_update_dto
                                                )
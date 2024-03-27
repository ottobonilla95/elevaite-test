from fastapi import (
   APIRouter,
   Body,
   Query,
   Depends,
   Path,
   status
)
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import (
   List,
   Optional,
   Any
)
from uuid import UUID
from elevaitedb.schemas.user_schemas import (
   UserPatchRequestDTO,
   UserProfileDTO,
   OrgUserListItemDTO,
)
from elevaitedb.schemas.role_schemas import (
   RoleListDTO,
   ProjectScopedPermissions
)
from app.utils.deps import get_db
from validators import (
   validate_get_user_profile,
   # validate_get_org_users,
   validate_patch_user,
   validate_patch_user_account_roles,
   validate_get_project_permission_overrides,
   validate_update_project_permission_overrides,
)

from app.services import user_service as service
from .utils.helpers import load_schema
from elevaitedb.db.models import (
   User,
   Account,
   User_Account
)
user_router = APIRouter(prefix="/users", tags=["users"])

# this is an internal function that should be called on /login

# @user_router.post("/", response_model=UserResponseDTO, status_code=status.HTTP_201_CREATED, responses={
#    status.HTTP_401_UNAUTHORIZED: {
#       "description": "No access token or invalid access token"
#    },
#    status.HTTP_403_FORBIDDEN: {
#       "description": "User does not have permissions to this resource"
#    },
#    status.HTTP_409_CONFLICT: {
#       "description": "User already exists"
#    },
#    status.HTTP_422_UNPROCESSABLE_ENTITY:  {
#       "description": "Validation error"
#    },
#    status.HTTP_503_SERVICE_UNAVAILABLE: {
#       "description": "The server is currently unable to handle the request due to a temporary overloading or maintenance of the server"
#    }
# })
# async def create_user(
#     user: UserCreationRequestDTO = Body(description= "user creation payload"),
#     db: Session = Depends(get_db),
#     _=Depends(validate_post_user)
# ):
#    try:
#       existing_user = db.query(User).filter(User.email == user.email).first()
#       if existing_user: # Application-side uniqueness check : Check if a user with the same email already exists in the specified account
#          pprint(f'in POST /users - A user with the same email already exists in users table')
#          raise ApiError.conflict("A user with the same email already exists")
#       new_user = User(
#          firstname=user.firstname,
#          lastname=user.lastname,
#          email=user.email,
#          created_at=datetime.now(),
#          updated_at=datetime.now()
#       )
#       db.add(new_user)
#       db.commit()
#       db.refresh(new_user)
#       return new_user
#    except SQLAlchemyError as e:
#       db.rollback()
#       pprint(f'Error in POST /users/ : {e}')
#       raise ApiError.serviceunavailable("The database is currently unavailable, please try again later.")

# @user_router.get("/", response_model=List[OrgUserListItemDTO], status_code=status.HTTP_200_OK, responses={
#    status.HTTP_401_UNAUTHORIZED: {
#       "description": "No access token or invalid access token",
#       "content": {
#          "application/json": {
#             "examples": load_schema('common/unauthorized_examples.json')
#             }
#          },
#    },
#    status.HTTP_403_FORBIDDEN: {
#       "description": "User does not have permissions to this resource",
#       "content": {
#          "application/json": {
#             "examples": load_schema('users/get_org_users/forbidden_examples.json')
#          }
#       },
#    },
#    status.HTTP_404_NOT_FOUND: {
#       "description": "organization not found",
#       "content": {
#          "application/json": {
#             "examples": load_schema('users/get_org_users/notfound_examples.json')
#          }
#       },
#    },
#    status.HTTP_422_UNPROCESSABLE_ENTITY: {
#       "description": "Payload validation error",
#       "content": {
#          "application/json": {
#             "examples": load_schema('users/get_org_users/validationerror_examples.json')
#          }
#       },
#    },
#    status.HTTP_503_SERVICE_UNAVAILABLE: {
#       "description": "The server is currently unable to handle the request due to a server-side error, temporary overloading, or maintenance of the server",
#       "content": {
#          "application/json": {
#             "examples": load_schema('common/serviceunavailable_examples.json')
#          }
#       },
#    }
# })
# async def get_org_users(
#    org_id: UUID = Query(..., description = "id of org that user belongs to"),
#    validation_info: dict[str, Any] = Depends(validate_get_org_users),
#    firstname: Optional[str] = Query(None, description="Filter users by first name"),
#    lastname: Optional[str] = Query(None, description="Filter users by last name"),
#    email: Optional[str] = Query(None, description="Filter users by email")
# ) -> List[OrgUserListItemDTO]:
#    db: Session = validation_info.get("db", None)
#    return service.get_org_users(db, org_id, firstname, lastname, email)

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
      "description": "User does not have superadmin/admin privileges to update other users",
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
   user_patch_payload: UserPatchRequestDTO = Body(description= "User patch payload"),
   validation_info: dict[str, Any] = Depends(validate_patch_user)
) -> OrgUserListItemDTO:
   user_to_patch: User = validation_info.get("user_to_patch", None)
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
   validation_info: dict[str, Any] = Depends(validate_get_user_profile),
) -> UserProfileDTO:
   user_to_profile = validation_info.get("user_to_profile", None)
   logged_in_user = validation_info.get("logged_in_user", None)
   db: Session = validation_info.get("db", None)
   return service.get_user_profile(user_to_profile, logged_in_user, db)
   
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
   role_list_dto: RoleListDTO = Body(description = "payload containing account-scoped role_id's and action to patch user"),
   validation_info:dict[str,Any] = Depends(validate_patch_user_account_roles)
) -> JSONResponse:
   user_to_patch: User = validation_info.get("user_to_patch", None)
   account: Account = validation_info.get("account", None)
   user_to_patch_account_association: User_Account = validation_info.get("user_to_patch_account_association", None)
   db: Session = validation_info.get("db", None)

   return service.patch_user_account_roles(user_to_patch=user_to_patch,
                                             account=account,
                                             user_to_patch_account_association=user_to_patch_account_association,
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
   project_id: UUID = Path(..., description="The ID of the project"),
   permission_overrides_payload: ProjectScopedPermissions = Body(...),
   validation_info: dict[str, Any] = Depends(validate_update_project_permission_overrides)
) -> JSONResponse:
   db: Session = validation_info.get("db", None)
   user_project_association: User_Account = validation_info.get("user_project_association", None)
   return service.update_user_project_permission_overrides(user_id, project_id, permission_overrides_payload, db, user_project_association)

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
   project_id: UUID = Path(..., description="The ID of the project"),
   validation_info: dict[str, Any] = Depends(validate_get_project_permission_overrides)
) -> ProjectScopedPermissions:
   db: Session = validation_info.get("db", None)
   user_project_association: User_Account = validation_info.get("user_project_association", None)
   return service.get_user_project_permission_overrides(user_id, project_id, db, user_project_association)
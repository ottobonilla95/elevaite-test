from fastapi import APIRouter, Body, Depends, Path, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import List, Any
from uuid import UUID

from elevaitedb.schemas import (
   role as role_schemas,
)

from rbac_api import validators
from ..services import role_service as service
from .utils.helpers import load_schema

role_router = APIRouter(prefix="/roles", tags=["roles"]) 

@role_router.post("/", status_code=status.HTTP_201_CREATED, responses={
   status.HTTP_201_CREATED: {
      "description": "Newly created role object",
      "model" : role_schemas.RoleResponseDTO
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
      "description": "User does not have permissions to create roles",
      "content": {
         "application/json": {
            "examples": load_schema('roles/post_role/forbidden_examples.json')
         }
      },
   },
   status.HTTP_409_CONFLICT: {
      "description": "Role with same name already exists",
      "content": {
         "application/json": {
            "examples": load_schema('roles/post_role/conflict_examples.json')
            }
         },
   },
   status.HTTP_422_UNPROCESSABLE_ENTITY: {
      "description": "Payload validation error",
      "content": {
         "application/json": {
            "examples": load_schema('roles/post_role/validationerror_examples.json')
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
async def create_role(
   role_creation_dto: role_schemas.RoleCreationRequestDTO = Body(description= "role creation payload"),
   validation_info: dict[str, Any] = Depends(validators.validate_post_roles)
) -> role_schemas.RoleResponseDTO :
   """
   Create Role resource

   Parameters:
      - Authorization Header (Bearer Token): Mandatory. Google access token containing user profile and email scope.
      - role_creation_dto : req body containing role creation details
      
   Returns: 
      - RoleResponseDTO  : Role response object 
   
   Notes:
      - only authorized for use by superadmin users
      - role contains a JSONB permissions fields which has AccountScopedPermissions object
   """
   db: Session = validation_info.get("db", None)
   return service.create_role(role_creation_dto, db)

@role_router.get("/{role_id}", response_model=role_schemas.RoleResponseDTO, responses={
   status.HTTP_200_OK: {
      "description": "Retrieved role response object",
      "model" : role_schemas.RoleResponseDTO
   },
   status.HTTP_401_UNAUTHORIZED: {
      "description": "No access token or invalid access token",
      "content": {
         "application/json": {
            "examples": load_schema('common/unauthorized_examples.json')
            }
         },
   },
   status.HTTP_404_NOT_FOUND: {
      "description": "Role not found",
      "content": {
         "application/json": {
            "examples": load_schema('roles/get_role/notfound_examples.json')
         }
      },
   },
   status.HTTP_422_UNPROCESSABLE_ENTITY: {
      "description": "Payload validation error",
      "content": {
         "application/json": {
            "examples": load_schema('roles/get_role/validationerror_examples.json')
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
async def get_role(
   role_id: UUID = Path(..., description= "role ID to retrieve role object"),
   validation_info: dict[str, Any] = Depends(validators.validate_get_role)
) -> List[role_schemas.RoleResponseDTO]:
   """
   Retrieve Role resource

   Parameters:
      - Authorization Header (Bearer Token): Mandatory. Google access token containing user profile and email scope.
      - role_id (UUID) : id of role to retrieve
      
   Returns: 
      - RoleResponseDTO  : Role response object 
   
   Notes:
      - authorized for use by all authenticated users
   """
   db: Session = validation_info.get("db", None)
   return service.get_role(db = db, role_id = role_id)
   
@role_router.get("/", status_code = status.HTTP_200_OK, responses={
   status.HTTP_200_OK: {
      "description": "Retrieved role response objects",
      "content": {
         "application/json": {
            "examples": load_schema('roles/get_roles/ok_examples.json')
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
      "description": "User does not have permission to read all roles",
      "content": {
         "application/json": {
            "examples": load_schema('roles/get_roles/forbidden_examples.json')
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
async def get_roles(
   validation_info: dict[str, Any] = Depends(validators.validate_get_roles)
) -> List[role_schemas.RoleResponseDTO]:
   """
   Retrieve Role resources

   Parameters:
      - Authorization Header (Bearer Token): Mandatory. Google access token containing user profile and email scope.
      
   Returns: 
      - List[RoleResponseDTO]  : Role response objects 
   
   Notes:
      - Authorized for use only by superadmin and account-admin users (in atleast 1 account)
      - Usecase is to display role list from which superadmin/admin users can select roles to append to user's account-scoped roles
   """
   db: Session = validation_info.get("db", None)
   return service.get_roles(db)
   
@role_router.patch("/{role_id}", responses={
   status.HTTP_200_OK: {
      "description": "Successfully patched role object",
      "model": role_schemas.RoleResponseDTO 
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
      "description": "User does not have permission to patch role",
      "content": {
         "application/json": {
            "examples": load_schema('roles/patch_role/forbidden_examples.json')
         }
      },
   },
   status.HTTP_404_NOT_FOUND: {
      "description": "Role not found",
      "content": {
         "application/json": {
            "examples": load_schema('roles/patch_role/notfound_examples.json')
         }
      },
   },
   status.HTTP_422_UNPROCESSABLE_ENTITY: {
      "description": "Payload validation error",
      "content": {
         "application/json": {
            "examples": load_schema('roles/patch_role/validationerror_examples.json')
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
async def patch_role(
   role_id: UUID = Path(..., description="The ID of the role to update"),
   role_patch_req_payload: role_schemas.RoleUpdateRequestDTO = Body(description= "Role patch payload"),
   validation_info:dict[str, Any] = Depends(validators.validate_patch_roles)
) -> role_schemas.RoleResponseDTO:
   """
   Patch Role resource

   Parameters:
      - Authorization Header (Bearer Token): Mandatory. Google access token containing user profile and email scope.
      - role_id (UUID) : id of role to update
      - role_patch_req_payload: req body containing role patch details; must provide atleast 1 field

   Returns: 
      - RoleResponseDTO  : Patched Role response object 
   
   Notes:
      - Authorized for use only by superadmin users
   """
   db: Session = validation_info.get("db", None)
   return service.patch_role(role_id, role_patch_req_payload, db)

@role_router.delete("/{role_id}", responses={
   status.HTTP_200_OK: {
      "description": "Successfully deleted role",
      "content": {
         "application/json": {
            "example": {
               "message": "Successfully deleted role"
            }
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
      "description": "User does not have permission to patch role",
      "content": {
         "application/json": {
            "examples": load_schema('roles/delete_role/forbidden_examples.json')
         }
      },
   },
   status.HTTP_404_NOT_FOUND: {
      "description": "Role not found",
      "content": {
         "application/json": {
            "examples": load_schema('roles/delete_role/notfound_examples.json')
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
async def delete_role(
   validation_info:dict[str, Any] = Depends(validators.validate_delete_roles),
   role_id: UUID = Path(..., description="role id to delete", examples = ['11111111-1111-1111-1111-111111111111']) 
) -> JSONResponse:
   """
   Delete Role resource

   Parameters:
      - Authorization Header (Bearer Token): Mandatory. Google access token containing user profile and email scope.
      - role_id (UUID) : id of role to delete

   Returns: 
      - JSONResponse : 200 success message for successful role object deletion
   
   Notes:
      - Authorized for use only by superadmin users
   """
   db: Session = validation_info.get("db", None)
   return service.delete_role(db, role_id)


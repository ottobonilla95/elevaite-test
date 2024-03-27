from fastapi import APIRouter, Body, Depends, Path, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import List, Any
from uuid import UUID

from elevaitedb.schemas.role_schemas import (
   RoleResponseDTO,
   RoleCreationRequestDTO,
   RoleUpdateRequestDTO,
)

from validators import (
   validate_post_roles,
   validate_patch_roles,
   validate_delete_roles,
   validate_get_roles,
   validate_get_role
)
from app.services import role_service as service
from .utils.helpers import load_schema
role_router = APIRouter(prefix="/roles", tags=["roles"])

@role_router.post("/", status_code=status.HTTP_201_CREATED, responses={
   status.HTTP_201_CREATED: {
      "description": "Newly created role object",
      "model" : RoleResponseDTO
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
   role_creation_dto: RoleCreationRequestDTO = Body(description= "role creation payload"),
   validation_info: dict[str, Any] = Depends(validate_post_roles)
) -> RoleResponseDTO :
   db: Session = validation_info.get("db", None)
   return service.create_role(role_creation_dto, db)

@role_router.get("/{role_id}", response_model=RoleResponseDTO, responses={
   status.HTTP_200_OK: {
      "description": "Retrieved role response object",
      "model" : RoleResponseDTO
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
   validation_info: dict[str, Any] = Depends(validate_get_role)
) -> List[RoleResponseDTO]:
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
   validation_info: dict[str, Any] = Depends(validate_get_roles)
) -> List[RoleResponseDTO]:
   db: Session = validation_info.get("db", None)
   return service.get_roles(db)
   
@role_router.patch("/{role_id}", responses={
   status.HTTP_200_OK: {
      "description": "Successfully patched role object",
      "model": RoleResponseDTO 
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
   role_patch_req_payload: RoleUpdateRequestDTO = Body(description= "Role patch payload"),
   validation_info:dict[str, Any] = Depends(validate_patch_roles)
) -> RoleResponseDTO:
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
   validation_info:dict[str, Any] = Depends(validate_delete_roles),
   role_id: UUID = Path(..., description="role id to delete", examples = ['11111111-1111-1111-1111-111111111111']) 
) -> JSONResponse:
   db: Session = validation_info.get("db", None)
   return service.delete_role(db, role_id)


from fastapi import APIRouter, Body, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import Any

from elevaitedb.schemas import (
   user_schemas,
)
from rbac_api.validators import validate_post_user
from ..services import user_service as service
from .utils.helpers import load_schema

auth_router = APIRouter(prefix="/register", tags=["auth"])

@auth_router.post("/", responses={
   status.HTTP_201_CREATED: {
      "description": "New user successfully registered",
      "content": {
         "application/json": {
            "examples": load_schema('users/post_user/created_examples.json')
            }
         },
   },
   status.HTTP_200_OK: {
      "description": "Existing user returned",
      "content": {
         "application/json": {
            "examples": load_schema('users/post_user/ok_examples.json')
            }
         },
   },
   status.HTTP_401_UNAUTHORIZED: {
      "description": "No access token or invalid access token",
      "content": {
         "application/json": {
            "examples": load_schema('users/post_user/unauthorized_examples.json')
            }
         },
   },
   status.HTTP_403_FORBIDDEN: {
      "description": "User does not have permissions to this resource",
      "content": {
         "application/json": {
            "examples": load_schema('users/post_user/forbidden_examples.json')
         }
      },
   },
   status.HTTP_404_NOT_FOUND: {
      "description": "organization not found",
      "content": {
         "application/json": {
            "examples": load_schema('users/post_user/notfound_examples.json')
         }
      },
   },
   # status.HTTP_409_CONFLICT: {
   #    "description": "User with same email already exists in organization",
   #    "content": {
   #       "application/json": {
   #          "examples": load_schema('users/post_user/conflict_examples.json')
   #       }
   #    },
   # },
   status.HTTP_422_UNPROCESSABLE_ENTITY:  {
      "description": "Validation error",
      "content": {
         "application/json": {
            "examples": load_schema('users/post_user/validationerror_examples.json')
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
async def create_user(
   user_creation_payload: user_schemas.UserCreationRequestDTO = Body(description= "user creation payload"),
   validation_info: dict[str, Any] = Depends(validate_post_user)
) -> JSONResponse:
   db: Session = validation_info.get("db", None)
   return service.create_user(db, user_creation_payload)



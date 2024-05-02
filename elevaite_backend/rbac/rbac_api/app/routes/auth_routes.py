from fastapi import APIRouter, Header, Body, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import Any, Optional
from uuid import UUID

from elevaitedb.schemas import (
   auth as auth_schemas
)
from rbac_api import validators
from ..services import auth_service as service
from .utils.helpers import load_schema

auth_router = APIRouter(prefix="/auth", tags=["auth"]) 

@auth_router.post("/register", responses={
   status.HTTP_201_CREATED: {
      "description": "New user successfully registered",
      "content": {
         "application/json": {
            "examples": load_schema('auth/register/created_examples.json')
            }
         },
   },
   status.HTTP_200_OK: {
      "description": "Existing user returned",
      "content": {
         "application/json": {
            "examples": load_schema('auth/register/ok_examples.json')
            }
         },
   },
   status.HTTP_401_UNAUTHORIZED: {
      "description": "No access token or invalid access token",
      "content": {
         "application/json": {
            "examples": load_schema('auth/register/unauthorized_examples.json')
            }
         },
   },
   status.HTTP_403_FORBIDDEN: {
      "description": "User does not have permissions to this resource",
      "content": {
         "application/json": {
            "examples": load_schema('auth/register/forbidden_examples.json')
         }
      },
   },
   status.HTTP_404_NOT_FOUND: {
      "description": "organization not found",
      "content": {
         "application/json": {
            "examples": load_schema('auth/register/notfound_examples.json')
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
            "examples": load_schema('auth/register/validationerror_examples.json')
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
async def register_user(
   register_user_payload: auth_schemas.RegisterUserRequestDTO = Body(description= "user creation payload"),
   validation_info: dict[str, Any] = Depends(validators.validate_register_user)
) -> JSONResponse:
   """
   Register/Sign-in User resource to Organization resource 

   Parameters:
      - Authorization Header (Bearer Token): Mandatory. Google access token containing user profile and email scope.
      - register_user_payload : Contains mandatory params - 'org_id' and 'email' - as well as optional params - 'firstname' , 'lastname'
      
   Returns: 
      - JSONResponse : A JSON with 200 success message containing existing user in org corresponding to email 
      - JSONResponse : A JSON with 201 success message containing newly registered user in org corresponding to payload params provided
   
   Notes:
      - only authorized for users who provide email in payload identical to the email in access token passed in header 
   """

   db: Session = validation_info.get("db", None)
   return service.register_user(db=db, register_user_payload=register_user_payload)

@auth_router.post("/rbac-permissions", responses={
   status.HTTP_200_OK: {
      "description": "RBAC permissions successfully retrieved",
      "model": auth_schemas.PermissionsValidationResponse
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
      "description": "User does not have permissions to account or project resource",
      "content": {
         "application/json": {
            "examples": load_schema('auth/rbac-permissions/forbidden_examples.json')
         }
      },
   },
   status.HTTP_404_NOT_FOUND: {
      "description": "resources not found",
      "content": {
         "application/json": {
            "examples": load_schema('auth/rbac-permissions/notfound_examples.json')
         }
      },
   },
   status.HTTP_422_UNPROCESSABLE_ENTITY:  {
      "description": "Validation error",
      "content": {
         "application/json": {
            "examples": load_schema('auth/rbac-permissions/validationerror_examples.json')
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
async def evaluate_rbac_permissions(
   account_id: Optional[UUID] = Header(None, alias='X-elevAIte-AccountId', description="account id under which rbac permissions are evaluated"),
   project_id: Optional[UUID] = Header(None, alias='X-elevAIte-projectId', description="project id under which rbac permissions are evaluated"),
   permissions_validation_request: auth_schemas.PermissionsValidationRequest = Body(...),
   validation_info: dict[str, Any] = Depends(validators.validate_evaluate_rbac_permissions)
) -> auth_schemas.PermissionsValidationResponse:
   """
    Retrieve an evaluated list of rbac permissions for requested resource actions, and additionally can also retrieve account/project admin status.

    Parameters:
    - X-elevAIte-AccountId (UUID): Optional. The ID of the account under which permissions are to be evaluated; This is optional if 'X-elevAIte-projectId' is provided since it can be derived from the project. In case both 'X-elevAIte-AccountId' and 'X-elevAIte-ProjectId' are provided, then they must be associated. 
    - X-elevAIte-ProjectId (UUID): Optional. The ID of the project under which permissions are to be evaluated; This is mandatory for project-only scoped resources and statuses such as Datasets, Collections, Instances and 'IS_PROJECT_ADMIN' 
    - request_body : The request body which should contain atleast 1 field for rbac permission evaluation.

    Returns:
    - json containing 'True' or 'False' boolean value denoting evaluated rbac permissions for requested input fields, along with other omitted fields containing 'NOT_EVALUATED' string value

    Notes:
    - If the scope of this api call is within a project context, X-elevAIte-ProjectId should always be passed to reflect accurate rbac permissions within that project.
   """
   db: Session = validation_info.get("db", None)
   logged_in_user = validation_info.get("logged_in_user", None)
   return await service.evaluate_rbac_permissions(
      logged_in_user=logged_in_user,
      permissions_validation_request=permissions_validation_request,
      account_id=account_id,
      project_id=project_id,
      db=db
   )



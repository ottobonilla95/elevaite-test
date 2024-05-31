from fastapi import APIRouter, Header, Body, Depends, status, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import Any, Optional
from uuid import UUID
from pydantic import EmailStr

from elevaitedb.schemas import (
   auth as auth_schemas,
   api as api_schemas,
)
from rbac_api import route_validator_map
from ..services import auth as service
from .utils.helpers import load_schema
from ...audit import AuditorProvider
auditor = AuditorProvider.get_instance()

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
            "examples": load_schema('auth/register/unauthorized_accesstoken_examples.json')
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
@auditor.audit(api_namespace=api_schemas.APINamespace.RBAC_API)
async def register_user(
   request: Request,
   register_user_payload: auth_schemas.RegisterUserRequestDTO = Body(description= "user creation payload"),
   _= Depends(route_validator_map[(api_schemas.APINamespace.RBAC_API, 'register_user')]),
) -> JSONResponse:
   """
   Register User resource to Organization resource 

   Parameters:
      - Authorization Header (Bearer Token): Mandatory. Google access token containing user profile and email scope (user will be registered with email corresponding to access token email)
      - register_user_payload : Contains optional user params - 'firstname' and 'lastname'
      
   Returns: 
      - JSONResponse : A JSON with 200 success message containing existing user in org corresponding to email 
      - JSONResponse : A JSON with 201 success message containing newly registered user in org 
    
   """

   db: Session = request.state.db
   user_email: EmailStr = request.state.user_email
   return service.register_user(
      request=request,
      db=db,
      register_user_payload=register_user_payload,
      user_email=user_email
   )

@auth_router.post("/rbac-permissions", responses={
   status.HTTP_200_OK: {
      "description": "Successfully evaluated rbac_permissions",
      "content": {
         "application/json": {
            "examples": load_schema('auth/rbac-permissions/ok_examples.json')
         }
      },
   },
   status.HTTP_401_UNAUTHORIZED: {
      "description": "No access token or invalid access token",
      "content": {
         "application/json": {
            "examples": load_schema('common/unauthorized_accesstoken_examples.json')
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
@auditor.audit(api_namespace=api_schemas.APINamespace.RBAC_API)
async def evaluate_rbac_permissions(
   request: Request,
   account_id: Optional[UUID] = Header(None, alias='X-elevAIte-AccountId', description="account id under which rbac permissions are evaluated"), 
   project_id: Optional[UUID] = Header(None, alias='X-elevAIte-ProjectId', description="project id under which rbac permissions are evaluated"),
   permissions_evaluation_request: auth_schemas.PermissionsEvaluationRequest = Body(...),
   validation_info: dict[str, Any] = Depends(route_validator_map[(api_schemas.APINamespace.RBAC_API, 'evaluate_rbac_permissions')]),
) -> auth_schemas.PermissionsEvaluationResponse:
   """
   Retrieve an evaluated list of rbac permissions for requested resource actions, and additionally can also retrieve account/project admin status.

   Parameters:
   - X-elevAIte-AccountId (UUID): Optional. The ID of the account under which permissions are to be evaluated; This is optional if 'X-elevAIte-projectId' is provided since it can be derived from the project. In case both 'X-elevAIte-AccountId' and 'X-elevAIte-ProjectId' are provided, then they must be associated. 
   - X-elevAIte-ProjectId (UUID): Optional. The ID of the project under which permissions are to be evaluated; This is mandatory for project-only scoped resources and statuses such as Projects, Apikeys, Datasets, Collections, Instances and 'IS_PROJECT_ADMIN' 
   - request_body : The request body which should contain atleast 1 field for rbac permission evaluation.

   Returns:
   - json containing OVERALL_PERMISSIONS object with 'True' or 'False' boolean value for each requested input field, and additionally may contain SPECIFIC_PERMISSIONS object for each requested input field if requested permission field has more than 1 type, with each type containing bool 'True' or 'False' values; Omitted fields contain 'NOT_EVALUATED' string value

   Notes:
   - evaluated permissions for a requested field will always return an 'OVERALL_PERMISSIONS' object containing a 'True' or 'False' boolean value
   - evaluated permissions for a requested field will contain a 'SPECIFIC_PERMISSIONS' object if the requested field has more than 1 type-value combination; This will contain permission information for all possible typenames and their corresponding typevalue permutations for the field
   - If a requested field's evaluated permission returns SPECIFIC_PERMISSIONS, and even 1 of the SPECIFIC_PERMISSIONS object's type-value permutation key has a 'True' value, then OVERALL_PERMISSIONS will evaluate to 'True'
   - OVERALL_PERMISSIONS can be used if endpoint access only depends on access to any type; SPECIFIC_PERMISSIONS can be used to restrict access conditionally based on types of the requested entity 
   - If the scope of this api call is within a project context, X-elevAIte-ProjectId should always be passed to reflect accurate rbac permissions within that project.
   - IS_ACCOUNT_ADMIN field is account-scoped only and requires 'X-elevAIte-AccountId'
   - IS_PROJECT_ADMIN field is project-scoped only and requires 'X-elevAIte-ProjectId'
   - APPLICATION_READ field is account-scoped only and requires 'X-elevAIte-AccountId'
   - PROJECT_READ field is account-scoped only and requires 'X-elevAIte-AccountId'
   - PROJECT_CREATE field is account-scoped and project-scoped and requires atleast one of 'X-elevAIte-AccountId' or 'X-elevAIte-ProjectId'
   - PROJECT_SERVICENOW_TICKET_INGEST field is project-scoped only and requires 'X-elevAIte-ProjectId'
   - APIKEY_READ field is project-scoped only and requires 'X-elevAIte-ProjectId'
   - APIKEY_CREATE field is project-scoped only and requires 'X-elevAIte-ProjectId'
   - DATASET_READ field is project-scoped only and requires 'X-elevAIte-ProjectId'
   - DATASET_TAG field is project-scoped only and requires 'X-elevAIte-ProjectId'
   - COLLECTION_READ field is project-scoped only and requires 'X-elevAIte-ProjectId'
   - COLLECTION_CREATE field is project-scoped only and requires 'X-elevAIte-ProjectId'
   - CONFIGURATION_READ field is account-scoped only and requires 'X-elevAIte-AccountId'
   - CONFIGURATION_CREATE field is account-scoped only and requires 'X-elevAIte-AccountId'
   - CONFIGURATION_UPDATE field is account-scoped only and requires 'X-elevAIte-AccountId'
   - INSTANCE_READ field is project-scoped only and requires 'X-elevAIte-ProjectId'
   - INSTANCE_CREATE field is project-scoped only and requires 'X-elevAIte-ProjectId'
   - INSTANCE_CONFIGURATION_READ field is project-scoped only and requires 'X-elevAIte-ProjectId'

   """
   db: Session = request.state.db
   logged_in_user = validation_info.get("authenticated_entity", None)
   return await service.evaluate_rbac_permissions(
      request=request,
      logged_in_user=logged_in_user,
      permissions_evaluation_request=permissions_evaluation_request,
      account_id=account_id,
      project_id=project_id,
      db=db
   )



from fastapi import APIRouter, Path, Body, status, Depends, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import List, Any
from uuid import UUID

from elevaitedb.schemas import (
   apikey as apikey_schemas,
)
from elevaitedb.db import models
from rbac_api import routes_to_middleware_imple_map

from ..services import apikey as service
from .utils.helpers import load_schema

apikey_router = APIRouter(prefix="/projects/{project_id}/apikeys", tags=["apikeys"]) 

@apikey_router.post("/", status_code=status.HTTP_201_CREATED, responses={
   status.HTTP_201_CREATED: {
      "description": "Successfully created api key",
      "content": {
         "application/json": {
            "examples": load_schema('apikeys/create_apikey/created_examples.json')
         }
      },
   },
   status.HTTP_401_UNAUTHORIZED: {
      "description": "No access token or invalid access token OR invalid or expired apikey",
      "content": {
         "application/json": {
            "examples": load_schema(
               'common/unauthorized_accesstoken_examples.json'
            )
         }
      },
   },
   status.HTTP_403_FORBIDDEN: {
      "description": "User does not have permissions to create api keys",
      "content": {
         "application/json": {
            "examples": load_schema('apikeys/create_apikey/forbidden_examples.json')
         }
      },
   },
   status.HTTP_404_NOT_FOUND: {
      "description": "account, or project in account not found",
      "content": {
         "application/json": {
            "examples": load_schema('apikeys/create_apikey/notfound_examples.json')
         }
      },
   },
   status.HTTP_422_UNPROCESSABLE_ENTITY: {
      "description": "Validation error",
      "content": {
         "application/json": {
            "examples": load_schema('apikeys/create_apikey/validationerror_examples.json')
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
async def create_apikey(
   request: Request,
   project_id: UUID = Path(..., description='project under which the apikey is created under and is scoped to'),
   create_apikey_dto: apikey_schemas.ApikeyCreate = Body(...),
   validation_info: dict[str, Any] = Depends(routes_to_middleware_imple_map['create_apikey']), 
) -> apikey_schemas.ApikeyCreateResponseDTO:
   """
   Create an api key

   Parameters:
      - project_id: project under which api key is created under, and project to which apikey is scoped to
      - create_apikey_dto: payload containing 'name', 'permissions_type', 'permissions' and 'expires_at' fields

   Returns:
      - ApikeyResponse: 201 CREATED message with created Apikey object
   
   Notes:
      - 'name' field must be unique within the project for the creator of the apikey
      - 'permissions' field is ignored if 'permissions_type' is 'cloned'; in this case, the permissions of the creator in the project is used; for superadmins/account-admins/project-admins - this means 'Allow' for all permissions in ApikeyScopedRBACPermissions model
      - 'permissions' field is considered if 'permissions_type' is 'custom'; in this case, the permissions will default to 'Deny' for all resources if not provided.
      - 'expires_at' field should provde a date in the future or 'NEVER' 
      - The response contains the 'key' field, and this is the only time the 'key' is exposed; GET methods on api key resources don't expose the 'key' field
   """
   db: Session = request.state.db
   logged_in_user: models.User = validation_info["authenticated_entity"]
   logged_in_user_project_association: models.User_Project | None = validation_info.get("logged_in_entity_project_association", None)
   logged_in_user_account_association: models.User_Account | None = validation_info.get("logged_in_entity_account_association", None)
   return service.create_apikey(db=db,
                                 project_id=project_id,
                                 logged_in_user_project_association=logged_in_user_project_association,
                                 logged_in_user_is_project_admin=logged_in_user_project_association.is_admin if logged_in_user_project_association else False,
                                 logged_in_user_is_account_admin=logged_in_user_account_association.is_admin if logged_in_user_account_association else False,
                                 logged_in_user=logged_in_user,
                                 create_apikey_dto=create_apikey_dto
                                 )

@apikey_router.get("/", status_code=status.HTTP_200_OK, responses={
   status.HTTP_200_OK: {
      "description": "Successfully retrieved list of api keys",
      "content": {
         "application/json": {
            "examples": load_schema('apikeys/get_apikeys/ok_examples.json')
         }
      },
   },
   status.HTTP_401_UNAUTHORIZED: {
      "description": "No access token or invalid access token OR invalid or expired apikey",
      "content": {
         "application/json": {
            "examples": load_schema(
               'common/unauthorized_accesstoken_examples.json'
            )
         }
      },
   },
   status.HTTP_403_FORBIDDEN: {
      "description": "no permissions to retrieve api keys",
      "content": {
         "application/json": {
            "examples": load_schema('apikeys/get_apikeys/forbidden_examples.json')
         }
      },
   },
   status.HTTP_404_NOT_FOUND: {
      "description": "account, or project in account not found",
      "content": {
         "application/json": {
            "examples": load_schema('apikeys/get_apikeys/notfound_examples.json')
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
async def get_apikeys(
   request: Request,
   project_id: UUID = Path(..., description='project under which the apikeys are retrieved under and are scoped to'),
   validation_info: dict[str, Any] = Depends(routes_to_middleware_imple_map['get_apikeys']), 
) -> List[apikey_schemas.ApikeyGetResponseDTO]:
   """
   Retrieve api keys

   Parameters:
      - project_id: project under which api keys are created under, and project to which apikeys are scoped to
      
   Returns:
      - List[ApikeyGetResponseDTO]: 200 OK message with retrieved Apikey objects

   Notes:
      - The response objects do not contain the 'key' field
      - users who are superadmins/account-admins/project-admins will retrieve list of all api keys created within project
      - users who are not superadmins and are not account-admins and are not project-admins will only retrieve list of their created api keys
   """
   db: Session = request.state.db
   logged_in_user: models.User  = validation_info["authenticated_entity"]
   logged_in_user_project_association: models.User_Project | None = validation_info.get("logged_in_entity_project_association", None)
   logged_in_user_account_association: models.User_Account | None = validation_info.get("logged_in_entity_account_association", None)
   return service.get_apikeys(db=db,
            logged_in_user=logged_in_user,
            logged_in_user_is_project_admin=logged_in_user_project_association.is_admin if logged_in_user_project_association else False,
            logged_in_user_is_account_admin=logged_in_user_account_association.is_admin if logged_in_user_account_association else False,
            project_id=project_id,
            )

@apikey_router.get("/{apikey_id}", status_code=status.HTTP_200_OK, responses={
   status.HTTP_200_OK: {
      "description": "Successfully retrieved list of api keys",
      "content": {
         "application/json": {
            "examples": load_schema('apikeys/get_apikey/ok_examples.json')
         }
      },
   },
   status.HTTP_401_UNAUTHORIZED: {
      "description": "No access token or invalid access token OR invalid or expired apikey",
      "content": {
         "application/json": {
            "examples": load_schema(
               'common/unauthorized_accesstoken_examples.json'
            )
         }
      },
   },
   status.HTTP_403_FORBIDDEN: {
      "description": "no permissions to retrieve api keys",
      "content": {
         "application/json": {
            "examples": load_schema('apikeys/get_apikey/forbidden_examples.json')
         }
      },
   },
   status.HTTP_404_NOT_FOUND: {
      "description": "account, or project in account not found",
      "content": {
         "application/json": {
            "examples": load_schema('apikeys/get_apikey/notfound_examples.json')
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
async def get_apikey(
   validation_info: dict[str, Any] = Depends(routes_to_middleware_imple_map['get_apikey']), 
) -> apikey_schemas.ApikeyGetResponseDTO:
   """
   Retrieve api keys

   Parameters:
      - project_id: project under which api keys are created under, and project to which apikeys are scoped to
      - apikey_id: ID of apikey to retrieve
      
   Returns:
      - ApikeyGetResponseDTO: 200 OK message with retrieved Apikey object

   Notes:
      - The response object does not contain the 'key' field
      - users who are not superadmins and not account-admins and not project-admins can only retrieve their own api keys
      - users who are superadmins/account-admins/project-admins can retrieve any api key within project
   """
   
   apikey: models.Apikey = validation_info["Apikey"]
   return apikey

@apikey_router.delete("/{apikey_id}", status_code=status.HTTP_200_OK, responses={
   status.HTTP_200_OK: {
      "description": "Successfully deleted apikey",
      "content": {
         "application/json": {
            "examples": load_schema('apikeys/delete_apikey/ok_examples.json')
         }
      }
   },
   status.HTTP_401_UNAUTHORIZED: {
      "description": "No access token or invalid access token OR invalid or expired apikey",
      "content": {
         "application/json": {
            "examples": load_schema(
               'common/unauthorized_accesstoken_examples.json'
            )
         }
      },
   },
   status.HTTP_403_FORBIDDEN: {
      "description": "no permissions to retrieve api keys",
      "content": {
         "application/json": {
            "examples": load_schema('apikeys/delete_apikey/forbidden_examples.json')
         }
      },
   },
   status.HTTP_404_NOT_FOUND: {
      "description": "account, or project in account not found",
      "content": {
         "application/json": {
            "examples": load_schema('apikeys/delete_apikey/notfound_examples.json')
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
async def delete_apikey(
   request: Request,
   validation_info: dict[str, Any] = Depends(routes_to_middleware_imple_map['delete_apikey']), 
) -> JSONResponse:
   """
   Revoke api key

   Parameters:
      - project_id: project under which api key is scoped to
      - apikey_id: ID of apikey to revoke
      
   Returns:
      - JSONResponse: 200 OK message with delete success message

   Notes:
      - users who are not superadmins and not account-admins and not project-admins can only revoke their own api keys
      - users who are superadmins/account-admins/project-admins can revoke any api key within project
   """
   
   apikey: models.Apikey = validation_info["Apikey"]
   db: Session = request.state.db
   return service.delete_apikey(apikey=apikey, db=db)
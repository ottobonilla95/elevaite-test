from fastapi import APIRouter, Body, status, Depends, Query, Request
from typing import Any, Optional, List
from sqlalchemy.orm import Session
from uuid import UUID

from elevaitedb.schemas import (
   organization as organization_schemas,
   user as user_schemas,
)
from elevaitedb.db import models
from rbac_api import routes_to_middleware_imple_map
from .utils.helpers import load_schema
from ..services import organization as service

organization_router = APIRouter(prefix="/organization", tags=["organizations"]) 

@organization_router.patch("/", responses={
            status.HTTP_200_OK: {
                "description": "Successfully patched organization resource",
                "content": {
                    "application/json": {
                        "examples": load_schema('organizations/patch_org/ok_examples.json')
                    }
                },
            },
            status.HTTP_401_UNAUTHORIZED: {
                "description": "Invalid, expired or no access token",
                "content": {
                    "application/json": {
                        "examples": load_schema('common/unauthorized_accesstoken_examples.json')
                    }
                },
            },
            status.HTTP_403_FORBIDDEN: {
                "description": "User lacks superadmin privileges to patch an organization",
                "content": {
                    "application/json": {
                        "examples": load_schema('organizations/patch_org/forbidden_examples.json')
                    }
                },
            },
            status.HTTP_404_NOT_FOUND: {
                "description": "Not found - org not found",
                "content": {
                    "application/json": {
                        "examples": load_schema('organizations/patch_org/notfound_examples.json')
                    }
                },
            },
            status.HTTP_422_UNPROCESSABLE_ENTITY: {
                "description": "Payload validation error",
                "content": {
                    "application/json": {
                        "examples": load_schema('organizations/patch_org/validationerror_examples.json')
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
async def patch_organization(
    request: Request,
    organization_patch_req_payload: organization_schemas.OrganizationPatchRequestDTO = Body(...),
    validation_info: dict[str, Any] = Depends(routes_to_middleware_imple_map['patch_organization']),
) -> organization_schemas.OrganizationResponseDTO:
    """
    Patch elevAIte organization resource.
    
    Parameters:
    - Authorization Header (Bearer Token): Mandatory. Google access token containing user profile and email scope.
    - Organization patch req body: Mandatory. Must contain 1 or more fields

    Returns:
    - OrganizationResponseDTO : The patched elevAIte organization response object

    Notes:
    - Only authorized for use by superadmin users.
    """
    db: Session = request.state.db
    org_to_patch : models.Organization = validation_info.get("Organization", None)
    return service.patch_organization(db=db, 
                                        org_to_patch=org_to_patch,
                                        organization_patch_req_payload=organization_patch_req_payload)
        
@organization_router.get("/", responses={
            status.HTTP_200_OK: {
                "description": "Successfully retrieved organization resource",
                "model": organization_schemas.OrganizationResponseDTO
            },
            status.HTTP_401_UNAUTHORIZED: {
                "description": "Invalid, expired or no access token",
                "content": {
                    "application/json": {
                        "examples": load_schema('common/unauthorized_accesstoken_examples.json')
                    }
                },
            },
            status.HTTP_404_NOT_FOUND: {
                "description": "Not found - org not found",
                "content": {
                    "application/json": {
                        "examples": load_schema('organizations/get_org/notfound_examples.json')
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
async def get_organization(
    request: Request,
    validation_info: dict[str, Any] = Depends(routes_to_middleware_imple_map['get_organization']),
) -> organization_schemas.OrganizationResponseDTO:
    """
    Retrieve elevAIte organization resource

    Parameters:
    - Authorization Header (Bearer Token): Mandatory. Google access token containing user profile and email scope.

    Returns:
    - OrganizationResponseDTO : elevAIte organization response object 
    """
    org = validation_info.get("Organization", None)
    return org


@organization_router.get("/users", response_model=List[user_schemas.OrgUserListItemDTO], status_code=status.HTTP_200_OK, responses={
    status.HTTP_200_OK: {
        "description": "Successfully retrieved organization users",
        "content": {
            "application/json": {
                "examples": load_schema('organizations/get_org_users/ok_examples.json')
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
        "description": "User does not have permissions to this resource",
        "content": {
            "application/json": {
                "examples": load_schema('organizations/get_org_users/forbidden_examples.json')
            }
        },
    },
    status.HTTP_404_NOT_FOUND: {
        "description": "organization not found",
        "content": {
            "application/json": {
                "examples": load_schema('organizations/get_org_users/notfound_examples.json')
            }
        },
    },
    status.HTTP_422_UNPROCESSABLE_ENTITY: {
        "description": "Payload validation error",
        "content": {
            "application/json": {
                "examples": load_schema('organizations/get_org_users/validationerror_examples.json')
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
async def get_org_users( 
    request: Request,
    validation_info: dict[str, Any] = Depends(routes_to_middleware_imple_map['get_org_users']),
    firstname: Optional[str] = Query(None, description="Filter users by first name"),
    lastname: Optional[str] = Query(None, description="Filter users by last name"),
    email: Optional[str] = Query(None, description="Filter users by email"),
) -> List[user_schemas.OrgUserListItemDTO]:
    """
    Retrieve elevAIte organization user resources. 

    Parameters:
    - Authorization Header (Bearer Token): Mandatory. Google access token containing user profile and email scope.
    - Filter query params for user firstname, lastname and email 
    - firstname (str): Optional filter query param for user firstname with case-insensitive pattern matching
    - lastname (str): Optional filter query param for user lastname with case-insensitive pattern matching
    - email (str): Optional filter query param for user email with case-insensitive pattern matching

    Returns:
    - List[OrgUserListItemDTO] : list of users registered to elevAIte platform

    Notes:
    - Only authorized for use by superadmins/account-admins.
    - Use case for superadmins/admins to add users to accounts
    """
    db: Session = request.state.db
    org_id: UUID = validation_info.get("org_id" , None)
    return service.get_org_users(db, org_id, firstname, lastname, email)

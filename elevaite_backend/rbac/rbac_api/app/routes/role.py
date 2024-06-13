from fastapi import APIRouter, Body, Depends, Path, status, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from elevaitelib.schemas import (
    role as role_schemas,
    api as api_schemas,
)

from rbac_api import route_validator_map
from ..services import role as service
from .utils.helpers import load_schema
from ...audit import AuditorProvider

auditor = AuditorProvider.get_instance()

role_router = APIRouter(prefix="/roles", tags=["roles"])


@role_router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_201_CREATED: {
            "description": "Newly created role object",
            "model": role_schemas.RoleResponseDTO,
        },
        status.HTTP_401_UNAUTHORIZED: {
            "description": "No access token or invalid access token",
            "content": {
                "application/json": {
                    "examples": load_schema(
                        "common/unauthorized_accesstoken_examples.json"
                    )
                }
            },
        },
        status.HTTP_403_FORBIDDEN: {
            "description": "User does not have permissions to create roles",
            "content": {
                "application/json": {
                    "examples": load_schema("roles/post_role/forbidden_examples.json")
                }
            },
        },
        status.HTTP_409_CONFLICT: {
            "description": "Role with same name already exists",
            "content": {
                "application/json": {
                    "examples": load_schema("roles/post_role/conflict_examples.json")
                }
            },
        },
        status.HTTP_422_UNPROCESSABLE_ENTITY: {
            "description": "Payload validation error",
            "content": {
                "application/json": {
                    "examples": load_schema(
                        "roles/post_role/validationerror_examples.json"
                    )
                }
            },
        },
        status.HTTP_503_SERVICE_UNAVAILABLE: {
            "description": "The server is currently unable to handle the request due to a temporary overloading or maintenance of the server",
            "content": {
                "application/json": {
                    "examples": load_schema("common/serviceunavailable_examples.json")
                }
            },
        },
    },
)
@auditor.audit(api_namespace=api_schemas.APINamespace.RBAC_API)
async def create_role(
    request: Request,
    role_creation_dto: role_schemas.RoleCreationRequestDTO = Body(
        description="role creation payload"
    ),
    _=Depends(route_validator_map[(api_schemas.APINamespace.RBAC_API, "create_role")]),
) -> role_schemas.RoleResponseDTO:
    """
    Create Role resource

    Parameters:
       - Authorization Header (Bearer Token): Mandatory. Google access token containing user profile and email scope.
       - role_creation_dto : req body containing role creation details

    Returns:
       - RoleResponseDTO  : Role response object

    Notes:
       - only authorized for use by superadmin users
       - role contains a JSONB permissions fields which has AccountScopedRBACPermissions object
       - Only Takes in fields with 'Allow' value; If a field is omitted, it is implied that it is 'Denied'. An empty permissions object implied all permissions are denied
       - If a field is not provided, it will have 'null' value, and its nested fields are ignored
    """
    db: Session = request.state.db
    return service.create_role(request, role_creation_dto, db)


@role_router.get(
    "/{role_id}",
    response_model=role_schemas.RoleResponseDTO,
    responses={
        status.HTTP_200_OK: {
            "description": "Retrieved role response object",
            "model": role_schemas.RoleResponseDTO,
        },
        status.HTTP_401_UNAUTHORIZED: {
            "description": "No access token or invalid access token",
            "content": {
                "application/json": {
                    "examples": load_schema(
                        "common/unauthorized_accesstoken_examples.json"
                    )
                }
            },
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "Role not found",
            "content": {
                "application/json": {
                    "examples": load_schema("roles/get_role/notfound_examples.json")
                }
            },
        },
        status.HTTP_422_UNPROCESSABLE_ENTITY: {
            "description": "Payload validation error",
            "content": {
                "application/json": {
                    "examples": load_schema(
                        "roles/get_role/validationerror_examples.json"
                    )
                }
            },
        },
        status.HTTP_503_SERVICE_UNAVAILABLE: {
            "description": "The server is currently unable to handle the request due to a temporary overloading or maintenance of the server",
            "content": {
                "application/json": {
                    "examples": load_schema("common/serviceunavailable_examples.json")
                }
            },
        },
    },
)
@auditor.audit(api_namespace=api_schemas.APINamespace.RBAC_API)
async def get_role(
    request: Request,
    role_id: UUID = Path(..., description="role ID to retrieve role object"),
    _=Depends(route_validator_map[(api_schemas.APINamespace.RBAC_API, "get_role")]),
) -> role_schemas.RoleResponseDTO:
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
    db: Session = request.state.db
    return service.get_role(request=request, db=db, role_id=role_id)


@role_router.get(
    "/",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {
            "description": "Retrieved role response objects",
            "content": {
                "application/json": {
                    "examples": load_schema("roles/get_roles/ok_examples.json")
                }
            },
        },
        status.HTTP_401_UNAUTHORIZED: {
            "description": "No access token or invalid access token",
            "content": {
                "application/json": {
                    "examples": load_schema(
                        "common/unauthorized_accesstoken_examples.json"
                    )
                }
            },
        },
        status.HTTP_403_FORBIDDEN: {
            "description": "User does not have permission to read all roles",
            "content": {
                "application/json": {
                    "examples": load_schema("roles/get_roles/forbidden_examples.json")
                }
            },
        },
        status.HTTP_503_SERVICE_UNAVAILABLE: {
            "description": "The server is currently unable to handle the request due to a temporary overloading or maintenance of the server",
            "content": {
                "application/json": {
                    "examples": load_schema("common/serviceunavailable_examples.json")
                }
            },
        },
    },
)
@auditor.audit(api_namespace=api_schemas.APINamespace.RBAC_API)
async def get_roles(
    request: Request,
    _=Depends(route_validator_map[(api_schemas.APINamespace.RBAC_API, "get_roles")]),
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
    db: Session = request.state.db
    return service.get_roles(request, db)


@role_router.patch(
    "/{role_id}",
    responses={
        status.HTTP_200_OK: {
            "description": "Successfully patched role object",
            "model": role_schemas.RoleResponseDTO,
        },
        status.HTTP_401_UNAUTHORIZED: {
            "description": "No access token or invalid access token",
            "content": {
                "application/json": {
                    "examples": load_schema(
                        "common/unauthorized_accesstoken_examples.json"
                    )
                }
            },
        },
        status.HTTP_403_FORBIDDEN: {
            "description": "User does not have permission to patch role",
            "content": {
                "application/json": {
                    "examples": load_schema("roles/patch_role/forbidden_examples.json")
                }
            },
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "Role not found",
            "content": {
                "application/json": {
                    "examples": load_schema("roles/patch_role/notfound_examples.json")
                }
            },
        },
        status.HTTP_409_CONFLICT: {
            "description": "Role with same name already exists",
            "content": {
                "application/json": {
                    "examples": load_schema("roles/patch_role/conflict_examples.json")
                }
            },
        },
        status.HTTP_422_UNPROCESSABLE_ENTITY: {
            "description": "Payload validation error",
            "content": {
                "application/json": {
                    "examples": load_schema(
                        "roles/patch_role/validationerror_examples.json"
                    )
                }
            },
        },
        status.HTTP_503_SERVICE_UNAVAILABLE: {
            "description": "The server is currently unable to handle the request due to a temporary overloading or maintenance of the server",
            "content": {
                "application/json": {
                    "examples": load_schema("common/serviceunavailable_examples.json")
                }
            },
        },
    },
)
@auditor.audit(api_namespace=api_schemas.APINamespace.RBAC_API)
async def patch_role(
    request: Request,
    role_id: UUID = Path(..., description="The ID of the role to update"),
    role_patch_req_payload: role_schemas.RoleUpdateRequestDTO = Body(
        description="Role patch payload"
    ),
    _=Depends(route_validator_map[(api_schemas.APINamespace.RBAC_API, "patch_role")]),
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
       - Patch payload for permission field will perform an update on the permissions json
    """
    db: Session = request.state.db
    return service.patch_role(request, role_id, role_patch_req_payload, db)


@role_router.delete(
    "/{role_id}",
    responses={
        status.HTTP_200_OK: {
            "description": "Successfully deleted role",
            "content": {
                "application/json": {
                    "examples": load_schema("roles/delete_role/ok_examples.json")
                }
            },
        },
        status.HTTP_401_UNAUTHORIZED: {
            "description": "No access token or invalid access token",
            "content": {
                "application/json": {
                    "examples": load_schema(
                        "common/unauthorized_accesstoken_examples.json"
                    )
                }
            },
        },
        status.HTTP_403_FORBIDDEN: {
            "description": "User does not have permission to patch role",
            "content": {
                "application/json": {
                    "examples": load_schema("roles/delete_role/forbidden_examples.json")
                }
            },
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "Role not found",
            "content": {
                "application/json": {
                    "examples": load_schema("roles/delete_role/notfound_examples.json")
                }
            },
        },
        status.HTTP_503_SERVICE_UNAVAILABLE: {
            "description": "The server is currently unable to handle the request due to a temporary overloading or maintenance of the server",
            "content": {
                "application/json": {
                    "examples": load_schema("common/serviceunavailable_examples.json")
                }
            },
        },
    },
)
@auditor.audit(api_namespace=api_schemas.APINamespace.RBAC_API)
async def delete_role(
    request: Request,
    _=Depends(route_validator_map[(api_schemas.APINamespace.RBAC_API, "delete_role")]),
    role_id: UUID = Path(
        ...,
        description="role id to delete",
        examples=["11111111-1111-1111-1111-111111111111"],
    ),
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
    db: Session = request.state.db
    return service.delete_role(request, db, role_id)

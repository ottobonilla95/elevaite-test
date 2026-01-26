from fastapi import status, HTTPException, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from typing import List
from uuid import UUID
from datetime import datetime
from pprint import pprint

from elevaitelib.schemas import (
    role as role_schemas,
)
from elevaitelib.orm.db import models

from rbac_lib.utils.api_error import ApiError

def create_role(
    request: Request,
    role_creation_dto: role_schemas.RoleCreationRequestDTO,
    db: Session,
) -> role_schemas.RoleResponseDTO:
    try:
        existing_role = (
            db.query(models.Role)
            .filter(models.Role.name == role_creation_dto.name)
            .first()
        )
        if (
            existing_role
        ):  # Application-side uniqueness check : Check if a user with the same email already exists in the specified account
            pprint(
                "in POST /roles - A role with the same name already exists in roles table"
            )
            raise ApiError.conflict(
                f"A role with name - '{role_creation_dto.name}' - already exists"
            )
        new_role = models.Role(
            name=role_creation_dto.name,
            permissions=role_creation_dto.permissions.dict(
                exclude_none=True
            ),  # exclude None values
        )
        db.add(new_role)
        db.commit()
        db.refresh(new_role)

        return new_role
    except HTTPException as e:
        db.rollback()
        pprint(f"API error in POST /roles service method : {e}")
        raise e
    except (
        IntegrityError
    ) as e:  # Database-side uniqueness check : Check if an account with the same name already exists in the organization
        db.rollback()
        pprint(f"DB error in POST /roles service method : {e}")
        raise ApiError.conflict(
            f"A role with name -'{role_creation_dto.name}'- already exists"
        )
    except (
        SQLAlchemyError
    ) as e:  # group db side error as 503 to not expose actual error to client
        db.rollback()
        pprint(f"DB error in POST /roles service method : {e}")
        request.state.source_error_msg = str(e)
        raise ApiError.serviceunavailable(
            "The server is currently unavailable, please try again later."
        )
    except Exception as e:
        db.rollback()
        pprint(f"Unexpected error in POST /roles service method: {e}")
        request.state.source_error_msg = str(e)
        raise ApiError.serviceunavailable(
            "The server is currently unavailable, please try again later."
        )


def get_role(
    request: Request, db: Session, role_id: UUID
) -> role_schemas.RoleResponseDTO:
    try:
        role = db.query(models.Role).filter(models.Role.id == role_id).first()
        if not role:
            raise ApiError.notfound(f"Role - '{role_id}' - not found")

        return role_schemas.RoleResponseDTO.from_orm(role)
    except HTTPException as e:
        db.rollback()
        pprint(f"API error in GET /roles/{role_id} service method : {e}")
        raise e
    except (
        SQLAlchemyError
    ) as e:  # group db side error as 503 to not expose actual error to client
        db.rollback()
        pprint(f"DB error in GET /roles/{role_id} service method : {e}")
        request.state.source_error_msg = str(e)
        raise ApiError.serviceunavailable(
            "The server is currently unavailable, please try again later."
        )
    except Exception as e:
        db.rollback()
        pprint(f"Unexpected error in GET /roles/{role_id} service method: {e}")
        request.state.source_error_msg = str(e)
        raise ApiError.serviceunavailable(
            "The server is currently unavailable, please try again later."
        )


def get_roles(request: Request, db: Session) -> List[role_schemas.RoleResponseDTO]:
    try:
        query = db.query(models.Role)
        roles = query.all()
        return [role_schemas.RoleResponseDTO.from_orm(role) for role in roles]
    except (
        SQLAlchemyError
    ) as e:  # group db side error as 503 to not expose actual error to client
        db.rollback()
        pprint(f"DB error in GET /roles service method : {e}")
        request.state.source_error_msg = str(e)
        raise ApiError.serviceunavailable(
            "The server is currently unavailable, please try again later."
        )
    except Exception as e:
        db.rollback()
        pprint(f"Unexpected error in GET /roles service method: {e}")
        request.state.source_error_msg = str(e)
        raise ApiError.serviceunavailable(
            "The server is currently unavailable, please try again later."
        )


def patch_role(
    request: Request,
    role_id: UUID,
    role_patch_req_payload: role_schemas.RoleUpdateRequestDTO,
    db: Session,
) -> role_schemas.RoleResponseDTO:
    try:
        db_role = db.query(models.Role).filter(models.Role.id == role_id).first()
        if not db_role:
            print(
                f'In PATCH: /roles/{role_id} service method : role -"{role_id}"- to patch not found'
            )
            raise ApiError.notfound(f"Role - '{role_id}' - not found")

        if role_patch_req_payload.name:
            setattr(db_role, "name", role_patch_req_payload.name)
        if role_patch_req_payload.permissions:
            setattr(
                db_role,
                "permissions",
                role_patch_req_payload.permissions.dict(exclude_none=True),
            )

        db_role.updated_at = datetime.now()
        db.commit()
        db.refresh(db_role)

        return role_schemas.RoleResponseDTO.from_orm(db_role)
    except HTTPException as e:
        db.rollback()
        pprint(f"API error in PATCH /roles/{role_id} service method: {e}")
        raise e
    except (
        IntegrityError
    ) as e:  # Database-side uniqueness check : Check if a role the same name already exists in the organization
        db.rollback()
        pprint(f"DB error in PATCH /roles/{role_id} service method : {e}")
        raise ApiError.conflict(
            f"A role with name - '{role_patch_req_payload.name}' - already exists"
        )
    except (
        SQLAlchemyError
    ) as e:  # group db side error as 503 to not expose actual error to client
        db.rollback()
        pprint(f"DB error in PATCH /roles/{role_id} service method: {e}")
        request.state.source_error_msg = str(e)
        raise ApiError.serviceunavailable(
            "The server is currently unavailable, please try again later."
        )
    except Exception as e:
        db.rollback()
        pprint(f"Unexpected error in PATCH /roles/{role_id} service method: {e}")
        request.state.source_error_msg = str(e)
        raise ApiError.serviceunavailable(
            "The server is currently unavailable, please try again later."
        )


def delete_role(request: Request, db: Session, role_id: UUID) -> JSONResponse:
    try:
        role = db.query(models.Role).filter(models.Role.id == role_id).first()
        if not role:
            print(
                f'in DELETE /roles/{role_id} service method : role - "{role_id}" - not found'
            )
            raise ApiError.notfound(f"Role - '{role_id}' - not found")

        db.delete(role)
        db.commit()
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"message": f"Successfully deleted role - '{role_id}'"},
        )
    except HTTPException as e:
        db.rollback()
        pprint(f"API error in DELETE /roles/{role_id} service method: {e}")
        raise e
    except (
        SQLAlchemyError
    ) as e:  # group db side error as 503 to not expose actual error to client
        db.rollback()
        pprint(f"DB error in DELETE /roles/{role_id} service method : {e}")
        request.state.source_error_msg = str(e)
        raise ApiError.serviceunavailable(
            "The server is currently unavailable, please try again later."
        )
    except Exception as e:
        db.rollback()
        pprint(f"Unexpected error in DELETE /roles/{role_id} service method: {e}")
        request.state.source_error_msg = str(e)
        raise ApiError.serviceunavailable(
            "The server is currently unavailable, please try again later."
        )

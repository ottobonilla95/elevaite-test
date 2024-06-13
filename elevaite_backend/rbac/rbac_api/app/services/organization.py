from fastapi import HTTPException, Request
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from typing import List, Optional, cast
from uuid import UUID
from datetime import datetime
from pprint import pprint
from ..errors.api_error import ApiError

from elevaitelib.schemas import (
    organization as organization_schemas,
    user as user_schemas,
)
from elevaitelib.orm.db import models


def patch_organization(
    request: Request,
    organization_patch_req_payload: organization_schemas.OrganizationPatchRequestDTO,
    db: Session,
    org_to_patch: models.Organization,
) -> organization_schemas.OrganizationResponseDTO:
    """
    Patches an organization based on given org_id path param, and org patch payload

     Args:
        org_id (UUID) : The id of the organization to be patched.
        organization_patch_req_payload (OrganizationPatchRequestDTO): The organization patch payload containing optional details of 'name', and 'description' for patch.
        db (Session): The db session object for db operations.

    Raises:
       404: Organization not found.
       503: Any db related error.
    Returns:
       OrganizationResponseDTO : The response containing patched OrganizationResponseDTO object.

    Notes:
       - logged-in user is assumed to be a superadmin.
       - the req body has either non-empty 'name' field, or non-empty 'description' field, or both fields are non-empty.
    """
    try:
        for var, value in vars(organization_patch_req_payload).items():
            setattr(org_to_patch, var, value) if value is not None else None
        org_to_patch.updated_at = datetime.now()
        db.commit()
        db.refresh(org_to_patch)
        return organization_schemas.OrganizationResponseDTO.from_orm(org_to_patch)
    except HTTPException as e:
        db.rollback()
        pprint(f"API error in PATCH /organization service method: {e}")
        raise e
    except (
        SQLAlchemyError
    ) as e:  # group db side error as 503 to not expose actual error to client
        db.rollback()
        pprint(f"DB error in PATCH /organization service method : {e}")
        request.state.source_error_msg = str(e)
        raise ApiError.serviceunavailable(
            "The server is currently unavailable, please try again later."
        )
    except Exception as e:
        db.rollback()
        pprint(f"Unexpected error in PATCH /organization service method: {e}")
        request.state.source_error_msg = str(e)
        raise ApiError.serviceunavailable(
            "The server is currently unavailable, please try again later."
        )


def get_org_users(
    request: Request,
    db: Session,
    org_id: UUID,
    firstname: Optional[str],
    lastname: Optional[str],
    email: Optional[str],
    account_id: Optional[UUID],
    assigned: Optional[bool] = True,
) -> List[user_schemas.OrgUserListItemDTO]:
    try:
        query = db.query(models.User).filter(models.User.organization_id == org_id)

        if firstname:
            query = query.filter(models.User.firstname.ilike(f"%{firstname}%"))
        if lastname:
            query = query.filter(models.User.lastname.ilike(f"%{lastname}%"))
        if email:
            query = query.filter(models.User.email.ilike(f"%{email}%"))

        if account_id:
            # Outer join with User_Account to have null/non-null values to distinguish account members/non-members
            query = query.outerjoin(
                models.User_Account,
                (models.User.id == models.User_Account.user_id)
                & (models.User_Account.account_id == account_id),
            )

        if assigned:
            # Filter users assigned to the account
            query = query.filter(models.User_Account.account_id != None)
        else:
            # Filter users not assigned to the account
            query = query.filter(models.User_Account.account_id == None)

        users = query.all()
        return [user_schemas.OrgUserListItemDTO.from_orm(user) for user in users]
    except HTTPException as e:
        db.rollback()
        pprint(f"API error in GET /users/ service method : {e}")
        raise e
    except SQLAlchemyError as e:
        db.rollback()
        pprint(f"Error in GET /users/ service method : {e}")
        request.state.source_error_msg = str(e)
        raise ApiError.serviceunavailable(
            "The server is currently unavailable, please try again later."
        )
    except Exception as e:
        db.rollback()
        pprint(f"Unexpected error in GET /users service method: {e}")
        request.state.source_error_msg = str(e)
        raise ApiError.serviceunavailable(
            "The server is currently unavailable, please try again later."
        )

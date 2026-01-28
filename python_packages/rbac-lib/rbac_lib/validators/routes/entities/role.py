from fastapi import Depends, Path, HTTPException, Request
from sqlalchemy import exists, and_
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from uuid import UUID
from pprint import pprint
from rbac_lib.auth.impl import AccessTokenAuthentication
from rbac_lib.utils.api_error import ApiError

from elevaitelib.orm.db import models
from elevaitelib.schemas import (
    api as api_schemas,
)
from ....audit import AuditorProvider

auditor = AuditorProvider.get_instance()


@auditor.audit(api_namespace=api_schemas.APINamespace.RBAC_API)
async def validate_post_roles(
    request: Request,
    logged_in_user: models.User = Depends(AccessTokenAuthentication.authenticate),
) -> None:
    db: Session = request.state.db
    try:
        # Validate if the user is a superadmin
        if logged_in_user.is_superadmin:
            return

        raise ApiError.forbidden(
            f"logged-in user - '{logged_in_user.id}' - does not have superadmin privileges to create roles"
        )
    except HTTPException as e:
        db.rollback()
        pprint(f"API error in validate_post_roles middleware : {e}")
        raise e
    except SQLAlchemyError as e:
        pprint(f"DB error in validate_post_roles middleware : {e}")
        request.state.source_error_msg = str(e)
        raise ApiError.serviceunavailable(
            "The server is currently unavailable, please try again later."
        )
    except Exception as e:
        db.rollback()
        print(f"Unexpected error in validate_post_roles middleware : {e}")
        request.state.source_error_msg = str(e)
        raise ApiError.serviceunavailable(
            "The server is currently unavailable, please try again later."
        )


@auditor.audit(api_namespace=api_schemas.APINamespace.RBAC_API)
async def validate_delete_roles(
    request: Request,
    logged_in_user: models.User = Depends(AccessTokenAuthentication.authenticate),
) -> None:
    db: Session = request.state.db
    try:
        # Validate if the user is a superadmin
        if logged_in_user.is_superadmin:
            return

        raise ApiError.forbidden(
            f"logged-in user - '{logged_in_user.id}' - does not have superadmin privileges to delete roles"
        )
    except HTTPException as e:
        db.rollback()
        pprint(f"API error in validate_delete_roles middleware : {e}")
        raise e
    except SQLAlchemyError as e:
        pprint(f"DB error in validate_delete_roles middleware : {e}")
        request.state.source_error_msg = str(e)
        raise ApiError.serviceunavailable(
            "The server is currently unavailable, please try again later."
        )
    except Exception as e:
        db.rollback()
        print(f"Unexpected error in validate_delete_roles middleware : {e}")
        request.state.source_error_msg = str(e)
        raise ApiError.serviceunavailable(
            "The server is currently unavailable, please try again later."
        )


@auditor.audit(api_namespace=api_schemas.APINamespace.RBAC_API)
async def validate_patch_roles(
    request: Request,
    logged_in_user: models.User = Depends(AccessTokenAuthentication.authenticate),
) -> None:
    db: Session = request.state.db
    try:
        # Validate if the user is a superadmin
        if logged_in_user.is_superadmin:
            return

        raise ApiError.forbidden(
            f"logged-in user - '{logged_in_user.id}' - does not have superadmin privileges to update roles"
        )
    except HTTPException as e:
        db.rollback()
        pprint(f"API error in validate_patch_roles middleware : {e}")
        raise e
    except SQLAlchemyError as e:
        pprint(f"DB error in validate_patch_roles middleware : {e}")
        request.state.source_error_msg = str(e)
        raise ApiError.serviceunavailable(
            "The server is currently unavailable, please try again later."
        )
    except Exception as e:
        db.rollback()
        print(f"Unexpected error in validate_patch_roles middleware : {e}")
        request.state.source_error_msg = str(e)
        raise ApiError.serviceunavailable(
            "The server is currently unavailable, please try again later."
        )


@auditor.audit(api_namespace=api_schemas.APINamespace.RBAC_API)
async def validate_get_roles(
    request: Request,
    logged_in_user: models.User = Depends(AccessTokenAuthentication.authenticate),
) -> None:
    db: Session = request.state.db
    try:
        # Validate if the logged-in user is a superadmin
        if logged_in_user.is_superadmin:
            return

        # validate if logged-in user is an admin in any account
        user_admin_accounts_exist = db.query(
            exists().where(
                and_(
                    models.User_Account.user_id == logged_in_user.id,
                    models.User_Account.is_admin,
                )
            )
        ).scalar()
        if user_admin_accounts_exist:
            return

        raise ApiError.forbidden(
            f"logged-in user - '{logged_in_user.id}' - does not have superadmin/account-admin privileges to read all roles"
        )
    except HTTPException as e:
        db.rollback()
        pprint(f"API error GET /roles/ - validate_get_all_roles middleware : {e}")
        raise e
    except SQLAlchemyError as e:
        pprint(f"DB error in GET /roles/ - validate_get_all_roles middleware : {e}")
        request.state.source_error_msg = str(e)
        raise ApiError.serviceunavailable(
            "The server is currently unavailable, please try again later."
        )
    except Exception as e:
        db.rollback()
        print(
            f"Unexpected error in GET /roles/ - validate_get_all_roles middleware : {e}"
        )
        request.state.source_error_msg = str(e)
        raise ApiError.serviceunavailable(
            "The server is currently unavailable, please try again later."
        )


@auditor.audit(api_namespace=api_schemas.APINamespace.RBAC_API)
async def validate_get_role(
    request: Request,
    logged_in_user: models.User = Depends(AccessTokenAuthentication.authenticate),
    role_id: UUID = Path(..., description="Role ID to retrieve"),
) -> None:
    db: Session = request.state.db
    try:
        return
    except HTTPException as e:
        db.rollback()
        pprint(
            f"API error in GET /roles/{role_id} - validate_get_role middleware : {e}"
        )
        raise e
    except SQLAlchemyError as e:
        pprint(f"DB error in GET /roles/{role_id} - validate_get_role middleware : {e}")
        request.state.source_error_msg = str(e)
        raise ApiError.serviceunavailable(
            "The server is currently unavailable, please try again later."
        )
    except Exception as e:
        db.rollback()
        print(
            f"Unexpected error in GET /roles/{role_id} - validate_get_role middleware : {e}"
        )
        request.state.source_error_msg = str(e)
        raise ApiError.serviceunavailable(
            "The server is currently unavailable, please try again later."
        )

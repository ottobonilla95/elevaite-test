from fastapi import Query, Path, Depends, HTTPException, Request
from uuid import UUID

from rbac_lib.auth.impl import AccessTokenAuthentication
from sqlalchemy.orm import Session
from sqlalchemy import and_, exists
from sqlalchemy.exc import SQLAlchemyError
from pprint import pprint
from typing import Any
from rbac_lib.utils.api_error import ApiError
from elevaitelib.orm.db import models
from elevaitelib.schemas import (
    api as api_schemas,
)
from ....audit import AuditorProvider

auditor = AuditorProvider.get_instance()


@auditor.audit(api_namespace=api_schemas.APINamespace.RBAC_API)
async def validate_post_account(
    request: Request,
    logged_in_user: models.User = Depends(AccessTokenAuthentication.authenticate),
) -> dict[str, Any]:
    db: Session = request.state.db
    try:
        # Check if user is a superadmin
        if logged_in_user.is_superadmin:
            return {"authenticated_entity": logged_in_user}

        # If not a superadmin, deny access
        raise ApiError.forbidden(
            f"logged-in user - '{logged_in_user.id}' - does not have superadmin privileges to create accounts"
        )
    except HTTPException as e:
        db.rollback()
        pprint(f"API error in POST /accounts/ - validate_post_account middleware : {e}")
        raise e
    except SQLAlchemyError as e:
        pprint(f"DB error in POST /accounts/ - validate_post_account middleware : {e}")
        request.state.source_error_msg = str(e)
        raise ApiError.serviceunavailable(
            "The server is currently unavailable, please try again later."
        )
    except Exception as e:
        db.rollback()
        print(
            f"Unexpected error in POST /accounts/ - validate_post_account middleware : {e}"
        )
        request.state.source_error_msg = str(e)
        raise ApiError.serviceunavailable(
            "The server is currently unavailable, please try again later."
        )


@auditor.audit(api_namespace=api_schemas.APINamespace.RBAC_API)
async def validate_patch_account(
    request: Request,
    logged_in_user: models.User = Depends(AccessTokenAuthentication.authenticate),
    account_id: UUID = Path(..., description="The ID of the account to patch"),
) -> dict[str, Any]:
    db: Session = request.state.db
    try:
        account = (
            db.query(models.Account).filter(models.Account.id == account_id).first()
        )
        if not account:
            raise ApiError.notfound(
                f"Account - '{account_id}' - not found"
            )  # Account not found

        if logged_in_user.is_superadmin:
            return {"Account": account}

        is_logged_in_user_account_admin = db.query(
            exists().where(
                and_(
                    models.User_Account.user_id == logged_in_user.id,
                    models.User_Account.account_id == account_id,
                    models.User_Account.is_admin,
                )
            )
        ).scalar()

        if is_logged_in_user_account_admin:
            return {"Account": account}

        raise ApiError.forbidden(
            f"logged-in user - '{logged_in_user.id}' - does not have superadmin/account-admin privileges to patch account - '{account_id}'"
        )
    except HTTPException as e:
        db.rollback()
        pprint(
            f"API error in PATCH /accounts/{account_id} - validate_patch_account middleware : {e}"
        )
        raise e
    except SQLAlchemyError as e:
        pprint(
            f"DB error in PATCH /accounts/{account_id} - validate_patch_account middleware : {e}"
        )
        request.state.source_error_msg = str(e)
        raise ApiError.serviceunavailable(
            "The server is currently unavailable, please try again later."
        )
    except Exception as e:
        db.rollback()
        print(
            f"Unexpected error in PATCH /accounts/{account_id} - validate_patch_account middleware : {e}"
        )
        request.state.source_error_msg = str(e)
        raise ApiError.serviceunavailable(
            "The server is currently unavailable, please try again later."
        )


@auditor.audit(api_namespace=api_schemas.APINamespace.RBAC_API)
async def validate_get_account(
    request: Request,
    logged_in_user: models.User = Depends(AccessTokenAuthentication.authenticate),
    account_id: UUID = Path(description="id of account to be queried"),
) -> dict[str, Any]:
    db: Session = request.state.db
    try:
        account = (
            db.query(models.Account).filter(models.Account.id == account_id).first()
        )
        if not account:
            raise ApiError.notfound(f"Account - '{account_id}' - not found")

        if logged_in_user.is_superadmin:
            return {"Account": account}

        user_account_association_exists = db.query(
            exists().where(
                models.User_Account.user_id == logged_in_user.id,
                models.User_Account.account_id == account_id,
            )
        ).scalar()

        if not user_account_association_exists:
            raise ApiError.forbidden(
                f"logged-in user - '{logged_in_user.id}' - is not assigned to account - '{account_id}'"
            )

        return {"Account": account}
    except HTTPException as e:
        db.rollback()
        pprint(
            f"API error in GET /accounts/{account_id} - validate_get_account middleware : {e}"
        )
        raise e
    except SQLAlchemyError as e:
        pprint(
            f"DB error in GET /accounts/{account_id} - validate_get_account middleware : {e}"
        )
        request.state.source_error_msg = str(e)
        raise ApiError.serviceunavailable(
            "The server is currently unavailable, please try again later."
        )
    except Exception as e:
        print(
            f"Unexpected error in GET /accounts/{account_id} - validate_get_account middleware : {e}"
        )
        request.state.source_error_msg = str(e)
        raise ApiError.serviceunavailable(
            "The server is currently unavailable, please try again later."
        )


@auditor.audit(api_namespace=api_schemas.APINamespace.RBAC_API)
async def validate_get_accounts(
    request: Request,
    logged_in_user: models.User = Depends(AccessTokenAuthentication.authenticate),
) -> dict[str, Any]:
    db: Session = request.state.db
    try:
        return {"authenticated_entity": logged_in_user}
    except HTTPException as e:
        db.rollback()
        pprint(f"API error in GET /accounts/ - validate_get_accounts middleware : {e}")
        raise e
    except SQLAlchemyError as e:
        pprint(f"DB error in GET /accounts/ - validate_get_accounts middleware : {e}")
        request.state.source_error_msg = str(e)
        raise ApiError.serviceunavailable(
            "The server is currently unavailable, please try again later."
        )
    except Exception as e:
        print(
            f"Unexpected error in GET /accounts/ - validate_get_accounts middleware : {e}"
        )
        request.state.source_error_msg = str(e)
        raise ApiError.serviceunavailable(
            "The server is currently unavailable, please try again later."
        )


@auditor.audit(api_namespace=api_schemas.APINamespace.RBAC_API)
async def validate_get_account_user_list(
    request: Request,
    logged_in_user: models.User = Depends(AccessTokenAuthentication.authenticate),
    account_id: UUID = Path(
        ..., description="Account id under which users are queried"
    ),
    project_id: UUID = Query(
        None,
        description="Optional param to filter account user's by their assignment to account-level project",
    ),
) -> dict[str, Any]:
    db: Session = request.state.db
    try:
        # Check if the account exists
        account = (
            db.query(models.Account).filter(models.Account.id == account_id).first()
        )
        if not account:
            raise ApiError.notfound(f"Account - '{account_id}' - not found")

        if logged_in_user.is_superadmin:
            if project_id:
                project = (
                    db.query(models.Project)
                    .filter(models.Project.id == project_id)
                    .first()
                )
                if not project or project.account_id != account_id:
                    raise ApiError.notfound(
                        f"Project - '{project_id}' - not found in account - '{account_id}'"
                    )
                if project.parent_project_id is not None:
                    raise ApiError.validationerror(
                        f"Project - '{project_id}' - is not a top-level project under account - '{account_id}'"
                    )
            return {
                "authenticated_entity": logged_in_user,
                "logged_in_user_account_association": None,
            }

        # user is non-superadmin here

        # Check if the logged-in user is associated with the account
        logged_in_user_account_association = (
            db.query(models.User_Account)
            .filter_by(user_id=logged_in_user.id, account_id=account_id)
            .first()
        )
        if not logged_in_user_account_association:
            raise ApiError.forbidden(
                f"logged-in user - '{logged_in_user.id}' - is not assigned to account - '{account_id}'"
            )

        # User is non-superadmin, and assigned to account here
        if project_id:
            project = (
                db.query(models.Project).filter(models.Project.id == project_id).first()
            )
            if not project or project.account_id != account_id:
                raise ApiError.notfound(
                    f"Project - '{project_id}' - not found in account - '{account_id}'"
                )
            if project.parent_project_id is not None:
                raise ApiError.validationerror(
                    f"Project - '{project_id}' - is not a top-level project under account - '{account_id}'"
                )

            if logged_in_user_account_association.is_admin:
                return {
                    "authenticated_entity": logged_in_user,
                    "logged_in_user_account_association": logged_in_user_account_association,
                }
            # user is non-superadmin and non-account-admin here
            logged_in_user_project_association = (
                db.query(models.User_Project)
                .filter(
                    models.User_Project.user_id == logged_in_user.id,
                    models.User_Project.project_id == project_id,
                )
                .first()
            )
            if (
                not logged_in_user_project_association
                or not logged_in_user_project_association.is_admin
            ):
                raise ApiError.forbidden(
                    f"logged-in user - '{logged_in_user.id}' - does not have superadmin privileges or account-admin privileges in account - '{account_id}' - or project-admin privileges in project - '{project_id}' - to view account users with project filter in account - '{account_id}'"
                )

        return {
            "authenticated_entity": logged_in_user,
            "logged_in_user_account_association": logged_in_user_account_association,
        }
    except HTTPException as e:
        db.rollback()
        pprint(
            f"API error in GET /accounts/{account_id}/users - validate_get_account_user_list middleware : {e}"
        )
        raise e
    except SQLAlchemyError as e:
        pprint(
            f"DB error in GET /accounts/{account_id}/users - validate_get_account_user_list middleware : {e}"
        )
        request.state.source_error_msg = str(e)
        raise ApiError.serviceunavailable(
            "The server is currently unavailable, please try again later."
        )
    except Exception as e:
        print(
            f"Unexpected error in GET /accounts/{account_id}/users - validate_get_account_user_list middleware : {e}"
        )
        request.state.source_error_msg = str(e)
        raise ApiError.serviceunavailable(
            "The server is currently unavailable, please try again later."
        )


@auditor.audit(api_namespace=api_schemas.APINamespace.RBAC_API)
async def validate_assign_users_to_account(
    request: Request,
    logged_in_user: models.User = Depends(AccessTokenAuthentication.authenticate),
    account_id: UUID = Path(..., description="The ID of the account"),
) -> dict[str, Any]:
    db: Session = request.state.db
    try:
        # Fetch account by ID
        account = (
            db.query(models.Account).filter(models.Account.id == account_id).first()
        )
        if not account:
            raise ApiError.notfound(f"Account - '{account_id}' - not found")

        # Check if the user is superadmin
        if logged_in_user.is_superadmin:
            return {"authenticated_entity": logged_in_user}

        # Check for User_Account association
        logged_in_user_account_association = (
            db.query(models.User_Account)
            .filter(
                models.User_Account.user_id == logged_in_user.id,
                models.User_Account.account_id == account_id,
            )
            .first()
        )

        if logged_in_user_account_association:
            if logged_in_user_account_association.is_admin:
                return {"authenticated_entity": logged_in_user}

        raise ApiError.forbidden(
            f"logged-in user - '{logged_in_user.id}' - does not have superadmin/account-admin privileges to assign users to account - '{account_id}'"
        )
    except HTTPException as e:
        db.rollback()
        pprint(
            f"API error in POST /accounts/{account_id}/users - validate_assign_users_to_account middleware : {e}"
        )
        raise e
    except SQLAlchemyError as e:
        pprint(
            f"DB error in POST /accounts/{account_id}/users - validate_assign_users_to_account middleware : {e}"
        )
        request.state.source_error_msg = str(e)
        raise ApiError.serviceunavailable(
            "The server is currently unavailable, please try again later."
        )
    except Exception as e:
        print(
            f"Unexpected error in POST /accounts/{account_id}/users - validate_assign_users_to_account middleware : {e}"
        )
        request.state.source_error_msg = str(e)
        raise ApiError.serviceunavailable(
            "The server is currently unavailable, please try again later."
        )


@auditor.audit(api_namespace=api_schemas.APINamespace.RBAC_API)
async def validate_deassign_user_from_account(
    request: Request,
    logged_in_user: models.User = Depends(AccessTokenAuthentication.authenticate),
    account_id: UUID = Path(..., description="The ID of the account"),
    user_id: UUID = Path(..., description="The ID of user to deassign from account"),
) -> dict[str, Any]:
    db: Session = request.state.db
    try:
        # Fetch account by ID
        account = (
            db.query(models.Account).filter(models.Account.id == account_id).first()
        )
        if not account:
            raise ApiError.notfound(f"Account - '{account_id}' - not found")

        # Check if the user is superadmin
        if logged_in_user.is_superadmin:
            return {"authenticated_entity": logged_in_user}

            # Check for User_Account association
        logged_in_user_account_association = (
            db.query(models.User_Account)
            .filter(
                models.User_Account.user_id == logged_in_user.id,
                models.User_Account.account_id == account_id,
            )
            .first()
        )

        if logged_in_user_account_association:
            if logged_in_user_account_association.is_admin:
                return {"authenticated_entity": logged_in_user}

        raise ApiError.forbidden(
            f"logged-in user - '{logged_in_user.id}' - does not have superadmin/account-admin privileges to deassign user from account - '{account_id}'"
        )
    except HTTPException as e:
        db.rollback()
        pprint(
            f"API error in DELETE /accounts/{account_id}/users/{user_id} - validate_deassign_user_from_account middleware : {e}"
        )
        raise e
    except SQLAlchemyError as e:
        pprint(
            f"DB error in DELETE /accounts/{account_id}/users/{user_id} - validate_deassign_user_from_account middleware : {e}"
        )
        request.state.source_error_msg = str(e)
        raise ApiError.serviceunavailable(
            "The server is currently unavailable, please try again later."
        )
    except Exception as e:
        print(
            f"Unexpected error in DELETE /accounts/{account_id}/users/{user_id} - validate_deassign_user_from_account middleware : {e}"
        )
        request.state.source_error_msg = str(e)
        raise ApiError.serviceunavailable(
            "The server is currently unavailable, please try again later."
        )


@auditor.audit(api_namespace=api_schemas.APINamespace.RBAC_API)
async def validate_patch_account_admin_status(
    request: Request,
    logged_in_user: models.User = Depends(AccessTokenAuthentication.authenticate),
    account_id: UUID = Path(..., description="The ID of the account"),
) -> dict[str, Any]:
    db: Session = request.state.db
    try:
        account = (
            db.query(models.Account).filter(models.Account.id == account_id).first()
        )

        if not account:
            raise ApiError.notfound(f"Account - '{account_id}' - not found")

        # Check if the user is superadmin
        if logged_in_user.is_superadmin:
            return {
                "authenticated_entity": logged_in_user,
                "logged_in_user_account_association": None,
            }

            # Check if there's an association between the logged-in user and the account
        logged_in_user_account_association = (
            db.query(models.User_Account)
            .filter(
                models.User_Account.user_id == logged_in_user.id,
                models.User_Account.account_id == account_id,
            )
            .first()
        )

        # Check if the user is an admin of the account
        if (
            logged_in_user_account_association
            and logged_in_user_account_association.is_admin
        ):
            return {
                "authenticated_entity": logged_in_user,
                "logged_in_user_account_association": logged_in_user_account_association,
            }

        raise ApiError.forbidden(
            f"logged-in user - '{logged_in_user.id}' - does not have superadmin/account-admin privileges to update user admin status in account - '{account_id}'"
        )

    except HTTPException as e:
        db.rollback()
        pprint(
            f"API error in PATCH validate_patch_account_admin_status middleware : {e}"
        )
        raise e
    except SQLAlchemyError as e:
        pprint(
            f"DB error in PATCH validate_patch_account_admin_status middleware : {e}"
        )
        request.state.source_error_msg = str(e)
        raise ApiError.serviceunavailable(
            "The server is currently unavailable, please try again later."
        )
    except Exception as e:
        print(
            f"Unexpected error in PATCH validate_patch_account_admin_status middleware : {e}"
        )
        request.state.source_error_msg = str(e)
        raise ApiError.serviceunavailable(
            "The server is currently unavailable, please try again later."
        )

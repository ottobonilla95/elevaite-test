from fastapi import Depends, Path, Depends, HTTPException, Request, Header
from sqlalchemy import exists
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from uuid import UUID
from pprint import pprint
from typing import Any, Type, Optional
from rbac_lib.utils.api_error import ApiError
import os
from rbac_lib.auth.impl import AccessTokenAuthentication

from elevaitelib.orm.db import models
from elevaitelib.schemas import (
    api as api_schemas,
)
from ...rbac_validator.rbac_validator_provider import RBACValidatorProvider
from ....audit import AuditorProvider
import inspect

rbacValidator = RBACValidatorProvider.get_instance()
auditor = AuditorProvider.get_instance()


@auditor.audit(api_namespace=api_schemas.APINamespace.RBAC_API)
async def validate_get_user_profile(
    request: Request,
    logged_in_user: models.User = Depends(AccessTokenAuthentication.authenticate),
    user_id: UUID = Path(..., description="user id of user whose profile is retrieved"),
    account_id: Optional[UUID] = Header(
        None,
        alias="X-elevAIte-AccountId",
        description="account_id under which user profile is queried",
    ),
) -> dict[str, Any]:
    db: Session = request.state.db
    try:
        logged_in_user_admin_accounts_exist = None
        if account_id:
            account = (
                db.query(models.Account).filter(models.Account.id == account_id).first()
            )
            if not account:
                raise ApiError.notfound(f"Account - '{account_id}' - not found")
        elif not logged_in_user.is_superadmin and user_id != logged_in_user.id:
            # Check for any entries in User_Account for the logged-in user where is_admin is true, and the account belongs to the org
            logged_in_user_admin_accounts_exist = (
                db.query(models.User_Account)
                .join(
                    models.Account, models.User_Account.account_id == models.Account.id
                )
                .filter(
                    models.User_Account.user_id == logged_in_user.id,
                    models.User_Account.is_admin,
                    models.Account.organization_id == os.getenv("ORGANIZATION_ID"),
                )
                .first()
            )
            if not logged_in_user_admin_accounts_exist:
                raise ApiError.forbidden(
                    f"logged-in user - '{logged_in_user.id}' - does not have superadmin/account-admin permissions and must provide an account_id to view user profile of other users"
                )

        if (
            not logged_in_user.is_superadmin
            and not logged_in_user_admin_accounts_exist
            and account_id
        ):
            logged_in_user_association = (
                db.query(models.User_Account)
                .filter(
                    models.User_Account.user_id == logged_in_user.id,
                    models.User_Account.account_id == account_id,
                )
                .first()
            )
            if not logged_in_user_association:
                raise ApiError.forbidden(
                    f"logged-in user - '{logged_in_user.id}' - is not assigned to account - '{account_id}'"
                )

        user = db.query(models.User).filter(models.User.id == user_id).first()
        if not user:
            raise ApiError.notfound(f"User - '{user_id}' - not found")

        return {
            "authenticated_entity": logged_in_user,
            "User": user,
        }

    except HTTPException as e:
        db.rollback()
        pprint(
            f"API error in GET /users/{user_id}/profile - validate_get_user_profile middleware: {e}"
        )
        raise e
    except SQLAlchemyError as e:
        pprint(
            f"DB error in GET /users/{user_id}/profile - validate_get_user_profile middleware: {e}"
        )
        request.state.source_error_msg = str(e)
        raise ApiError.serviceunavailable(
            "The server is currently unavailable, please try again later."
        )
    except Exception as e:
        db.rollback()
        print(
            f"Unexpected error in GET /users/{user_id}/profile - validate_get_user_profile middleware: {e}"
        )
        request.state.source_error_msg = str(e)
        raise ApiError.serviceunavailable(
            "The server is currently unavailable, please try again later."
        )


@auditor.audit(api_namespace=api_schemas.APINamespace.RBAC_API)
async def validate_get_user_accounts(
    request: Request,
    user_id: UUID,
    logged_in_user: models.User = Depends(AccessTokenAuthentication.authenticate),
) -> dict[str, Any]:
    db: Session = request.state.db
    try:
        if not logged_in_user.is_superadmin:
            raise ApiError.forbidden(
                f"logged-in user - '{logged_in_user.id}' - does not have superadmin privileges to read user accounts"
            )
        return {"authenticated_entity": logged_in_user}
    except HTTPException as e:
        db.rollback()
        pprint(
            f"API error in GET /users/{user_id}/accounts/ - validate_get_user_accounts middleware : {e}"
        )
        raise e
    except SQLAlchemyError as e:
        pprint(
            f"DB error in GET /users/{user_id}/accounts/ - validate_get_user_accounts middleware : {e}"
        )
        request.state.source_error_msg = str(e)
        raise ApiError.serviceunavailable(
            "The server is currently unavailable, please try again later."
        )
    except Exception as e:
        print(
            f"Unexpected error in GET /users/{user_id}/accounts/ - validate_get_user_accounts middleware : {e}"
        )
        request.state.source_error_msg = str(e)
        raise ApiError.serviceunavailable(
            "The server is currently unavailable, please try again later."
        )


@auditor.audit(api_namespace=api_schemas.APINamespace.RBAC_API)
async def validate_get_user_projects(
    request: Request,
    user_id: UUID,
    account_id: UUID = Header(
        ...,
        alias="X-elevAIte-AccountId",
        description="account_id under which user projects are queried",
    ),
    logged_in_user: models.User = Depends(AccessTokenAuthentication.authenticate),
) -> dict[str, Any]:
    db: Session = request.state.db
    try:
        account_exists = db.query(
            exists().where(models.Account.id == account_id)
        ).scalar()
        if not account_exists:
            raise ApiError.notfound(f"Account - '{account_id}' - not found")

        if logged_in_user.is_superadmin:
            return {"authenticated_entity": logged_in_user}

        logged_in_user_account_association = (
            db.query(models.User_Account)
            .filter(
                models.User_Account.user_id == logged_in_user.id,
                models.User_Account.account_id == account_id,
            )
            .first()
        )
        if (
            logged_in_user_account_association
            and logged_in_user_account_association.is_admin
        ):
            return {"authenticated_entity": logged_in_user}

        raise ApiError.forbidden(
            f"logged-in user - '{logged_in_user.id}' - does not have superadmin or account-admin privileges to read user projects in account - '{account_id}'"
        )
    except HTTPException as e:
        db.rollback()
        pprint(
            f"API error in GET /users/{user_id}/accounts/ - validate_get_user_accounts middleware : {e}"
        )
        raise e
    except SQLAlchemyError as e:
        pprint(
            f"DB error in GET /users/{user_id}/accounts/ - validate_get_user_accounts middleware : {e}"
        )
        request.state.source_error_msg = str(e)
        raise ApiError.serviceunavailable(
            "The server is currently unavailable, please try again later."
        )
    except Exception as e:
        print(
            f"Unexpected error in GET /users/{user_id}/accounts/ - validate_get_user_accounts middleware : {e}"
        )
        request.state.source_error_msg = str(e)
        raise ApiError.serviceunavailable(
            "The server is currently unavailable, please try again later."
        )


@auditor.audit(api_namespace=api_schemas.APINamespace.RBAC_API)
async def validate_patch_user(
    request: Request,
    logged_in_user: models.User = Depends(AccessTokenAuthentication.authenticate),
    user_id: UUID = Path(..., description="The ID of the user to patch"),
) -> dict[str, Any]:
    db: Session = request.state.db
    try:
        user_to_patch = db.query(models.User).filter(models.User.id == user_id).first()
        if not user_to_patch:
            raise ApiError.notfound(f"User - '{user_id}' - not found")

        # Validate if the current user is a superadmin
        if logged_in_user.is_superadmin:
            return {"User": user_to_patch}

        # Check if the current user is trying to patch their own data
        if logged_in_user.id == user_id:
            return {"User": user_to_patch}

        # If the flow reaches here, the user does not have superadmin/account-admin permissions
        raise ApiError.forbidden(
            f"logged-in user - '{logged_in_user.id}' - does not have superadmin privileges to update User - '{user_id}'"
        )
    except HTTPException as e:
        db.rollback()
        pprint(
            f"API error in PATCH: /users/{user_id} - validate_patch_user middleware : {e}"
        )
        raise e
    except SQLAlchemyError as e:
        pprint(
            f"DB error in PATCH: /users/{user_id} - validate_patch_user middleware : {e}"
        )
        request.state.source_error_msg = str(e)
        raise ApiError.serviceunavailable(
            "The server is currently unavailable, please try again later."
        )
    except Exception as e:
        db.rollback()
        print(
            f"Unexpected error in PATCH: /users/{user_id} - validate_patch_user middlware : {e}"
        )
        request.state.source_error_msg = str(e)
        raise ApiError.serviceunavailable(
            "The server is currently unavailable, please try again later."
        )


@auditor.audit(api_namespace=api_schemas.APINamespace.RBAC_API)
async def validate_patch_user_account_roles(
    request: Request,
    logged_in_user: models.User = Depends(AccessTokenAuthentication.authenticate),
    user_id: UUID = Path(..., description="The ID of the user to patch"),
    account_id: UUID = Path(
        ..., description="The ID of the account to scope the user roles to"
    ),
) -> dict[str, Any]:
    db: Session = request.state.db
    try:
        # Check existence of account
        account = (
            db.query(models.Account).filter(models.Account.id == account_id).first()
        )
        if not account:
            raise ApiError.notfound(f"Account - '{account_id}' - not found")

        if not logged_in_user.is_superadmin:
            logged_in_user_account_association = (
                db.query(models.User_Account)
                .filter(
                    models.User_Account.user_id == logged_in_user.id,
                    models.User_Account.account_id == account_id,
                )
                .first()
            )
            if not logged_in_user_account_association:
                raise ApiError.forbidden(
                    f"logged-in user - '{logged_in_user.id}' - does not assigned to account - '{account_id}'"
                )

        # Check existence of user
        user_to_patch = db.query(models.User).filter(models.User.id == user_id).first()
        if not user_to_patch:
            raise ApiError.notfound(f"User - '{user_id}' - not found")

        # Check superadmin
        if logged_in_user.is_superadmin:
            return {"User": user_to_patch}
        # check account admin
        if logged_in_user_account_association.is_admin:
            return {"User": user_to_patch}

        raise ApiError.forbidden(
            f"logged-in user - '{logged_in_user.id}' - does not have superadmin/account-admin privileges to update user-account roles in account - '{account_id}'"
        )
    except HTTPException as e:
        db.rollback()
        pprint(
            f"API error in PATCH /users/{user_id}/accounts/{account_id}/roles validate_patch_user_account_roles middleware: {e}"
        )
        raise e
    except SQLAlchemyError as e:
        db.rollback()
        pprint(
            f"DB error in PATCH /users/{user_id}/accounts/{account_id}/roles validate_patch_user_account_roles middleware: {e}"
        )
        request.state.source_error_msg = str(e)
        raise ApiError.serviceunavailable(
            "The server is currently unavailable, please try again later."
        )
    except Exception as e:
        db.rollback()
        print(
            f"Unexpected error in PATCH /users/{user_id}/accounts/{account_id}/roles validate_patch_user_account_roles middleware: {e}"
        )
        request.state.source_error_msg = str(e)
        raise ApiError.serviceunavailable(
            "The server is currently unavailable, please try again later."
        )


def validate_update_project_permission_overrides_factory(
    target_model_class: Type[models.Base], target_model_action_sequence: tuple[str, ...]
):
    @auditor.audit(api_namespace=api_schemas.APINamespace.RBAC_API)
    async def validate_update_project_permission_overrides(
        request: Request,
        logged_in_user: models.User = Depends(AccessTokenAuthentication.authenticate),
        user_id: UUID = Path(
            ...,
            description="The ID of the user to update project-specific permission-overrides for",
        ),
        project_id: UUID = Path(
            ...,
            description="The ID of the project to update user-specific permission-overrides on",
        ),
    ) -> dict[str, Any]:
        db: Session = request.state.db
        try:
            # Set the context flags in request.state
            current_frame = inspect.currentframe()
            if current_frame and current_frame.f_locals:
                frame_locals = current_frame.f_locals
                request.state.account_context_exists = "account_id" in frame_locals
                request.state.project_context_exists = "project_id" in frame_locals
            else:
                request.state.account_context_exists = False
                request.state.project_context_exists = False

            validation_info: dict[str, Any] = (
                await rbacValidator.validate_rbac_permissions(
                    request=request,
                    db=db,
                    target_model_action_sequence=target_model_action_sequence,
                    authenticated_entity=logged_in_user,
                    target_model_class=target_model_class,
                )
            )

            if logged_in_user:
                if logged_in_user.is_superadmin:
                    return validation_info

            logged_in_user_account_association = validation_info.get(
                "logged_in_entity_account_association", None
            )

            if logged_in_user_account_association:
                if logged_in_user_account_association.is_admin:
                    return validation_info

            logged_in_user_project_association = validation_info.get(
                "logged_in_entity_project_association", None
            )

            if logged_in_user_project_association:
                if logged_in_user_project_association.is_admin:
                    return validation_info

            raise ApiError.forbidden(
                f"logged-in user - '{logged_in_user.id}' - does not have superadmin,admin or project association with project-admin privileges to update project permission overrides for user - '{user_id}' - in project - '{project_id}'"
            )

        except HTTPException as e:
            db.rollback()
            pprint(
                f"API error in PATCH users/{user_id}/projects/{project_id}/permission-overrides - validate_update_project_permission_overrides middleware: {e}"
            )
            raise e
        except SQLAlchemyError as e:
            db.rollback()
            pprint(
                f"DB error in PATCH users/{user_id}/projects/{project_id}/permission-overrides - validate_update_project_permission_overrides middleware: {e}"
            )
            request.state.source_error_msg = str(e)
            raise ApiError.serviceunavailable(
                "The server is currently unavailable, please try again later."
            )
        except Exception as e:
            db.rollback()
            print(
                f"Unexpected error in PATCH users/{user_id}/projects/{project_id}/permission-overrides - validate_update_project_permission_overrides middleware: {e}"
            )
            request.state.source_error_msg = str(e)
            raise ApiError.serviceunavailable(
                "The server is currently unavailable, please try again later."
            )

    return validate_update_project_permission_overrides


def validate_get_project_permission_overrides_factory(
    target_model_class: Type[models.Base], target_model_action_sequence: tuple[str, ...]
):
    @auditor.audit(api_namespace=api_schemas.APINamespace.RBAC_API)
    async def validate_get_project_permission_overrides(
        request: Request,
        logged_in_user: models.User = Depends(AccessTokenAuthentication.authenticate),
        user_id: UUID = Path(
            ...,
            description="The ID of the user to get project-specific permission-overrides for",
        ),
        project_id: UUID = Path(
            ...,
            description="The ID of the project to get user-specific permission-overrides for",
        ),
    ) -> dict[str, Any]:
        db: Session = request.state.db
        try:
            # Set the context flags in request.state
            current_frame = inspect.currentframe()
            if current_frame and current_frame.f_locals:
                frame_locals = current_frame.f_locals
                request.state.account_context_exists = "account_id" in frame_locals
                request.state.project_context_exists = "project_id" in frame_locals
            else:
                request.state.account_context_exists = False
                request.state.project_context_exists = False

            validation_info: dict[str, Any] = (
                await rbacValidator.validate_rbac_permissions(
                    request=request,
                    db=db,
                    target_model_action_sequence=target_model_action_sequence,
                    authenticated_entity=logged_in_user,
                    target_model_class=target_model_class,
                )
            )

            if logged_in_user:
                if logged_in_user.is_superadmin or logged_in_user.id == user_id:
                    return validation_info

            logged_in_user_account_association = validation_info.get(
                "logged_in_entity_account_association", None
            )

            if logged_in_user_account_association:
                if logged_in_user_account_association.is_admin:
                    return validation_info

            logged_in_user_project_association = validation_info.get(
                "logged_in_entity_project_association", None
            )

            if logged_in_user_project_association:
                if logged_in_user_project_association.is_admin:
                    return validation_info

            raise ApiError.forbidden(
                f"logged-in user - '{logged_in_user.id}' - does not have superadmin,admin or project association with project-admin privileges to read project permission overrides for user - '{user_id}' - in project - '{project_id}'"
            )
        except HTTPException as e:
            db.rollback()
            pprint(
                f"API error in GET users/{user_id}/projects/{project_id}/permission-overrides - validate_get_project_permission_overrides middleware: {e}"
            )
            raise e
        except SQLAlchemyError as e:
            db.rollback()
            pprint(
                f"DB error in GET users/{user_id}/projects/{project_id}/permission-overrides - validate_get_project_permission_overrides middleware: {e}"
            )
            request.state.source_error_msg = str(e)
            raise ApiError.serviceunavailable(
                "The server is currently unavailable, please try again later."
            )
        except Exception as e:
            db.rollback()
            print(
                f"Unexpected error in GET users/{user_id}/projects/{project_id}/permission-overrides - validate_get_project_permission_overrides middleware: {e}"
            )
            request.state.source_error_msg = str(e)
            raise ApiError.serviceunavailable(
                "The server is currently unavailable, please try again later."
            )

    return validate_get_project_permission_overrides


@auditor.audit(api_namespace=api_schemas.APINamespace.RBAC_API)
async def validate_patch_user_superadmin_status(
    request: Request,
    logged_in_user: models.User = Depends(AccessTokenAuthentication.authenticate),
    user_id: UUID = Path(...),
) -> dict[str, Any]:
    db: Session = request.state.db
    try:
        # Check if the user is superadmin
        if not logged_in_user.is_superadmin:
            raise ApiError.forbidden(
                f"logged-in user - '{logged_in_user.id}' - does not have superadmin privileges to update user superadmin status"
            )

        return {"authenticated_entity": logged_in_user}
    except HTTPException as e:
        db.rollback()
        pprint(
            f"API error in PATCH /users/{user_id}/superadmin - validate_update_user_superadmin_status middleware: {e}"
        )
        raise e
    except SQLAlchemyError as e:
        db.rollback()
        pprint(
            f"DB error in PATCH /users/{user_id}/superadmin - validate_update_user_superadmin_status middleware: {e}"
        )
        request.state.source_error_msg = str(e)
        raise ApiError.serviceunavailable(
            "The server is currently unavailable, please try again later."
        )
    except Exception as e:
        db.rollback()
        print(
            f"Unexpected error in PATCH /users/{user_id}/superadmin - validate_update_user_superadmin_status middleware: {e}"
        )
        request.state.source_error_msg = str(e)
        raise ApiError.serviceunavailable(
            "The server is currently unavailable, please try again later."
        )

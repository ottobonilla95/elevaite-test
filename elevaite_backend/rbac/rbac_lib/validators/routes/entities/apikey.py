from fastapi import Depends, HTTPException, Header, Request, Path, Body
from uuid import UUID
from rbac_lib.auth.impl import AccessTokenAuthentication
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from pprint import pprint
from typing import Any, Type
from rbac_api.app.errors.api_error import ApiError

from rbac_lib.utils.deps import get_db
from elevaitelib.orm.db import models
from elevaitelib.schemas import (
    apikey as apikey_schemas,
    api as api_schemas,
)
from ...rbac_validator.rbac_validator_provider import RBACValidatorProvider
from ....audit import AuditorProvider
import inspect

rbacValidator = RBACValidatorProvider.get_instance()
auditor = AuditorProvider.get_instance()


def validate_create_apikey_factory(
    target_model_class: Type[models.Base], target_model_action_sequence: tuple[str, ...]
):
    @auditor.audit(api_namespace=api_schemas.APINamespace.RBAC_API)
    async def validate_create_apikey(
        request: Request,
        # The params below are required for pydantic validation even when unused
        project_id: UUID = Path(
            ..., description="The ID of the project under which apikey is created"
        ),
        authenticated_entity: models.User = Depends(
            AccessTokenAuthentication.authenticate
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

            return await rbacValidator.validate_rbac_permissions(
                request=request,
                db=db,
                target_model_action_sequence=target_model_action_sequence,
                authenticated_entity=authenticated_entity,
                target_model_class=target_model_class,
            )
        except HTTPException as e:
            db.rollback()
            pprint(
                f"API error in POST /apikeys/ - validate_create_apikey middleware : {e}"
            )
            raise e
        except SQLAlchemyError as e:
            db.rollback()
            pprint(f"DB error in POST /apikeys/ validate_create_apikey middleware: {e}")
            request.state.source_error_msg = str(e)
            raise ApiError.serviceunavailable(
                "The server is currently unavailable, please try again later."
            )
        except Exception as e:
            db.rollback()
            print(
                f"Unexpected error in POST /apikeys/ - validate_create_apikey middleware : {e}"
            )
            request.state.source_error_msg = str(e)
            raise ApiError.serviceunavailable(
                "The server is currently unavailable, please try again later."
            )

    return validate_create_apikey


def validate_get_apikeys_factory(
    target_model_class: Type[models.Base], target_model_action_sequence: tuple[str, ...]
):
    @auditor.audit(api_namespace=api_schemas.APINamespace.RBAC_API)
    async def validate_get_apikeys(
        request: Request,
        # The params below are required for pydantic validation even when unused
        project_id: UUID = Path(
            ..., description="The ID of the project under which apikeys are read"
        ),
        authenticated_entity: models.User = Depends(
            AccessTokenAuthentication.authenticate
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

            return await rbacValidator.validate_rbac_permissions(
                request=request,
                db=db,
                target_model_action_sequence=target_model_action_sequence,
                authenticated_entity=authenticated_entity,
                target_model_class=target_model_class,
            )
        except HTTPException as e:
            db.rollback()
            pprint(
                f"API error in GET /apikeys/ - validate_get_apikeys middleware : {e}"
            )
            raise e
        except SQLAlchemyError as e:
            db.rollback()
            pprint(f"DB error in GET /apikeys/ validate_get_apikeys middleware: {e}")
            request.state.source_error_msg = str(e)
            raise ApiError.serviceunavailable(
                "The server is currently unavailable, please try again later."
            )
        except Exception as e:
            db.rollback()
            print(
                f"Unexpected error in GET /apikeys/ - validate_get_apikeys middleware : {e}"
            )
            request.state.source_error_msg = str(e)
            raise ApiError.serviceunavailable(
                "The server is currently unavailable, please try again later."
            )

    return validate_get_apikeys


def validate_get_apikey_factory(
    target_model_class: Type[models.Base], target_model_action_sequence: tuple[str, ...]
):
    @auditor.audit(api_namespace=api_schemas.APINamespace.RBAC_API)
    async def validate_get_apikey(
        request: Request,
        apikey_id: UUID = Path(..., description="id of apikey to retrieve"),
        # The params below are required for pydantic validation even when unused
        project_id: UUID = Path(
            ..., description="The ID of the project under which apikey is read"
        ),
        logged_in_user: models.User = Depends(AccessTokenAuthentication.authenticate),
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

            apikey: models.Apikey = validation_info["Apikey"]

            if logged_in_user.is_superadmin:
                return validation_info

            logged_in_user_account_association = validation_info.get(
                "logged_in_entity_account_association", None
            )
            logged_in_user_project_association = validation_info.get(
                "logged_in_entity_project_association", None
            )

            if (
                logged_in_user_account_association
                and logged_in_user_account_association.is_admin
            ) or (
                logged_in_user_project_association
                and logged_in_user_project_association.is_admin
            ):
                return validation_info

            if apikey.creator_id != logged_in_user.id:
                raise ApiError.forbidden(
                    f"logged-in user - '{logged_in_user.id}' - does not have superadmin/account-admin/project-admin privileges to read api keys that were created by other users in the project"
                )

            return validation_info
        except HTTPException as e:
            db.rollback()
            pprint(
                f"API error in GET /apikeys/{apikey_id} - validate_get_apikey middleware : {e}"
            )
            raise e
        except SQLAlchemyError as e:
            db.rollback()
            pprint(
                f"DB error in GET /apikeys/{apikey_id} validate_get_apikey middleware: {e}"
            )
            request.state.source_error_msg = str(e)
            raise ApiError.serviceunavailable(
                "The server is currently unavailable, please try again later."
            )
        except Exception as e:
            db.rollback()
            print(
                f"Unexpected error in GET /apikeys/{apikey_id} - validate_get_apikey middleware : {e}"
            )
            request.state.source_error_msg = str(e)
            raise ApiError.serviceunavailable(
                "The server is currently unavailable, please try again later."
            )

    return validate_get_apikey


def validate_delete_apikey_factory(
    target_model_class: Type[models.Base], target_model_action_sequence: tuple[str, ...]
):
    @auditor.audit(api_namespace=api_schemas.APINamespace.RBAC_API)
    async def validate_delete_apikey(
        request: Request,
        apikey_id: UUID = Path(..., description="id of apikey to delete"),
        # The params below are required for pydantic validation even when unused
        project_id: UUID = Path(
            ..., description="The ID of the project under which apikey is deleted"
        ),
        logged_in_user: models.User = Depends(AccessTokenAuthentication.authenticate),
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

            apikey: models.Apikey = validation_info["Apikey"]

            if logged_in_user.is_superadmin:
                return validation_info

            logged_in_user_account_association = validation_info.get(
                "logged_in_entity_account_association", None
            )
            logged_in_user_project_association = validation_info.get(
                "logged_in_entity_project_association", None
            )

            if (
                logged_in_user_account_association
                and logged_in_user_account_association.is_admin
            ) or (
                logged_in_user_project_association
                and logged_in_user_project_association.is_admin
            ):
                return validation_info

            if apikey.creator_id != logged_in_user.id:
                raise ApiError.forbidden(
                    f"logged-in user - '{logged_in_user.id}' - does not have superadmin/account-admin/project-admin privileges to revoke api keys that were created by other users"
                )

            return validation_info
        except HTTPException as e:
            db.rollback()
            pprint(
                f"API error in DELETE /apikeys/{apikey_id} - validate_delete_apikey middleware : {e}"
            )
            raise e
        except SQLAlchemyError as e:
            db.rollback()
            pprint(
                f"DB error in DELETE /apikeys/{apikey_id} validate_delete_apikey middleware: {e}"
            )
            request.state.source_error_msg = str(e)
            raise ApiError.serviceunavailable(
                "The server is currently unavailable, please try again later."
            )
        except Exception as e:
            db.rollback()
            print(
                f"Unexpected error in DELETE /apikeys/{apikey_id} - validate_delete_apikey middleware : {e}"
            )
            request.state.source_error_msg = str(e)
            raise ApiError.serviceunavailable(
                "The server is currently unavailable, please try again later."
            )

    return validate_delete_apikey

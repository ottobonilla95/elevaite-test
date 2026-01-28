from fastapi import Path, Depends, Request, HTTPException
from uuid import UUID
from rbac_lib.auth.impl import AccessTokenOrApikeyAuthentication
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from rbac_lib.utils.api_error import ApiError
from pprint import pprint
from typing import Any, Type, Callable, Coroutine

from elevaitelib.orm.db import models
from elevaitelib.schemas import (
    api as api_schemas,
)
from ...rbac_validator.rbac_validator_provider import RBACValidatorProvider
from ....audit import AuditorProvider
import inspect

rbacValidator = RBACValidatorProvider.get_instance()
auditor = AuditorProvider.get_instance()


def validate_get_project_collections_factory(
    target_model_class: Type[models.Base], target_model_action_sequence: tuple[str, ...]
) -> Callable[..., Coroutine[Any, Any, dict[str, Any]]]:
    @auditor.audit(api_namespace=api_schemas.APINamespace.RBAC_API)
    async def validate_get_project_collections(
        request: Request,
        authenticated_entity: models.User | models.Apikey = Depends(
            AccessTokenOrApikeyAuthentication.authenticate
        ),
        project_id: UUID = Path(
            ..., description="project_id under which project collections are queried"
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
                f"API error in GET /project/{project_id}/collection - validate_get_project_collections middleware : {e}"
            )
            raise e
        except SQLAlchemyError as e:
            pprint(
                f"DB error in GET /project/{project_id}/collection - validate_get_project_collections middleware : {e}"
            )
            request.state.source_error_msg = str(e)
            raise ApiError.serviceunavailable(
                "The server is currently unavailable, please try again later."
            )
        except Exception as e:
            db.rollback()
            print(
                f"Unexpected error in GET /project/{project_id}/collection - validate_get_project_collections middleware : {e}"
            )
            request.state.source_error_msg = str(e)
            raise ApiError.serviceunavailable(
                "The server is currently unavailable, please try again later."
            )

    return validate_get_project_collections


def validate_get_project_collection_factory(
    target_model_class: Type[models.Base], target_model_action_sequence: tuple[str, ...]
) -> Callable[..., Coroutine[Any, Any, dict[str, Any]]]:
    @auditor.audit(api_namespace=api_schemas.APINamespace.RBAC_API)
    async def validate_get_project_collection(
        request: Request,
        authenticated_entity: models.User | models.Apikey = Depends(
            AccessTokenOrApikeyAuthentication.authenticate
        ),
        project_id: UUID = Path(
            ..., description="project_id under which collection is queried"
        ),
        collection_id: UUID = Path(..., description=" id of collection being queried"),
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
                f"API error in GET /project/{project_id}/collection/{collection_id} - validate_get_project_collection middleware : {e}"
            )
            raise e
        except SQLAlchemyError as e:
            pprint(
                f"DB error in GET /project/{project_id}/collection/{collection_id} - validate_get_project_collection middleware : {e}"
            )
            request.state.source_error_msg = str(e)
            raise ApiError.serviceunavailable(
                "The server is currently unavailable, please try again later."
            )
        except Exception as e:
            db.rollback()
            print(
                f"Unexpected error in GET /project/{project_id}/collection/{collection_id} - validate_get_project_collection middleware : {e}"
            )
            request.state.source_error_msg = str(e)
            raise ApiError.serviceunavailable(
                "The server is currently unavailable, please try again later."
            )

    return validate_get_project_collection


def validate_get_project_collection_scroll_factory(
    target_model_class: Type[models.Base], target_model_action_sequence: tuple[str, ...]
) -> Callable[..., Coroutine[Any, Any, dict[str, Any]]]:
    @auditor.audit(api_namespace=api_schemas.APINamespace.RBAC_API)
    async def validate_get_project_collection_scroll(
        request: Request,
        authenticated_entity: models.User | models.Apikey = Depends(
            AccessTokenOrApikeyAuthentication.authenticate
        ),
        project_id: UUID = Path(
            ..., description="project_id under which collection scroll is queried"
        ),
        collection_id: UUID = Path(..., description=" id of collection being queried"),
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
                f"API error in GET /project/{project_id}/collection/{collection_id}/scroll - validate_get_project_collection_scroll middleware : {e}"
            )
            raise e
        except SQLAlchemyError as e:
            pprint(
                f"DB error in GET /project/{project_id}/collection/{collection_id}/scroll - validate_get_project_collection_scroll middleware : {e}"
            )
            request.state.source_error_msg = str(e)
            raise ApiError.serviceunavailable(
                "The server is currently unavailable, please try again later."
            )
        except Exception as e:
            db.rollback()
            print(
                f"Unexpected error in GET /project/{project_id}/collection/{collection_id}/scroll - validate_get_project_collection_scroll middleware : {e}"
            )
            request.state.source_error_msg = str(e)
            raise ApiError.serviceunavailable(
                "The server is currently unavailable, please try again later."
            )

    return validate_get_project_collection_scroll


def validate_create_project_collection_factory(
    target_model_class: Type[models.Base], target_model_action_sequence: tuple[str, ...]
) -> Callable[..., Coroutine[Any, Any, dict[str, Any]]]:
    @auditor.audit(api_namespace=api_schemas.APINamespace.RBAC_API)
    async def validate_create_project_collection(
        request: Request,
        authenticated_entity: models.User | models.Apikey = Depends(
            AccessTokenOrApikeyAuthentication.authenticate
        ),
        project_id: UUID = Path(
            ..., description="project_id under which dataset is tagged"
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
                f"API error in POST /project/{project_id}/collection - validate_create_project_collection middleware : {e}"
            )
            raise e
        except SQLAlchemyError as e:
            pprint(
                f"DB error in POST /project/{project_id}/collection - validate_create_project_collection middleware : {e}"
            )
            request.state.source_error_msg = str(e)
            raise ApiError.serviceunavailable(
                "The server is currently unavailable, please try again later."
            )
        except Exception as e:
            db.rollback()
            print(
                f"Unexpected error in POST /project/{project_id}/collection - validate_create_project_collection middleware : {e}"
            )
            request.state.source_error_msg = str(e)
            raise ApiError.serviceunavailable(
                "The server is currently unavailable, please try again later."
            )

    return validate_create_project_collection

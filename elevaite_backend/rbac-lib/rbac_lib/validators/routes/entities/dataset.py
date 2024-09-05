from fastapi import Path, Depends, Header, Request, HTTPException, Request
from uuid import UUID

from rbac_lib.auth.impl import AccessTokenOrApikeyAuthentication
from sqlalchemy import exists
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from rbac_lib.utils.deps import get_db
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


def validate_get_project_datasets_factory(
    target_model_class: Type[models.Base], target_model_action_sequence: tuple[str, ...]
) -> Callable[..., Coroutine[Any, Any, dict[str, Any]]]:
    @auditor.audit(api_namespace=api_schemas.APINamespace.RBAC_API)
    async def validate_get_project_datasets(
        request: Request,
        authenticated_entity: models.User | models.Apikey = Depends(
            AccessTokenOrApikeyAuthentication.authenticate
        ),
        project_id: UUID = Path(
            ..., description="project_id under which project datasets are queried"
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
                f"API error in GET /project/{project_id}/datasets - validate_get_project_datasets middleware : {e}"
            )
            raise e
        except SQLAlchemyError as e:
            pprint(
                f"DB error in GET /project/{project_id}/datasets - validate_get_project_datasets middleware : {e}"
            )
            request.state.source_error_msg = str(e)
            raise ApiError.serviceunavailable(
                "The server is currently unavailable, please try again later."
            )
        except Exception as e:
            db.rollback()
            print(
                f"Unexpected error in GET /project/{project_id}/datasets - validate_get_project_datasets middleware : {e}"
            )
            request.state.source_error_msg = str(e)
            raise ApiError.serviceunavailable(
                "The server is currently unavailable, please try again later."
            )

    return validate_get_project_datasets


def validate_get_project_dataset_factory(
    target_model_class: Type[models.Base], target_model_action_sequence: tuple[str, ...]
) -> Callable[..., Coroutine[Any, Any, dict[str, Any]]]:
    @auditor.audit(api_namespace=api_schemas.APINamespace.RBAC_API)
    async def validate_get_project_dataset(
        request: Request,
        authenticated_entity: models.User | models.Apikey = Depends(
            AccessTokenOrApikeyAuthentication.authenticate
        ),
        project_id: UUID = Path(
            ..., description="project_id under which dataset is queried"
        ),
        dataset_id: UUID = Path(..., description=" id of dataset being queried"),
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
                f"API error in GET /project/{project_id}/datasets/{dataset_id} - validate_get_project_dataset middleware : {e}"
            )
            raise e
        except SQLAlchemyError as e:
            pprint(
                f"DB error in GET /project/{project_id}/datasets/{dataset_id} - validate_get_project_dataset middleware : {e}"
            )
            request.state.source_error_msg = str(e)
            raise ApiError.serviceunavailable(
                "The server is currently unavailable, please try again later."
            )
        except Exception as e:
            db.rollback()
            print(
                f"Unexpected error in GET /project/{project_id}/datasets/{dataset_id} - validate_get_project_dataset middleware : {e}"
            )
            request.state.source_error_msg = str(e)
            raise ApiError.serviceunavailable(
                "The server is currently unavailable, please try again later."
            )

    return validate_get_project_dataset


def validate_add_tag_to_dataset_factory(
    target_model_class: Type[models.Base], target_model_action_sequence: tuple[str, ...]
) -> Callable[..., Coroutine[Any, Any, dict[str, Any]]]:
    @auditor.audit(api_namespace=api_schemas.APINamespace.RBAC_API)
    async def validate_add_tag_to_dataset(
        request: Request,
        authenticated_entity: models.User | models.Apikey = Depends(
            AccessTokenOrApikeyAuthentication.authenticate
        ),
        project_id: UUID = Path(
            ..., description="project_id under which dataset is tagged"
        ),
        dataset_id: UUID = Path(..., description=" id of dataset being queried"),
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
                f"API error in POST /project/{project_id}/datasets/{dataset_id}/tags - validate_add_tag_to_dataset middleware : {e}"
            )
            raise e
        except SQLAlchemyError as e:
            pprint(
                f"DB error in POST /project/{project_id}/datasets/{dataset_id}/tags - validate_add_tag_to_dataset middleware : {e}"
            )
            request.state.source_error_msg = str(e)
            raise ApiError.serviceunavailable(
                "The server is currently unavailable, please try again later."
            )
        except Exception as e:
            db.rollback()
            print(
                f"Unexpected error in POST /project/{project_id}/datasets/{dataset_id}/tags - validate_add_tag_to_dataset middleware : {e}"
            )
            request.state.source_error_msg = str(e)
            raise ApiError.serviceunavailable(
                "The server is currently unavailable, please try again later."
            )

    return validate_add_tag_to_dataset

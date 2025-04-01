from fastapi import Path, Depends, Header, Query, Request, HTTPException
from uuid import UUID
from sqlalchemy import or_, and_
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from rbac_lib.utils.deps import get_db
from rbac_lib.utils.api_error import ApiError
from pprint import pprint
from typing import Any, Optional, Type, Callable, Dict

from elevaitelib.orm.db import models
from elevaitelib.schemas import (
    application as application_schemas,
    api as api_schemas,
)
from rbac_lib.auth.impl import AccessTokenOrApikeyAuthentication
from ...rbac_validator.rbac_validator_provider import RBACValidatorProvider
from ....audit import AuditorProvider
import inspect

rbacValidator = RBACValidatorProvider.get_instance()
auditor = AuditorProvider.get_instance()


def validate_get_pipelines_factory(
    target_model_class: Type[models.Base], target_model_action_sequence: tuple[str, ...]
):
    @auditor.audit(api_namespace=api_schemas.APINamespace.RBAC_API)
    async def validate_get_pipelines(
        request: Request,
        authenticated_entity: models.User | models.Apikey = Depends(
            AccessTokenOrApikeyAuthentication.authenticate
        ),
        # The params below are required for pydantic and rbac validation even when unused
        project_id: UUID = Header(
            ...,
            alias="X-elevAIte-ProjectId",
            description="project_id under which connector instances are queried",
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
                f"API error in GET /pipeline - validate_get_pipelines middleware : {e}"
            )
            raise e
        except SQLAlchemyError as e:
            pprint(
                f"DB error in GET /pipeline - validate_get_pipelines middleware : {e}"
            )
            request.state.source_error_msg = str(e)
            raise ApiError.serviceunavailable(
                "The server is currently unavailable, please try again later."
            )
        except Exception as e:
            db.rollback()
            print(
                f"Unexpected error in GET /pipeline - validate_get_pipelines middleware : {e}"
            )
            request.state.source_error_msg = str(e)
            raise ApiError.serviceunavailable(
                "The server is currently unavailable, please try again later."
            )

    return validate_get_pipelines


def validate_get_pipeline_factory(
    target_model_class: Type[models.Base], target_model_action_sequence: tuple[str, ...]
):
    @auditor.audit(api_namespace=api_schemas.APINamespace.RBAC_API)
    async def validate_get_pipeline(
        request: Request,
        authenticated_entity: models.User | models.Apikey = Depends(
            AccessTokenOrApikeyAuthentication.authenticate
        ),
        # The params below are required for pydantic and rbac validation even when unused
        project_id: UUID = Header(
            ...,
            alias="X-elevAIte-ProjectId",
            description="project_id under which pipeline is queried",
        ),
        pipeline_id: str = Path(..., description="id of pipeline to be retrieved"),
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
                f"API error in GET /pipeline/{pipeline_id} - validate_get_pipeline middleware : {e}"
            )
            raise e
        except SQLAlchemyError as e:
            pprint(
                f"DB error in GET /pipeline/{pipeline_id} - validate_get_pipeline middleware : {e}"
            )
            request.state.source_error_msg = str(e)
            raise ApiError.serviceunavailable(
                "The server is currently unavailable, please try again later."
            )
        except Exception as e:
            db.rollback()
            print(
                f"Unexpected error in GET /pipeline/{pipeline_id} - validate_get_pipeline middleware : {e}"
            )
            request.state.source_error_msg = str(e)
            raise ApiError.serviceunavailable(
                "The server is currently unavailable, please try again later."
            )

    return validate_get_pipeline


def validate_create_pipeline_factory(
    target_model_class: Type[models.Base], target_model_action_sequence: tuple[str, ...]
):
    @auditor.audit(api_namespace=api_schemas.APINamespace.RBAC_API)
    async def validate_create_pipeline(
        request: Request,
        authenticated_entity: models.User | models.Apikey = Depends(
            AccessTokenOrApikeyAuthentication.authenticate
        ),
        # The params below are required for pydantic and rbac validation even when unused
        project_id: UUID = Header(
            ...,
            alias="X-elevAIte-ProjectId",
            description="project_id under which connector instance logs are queried",
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
                f"API error in POST /pipeline - validate_create_pipeline middleware : {e}"
            )
            raise e
        except SQLAlchemyError as e:
            pprint(
                f"DB error in POST /pipeline - validate_create_pipeline middleware : {e}"
            )
            request.state.source_error_msg = str(e)
            raise ApiError.serviceunavailable(
                "The server is currently unavailable, please try again later."
            )
        except Exception as e:
            db.rollback()
            print(
                f"Unexpected error in POST /pipeline - validate_create_pipeline middleware : {e}"
            )
            request.state.source_error_msg = str(e)
            raise ApiError.serviceunavailable(
                "The server is currently unavailable, please try again later."
            )

    return validate_create_pipeline


pipelines_map = {
    (
        api_schemas.APINamespace.ETL_API,
        "getPipelines",
    ): validate_get_pipelines_factory(models.Pipeline, ("READ",)),
    (
        api_schemas.APINamespace.ETL_API,
        "getPipelineById",
    ): validate_get_pipeline_factory(models.Pipeline, ("READ",)),
    (
        api_schemas.APINamespace.ETL_API,
        "registerFlytePipeline",
    ): validate_create_pipeline_factory(models.Pipeline, ("CREATE",)),
}

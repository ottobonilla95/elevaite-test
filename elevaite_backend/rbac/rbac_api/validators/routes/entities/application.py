from fastapi import Path, Depends, Header, Query, Request, HTTPException
from uuid import UUID
from sqlalchemy import or_, and_
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from rbac_api.utils.deps import get_db
from rbac_api.app.errors.api_error import ApiError
from pprint import pprint
from typing import Any, Optional, Type, Callable, Dict

from elevaitelib.orm.db import models
from elevaitelib.schemas import (
    application as application_schemas,
    api as api_schemas,
)
from rbac_api.auth.impl import AccessTokenAuthentication
from ...rbac_validator.rbac_validator_provider import RBACValidatorProvider
from ....audit import AuditorProvider
import inspect

rbacValidator = RBACValidatorProvider.get_instance()
auditor = AuditorProvider.get_instance()


def validate_get_application_factory(
    target_model_class: Type[models.Base], target_model_action_sequence: tuple[str, ...]
):
    @auditor.audit(api_namespace=api_schemas.APINamespace.RBAC_API)
    async def validate_get_application(
        request: Request,
        authenticated_entity: models.User = Depends(
            AccessTokenAuthentication.authenticate
        ),
        # The params below are required for pydantic and rbac validation even when unused
        account_id: UUID = Header(
            ...,
            alias="X-elevAIte-AccountId",
            description="account_id under which connector application is queried",
        ),
        application_id: int = Path(
            ..., description="id of connector application to be retrieved"
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
                f"API error in GET /application/{application_id} - validate_get_connector middleware : {e}"
            )
            raise e
        except SQLAlchemyError as e:
            pprint(
                f"DB error in GET /application/{application_id} - validate_get_connector middleware : {e}"
            )
            request.state.source_error_msg = str(e)
            raise ApiError.serviceunavailable(
                "The server is currently unavailable, please try again later."
            )
        except Exception as e:
            db.rollback()
            print(
                f"Unexpected error in GET /application/{application_id} - validate_get_connector middleware : {e}"
            )
            request.state.source_error_msg = str(e)
            raise ApiError.serviceunavailable(
                "The server is currently unavailable, please try again later."
            )

    return validate_get_application


def validate_get_applications_factory(
    target_model_class: Type[models.Base], target_model_action_sequence: tuple[str, ...]
):
    @auditor.audit(api_namespace=api_schemas.APINamespace.RBAC_API)
    async def validate_get_applications(
        request: Request,
        authenticated_entity: models.User = Depends(
            AccessTokenAuthentication.authenticate
        ),
        # The params below are required for pydantic and rbac validation even when unused
        account_id: UUID = Header(
            ...,
            alias="X-elevAIte-AccountId",
            description="account_id under which connectors are queried",
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
                f"API error in GET /application - validate_get_connectors middleware : {e}"
            )
            raise e
        except SQLAlchemyError as e:
            pprint(
                f"DB error in GET /application - validate_get_connectors middleware : {e}"
            )
            request.state.source_error_msg = str(e)
            raise ApiError.serviceunavailable(
                "The server is currently unavailable, please try again later."
            )
        except Exception as e:
            db.rollback()
            print(
                f"Unexpected error in GET /application - validate_get_connectors middleware : {e}"
            )
            request.state.source_error_msg = str(e)
            raise ApiError.serviceunavailable(
                "The server is currently unavailable, please try again later."
            )

    return validate_get_applications


def validate_get_application_pipelines_factory(
    target_model_class: Type[models.Base], target_model_action_sequence: tuple[str, ...]
):
    @auditor.audit(api_namespace=api_schemas.APINamespace.RBAC_API)
    async def validate_get_application_pipelines(
        request: Request,
        authenticated_entity: models.User = Depends(
            AccessTokenAuthentication.authenticate
        ),
        # The params below are required for pydantic and rbac validation even when unused
        account_id: UUID = Header(
            ...,
            alias="X-elevAIte-AccountId",
            description="account_id under which connector pipelines are queried",
        ),
        application_id: int = Path(..., description="id of connector application"),
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
                f"API error in GET /application/{application_id}/pipelines - validate_get_connector_pipelines middleware : {e}"
            )
            raise e
        except SQLAlchemyError as e:
            pprint(
                f"DB error in GET /application/{application_id}/pipelines - validate_get_connector_pipelines middleware : {e}"
            )
            request.state.source_error_msg = str(e)
            raise ApiError.serviceunavailable(
                "The server is currently unavailable, please try again later."
            )
        except Exception as e:
            db.rollback()
            print(
                f"Unexpected error in GET /application/{application_id}/pipelines - validate_get_connector_pipelines middleware : {e}"
            )
            request.state.source_error_msg = str(e)
            raise ApiError.serviceunavailable(
                "The server is currently unavailable, please try again later."
            )

    return validate_get_application_pipelines

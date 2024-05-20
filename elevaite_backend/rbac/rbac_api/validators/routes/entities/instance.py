from fastapi import Path, Depends, Header, Query, Request, HTTPException
from uuid import UUID
from sqlalchemy import or_, and_
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from rbac_api.utils.deps import get_db
from rbac_api.app.errors.api_error import ApiError
from pprint import pprint
from typing import Any, Optional, Type, Callable, Dict

from elevaitedb.db import models
from elevaitedb.schemas import (
    application as application_schemas,
    api as api_schemas,
)
from rbac_api.auth.impl import AccessTokenOrApikeyAuthentication
from ...rbac_validator.rbac_validator_provider import RBACValidatorProvider
from ....audit import AuditorProvider
import inspect

rbacValidator = RBACValidatorProvider.get_instance()
auditor = AuditorProvider.get_instance()


def validate_get_application_instances_factory(
    target_model_class: Type[models.Base], target_model_action_sequence: tuple[str, ...]
):
    @auditor.audit(api_namespace=api_schemas.APINamespace.RBAC_API)
    async def validate_get_application_instances(
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
                f"API error in GET /application/{application_id}/instance - validate_get_connector_instances middleware : {e}"
            )
            raise e
        except SQLAlchemyError as e:
            pprint(
                f"DB error in GET /application/{application_id}/instance - validate_get_connector_instances middleware : {e}"
            )
            request.state.source_error_msg = str(e)
            raise ApiError.serviceunavailable(
                "The server is currently unavailable, please try again later."
            )
        except Exception as e:
            db.rollback()
            print(
                f"Unexpected error in GET /application/{application_id}/instance - validate_get_connector_instances middleware : {e}"
            )
            request.state.source_error_msg = str(e)
            raise ApiError.serviceunavailable(
                "The server is currently unavailable, please try again later."
            )

    return validate_get_application_instances


def validate_get_application_instance_factory(
    target_model_class: Type[models.Base], target_model_action_sequence: tuple[str, ...]
):
    @auditor.audit(api_namespace=api_schemas.APINamespace.RBAC_API)
    async def validate_get_application_instance(
        request: Request,
        authenticated_entity: models.User | models.Apikey = Depends(
            AccessTokenOrApikeyAuthentication.authenticate
        ),
        # The params below are required for pydantic and rbac validation even when unused
        project_id: UUID = Header(
            ...,
            alias="X-elevAIte-ProjectId",
            description="project_id under which connector instances are queried",
        ),  # use of given alias for header params is mandatory
        application_id: int = Path(..., description="id of connector application"),
        instance_id: UUID = Path(..., description="id of connector instance"),
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
                f"API error in GET /application/{application_id}/instance - validate_get_connector_instances middleware : {e}"
            )
            raise e
        except SQLAlchemyError as e:
            pprint(
                f"DB error in GET /application/{application_id}/instance - validate_get_connector_instances middleware : {e}"
            )
            request.state.source_error_msg = str(e)
            raise ApiError.serviceunavailable(
                "The server is currently unavailable, please try again later."
            )
        except Exception as e:
            db.rollback()
            print(
                f"Unexpected error in GET /application/{application_id}/instance - validate_get_connector_instances middleware : {e}"
            )
            request.state.source_error_msg = str(e)
            raise ApiError.serviceunavailable(
                "The server is currently unavailable, please try again later."
            )

    return validate_get_application_instance


def validate_get_application_instance_chart_factory(
    target_model_class: Type[models.Base], target_model_action_sequence: tuple[str, ...]
):
    @auditor.audit(api_namespace=api_schemas.APINamespace.RBAC_API)
    async def validate_get_application_instance_chart(
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
        application_id: int = Path(..., description="id of connector application"),
        instance_id: UUID = Path(..., description="id of connector instance"),
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
                f"API error in GET /application/{application_id}/instance/{instance_id}/chart - validate_get_connector_instance_chart middleware : {e}"
            )
            raise e
        except SQLAlchemyError as e:
            pprint(
                f"DB error in GET /application/{application_id}/instance/{instance_id}/chart - validate_get_connector_instance_chart middleware : {e}"
            )
            request.state.source_error_msg = str(e)
            raise ApiError.serviceunavailable(
                "The server is currently unavailable, please try again later."
            )
        except Exception as e:
            db.rollback()
            print(
                f"Unexpected error in GET /application/{application_id}/instance/{instance_id}/chart - validate_get_connector_instance_chart middleware : {e}"
            )
            request.state.source_error_msg = str(e)
            raise ApiError.serviceunavailable(
                "The server is currently unavailable, please try again later."
            )

    return validate_get_application_instance_chart


def validate_get_application_instance_configuration_factory(
    target_model_class: Type[models.Base], target_model_action_sequence: tuple[str, ...]
):
    @auditor.audit(api_namespace=api_schemas.APINamespace.RBAC_API)
    async def validate_get_application_instance_configuration(
        request: Request,
        authenticated_entity: models.User | models.Apikey = Depends(
            AccessTokenOrApikeyAuthentication.authenticate
        ),
        # The params below are required for pydantic and rbac validation even when unused
        project_id: UUID = Header(
            ...,
            alias="X-elevAIte-ProjectId",
            description="project_id under which connector instance configuration is queried",
        ),
        application_id: int = Path(..., description="id of connector application"),
        instance_id: UUID = Path(..., description="id of connector instance"),
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
                f"API error in GET /application/{application_id}/instance/{instance_id}/configuration - validate_get_connector_instance_configuration middleware : {e}"
            )
            raise e
        except SQLAlchemyError as e:
            pprint(
                f"DB error in GET /application/{application_id}/instance/{instance_id}/configuration - validate_get_connector_instance_configuration middleware : {e}"
            )
            request.state.source_error_msg = str(e)
            raise ApiError.serviceunavailable(
                "The server is currently unavailable, please try again later."
            )
        except Exception as e:
            db.rollback()
            print(
                f"Unexpected error in GET /application/{application_id}/instance/{instance_id}/configuration - validate_get_connector_instance_configuration middleware : {e}"
            )
            request.state.source_error_msg = str(e)
            raise ApiError.serviceunavailable(
                "The server is currently unavailable, please try again later."
            )

    return validate_get_application_instance_configuration


def validate_get_application_instance_logs_factory(
    target_model_class: Type[models.Base], target_model_action_sequence: tuple[str, ...]
):
    @auditor.audit(api_namespace=api_schemas.APINamespace.RBAC_API)
    async def validate_get_application_instance_logs(
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
        application_id: int = Path(..., description="id of connector application"),
        instance_id: UUID = Path(..., description="id of connector instance"),
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
                f"API error in GET /application/{application_id}/instance/{instance_id}/log - validate_get_connector_instance_logs middleware : {e}"
            )
            raise e
        except SQLAlchemyError as e:
            pprint(
                f"DB error in GET /application/{application_id}/instance/{instance_id}/log - validate_get_connector_instance_logs middleware : {e}"
            )
            request.state.source_error_msg = str(e)
            raise ApiError.serviceunavailable(
                "The server is currently unavailable, please try again later."
            )
        except Exception as e:
            db.rollback()
            print(
                f"Unexpected error in GET /application/{application_id}/instance/{instance_id}/log - validate_get_connector_instance_logs middleware : {e}"
            )
            request.state.source_error_msg = str(e)
            raise ApiError.serviceunavailable(
                "The server is currently unavailable, please try again later."
            )

    return validate_get_application_instance_logs


def validate_create_application_instance_factory(
    target_model_class: Type[models.Base], target_model_action_sequence: tuple[str, ...]
):
    @auditor.audit(api_namespace=api_schemas.APINamespace.RBAC_API)
    async def validate_create_application_instance(
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
                f"API error in POST /application/{application_id}/instance/ - validate_create_connector_instance middleware : {e}"
            )
            raise e
        except SQLAlchemyError as e:
            pprint(
                f"DB error in POST /application/{application_id}/instance/ - validate_create_connector_instance middleware : {e}"
            )
            request.state.source_error_msg = str(e)
            raise ApiError.serviceunavailable(
                "The server is currently unavailable, please try again later."
            )
        except Exception as e:
            db.rollback()
            print(
                f"Unexpected error in POST /application/{application_id}/instance/ - validate_create_connector_instance middleware : {e}"
            )
            request.state.source_error_msg = str(e)
            raise ApiError.serviceunavailable(
                "The server is currently unavailable, please try again later."
            )

    return validate_create_application_instance

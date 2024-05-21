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
)
from rbac_api.auth.impl import (
   AccessTokenAuthentication
)
from ...main import RBACProvider
import inspect

def validate_get_application_configurations_factory(target_model_class : Type[models.Base], target_model_action_sequence: tuple[str, ...]):
   async def validate_get_application_configurations(
      request: Request,
      authenticated_entity: models.User = Depends(AccessTokenAuthentication.authenticate),  
      # The params below are required for pydantic and rbac validation even when unused
      account_id: UUID = Header(..., alias = "X-elevAIte-AccountId", description="account_id under which connector appication configurations are queried"),
      application_id: int = Path(..., description="id of connector application"),
   ) -> dict[str, Any]:
      db: Session = request.state.db
      try:
         # Set the context flags in request.state
         current_frame = inspect.currentframe()
         if current_frame and current_frame.f_locals:   
            frame_locals = current_frame.f_locals
            request.state.account_context_exists = 'account_id' in frame_locals
            request.state.project_context_exists = 'project_id' in frame_locals
         else:
            request.state.account_context_exists = False
            request.state.project_context_exists = False

         return await RBACProvider.get_instance().validate_rbac_permissions(
            request=request,
            db=db,
            target_model_action_sequence=target_model_action_sequence,
            authenticated_entity=authenticated_entity,
            target_model_class=target_model_class
         )
      except HTTPException as e:
         db.rollback()
         pprint(f'API error in GET /application/{application_id}/configuration - validate_get_connector_configurations middleware : {e}')
         raise e
      except SQLAlchemyError as e:
         pprint(f'DB error in GET /application/{application_id}/configuration - validate_get_connector_configurations middleware : {e}')
         raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
      except Exception as e:
         db.rollback()
         print(f'Unexpected error in GET /application/{application_id}/configuration - validate_get_connector_configurations middleware : {e}')
         raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
   
   return validate_get_application_configurations

def validate_get_application_configuration_factory(target_model_class : Type[models.Base], target_model_action_sequence: tuple[str, ...]):
   async def validate_get_application_configuration(
      request: Request,
      authenticated_entity: models.User = Depends(AccessTokenAuthentication.authenticate), 
      # The params below are required for pydantic and rbac validation even when unused
      account_id: UUID = Header(..., alias = "X-elevAIte-AccountId", description="account_id under which connector appication configuration is queried"),
      application_id: int = Path(..., description="id of connector application"),
      configuration_id: UUID = Path(..., description="id of connector application configuration"),
   ) -> dict[str, Any]:
      db: Session = request.state.db
      try:
         # Set the context flags in request.state
         current_frame = inspect.currentframe()
         if current_frame and current_frame.f_locals:   
            frame_locals = current_frame.f_locals
            request.state.account_context_exists = 'account_id' in frame_locals
            request.state.project_context_exists = 'project_id' in frame_locals
         else:
            request.state.account_context_exists = False
            request.state.project_context_exists = False

         return await RBACProvider.get_instance().validate_rbac_permissions(
            request=request,
            db=db,
            target_model_action_sequence=target_model_action_sequence,
            authenticated_entity=authenticated_entity,
            target_model_class=target_model_class
         )
      except HTTPException as e:
         db.rollback()
         pprint(f'API error in GET /application/{application_id}/configuration/{configuration_id} - validate_get_connector_configuration middleware : {e}')
         raise e
      except SQLAlchemyError as e:
         pprint(f'DB error in GET /application/{application_id}/configuration/{configuration_id} - validate_get_connector_configuration middleware : {e}')
         raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
      except Exception as e:
         db.rollback()
         print(f'Unexpected error in GET /application/{application_id}/configuration/{configuration_id} - validate_get_connector_configuration middleware : {e}')
         raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
   
   return validate_get_application_configuration

def validate_update_application_configuration_factory(target_model_class : Type[models.Base], target_model_action_sequence: tuple[str, ...]):
   async def validate_update_application_configuration(
      request: Request,
      authenticated_entity: models.User = Depends(AccessTokenAuthentication.authenticate), 
      # The params below are required for pydantic and rbac validation even when unused
      account_id: UUID = Header(..., alias = "X-elevAIte-AccountId", description="account_id under which connector appication configuration is queried"),
      application_id: int = Path(..., description="id of connector application"),
      configuration_id: UUID = Path(..., description="id of connector application configuration"),
   ) -> dict[str, Any]:
      db: Session = request.state.db
      try:
         # Set the context flags in request.state
         current_frame = inspect.currentframe()
         if current_frame and current_frame.f_locals:   
            frame_locals = current_frame.f_locals
            request.state.account_context_exists = 'account_id' in frame_locals
            request.state.project_context_exists = 'project_id' in frame_locals
         else:
            request.state.account_context_exists = False
            request.state.project_context_exists = False

         return await RBACProvider.get_instance().validate_rbac_permissions(
            request=request,
            db=db,
            target_model_action_sequence=target_model_action_sequence,
            authenticated_entity=authenticated_entity,
            target_model_class=target_model_class
         )
      except HTTPException as e:
         db.rollback()
         pprint(f'API error in PUT /application/{application_id}/configuration/{configuration_id} - validate_update_connector_configuration middleware : {e}')
         raise e
      except SQLAlchemyError as e:
         pprint(f'DB error in PUT /application/{application_id}/configuration/{configuration_id} - validate_update_connector_configuration middleware : {e}')
         raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
      except Exception as e:
         db.rollback()
         print(f'Unexpected error in PUT /application/{application_id}/configuration/{configuration_id} - validate_update_connector_configuration middleware : {e}')
         raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
   
   return validate_update_application_configuration

def validate_create_application_configuration_factory(target_model_class : Type[models.Base], target_model_action_sequence: tuple[str, ...]):
   async def validate_create_application_configuration(
      request: Request,
      authenticated_entity: models.User = Depends(AccessTokenAuthentication.authenticate), 
      # The params below are required for pydantic and rbac validation even when unused
      account_id: UUID = Header(..., alias = "X-elevAIte-AccountId", description="account_id under which connector appication configurations are queried"),
      application_id: int = Path(..., description="id of connector application"),
   ) -> dict[str, Any]:
      db: Session = request.state.db
      try:
         # Set the context flags in request.state
         current_frame = inspect.currentframe()
         if current_frame and current_frame.f_locals:   
            frame_locals = current_frame.f_locals
            request.state.account_context_exists = 'account_id' in frame_locals
            request.state.project_context_exists = 'project_id' in frame_locals
         else:
            request.state.account_context_exists = False
            request.state.project_context_exists = False

         return await RBACProvider.get_instance().validate_rbac_permissions(
            request=request,
            db=db,
            target_model_action_sequence=target_model_action_sequence,
            authenticated_entity=authenticated_entity,
            target_model_class=target_model_class
         )
      except HTTPException as e:
         db.rollback()
         pprint(f'API error in POST /application/{application_id}/configuration - validate_create_connector_configuration middleware : {e}')
         raise e
      except SQLAlchemyError as e:
         pprint(f'DB error in POST /application/{application_id}/configuration - validate_create_connector_configuration middleware : {e}')
         raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
      except Exception as e:
         db.rollback()
         print(f'Unexpected error in POST /application/{application_id}/configuration - validate_create_connector_configuration middleware : {e}')
         raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
   
   return validate_create_application_configuration
from fastapi import Path, Depends, Header, Query, Request, HTTPException
from uuid import UUID
from ..auth.token import validate_token
from sqlalchemy import or_, and_
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from rbac_api.utils.deps import get_db  
from rbac_api.app.errors.api_error import ApiError
from pprint import pprint
from typing import Any, Optional, Type, Callable, Coroutine

from elevaitedb.db import models
from elevaitedb.schemas import (
   application as application_schemas,
)

from ...rbac import rbac_instance

def validate_get_connector_factory(target_model_class : Type[models.Base], target_model_action_sequence: tuple[str, ...]) -> Callable[..., Coroutine[Any, Any, dict[str, Any]]]:
   async def validate_get_connector(
      request: Request,
      user_email: str = Depends(validate_token),
      # The params below are required for pydantic validation even when unused
      account_id: UUID = Header(..., alias = "X-elevAIte-AccountId", description="account_id under which connector application is queried"),
      application_id: int = Path(..., description="id of connector application to be retrieved"),
      db: Session = Depends(get_db)
   ) -> dict[str, Any]:
      try:
         return await rbac_instance.validate_endpoint_rbac_permissions( 
            request=request,
            db=db,
            target_model_action_sequence=target_model_action_sequence,
            user_email=user_email,
            target_model_class=target_model_class
         )
      except HTTPException as e:
         db.rollback()
         pprint(f'API error in GET /application/{application_id} - validate_get_connector dependency : {e}')
         raise e
      except SQLAlchemyError as e:
         pprint(f'DB error in GET /application/{application_id} - validate_get_connector dependency : {e}')
         raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
      except Exception as e:
         db.rollback()
         print(f'Unexpected error in GET /application/{application_id} - validate_get_connector dependency : {e}')
         raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
   return validate_get_connector

def validate_get_connectors_factory(target_model_class : Type[models.Base], target_model_action_sequence: tuple[str, ...]) -> Callable[..., Coroutine[Any, Any, dict[str, Any]]]:
   async def validate_get_connectors(
      request: Request,
      user_email: str = Depends(validate_token),
      # The params below are required for pydantic validation even when unused
      account_id: UUID = Header(..., alias = "X-elevAIte-AccountId", description="account_id under which connectors are queried"),
      db: Session = Depends(get_db)
   ) -> dict[str, Any]:
      try:
         return await rbac_instance.validate_endpoint_rbac_permissions(
            request=request,
            db=db,
            target_model_action_sequence=target_model_action_sequence,
            user_email=user_email,
            target_model_class=target_model_class
         )
      except HTTPException as e:
         db.rollback()
         pprint(f'API error in GET /application - validate_get_connectors dependency : {e}')
         raise e
      except SQLAlchemyError as e:
         pprint(f'DB error in GET /application - validate_get_connectors dependency : {e}')
         raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
      except Exception as e:
         db.rollback()
         print(f'Unexpected error in GET /application - validate_get_connectors dependency : {e}')
         raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
   return validate_get_connectors

def validate_get_connector_pipelines_factory(target_model_class : Type[models.Base], target_model_action_sequence: tuple[str, ...]) -> Callable[..., Coroutine[Any, Any, dict[str, Any]]]:
   async def validate_get_connector_pipelines(
      request: Request,
      user_email: str = Depends(validate_token),
      # The params below are required for pydantic validation even when unused
      account_id: UUID = Header(..., alias = "X-elevAIte-AccountId", description="account_id under which connector pipelines are queried"),
      application_id: int = Path(..., description="id of connector application"),
      db: Session = Depends(get_db)
   ) -> dict[str, Any]:
      try:
         return await rbac_instance.validate_endpoint_rbac_permissions(
            request=request,
            db=db,
            target_model_action_sequence=target_model_action_sequence,
            user_email=user_email,
            target_model_class=target_model_class
         )
      except HTTPException as e:
         db.rollback()
         pprint(f'API error in GET /application/{application_id}/pipelines - validate_get_connector_pipelines dependency : {e}')
         raise e
      except SQLAlchemyError as e:
         pprint(f'DB error in GET /application/{application_id}/pipelines - validate_get_connector_pipelines dependency : {e}')
         raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
      except Exception as e:
         db.rollback()
         print(f'Unexpected error in GET /application/{application_id}/pipelines - validate_get_connector_pipelines dependency : {e}')
         raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
   
   return validate_get_connector_pipelines

def validate_get_connector_configurations_factory(target_model_class : Type[models.Base], target_model_action_sequence: tuple[str, ...]) -> Callable[..., Coroutine[Any, Any, dict[str, Any]]]:
   async def validate_get_connector_configurations(
      request: Request,
      user_email: str = Depends(validate_token),
      # The params below are required for pydantic validation even when unused
      account_id: UUID = Header(..., alias = "X-elevAIte-AccountId", description="account_id under which connector appication configurations are queried"),
      application_id: int = Path(..., description="id of connector application"),
      db: Session = Depends(get_db)
   ) -> dict[str, Any]:
      try:
         return await rbac_instance.validate_endpoint_rbac_permissions(
            request=request,
            db=db,
            target_model_action_sequence=target_model_action_sequence,
            user_email=user_email,
            target_model_class=target_model_class
         )
      except HTTPException as e:
         db.rollback()
         pprint(f'API error in GET /application/{application_id}/configuration - validate_get_connector_configurations dependency : {e}')
         raise e
      except SQLAlchemyError as e:
         pprint(f'DB error in GET /application/{application_id}/configuration - validate_get_connector_configurations dependency : {e}')
         raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
      except Exception as e:
         db.rollback()
         print(f'Unexpected error in GET /application/{application_id}/configuration - validate_get_connector_configurations dependency : {e}')
         raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
   
   return validate_get_connector_configurations

def validate_get_connector_configuration_factory(target_model_class : Type[models.Base], target_model_action_sequence: tuple[str, ...]) -> Callable[..., Coroutine[Any, Any, dict[str, Any]]]:
   async def validate_get_connector_configuration(
      request: Request,
      user_email: str = Depends(validate_token),
      # The params below are required for pydantic validation even when unused
      account_id: UUID = Header(..., alias = "X-elevAIte-AccountId", description="account_id under which connector appication configuration is queried"),
      application_id: int = Path(..., description="id of connector application"),
      configuration_id: UUID = Path(..., description="id of connector application configuration"),
      db: Session = Depends(get_db)
   ) -> dict[str, Any]:
      try:
         return await rbac_instance.validate_endpoint_rbac_permissions(
            request=request,
            db=db,
            target_model_action_sequence=target_model_action_sequence,
            user_email=user_email,
            target_model_class=target_model_class
         )
      except HTTPException as e:
         db.rollback()
         pprint(f'API error in GET /application/{application_id}/configuration/{configuration_id} - validate_get_connector_configuration dependency : {e}')
         raise e
      except SQLAlchemyError as e:
         pprint(f'DB error in GET /application/{application_id}/configuration/{configuration_id} - validate_get_connector_configuration dependency : {e}')
         raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
      except Exception as e:
         db.rollback()
         print(f'Unexpected error in GET /application/{application_id}/configuration/{configuration_id} - validate_get_connector_configuration dependency : {e}')
         raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
   
   return validate_get_connector_configuration

def validate_update_connector_configuration_factory(target_model_class : Type[models.Base], target_model_action_sequence: tuple[str, ...]) -> Callable[..., Coroutine[Any, Any, dict[str, Any]]]:
   async def validate_update_connector_configuration(
      request: Request,
      user_email: str = Depends(validate_token),
      # The params below are required for pydantic validation even when unused
      account_id: UUID = Header(..., alias = "X-elevAIte-AccountId", description="account_id under which connector appication configuration is queried"),
      application_id: int = Path(..., description="id of connector application"),
      configuration_id: UUID = Path(..., description="id of connector application configuration"),
      db: Session = Depends(get_db)
   ) -> dict[str, Any]:
      try:
         return await rbac_instance.validate_endpoint_rbac_permissions(
            request=request,
            db=db,
            target_model_action_sequence=target_model_action_sequence,
            user_email=user_email,
            target_model_class=target_model_class
         )
      except HTTPException as e:
         db.rollback()
         pprint(f'API error in PUT /application/{application_id}/configuration/{configuration_id} - validate_update_connector_configuration dependency : {e}')
         raise e
      except SQLAlchemyError as e:
         pprint(f'DB error in PUT /application/{application_id}/configuration/{configuration_id} - validate_update_connector_configuration dependency : {e}')
         raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
      except Exception as e:
         db.rollback()
         print(f'Unexpected error in PUT /application/{application_id}/configuration/{configuration_id} - validate_update_connector_configuration dependency : {e}')
         raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
   
   return validate_update_connector_configuration

def validate_create_connector_configuration_factory(target_model_class : Type[models.Base], target_model_action_sequence: tuple[str, ...]) -> Callable[..., Coroutine[Any, Any, dict[str, Any]]]:
   async def validate_create_connector_configuration(
      request: Request,
      user_email: str = Depends(validate_token),
      # The params below are required for pydantic validation even when unused
      account_id: UUID = Header(..., alias = "X-elevAIte-AccountId", description="account_id under which connector appication configurations are queried"),
      application_id: int = Path(..., description="id of connector application"),
      db: Session = Depends(get_db)
   ) -> dict[str, Any]:
      try:
         return await rbac_instance.validate_endpoint_rbac_permissions(
            request=request,
            db=db,
            target_model_action_sequence=target_model_action_sequence,
            user_email=user_email,
            target_model_class=target_model_class
         )
      except HTTPException as e:
         db.rollback()
         pprint(f'API error in POST /application/{application_id}/configuration - validate_create_connector_configuration dependency : {e}')
         raise e
      except SQLAlchemyError as e:
         pprint(f'DB error in POST /application/{application_id}/configuration - validate_create_connector_configuration dependency : {e}')
         raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
      except Exception as e:
         db.rollback()
         print(f'Unexpected error in POST /application/{application_id}/configuration - validate_create_connector_configuration dependency : {e}')
         raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
   
   return validate_create_connector_configuration

def validate_get_connector_instances_factory(target_model_class : Type[models.Base], target_model_action_sequence: tuple[str, ...]) -> Callable[..., Coroutine[Any, Any, dict[str, Any]]]:
   async def validate_get_connector_instances(
      request: Request,
      user_email: str = Depends(validate_token),
      # The params below are required for pydantic validation even when unused
      project_id: UUID = Header(..., alias = "X-elevAIte-ProjectId", description="project_id under which connector instances are queried"),
      application_id: int = Path(..., description="id of connector application"),
      db: Session = Depends(get_db)
   ) -> dict[str, Any]:
      try:
         return await rbac_instance.validate_endpoint_rbac_permissions(
            request=request,
            db=db,
            target_model_action_sequence=target_model_action_sequence,
            user_email=user_email,
            target_model_class=target_model_class
         )
      except HTTPException as e:
         db.rollback()
         pprint(f'API error in GET /application/{application_id}/instance - validate_get_connector_instances dependency : {e}')
         raise e
      except SQLAlchemyError as e:
         pprint(f'DB error in GET /application/{application_id}/instance - validate_get_connector_instances dependency : {e}')
         raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
      except Exception as e:
         db.rollback()
         print(f'Unexpected error in GET /application/{application_id}/instance - validate_get_connector_instances dependency : {e}')
         raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
   
   return validate_get_connector_instances

def validate_get_connector_instance_factory(target_model_class : Type[models.Base], target_model_action_sequence: tuple[str, ...]) -> Callable[..., Coroutine[Any, Any, dict[str, Any]]]:
   async def validate_get_connector_instance(
      request: Request,
      user_email: str = Depends(validate_token),
      # The params below are required for pydantic validation even when unused
      project_id: UUID = Header(..., alias = "X-elevAIte-ProjectId", description="project_id under which connector instances are queried"),
      application_id: int = Path(..., description="id of connector application"),
      instance_id: UUID = Path(..., description="id of connector instance"),
      db: Session = Depends(get_db)
   ) -> dict[str, Any]:
      try:
         return await rbac_instance.validate_endpoint_rbac_permissions(
            request=request,
            db=db,
            target_model_action_sequence=target_model_action_sequence,
            user_email=user_email,
            target_model_class=target_model_class
         )
      except HTTPException as e:
         db.rollback()
         pprint(f'API error in GET /application/{application_id}/instance - validate_get_connector_instances dependency : {e}')
         raise e
      except SQLAlchemyError as e:
         pprint(f'DB error in GET /application/{application_id}/instance - validate_get_connector_instances dependency : {e}')
         raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
      except Exception as e:
         db.rollback()
         print(f'Unexpected error in GET /application/{application_id}/instance - validate_get_connector_instances dependency : {e}')
         raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
   
   return validate_get_connector_instance

def validate_get_connector_instance_chart_factory(target_model_class : Type[models.Base], target_model_action_sequence: tuple[str, ...]) -> Callable[..., Coroutine[Any, Any, dict[str, Any]]]:
   async def validate_get_connector_instance_chart(
      request: Request,
      user_email: str = Depends(validate_token),
      # The params below are required for pydantic validation even when unused
      project_id: UUID = Header(..., alias = "X-elevAIte-ProjectId", description="project_id under which connector instances are queried"),
      application_id: int = Path(..., description="id of connector application"),
      instance_id: UUID = Path(..., description="id of connector instance"),
      db: Session = Depends(get_db)
   ) -> dict[str, Any]:
      try:
         return await rbac_instance.validate_endpoint_rbac_permissions(
            request=request,
            db=db,
            target_model_action_sequence=target_model_action_sequence,
            user_email=user_email,
            target_model_class=target_model_class
         )
      except HTTPException as e:
         db.rollback()
         pprint(f'API error in GET /application/{application_id}/instance/{instance_id}/chart - validate_get_connector_instance_chart dependency : {e}')
         raise e
      except SQLAlchemyError as e:
         pprint(f'DB error in GET /application/{application_id}/instance/{instance_id}/chart - validate_get_connector_instance_chart dependency : {e}')
         raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
      except Exception as e:
         db.rollback()
         print(f'Unexpected error in GET /application/{application_id}/instance/{instance_id}/chart - validate_get_connector_instance_chart dependency : {e}')
         raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
   return validate_get_connector_instance_chart

def validate_get_connector_instance_configuration_factory(target_model_class : Type[models.Base], target_model_action_sequence: tuple[str, ...]) -> Callable[..., Coroutine[Any, Any, dict[str, Any]]]:
   async def validate_get_connector_instance_configuration(
      request: Request,
      user_email: str = Depends(validate_token),
      # The params below are required for pydantic validation even when unused
      project_id: UUID = Header(..., alias = "X-elevAIte-ProjectId", description="project_id under which connector instance configuration is queried"),
      application_id: int = Path(..., description="id of connector application"),
      instance_id: UUID = Path(..., description="id of connector instance"),
      db: Session = Depends(get_db)
   ) -> dict[str, Any]:
      try:
         return await rbac_instance.validate_endpoint_rbac_permissions(
            request=request,
            db=db,
            target_model_action_sequence=target_model_action_sequence,
            user_email=user_email,
            target_model_class=target_model_class
         )
      except HTTPException as e:
         db.rollback()
         pprint(f'API error in GET /application/{application_id}/instance/{instance_id}/configuration - validate_get_connector_instance_configuration dependency : {e}')
         raise e
      except SQLAlchemyError as e:
         pprint(f'DB error in GET /application/{application_id}/instance/{instance_id}/configuration - validate_get_connector_instance_configuration dependency : {e}')
         raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
      except Exception as e:
         db.rollback()
         print(f'Unexpected error in GET /application/{application_id}/instance/{instance_id}/configuration - validate_get_connector_instance_configuration dependency : {e}')
         raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
   
   return validate_get_connector_instance_configuration

def validate_get_connector_instance_logs_factory(target_model_class : Type[models.Base], target_model_action_sequence: tuple[str, ...]) -> Callable[..., Coroutine[Any, Any, dict[str, Any]]]:
   async def validate_get_connector_instance_logs(
      request: Request,
      user_email: str = Depends(validate_token),
      # The params below are required for pydantic validation even when unused
      project_id: UUID = Header(..., alias = "X-elevAIte-ProjectId", description="project_id under which connector instance logs are queried"),
      application_id: int = Path(..., description="id of connector application"),
      instance_id: UUID = Path(..., description="id of connector instance"),
      db: Session = Depends(get_db)
   ) -> dict[str, Any]:
      try:
         return await rbac_instance.validate_endpoint_rbac_permissions(
            request=request,
            db=db,
            target_model_action_sequence=target_model_action_sequence,
            user_email=user_email,
            target_model_class=target_model_class
         )
      except HTTPException as e:
         db.rollback()
         pprint(f'API error in GET /application/{application_id}/instance/{instance_id}/log - validate_get_connector_instance_logs dependency : {e}')
         raise e
      except SQLAlchemyError as e:
         pprint(f'DB error in GET /application/{application_id}/instance/{instance_id}/log - validate_get_connector_instance_logs dependency : {e}')
         raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
      except Exception as e:
         db.rollback()
         print(f'Unexpected error in GET /application/{application_id}/instance/{instance_id}/log - validate_get_connector_instance_logs dependency : {e}')
         raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
   
   return validate_get_connector_instance_logs

def validate_create_connector_instance_factory(target_model_class : Type[models.Base], target_model_action_sequence: tuple[str, ...]) -> Callable[..., Coroutine[Any, Any, dict[str, Any]]]:
   async def validate_create_connector_instance(
      request: Request,
      user_email: str = Depends(validate_token),
      # The params below are required for pydantic validation even when unused
      project_id: UUID = Header(..., alias = "X-elevAIte-ProjectId", description="project_id under which connector instance logs are queried"),
      application_id: int = Path(..., description="id of connector application"),
      db: Session = Depends(get_db)
   ) -> dict[str, Any]:
      try:
         return await rbac_instance.validate_endpoint_rbac_permissions(
            request=request,
            db=db,
            target_model_action_sequence=target_model_action_sequence,
            user_email=user_email,
            target_model_class=target_model_class
         )
      except HTTPException as e:
         db.rollback()
         pprint(f'API error in POST /application/{application_id}/instance/ - validate_create_connector_instance dependency : {e}')
         raise e
      except SQLAlchemyError as e:
         pprint(f'DB error in POST /application/{application_id}/instance/ - validate_create_connector_instance dependency : {e}')
         raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
      except Exception as e:
         db.rollback()
         print(f'Unexpected error in POST /application/{application_id}/instance/ - validate_create_connector_instance dependency : {e}')
         raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
   return validate_create_connector_instance
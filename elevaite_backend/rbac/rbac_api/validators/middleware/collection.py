from fastapi import Path, Depends, Header, Request, HTTPException
from uuid import UUID
from .header import validate_token
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from rbac_api.utils.deps import get_db  
from rbac_api.app.errors.api_error import ApiError
from pprint import pprint
from typing import Any, Type, Callable, Coroutine

from elevaitedb.db import models
from ..rbac import rbac_instance

def validate_get_project_collections_factory(target_model_class : Type[models.Base], target_model_action_sequence: tuple[str, ...]) -> Callable[..., Coroutine[Any, Any, dict[str, Any]]]:
   async def validate_get_project_collections(
      request: Request,
      user_email: str = Depends(validate_token),
      # The params below are required for pydantic validation even when unused
      account_id: UUID = Header(..., alias = "X-elevAIte-AccountId", description="account_id under which project collections are queried"),
      project_id: UUID = Path(..., description="project_id under which project collections are queried"),
      
      db: Session = Depends(get_db)
   ) -> dict[str, Any]:
      try:
         return await rbac_instance.validate_rbac(
            request=request,
            db=db,
            target_model_action_sequence=target_model_action_sequence,
            user_email=user_email,
            target_model_class=target_model_class
         )
      except HTTPException as e:
         db.rollback()
         pprint(f'API error in GET /project/{project_id}/collection - validate_get_project_collections dependency : {e}')
         raise e
      except SQLAlchemyError as e:
         pprint(f'DB error in GET /project/{project_id}/collection - validate_get_project_collections dependency : {e}')
         raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
      except Exception as e:
         db.rollback()
         print(f'Unexpected error in GET /project/{project_id}/collection - validate_get_project_collections dependency : {e}')
         raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
   return validate_get_project_collections

def validate_get_project_collection_factory(target_model_class : Type[models.Base], target_model_action_sequence: tuple[str, ...]) -> Callable[..., Coroutine[Any, Any, dict[str, Any]]]:
   async def validate_get_project_collection(
      request: Request,
      user_email: str = Depends(validate_token),
      # The params below are required for pydantic validation even when unused
      account_id: UUID = Header(..., alias = "X-elevAIte-AccountId", description="account_id under which project collection is queried"),
      project_id: UUID = Path(..., description="project_id under which collection is queried"),
      collection_id: UUID = Path(..., description=" id of collection being queried"),
      db: Session = Depends(get_db)
   ) -> dict[str, Any]:
      try:
         return await rbac_instance.validate_rbac(
            request=request,
            db=db,
            target_model_action_sequence=target_model_action_sequence,
            user_email=user_email,
            target_model_class=target_model_class
         )
      except HTTPException as e:
         db.rollback()
         pprint(f'API error in GET /project/{project_id}/collection/{collection_id} - validate_get_project_collection dependency : {e}')
         raise e
      except SQLAlchemyError as e:
         pprint(f'DB error in GET /project/{project_id}/collection/{collection_id} - validate_get_project_collection dependency : {e}')
         raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
      except Exception as e:
         db.rollback()
         print(f'Unexpected error in GET /project/{project_id}/collection/{collection_id} - validate_get_project_collection dependency : {e}')
         raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
   return validate_get_project_collection

def validate_create_project_collection_factory(target_model_class : Type[models.Base], target_model_action_sequence: tuple[str, ...]) -> Callable[..., Coroutine[Any, Any, dict[str, Any]]]:
   async def validate_create_project_collection(
      request: Request,
      user_email: str = Depends(validate_token),
      # The params below are required for pydantic validation even when unused
      account_id: UUID = Header(..., alias = "X-elevAIte-AccountId", description="account_id under which project dataset is tagged"),
      project_id: UUID = Path(..., description="project_id under which dataset is tagged"),
      db: Session = Depends(get_db)
   ) -> dict[str, Any]:
      try:
         return await rbac_instance.validate_rbac(
            request=request,
            db=db,
            target_model_action_sequence=target_model_action_sequence,
            user_email=user_email,
            target_model_class=target_model_class
         )
      except HTTPException as e:
         db.rollback()
         pprint(f'API error in POST /project/{project_id}/collection - validate_create_project_collection dependency : {e}')
         raise e
      except SQLAlchemyError as e:
         pprint(f'DB error in POST /project/{project_id}/collection - validate_create_project_collection dependency : {e}')
         raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
      except Exception as e:
         db.rollback()
         print(f'Unexpected error in POST /project/{project_id}/collection - validate_create_project_collection dependency : {e}')
         raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
   
   return validate_create_project_collection


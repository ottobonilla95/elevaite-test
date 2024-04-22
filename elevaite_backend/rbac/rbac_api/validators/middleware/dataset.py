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

def validate_get_project_datasets_factory(target_model_class : Type[models.Base], target_model_action_sequence: tuple[str, ...]) -> Callable[..., Coroutine[Any, Any, dict[str, Any]]]:
   async def validate_get_project_datasets(
      request: Request,
      user_email: str = Depends(validate_token),
      # The params below are required for pydantic validation even when unused
      account_id: UUID = Header(..., alias = "X-elevAIte-AccountId", description="account_id under which project datasets are queried"),
      project_id: UUID = Path(..., description="project_id under which project datasets are queried"),
      
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
         pprint(f'API error in GET /project/{project_id}/datasets - validate_get_project_datasets dependency : {e}')
         raise e
      except SQLAlchemyError as e:
         pprint(f'DB error in GET /project/{project_id}/datasets - validate_get_project_datasets dependency : {e}')
         raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
      except Exception as e:
         db.rollback()
         print(f'Unexpected error in GET /project/{project_id}/datasets - validate_get_project_datasets dependency : {e}')
         raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
   return validate_get_project_datasets

def validate_get_project_dataset_factory(target_model_class : Type[models.Base], target_model_action_sequence: tuple[str, ...]) -> Callable[..., Coroutine[Any, Any, dict[str, Any]]]:
   async def validate_get_project_dataset(
      request: Request,
      user_email: str = Depends(validate_token),
      # The params below are required for pydantic validation even when unused
      account_id: UUID = Header(..., alias = "X-elevAIte-AccountId", description="account_id under which project dataset is queried"),
      project_id: UUID = Path(..., description="project_id under which dataset is queried"),
      dataset_id: UUID = Path(..., description=" id of dataset being queried"),
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
         pprint(f'API error in GET /project/{project_id}/datasets/{dataset_id} - validate_get_project_dataset dependency : {e}')
         raise e
      except SQLAlchemyError as e:
         pprint(f'DB error in GET /project/{project_id}/datasets/{dataset_id} - validate_get_project_dataset dependency : {e}')
         raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
      except Exception as e:
         db.rollback()
         print(f'Unexpected error in GET /project/{project_id}/datasets/{dataset_id} - validate_get_project_dataset dependency : {e}')
         raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
   return validate_get_project_dataset

def validate_add_tag_to_dataset_factory(target_model_class : Type[models.Base], target_model_action_sequence: tuple[str, ...]) -> Callable[..., Coroutine[Any, Any, dict[str, Any]]]:
   async def validate_add_tag_to_dataset(
      request: Request,
      user_email: str = Depends(validate_token),
      # The params below are required for pydantic validation even when unused
      account_id: UUID = Header(..., alias = "X-elevAIte-AccountId", description="account_id under which project dataset is tagged"),
      project_id: UUID = Path(..., description="project_id under which dataset is tagged"),
      dataset_id: UUID = Path(..., description=" id of dataset being queried"),
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
         pprint(f'API error in POST /project/{project_id}/datasets/{dataset_id}/tags - validate_add_tag_to_dataset dependency : {e}')
         raise e
      except SQLAlchemyError as e:
         pprint(f'DB error in POST /project/{project_id}/datasets/{dataset_id}/tags - validate_add_tag_to_dataset dependency : {e}')
         raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
      except Exception as e:
         db.rollback()
         print(f'Unexpected error in POST /project/{project_id}/datasets/{dataset_id}/tags - validate_add_tag_to_dataset dependency : {e}')
         raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
   
   return validate_add_tag_to_dataset


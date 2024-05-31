
from fastapi import status, HTTPException, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session, load_only
from sqlalchemy.exc import  SQLAlchemyError
from sqlalchemy.sql import and_, exists
from typing import List, cast
from uuid import UUID
from datetime import datetime
from pprint import pprint
from ..errors.api_error import ApiError
from datetime import UTC
import secrets
from fastapi.encoders import jsonable_encoder

from elevaitedb.schemas import (
   apikey as apikey_schemas,
   permission as permission_schemas,
)
from elevaitedb.db import models
from rbac_api import RBACValidatorProvider
from .utils.apikey_helpers import is_permission_subset

async def create_apikey(
   request: Request,
   create_apikey_dto: apikey_schemas.ApikeyCreate,
   project_id: UUID,
   db: Session,
   logged_in_user: models.User,
   logged_in_user_is_account_admin: bool,
   logged_in_user_is_project_admin: bool,
   logged_in_user_project_association: models.User_Project,
   logged_in_user_account_association: models.User_Account
   )-> apikey_schemas.ApikeyCreateResponseDTO:
   try:
      creator_id = logged_in_user.id
      apikey_name_exists = db.query(exists().where(
         and_(
            models.Apikey.name == create_apikey_dto.name,
            models.Apikey.creator_id == creator_id,
            models.Apikey.project_id == project_id
         )
      )).scalar()
      if apikey_name_exists:
         raise ApiError.conflict(f"An api key with the same name - '{create_apikey_dto.name}' - already exists and was created under project - '{project_id}' - by user - '{creator_id}'")

      apikey_permissions_type: apikey_schemas.ApikeyPermissionsType = create_apikey_dto.permissions_type


      if apikey_permissions_type is apikey_schemas.ApikeyPermissionsType.CLONED:
         if logged_in_user.is_superadmin or logged_in_user_is_account_admin or logged_in_user_is_project_admin:
            apikey_overall_permissions = permission_schemas.ApikeyScopedRBACPermission.create().dict(exclude_none = True)
         else:
            logged_in_user_account_association_id = logged_in_user_account_association.id
            logged_in_entity_account_and_project_association_info = {"authenticated_entity" : logged_in_user, "logged_in_entity_account_association" : logged_in_user_account_association, "logged_in_entity_project_association" : logged_in_user_project_association}
            apikey_overall_permissions = await RBACValidatorProvider.get_instance().evaluate_apikey_permissions(request=request, db=db, logged_in_entity_account_and_project_association_info=logged_in_entity_account_and_project_association_info, logged_in_user_account_association_id=logged_in_user_account_association_id)    
      else:
         if logged_in_user.is_superadmin or logged_in_user_is_account_admin or logged_in_user_is_project_admin:
            apikey_overall_permissions = create_apikey_dto.permissions.dict(exclude_none=True)
         else:
            logged_in_user_account_association_id = logged_in_user_account_association.id
            logged_in_entity_account_and_project_association_info = {"authenticated_entity" : logged_in_user, "logged_in_entity_account_association" : logged_in_user_account_association, "logged_in_entity_project_association" : logged_in_user_project_association}
            logged_in_user_overall_permissions = await RBACValidatorProvider.get_instance().evaluate_apikey_permissions(request=request, db=db, logged_in_entity_account_and_project_association_info=logged_in_entity_account_and_project_association_info, logged_in_user_account_association_id=logged_in_user_account_association_id) 
            payload_custom_permissions = create_apikey_dto.permissions.dict(exclude_none=True)
            if not is_permission_subset(payload_custom_permissions, logged_in_user_overall_permissions):
               raise ApiError.forbidden(f'Attempting to create api key with custom permissions which exceed your current user permissions')    
            apikey_overall_permissions = payload_custom_permissions


      # generate unique key
      api_key_value = f"eAI_{secrets.token_urlsafe(16)}"

      apikey_kwargs = {
        "name": create_apikey_dto.name,
        "creator_id": creator_id,
        "permissions_type": apikey_permissions_type,
        "permissions": apikey_overall_permissions,
        "key": api_key_value,
        "project_id": project_id,
        "created_at": datetime.now(UTC),
        "expires_at": datetime.max if create_apikey_dto.expires_at == "NEVER" else create_apikey_dto.expires_at
      }
      
      # Creating the Apikey instance
      new_apikey = models.Apikey(**apikey_kwargs)

      # Adding to the session and committing
      db.add(new_apikey)
      db.commit()
      db.refresh(new_apikey)
      
      return apikey_schemas.ApikeyCreateResponseDTO.from_orm(new_apikey)
   except HTTPException as e:
      db.rollback()
      pprint(f'API error in POST /apikeys/ service method: {e}')
      raise e
   except SQLAlchemyError as e:
      db.rollback()
      pprint(f'DB error in POST /apikeys service method: Error creating apikey: {e}')
      request.state.source_error_msg = str(e)
      raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
   except Exception as e:
      db.rollback()
      pprint(f'Unexpected error in POST /apikeys service method: Error creating apikey: {e}')
      request.state.source_error_msg = str(e)
      raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")  

def get_apikey(
   request: Request,
   apikey: apikey_schemas.ApikeyGetResponseDTO
) -> apikey_schemas.ApikeyGetResponseDTO:
   try:
      return apikey_schemas.ApikeyGetResponseDTO.from_orm(apikey)
   except Exception as e:
      pprint(f'Unexpected error in GET /apikeys/{apikey.id} service method: Error retrieving apikey: {e}')
      request.state.source_error_msg = str(e)
      raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")  
   
def get_apikeys(
   request: Request,
   db: Session,
   logged_in_user: models.User,
   logged_in_user_is_account_admin: bool,
   logged_in_user_is_project_admin: bool,
   project_id : UUID
   )-> List[apikey_schemas.ApikeyGetResponseDTO]:
   try:
      query = db.query(models.Apikey)\
               .options(load_only( # exclude key
                  models.Apikey.id,
                  models.Apikey.name,
                  models.Apikey.project_id,
                  models.Apikey.creator_id,
                  models.Apikey.permissions, 
                  models.Apikey.permissions_type,
                  models.Apikey.created_at,
                  models.Apikey.expires_at
               ))
      if logged_in_user.is_superadmin or logged_in_user_is_account_admin or logged_in_user_is_project_admin:
         query = query.filter(models.Apikey.project_id == project_id)
      else:
         query = query.filter(models.Apikey.creator_id == logged_in_user.id,
                              models.Apikey.project_id == project_id)

      apikeys = query.all()
      return [apikey_schemas.ApikeyGetResponseDTO.from_orm(apikey) for apikey in apikeys] 
   except HTTPException as e:
      db.rollback()
      pprint(f'API error in GET /apikeys/ service method: {e}')
      raise e
   except SQLAlchemyError as e:
      db.rollback()
      pprint(f'DB error in GET /apikeys service method: Error retrieving apikeys: {e}')
      request.state.source_error_msg = str(e)
      raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
   except Exception as e:
      db.rollback()
      pprint(f'Unexpected error in GET /apikeys service method: Error retrieving apikeys: {e}')
      request.state.source_error_msg = str(e)
      raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")  

def delete_apikey(
   request: Request,
   db: Session,
   apikey : models.Apikey
   )-> JSONResponse:
   try:
      db.delete(apikey)
      db.commit()
      return JSONResponse(
         status_code=status.HTTP_200_OK,
         content={"message": f"Successfully revoked api key - '{apikey.id}'"},
      )
   except HTTPException as e:
      db.rollback()
      pprint(f'API error in DELETE /apikeys/{apikey.id} service method: {e}')
      raise e
   except SQLAlchemyError as e:
      db.rollback()
      pprint(f'DB error in DELETE /apikeys/{apikey.id} service method: Error deleting apikey: {e}')
      request.state.source_error_msg = str(e)
      raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
   except Exception as e:
      db.rollback()
      pprint(f'Unexpected error in DELETE /apikeys/{apikey.id} service method: Error deleting apikey: {e}')
      request.state.source_error_msg = str(e)
      raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")  
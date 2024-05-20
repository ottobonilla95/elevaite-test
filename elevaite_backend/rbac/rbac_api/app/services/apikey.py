
from fastapi import status, HTTPException
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

from elevaitedb.schemas import (
   apikey as apikey_schemas,
   permission as permission_schemas,
)
from elevaitedb.db import models

def create_apikey(
   create_apikey_dto: apikey_schemas.ApikeyCreate,
   project_id: UUID,
   db: Session,
   logged_in_user: models.User,
   logged_in_user_is_account_admin: bool,
   logged_in_user_is_project_admin: bool,
   logged_in_user_project_association: models.User_Project
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
            permissions = permission_schemas.ApikeyScopedRBACPermission.create("Allow").dict()
         else:
            permissions = permission_schemas.ApikeyScopedRBACPermission.map_to_apikey_scoped_permissions(logged_in_user_project_association.permission_overrides, permission_schemas.RBACPermissionScope.PROJECT_SCOPE) 
      else:
         permissions = create_apikey_dto.permissions.dict()

      # generate unique key
      api_key_value = f"eAI_{secrets.token_urlsafe(16)}"

      apikey_kwargs = {
        "name": create_apikey_dto.name,
        "creator_id": creator_id,
        "permissions_type": apikey_permissions_type,
        "permissions": permissions,
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
      raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
   except Exception as e:
      db.rollback()
      pprint(f'Unexpected error in POST /apikeys service method: Error creating apikey: {e}')
      raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")  

def get_apikeys(
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
      return cast(List[apikey_schemas.ApikeyGetResponseDTO], apikeys) 
   except HTTPException as e:
      db.rollback()
      pprint(f'API error in GET /apikeys/ service method: {e}')
      raise e
   except SQLAlchemyError as e:
      db.rollback()
      pprint(f'DB error in GET /apikeys service method: Error retrieving apikeys: {e}')
      raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
   except Exception as e:
      db.rollback()
      pprint(f'Unexpected error in GET /apikeys service method: Error retrieving apikeys: {e}')
      raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")  

def delete_apikey(
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
      raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
   except Exception as e:
      db.rollback()
      pprint(f'Unexpected error in DELETE /apikeys/{apikey.id} service method: Error deleting apikey: {e}')
      raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")  
from fastapi import status, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from typing import List, cast
from uuid import UUID
from datetime import datetime
from pprint import pprint

from elevaitedb.schemas import (
   role_schemas,
)
from elevaitedb.db import models

from ..errors.api_error import ApiError

def create_role(
    role_creation_dto: role_schemas.RoleCreationRequestDTO,
    db: Session
) -> role_schemas.RoleResponseDTO :
   try:
      existing_role = db.query(models.Role).filter(models.Role.name == role_creation_dto.name).first()
      if existing_role: # Application-side uniqueness check : Check if a user with the same email already exists in the specified account
         pprint(f'in POST /roles - A role with the same name already exists in roles table')
         raise ApiError.conflict(f"A role with name - '{role_creation_dto.name}' - already exists")
      new_role = models.Role(
         name=role_creation_dto.name,
         # permissions=role_creation_dto.permissions.model_dump(),
         permissions=role_creation_dto.permissions.dict(),
      )
      db.add(new_role)
      db.commit()
      db.refresh(new_role)
      return new_role
   except HTTPException as e:
      db.rollback()
      pprint(f'API error in POST /roles service method : {e}')
      raise e
   except IntegrityError as e: # Database-side uniqueness check : Check if an account with the same name already exists in the organization
      db.rollback()  
      pprint(f'DB error in POST /roles service method : {e}')
      raise ApiError.conflict(f"A role with name -'{role_creation_dto.name}'- already exists")
   except SQLAlchemyError as e: # group db side error as 503 to not expose actual error to client
      db.rollback()
      pprint(f'DB error in POST /roles service method : {e}')
      raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
   except Exception as e:
      db.rollback()
      pprint(f'Unexpected error in POST /roles service method: {e}')
      raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
   
def get_role(
   db: Session,
   role_id: UUID
   ) -> List[role_schemas.RoleResponseDTO]:
   try:
      role = db.query(models.Role).filter(models.Role.id == role_id).first()
      if not role:
         print(f"in GET /roles/{role_id} - validate_get_role dependency : role -'{role_id}'- not found in role table")
         raise ApiError.notfound(f"role - '{role_id}' - not found")
      return role
   except SQLAlchemyError as e: # group db side error as 503 to not expose actual error to client
      db.rollback()
      pprint(f'DB error in GET /roles service method : {e}')
      raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
   except Exception as e:
      db.rollback()
      pprint(f'Unexpected error in GET /roles service method: {e}')
      raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")

def get_roles(
    db: Session
) -> List[role_schemas.RoleResponseDTO]:
   try:
      query = db.query(models.Role)
      roles = query.all()
      return cast(List[role_schemas.RoleResponseDTO], roles)
   except SQLAlchemyError as e: # group db side error as 503 to not expose actual error to client
      db.rollback()
      pprint(f'DB error in GET /roles service method : {e}')
      raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
   except Exception as e:
      db.rollback()
      pprint(f'Unexpected error in GET /roles service method: {e}')
      raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
   
def patch_role(
   role_id: UUID,
   role_patch_req_payload: role_schemas.RoleUpdateRequestDTO,
   db: Session,
) -> role_schemas.RoleResponseDTO:
   try:
      db_role = db.query(models.Role).filter(models.Role.id == role_id).first()
      if not db_role:
         print(f'In PATCH: /roles/{role_id} service method : role -"{role_id}"- to patch not found')
         raise ApiError.notfound(f"role - '{role_id}' - not found")
         
      for key, value in vars(role_patch_req_payload).items():
         # print(f'key = {key}, value = {value}')
         if key == 'permissions':
            # value = value.model_dump()
            value = value.dict()
         # print(f'key = {key}, value = {value}')
         setattr(db_role, key, value) if value is not None else None
      db_role.updated_at = datetime.now()
      db.commit()
      db.refresh(db_role)
      return db_role
   except HTTPException as e:
      db.rollback()
      pprint(f'API error in PATCH /roles/{role_id} service method: {e}')
      raise e
   except SQLAlchemyError as e: # group db side error as 503 to not expose actual error to client
      db.rollback()
      pprint(f'DB error in PATCH /roles/{role_id} service method: {e}')
      raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
   except Exception as e:
      db.rollback()
      pprint(f'Unexpected error in PATCH /roles/{role_id} service method: {e}')
      raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
   
def delete_role(
   db: Session,
   role_id: UUID
) -> JSONResponse:
   try:
      role = db.query(models.Role).filter(models.Role.id == role_id).first()
      if not role:
         print(f'in DELETE /roles/{role_id} service method : role - "{role_id}" - not found')
         raise ApiError.notfound(f"role - '{role_id}' - not found")
      
      db.delete(role)
      db.commit()
      return JSONResponse(
         status_code=status.HTTP_200_OK,
         content={"message": f"Successfully deleted role"},
      )
   except HTTPException as e:
      db.rollback()
      pprint(f'API error in DELETE /roles/{role_id} service method: {e}')
      raise e
   except SQLAlchemyError as e: # group db side error as 503 to not expose actual error to client
      db.rollback()
      pprint(f'DB error in DELETE /roles/{role_id} service method : {e}')
      raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
   except Exception as e:
      db.rollback()
      pprint(f'Unexpected error in DELETE /roles/{role_id} service method: {e}')
      raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
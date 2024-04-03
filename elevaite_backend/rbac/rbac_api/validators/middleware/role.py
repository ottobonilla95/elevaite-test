from fastapi import Depends, Path, HTTPException
from sqlalchemy import exists, and_
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from uuid import UUID
from pprint import pprint
from typing import Any
from .header import validate_token
from rbac_api.app.errors.api_error import ApiError

from rbac_api.utils.deps import get_db
from elevaitedb.db import models

async def validate_post_roles(
   user_email: str = Depends(validate_token),
   db: Session = Depends(get_db)
) -> dict[str, Any]:
   try:
      # Fetch user by email
      logged_in_user = db.query(models.User).filter(models.User.email == user_email).first()
      if not logged_in_user:
         print(f"in in validate_post_patch_delete_roles dependency : logged-in user with email -'{user_email}'- not found in user table")
         raise ApiError.unauthorized("user is unauthenticated")

      # Validate if the user is a superadmin
      if logged_in_user.is_superadmin: 
         return {"db" : db}
      
      print(f"in validate_post_roles dependency : logged in user -'{logged_in_user.id}'- does not have super-admin privileges to create roles")
      raise ApiError.forbidden("you do not have superadmin privileges to create roles")
   except HTTPException as e:
      db.rollback()
      pprint(f'API error in validate_post_roles dependency : {e}')
      raise e
   except SQLAlchemyError as e:
      pprint(f'DB error in validate_post_roles dependency : {e}')
      raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
   except Exception as e:
      db.rollback()
      print(f'Unexpected error in validate_post_roles dependency : {e}')
      raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
   
async def validate_delete_roles(
   user_email: str = Depends(validate_token),
   db: Session = Depends(get_db)
) -> dict[str, Any]:
   try:
      # Fetch user by email
      logged_in_user = db.query(models.User).filter(models.User.email == user_email).first()
      if not logged_in_user:
         print(f"in in validate_delete_roles dependency : logged-in user with email -'{user_email}'- not found in user table")
         raise ApiError.unauthorized("user is unauthenticated")

      # Validate if the user is a superadmin
      if logged_in_user.is_superadmin: 
         return {"db" : db}
      
      print(f"in validate_delete_roles dependency : logged in user -'{logged_in_user.id}'- does not have super-admin privileges to delete roles")
      raise ApiError.forbidden("you do not have superadmin privileges to delete roles")
   except HTTPException as e:
      db.rollback()
      pprint(f'API error in validate_delete_roles dependency : {e}')
      raise e
   except SQLAlchemyError as e:
      pprint(f'DB error in validate_delete_roles dependency : {e}')
      raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
   except Exception as e:
      db.rollback()
      print(f'Unexpected error in validate_delete_roles dependency : {e}')
      raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")

async def validate_patch_roles(
   user_email: str = Depends(validate_token),
   db: Session = Depends(get_db)
) -> dict[str, Any]:
   try:
      # Fetch user by email
      logged_in_user = db.query(models.User).filter(models.User.email == user_email).first()
      if not logged_in_user:
         print(f"in in validate_post_patch_delete_roles dependency : logged-in user with email -'{user_email}'- not found in user table")
         raise ApiError.unauthorized("user is unauthenticated")

      # Validate if the user is a superadmin
      if logged_in_user.is_superadmin: 
         return {"db" : db}
      
      print(f"in validate_patch_roles dependency : logged in user -'{logged_in_user.id}'- does not have super-admin privileges to update roles")
      raise ApiError.forbidden("you do not have superadmin privileges to update roles")
   except HTTPException as e:
      db.rollback()
      pprint(f'API error in validate_patch_roles dependency : {e}')
      raise e
   except SQLAlchemyError as e:
      pprint(f'DB error in validate_patch_roles dependency : {e}')
      raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
   except Exception as e:
      db.rollback()
      print(f'Unexpected error in validate_patch_roles dependency : {e}')
      raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")

async def validate_get_roles(
   user_email: str = Depends(validate_token),
   db: Session = Depends(get_db)
) -> dict[str, Any]:
   try:
      # Fetch user by email
      logged_in_user = db.query(models.User).filter(models.User.email == user_email).first()
      if not logged_in_user:
         print(f"in GET /roles/ - validate_get_all_roles dependency : logged-in user with email -'{user_email}'- not found in user table")
         raise ApiError.unauthorized("user is unauthenticated")

      # Validate if the logged-in user is a superadmin
      if logged_in_user.is_superadmin: 
         return {"db" : db}
      
      # validate if logged-in user is an admin in any account
      user_admin_accounts_exist = db.query(exists().where(
        and_(
            models.User_Account.user_id == logged_in_user.id,
            models.User_Account.is_admin == True
        )
      )).scalar()
      if user_admin_accounts_exist:
         return {"db" : db}
      
      print(f"in GET /roles/ - validate_get_all_roles dependency : logged in user -'{logged_in_user.id}'- does not have superadmin/admin privileges to read all roles")
      raise ApiError.forbidden("you do not have superadmin/admin privileges to read all roles")
   except HTTPException as e:
      db.rollback()
      pprint(f'API error GET /roles/ - validate_get_all_roles dependency : {e}')
      raise e
   except SQLAlchemyError as e:
      pprint(f'DB error in GET /roles/ - validate_get_all_roles dependency : {e}')
      raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
   except Exception as e:
      db.rollback()
      print(f'Unexpected error in GET /roles/ - validate_get_all_roles dependency : {e}')
      raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
   
async def validate_get_role(
   user_email: str = Depends(validate_token),
   role_id: UUID = Path(..., description = "Role ID to retrieve"),
   db: Session = Depends(get_db)
) -> dict[str, Any]:
   try:
      # Fetch user by email
      logged_in_user = db.query(models.User).filter(models.User.email == user_email).first()
      if not logged_in_user:
         print(f"in GET /roles/{role_id} - validate_get_role dependency : logged-in user with email -'{user_email}'- not found in user table")
         raise ApiError.unauthorized("user is unauthenticated")
      
      return {"db" : db} # Allow access to all users to get role.
   except HTTPException as e:
      db.rollback()
      pprint(f'API error in GET /roles/{role_id} - validate_get_role dependency : {e}')
      raise e
   except SQLAlchemyError as e:
      pprint(f'DB error in GET /roles/{role_id} - validate_get_role dependency : {e}')
      raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
   except Exception as e:
      db.rollback()
      print(f'Unexpected error in GET /roles/{role_id} - validate_get_role dependency : {e}')
      raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
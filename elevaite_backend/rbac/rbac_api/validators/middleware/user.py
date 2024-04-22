from fastapi import Depends, Body, Path, Depends, HTTPException, Request, Header
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from uuid import UUID
from pprint import pprint
from typing import Any, Type, Optional
from rbac_api.app.errors.api_error import ApiError
from .header import validate_token

from rbac_api.utils.deps import get_db
from elevaitedb.db import models
from elevaitedb.schemas import (
   user_schemas,
)
from rbac_api.utils.cte import (
   is_user_project_association_till_root,
)
from ..rbac import rbac_instance

async def validate_post_user(
   user_creation_payload: user_schemas.UserCreationRequestDTO = Body(description= "user creation payload"),  
   user_email: str = Depends(validate_token), 
   db: Session = Depends(get_db)
) -> dict[str, Any]:
   """
   For now, every user is allowed to register themselves. Include whitelist validation here later.
   Returns the user_email and db session for use in service method
   """
   try:
      if user_creation_payload.email != user_email:
         print(f"in POST /register - validate_post_user dependency: logged-in user does not have permissions to register user with email - '{user_creation_payload.email}'")
         raise ApiError.forbidden(f"you do not have permissions to register user with email - '{user_creation_payload.email}'")
      organization = db.query(models.Organization).filter(models.Organization.id == user_creation_payload.org_id).first()
      if not organization:
         print(f"in POST /register - validate_post_user dependency: Organization - '{user_creation_payload.org_id}' - not found")
         raise ApiError.notfound(f"Organization - '{user_creation_payload.org_id}' - not found")
      return {"db" : db}
   except HTTPException as e:
      db.rollback()
      pprint(f'API error in POST /register - validate_post_user middleware: {e}')
      raise e
   except SQLAlchemyError as e:
      pprint(f'DB error in POST /register - validate_post_user middleware: {e}')
      raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
   except Exception as e:
      db.rollback()
      print(f'Unexpected error in POST /register - validate_post_user middleware: {e}')
      raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")

def validate_get_user_profile_factory(target_model_class : Type[models.Base], target_model_action_sequence: tuple[str, ...]):
   async def validate_get_user_profile(
      request: Request,
      user_email: str = Depends(validate_token), 
      user_id: UUID = Path(..., description="user id of user whose profile is retrieved"),
      account_id: Optional[UUID] = Header(None, alias = "X-elevAIte-AccountId", description="account_id under which user profile is queried"),
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
         pprint(f'API error in GET /users/{user_id}/profile - validate_get_user_profile middleware: {e}')
         raise e
      except SQLAlchemyError as e:
         pprint(f'DB error in GET /users/{user_id}/profile - validate_get_user_profile middleware: {e}')
         raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
      except Exception as e:
         db.rollback()
         print(f'Unexpected error in GET /users/{user_id}/profile - validate_get_user_profile middleware: {e}')
         raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
   
   return validate_get_user_profile

async def validate_patch_user(
   user_email: str = Depends(validate_token),
   user_id: UUID = Path(..., description="The ID of the user to patch"),
   db: Session = Depends(get_db)
) -> dict[str, Any]:
   try:
      # Fetch user by email
      logged_in_user = db.query(models.User).filter(models.User.email == user_email).first()
      if not logged_in_user:
         raise ApiError.unauthorized("User is unauthenticated")

      user_to_patch = db.query(models.User).filter(models.User.id == user_id).first()
      if not user_to_patch:
         raise ApiError.notfound(f"User - '{user_id}' - not found")
         
      # Validate if the current user is a superadmin
      if logged_in_user.is_superadmin: 
         return {"User" : user_to_patch, "db" : db}

      # Check if the current user is trying to patch their own data
      if logged_in_user.id == user_id: 
         return {"User" : user_to_patch, "db" : db}

      # If the flow reaches here, the user does not have superadmin/account-admin permissions
      raise ApiError.forbidden(f"you do not have superadmin/account-admin privileges to update User - '{user_id}'")
   except HTTPException as e:
      db.rollback()
      pprint(f'API error in PATCH: /users/{user_id} - validate_patch_user middleware : {e}')
      raise e
   except SQLAlchemyError as e:
      pprint(f'DB error in PATCH: /users/{user_id} - validate_patch_user middleware : {e}')
      raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
   except Exception as e:
      db.rollback()
      print(f'Unexpected error in PATCH: /users/{user_id} - validate_patch_user middlware : {e}')
      raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")

def validate_patch_user_account_roles_factory(target_model_class : Type[models.Base], target_model_action_sequence: tuple[str, ...]):
   async def validate_patch_user_account_roles(
      request: Request,
      user_email: str = Depends(validate_token),
      user_id: UUID = Path(..., description="The ID of the user to patch"),
      account_id: UUID = Path(..., description="The ID of the account to scope the user roles to"),
      db: Session = Depends(get_db)
   ) -> dict[str, Any]:
      try:

         validation_info:dict[str, Any] = await rbac_instance.validate_rbac(
            request=request,
            db=db,
            target_model_action_sequence=target_model_action_sequence,
            user_email=user_email,
            target_model_class=target_model_class
         )

         logged_in_user = validation_info.get("logged_in_user", None)
         
         if logged_in_user:
            if logged_in_user.is_superadmin:
               return validation_info 
         
         logged_in_user_account_association = validation_info.get("logged_in_user_account_association",None)
         
         if logged_in_user_account_association:
            if logged_in_user_account_association.is_admin:
               return validation_info

         raise ApiError.forbidden(f"you do not have superadmin/account-admin privileges to update user-account roles in account - '{account_id}'")
         
      except HTTPException as e:
         db.rollback()
         pprint(f'API error in PATCH /users/{user_id}/accounts/{account_id}/roles validate_patch_user_account_roles dependency: {e}')
         raise e
      except SQLAlchemyError as e:
         db.rollback()
         pprint(f'DB error in PATCH /users/{user_id}/accounts/{account_id}/roles validate_patch_user_account_roles dependency: {e}')
         raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
      except Exception as e:
         db.rollback()
         print(f'Unexpected error in PATCH /users/{user_id}/accounts/{account_id}/roles validate_patch_user_account_roles dependency: {e}')
         raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
   
   return validate_patch_user_account_roles
   
def validate_update_project_permission_overrides_factory(target_model_class : Type[models.Base], target_model_action_sequence: tuple[str, ...]):
   async def validate_update_project_permission_overrides(
      request: Request,
      user_email: str = Depends(validate_token),
      user_id: UUID = Path(..., description="The ID of the user to update project-specific permission-overrides for"),
      account_id: UUID = Header(..., alias = "X-elevAIte-AccountId", description="The ID of the account that contains the project"),
      project_id: UUID = Path(..., description="The ID of the project to update user-specific permission-overrides on"),
      db: Session = Depends(get_db)
   ) -> dict[str, Any]:
      try:

         validation_info:dict[str, Any] = await rbac_instance.validate_rbac(
            request=request,
            db=db,
            target_model_action_sequence=target_model_action_sequence,
            user_email=user_email,
            target_model_class=target_model_class
         )

         logged_in_user = validation_info.get("logged_in_user", None)
         
         if logged_in_user:
            if logged_in_user.is_superadmin:
               return validation_info 
         
         logged_in_user_account_association = validation_info.get("logged_in_user_account_association",None)
         
         if logged_in_user_account_association:
            if logged_in_user_account_association.is_admin:
               return validation_info

         logged_in_user_project_association = validation_info.get("logged_in_user_project_association", None)
         
         if logged_in_user_project_association:
            if logged_in_user_project_association.is_admin:
               return validation_info
         
         raise ApiError.forbidden(f"you do not have superadmin,admin or project association with project-admin privileges to update project permission overrides for user - '{user_id}' - in project - '{project_id}'")

      except HTTPException as e:
         db.rollback()
         pprint(f'API error in PATCH users/{user_id}/projects/{project_id}/permission-overrides - validate_update_project_permission_overrides dependency: {e}')
         raise e
      except SQLAlchemyError as e:
         db.rollback()
         pprint(f'DB error in PATCH users/{user_id}/projects/{project_id}/permission-overrides - validate_update_project_permission_overrides dependency: {e}')
         raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
      except Exception as e:
         db.rollback()
         print(f'Unexpected error in PATCH users/{user_id}/projects/{project_id}/permission-overrides - validate_update_project_permission_overrides dependency: {e}')
         raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
   
   return validate_update_project_permission_overrides

def validate_get_project_permission_overrides_factory(target_model_class : Type[models.Base], target_model_action_sequence: tuple[str, ...]):
   async def validate_get_project_permission_overrides(
      request: Request,
      user_email: str = Depends(validate_token),
      user_id: UUID = Path(..., description="The ID of the user to get project-specific permission-overrides for"),
      account_id: UUID = Header(..., alias = "X-elevAIte-AccountId", description="The ID of the account that contains the project"),
      project_id: UUID = Path(..., description="The ID of the project to get user-specific permission-overrides for"),
      db: Session = Depends(get_db)
   ) -> dict[str, Any]:
      try:
         validation_info:dict[str, Any] = await rbac_instance.validate_rbac(
            request=request,
            db=db,
            target_model_action_sequence=target_model_action_sequence,
            user_email=user_email,
            target_model_class=target_model_class
         )

         logged_in_user = validation_info.get("logged_in_user", None)
         
         if logged_in_user:
            if logged_in_user.is_superadmin or logged_in_user.id == user_id:
               return validation_info 

         logged_in_user_account_association = validation_info.get("logged_in_user_account_association",None)
         
         if logged_in_user_account_association:
            if logged_in_user_account_association.is_admin:
               return validation_info

         logged_in_user_project_association = validation_info.get("logged_in_user_project_association", None)
         
         if logged_in_user_project_association:
            if logged_in_user_project_association.is_admin:
               return validation_info
         
         raise ApiError.forbidden(f"you do not have superadmin,admin or project association with project-admin privileges to read project permission overrides for user - '{user_id}' - in project - '{project_id}'")
      except HTTPException as e:
         db.rollback()
         pprint(f'API error in GET users/{user_id}/projects/{project_id}/permission-overrides - validate_get_project_permission_overrides dependency: {e}')
         raise e
      except SQLAlchemyError as e:
         db.rollback()
         pprint(f'DB error in GET users/{user_id}/projects/{project_id}/permission-overrides - validate_get_project_permission_overrides dependency: {e}')
         raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
      except Exception as e:
         db.rollback()
         print(f'Unexpected error in GET users/{user_id}/projects/{project_id}/permission-overrides - validate_get_project_permission_overrides dependency: {e}')
         raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
   
   return validate_get_project_permission_overrides

async def validate_patch_user_superadmin_status(
   user_email: str = Depends(validate_token),
   user_id: UUID = Path(...),
   db: Session = Depends(get_db)
) -> dict[str, Any]:
   try:
      # Fetch user by email
      logged_in_user = db.query(models.User).filter(models.User.email == user_email).first()
      if not logged_in_user:
         raise ApiError.unauthorized("User is unauthenticated")
      
      # Check if the user is superadmin
      if not logged_in_user.is_superadmin: 
         raise ApiError.forbidden(f"you do not have superadmin privileges to update user superadmin status")
      
      return {"logged_in_user" : logged_in_user, "db": db}
   except HTTPException as e:
      db.rollback()
      pprint(f'API error in PATCH /users/{user_id}/superadmin - validate_update_user_superadmin_status middleware: {e}')
      raise e
   except SQLAlchemyError as e:
      db.rollback()
      pprint(f'DB error in PATCH /users/{user_id}/superadmin - validate_update_user_superadmin_status middleware: {e}')
      raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
   except Exception as e:
      db.rollback()
      print(f'Unexpected error in PATCH /users/{user_id}/superadmin - validate_update_user_superadmin_status middleware: {e}')
      raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")


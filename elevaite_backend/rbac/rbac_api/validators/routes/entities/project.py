from fastapi import Path, Depends, HTTPException, Header, Request, Query
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from pprint import pprint
from typing import Optional, Any, Type
from rbac_api.app.errors.api_error import ApiError
from rbac_api.auth.impl import AccessTokenAuthentication
 
from elevaitedb.db import models
from ...rbac_validator.rbac_validator_provider import RBACValidatorProvider
import inspect
# from ....audit import AuditorProvider
rbacValidator = RBACValidatorProvider.get_instance()

def validate_get_project_factory(target_model_class : Type[models.Base], target_model_action_sequence: tuple[str, ...]):
   async def validate_get_project(
      request: Request,
      logged_in_user: models.User = Depends(AccessTokenAuthentication.authenticate),  
      project_id: UUID = Path(..., description="project_id to query"),
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

         return await rbacValidator.validate_rbac_permissions(
            request=request,
            db=db,
            target_model_action_sequence=target_model_action_sequence,
            authenticated_entity=logged_in_user,
            target_model_class=target_model_class
         )
      except HTTPException as e:
         db.rollback()
         pprint(f'API error in GET /projects/{project_id} - validate_get_project middleware: {e}')
         raise e
      except SQLAlchemyError as e:
         db.rollback()
         print(f'DB error in GET /projects/{project_id} - validate_get_project middleware: {e}')
         raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
      except Exception as e:
         db.rollback()
         print(f'Unexpected error in GET /projects/{project_id} - validate_get_project middleware: {e}')
         raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
   
   return validate_get_project

def validate_get_projects_factory(target_model_class : Type[models.Base], target_model_action_sequence: tuple[str, ...]):
   async def validate_get_projects(
         request: Request,
         logged_in_user: models.User = Depends(AccessTokenAuthentication.authenticate),  
         # The params below are required for pydantic validation even when unused
         account_id: UUID = Header(..., alias = "X-elevAIte-AccountId", description="account_id under which project is queried"),
         project_id: Optional[UUID] = Header(None, alias = "X-elevAIte-ProjectId", description="optional parent project_id under which projects are queried"),
      ) -> dict[str,Any]:
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

         return await rbacValidator.validate_rbac_permissions(
            request=request,
            db=db,
            target_model_action_sequence=target_model_action_sequence,
            authenticated_entity=logged_in_user,
            target_model_class=target_model_class
         )
      except HTTPException as e:
         db.rollback()
         pprint(f'API error in GET - /projects/ validate_get_projects middleware : {e}')
         raise e
      except SQLAlchemyError as e:
         db.rollback()
         pprint(f'DB error in GET - /projects/ validate_get_projects middleware: {e}')
         raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
      except Exception as e:
         db.rollback()
         print(f'Unexpected error in GET - /projects/ - validate_get_projects middleware: {e}')
         raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
   return validate_get_projects


def validate_get_project_user_list_factory(target_model_class : Type[models.Base], target_model_action_sequence: tuple[str, ...]):
   async def validate_get_project_user_list(
      request: Request,
      logged_in_user: models.User = Depends(AccessTokenAuthentication.authenticate),  
      project_id: UUID = Path(..., description="Project id under which users are queried"),
      child_project_id: UUID = Query(None, description="Optional param to filter project user's by their assignment to immediate child project")
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

         validation_info:dict[str, Any] = await rbacValidator.validate_rbac_permissions(
            request=request,
            db=db,
            target_model_action_sequence=target_model_action_sequence,
            authenticated_entity=logged_in_user,
            target_model_class=target_model_class
         )

         logged_in_user = validation_info.get("authenticated_entity", None)
         logged_in_user_account_association = validation_info.get("logged_in_entity_account_association", None)
         account = validation_info.get("Account", None)

         if child_project_id:
            child_project = db.query(models.Project).filter(models.Project.id == child_project_id).first()
            if not child_project or child_project.parent_project_id != project_id:
               raise ApiError.notfound(f"Immediate child project - '{child_project_id}' - not found under parent project - '{project_id}'")
         
         if (logged_in_user and logged_in_user.is_superadmin) or (logged_in_user_account_association and logged_in_user_account_association.is_admin):
            return validation_info
         
         if child_project_id:
            logged_in_user_child_project_association = db.query(models.User_Project).filter(models.User_Project.user_id == logged_in_user.id,
                                                                                          models.User_Project.project_id == child_project_id).first()
            if not logged_in_user_child_project_association or not logged_in_user_child_project_association.is_admin:
               raise ApiError.forbidden(f"logged-in user - '{logged_in_user.id}' - does not have superadmin privileges or account-admin privileges in account - '{account.id}' - or project-admin privileges in child project - '{child_project_id}' - to filter project users with child project filters")

         return validation_info
      except HTTPException as e:
            db.rollback()
            pprint(f'API error in GET /projects/{project_id}/users - validate_get_project_user_list middleware : {e}')
            raise e
      except SQLAlchemyError as e:
         pprint(f'DB error in GET /projects/{project_id}/users - validate_get_project_user_list middleware : {e}')
         raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
      except Exception as e:
         print(f'Unexpected error in GET /projects/{project_id}/users - validate_get_project_user_list middleware : {e}')
         raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
   
   return validate_get_project_user_list

def validate_patch_project_factory(target_model_class : Type[models.Base], target_model_action_sequence: tuple[str, ...]):
   async def validate_patch_project(
      request: Request,
      logged_in_user: models.User = Depends(AccessTokenAuthentication.authenticate),  
      project_id: UUID = Path(..., description="The ID of the project to patch"),
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

         validation_info:dict[str, Any] =  await rbacValidator.validate_rbac_permissions(
            request=request,
            db=db,
            target_model_action_sequence=target_model_action_sequence,
            authenticated_entity=logged_in_user,
            target_model_class=target_model_class
         )
         
         if logged_in_user:
            if logged_in_user.is_superadmin:
               return validation_info 
         
         logged_in_user_account_association = validation_info.get("logged_in_entity_account_association",None)
         
         if logged_in_user_account_association:
            if logged_in_user_account_association.is_admin:
               return validation_info

         logged_in_user_project_association = validation_info.get("logged_in_entity_project_association", None)
         
         if logged_in_user_project_association:
            if logged_in_user_project_association.is_admin:
               return validation_info

         raise ApiError.forbidden(f"logged-in user - '{logged_in_user.id}' - does not have superadmin/account-admin or project-admin permissions to update project - '{project_id}'")
         
      except HTTPException as e:
         db.rollback()
         pprint(f'API error in PATCH /projects/{project_id} - validate_patch_project middleware : {e}')
         raise e
      except SQLAlchemyError as e:
         db.rollback()
         pprint(f'DB error in PATCH /projects/{project_id}  - validate_patch_project middleware: {e}')
         raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
      except Exception as e:
         db.rollback()
         print(f'Unexpected error in PATCH /projects/{project_id} - validate_patch_project middleware : {e}')
         raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
   return validate_patch_project

def validate_post_project_factory(target_model_class : Type[models.Base], target_model_action_sequence: tuple[str, ...]):
   async def validate_post_project( # cascade delete on associations will make this work as intended. disabled status of account and projects need to be checked
      request: Request,
      logged_in_user: models.User = Depends(AccessTokenAuthentication.authenticate),  
      # The params below are required for pydantic validation even when unused
      project_id: Optional[UUID] = Header(None, alias = "X-elevAIte-ProjectId", description="The ID of the parent project to post under"),
      account_id: UUID = Header(..., alias = "X-elevAIte-AccountId", description="account_id in which project is posted"),
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

         return await rbacValidator.validate_rbac_permissions(
            request=request,
            db=db,
            target_model_action_sequence=target_model_action_sequence,
            authenticated_entity=logged_in_user,
            target_model_class=target_model_class
         )
      except HTTPException as e:
         db.rollback()
         pprint(f'API error in POST /projects/ - validate_post_project middleware : {e}')
         raise e
      except SQLAlchemyError as e:
         db.rollback()
         pprint(f'DB error in POST /projects validate_post_project: {e}')
         raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
      except Exception as e:
         db.rollback()
         print(f'Unexpected error in POST /projects - validate_post_projects middleware : {e}')
         raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
   return validate_post_project

def validate_assign_users_to_project_factory(target_model_class : Type[models.Base], target_model_action_sequence: tuple[str, ...]):
   async def validate_assign_users_to_project(
      request: Request,
      logged_in_user: models.User = Depends(AccessTokenAuthentication.authenticate),   
      project_id: UUID = Path(..., description ="The ID of the project"),
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

         validation_info:dict[str, Any] =  await rbacValidator.validate_rbac_permissions(
            request=request,
            db=db,
            target_model_action_sequence=target_model_action_sequence,
            authenticated_entity=logged_in_user,
            target_model_class=target_model_class
         )
         
         if logged_in_user:
            if logged_in_user.is_superadmin:
               return validation_info 
         
         logged_in_user_account_association = validation_info.get("logged_in_entity_account_association",None)
         
         if logged_in_user_account_association:
            if logged_in_user_account_association.is_admin:
               return validation_info

         logged_in_user_project_association = validation_info.get("logged_in_entity_project_association", None)
         
         if logged_in_user_project_association:
            if logged_in_user_project_association.is_admin:
               return validation_info
            
         # If flow reaches here, user does not have required permissions
         raise ApiError.forbidden(f"logged-in user - '{logged_in_user.id}' - does not have superadmin,account-admin or project-admin privileges to assign users to project - '{project_id}'")
      except HTTPException as e:
         db.rollback()
         pprint(f'API error in POST /projects/{project_id}/users - validate_assign_users_to_project middleware : {e}')
         raise e
      except SQLAlchemyError as e:
         # Handle SQLAlchemy errors
         db.rollback()
         pprint(f'DB error in POST /projects/{project_id}/users - validate_assign_users_to_project middleware : {e}')
         raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
      except Exception as e:
         db.rollback()
         print(f'Unexpected error in POST /projects/{project_id}/users - validate_assign_users_to_project middleware : {e}')
         raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
   return validate_assign_users_to_project   

def validate_deassign_user_from_project_factory(target_model_class : Type[models.Base], target_model_action_sequence: tuple[str, ...]):
   async def validate_deassign_user_from_project(
      request: Request,
      logged_in_user: models.User = Depends(AccessTokenAuthentication.authenticate),   
      project_id: UUID = Path(..., description ="The ID of the project"),
      user_id: UUID = Path(..., description = "The ID of the user to deassign from project"),
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

         validation_info:dict[str, Any] =  await rbacValidator.validate_rbac_permissions(
            request=request,
            db=db,
            target_model_action_sequence=target_model_action_sequence,
            authenticated_entity=logged_in_user,
            target_model_class=target_model_class
         )
         
         if logged_in_user:
            if logged_in_user.id == user_id or logged_in_user.is_superadmin:
               return validation_info

         logged_in_user_account_association = validation_info.get("logged_in_entity_account_association",None)
         
         if logged_in_user_account_association:
            if logged_in_user_account_association.is_admin:
               return validation_info

         logged_in_user_project_association = validation_info.get("logged_in_entity_project_association", None)
         
         if logged_in_user_project_association:
            if logged_in_user_project_association.is_admin:
               return validation_info
         
         # If flow reaches here, user does not have required permissions
         raise ApiError.forbidden(f"logged-in user - '{logged_in_user.id}' - does not have superadmin,account-admin or project-admin privileges to deassign user - '{user_id}' - from project - '{project_id}'")
      except HTTPException as e:
         db.rollback()
         pprint(f'API error in DELETE /projects/{project_id}/users/{user_id} - validate_deassign_user_from_project middleware : {e}')
         raise e
      except SQLAlchemyError as e:
         # Handle SQLAlchemy errors
         db.rollback()
         pprint(f'DB error in DELETE /projects/{project_id}/users/{user_id} - validate_deassign_user_from_project middleware : {e}')
         raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
      except Exception as e:
         db.rollback()
         print(f'Unexpected error in DELETE /projects/{project_id}/users/{user_id} - validate_deassign_user_from_project middleware : {e}')
         raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
   return validate_deassign_user_from_project   

def validate_update_user_project_admin_status_factory(target_model_class : Type[models.Base], target_model_action_sequence: tuple[str, ...]):
   async def validate_update_user_project_admin_status(
      request: Request,
      logged_in_user: models.User = Depends(AccessTokenAuthentication.authenticate),   
      project_id: UUID = Path(..., description ="The ID of the project"),
      user_id: UUID = Path(..., description = "ID of the user"),
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
            
         validation_info:dict[str, Any] =  await rbacValidator.validate_rbac_permissions(
            request=request,
            db=db,
            target_model_action_sequence=target_model_action_sequence,
            authenticated_entity=logged_in_user,
            target_model_class=target_model_class
         )
         
         if logged_in_user:
            if logged_in_user.is_superadmin:
               return validation_info 
         
         logged_in_user_account_association = validation_info.get("logged_in_entity_account_association",None)
         
         if logged_in_user_account_association:
            if logged_in_user_account_association.is_admin:
               return validation_info

         logged_in_user_project_association = validation_info.get("logged_in_entity_project_association", None)
         
         if logged_in_user_project_association:
            if logged_in_user_project_association.is_admin:
               return validation_info
            
         # If flow reaches here, user does not have required permissions
         raise ApiError.forbidden(f"logged-in user - '{logged_in_user.id}' - does not have superadmin,account-admin or project-admin privileges to update user project admin status in project - '{project_id}'")
      except HTTPException as e:
         db.rollback()
         pprint(f'API error in PATCH /projects/{project_id}/users/{user_id}/admin - validate_update_user_project_admin_status middleware : {e}')
         raise e
      except SQLAlchemyError as e:
         # Handle SQLAlchemy errors
         db.rollback()
         pprint(f'DB error in PATCH /projects/{project_id}/users/{user_id}/admin - validate_update_user_project_admin_status middleware : {e}')
         raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
      except Exception as e:
         db.rollback()
         print(f'Unexpected error in PATCH /projects/{project_id}/users/{user_id}/admin - validate_update_user_project_admin_status middleware : {e}')
         raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
   return validate_update_user_project_admin_status 
            

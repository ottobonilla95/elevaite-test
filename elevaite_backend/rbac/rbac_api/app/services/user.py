from fastapi import status, HTTPException, Request
from fastapi.responses import JSONResponse
from sqlalchemy import func,exists, and_
from sqlalchemy.orm import Session, aliased
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from typing import List, Optional, cast
from uuid import UUID
from datetime import datetime
from fastapi.encoders import jsonable_encoder
from pprint import pprint
import os 

from elevaitedb.schemas import (
   user as user_schemas,
   role as role_schemas,
   account as account_schemas,
   project as project_schemas,
   permission as permission_schemas,
)
from .utils.project_helpers import (
   get_top_level_associated_project_ids_for_user_in_all_non_admin_accounts,
)
from rbac_api.utils.cte import (
   delete_unrooted_user_project_associations_in_all_non_admin_accounts
)
from elevaitedb.db import models
from ..errors.api_error import ApiError

def get_user_profile(
   request: Request,
   user_to_profile: models.User,
   logged_in_user: models.User,
   account_id: Optional[UUID],
   db: Session
) -> user_schemas.UserProfileDTO:
   try:
      if account_id:
         user_account_association_exists = db.query(exists().where(and_(models.User_Account.user_id == user_to_profile.id, models.User_Account.account_id == account_id))).scalar()
         if not user_account_association_exists: 
            raise ApiError.validationerror(f"User - '{user_to_profile.id}' - is not assigned to account - '{account_id}'")
      
      # Initialize the user data structure
      user_data = {
         "id": user_to_profile.id,
         "organization_id": user_to_profile.organization_id,
         "firstname": user_to_profile.firstname,
         "lastname": user_to_profile.lastname,
         "email": user_to_profile.email,
         "is_superadmin": user_to_profile.is_superadmin,
         "created_at": user_to_profile.created_at,
         "updated_at": user_to_profile.updated_at,
         "account_memberships": []
      }

      # Base query for User_Account with joined Account to get account name
      user_accounts_query = db.query(
         models.User_Account,
         models.Account.name.label("account_name")
      ).join(
         models.Account, models.User_Account.account_id == models.Account.id
      )

      # Modify the query based on whether the logged-in user is a superadmin
      if logged_in_user.is_superadmin:
         # If logged-in user is a superadmin, fetch all user_accounts where user is a member, since superadmin can see all accounts.
         user_accounts_query = user_accounts_query.filter(
            models.User_Account.user_id == user_to_profile.id
         )
      else: # if logged-in user is not a superadmin, he should only be able to see common accounts 
         logged_in_user_accounts_subquery = db.query( # Get account IDs associated with the logged-in user
            models.User_Account.account_id
         ).filter(
            models.User_Account.user_id == logged_in_user.id
         ).subquery()

         # Use .alias() to reference the column in the subquery for use with .in_()
         logged_in_user_accounts_alias = logged_in_user_accounts_subquery.alias()
         
         # Filter user accounts to include only those where account_id matches
         # both the target user and logged-in user
         user_accounts_query = user_accounts_query.filter(
            models.User_Account.user_id == user_to_profile.id,
            models.User_Account.account_id.in_(db.query(logged_in_user_accounts_alias.c.account_id))
         )
         
      user_accounts = user_accounts_query.all()
      
      for user_account, account_name in user_accounts:
         # if user is superadmin or account-admin, do not fetch roles
         if user_to_profile.is_superadmin or user_account.is_admin:
            account_membership = {
               "account_id": user_account.account_id,
               "account_name": account_name,  
               "is_admin": user_account.is_admin,
               "roles": []
            }
         else:
            # Fetch Account-Scoped Roles for Each User_Account using user_account.id
            roles = db.query(models.Role)\
                        .join(models.Role_User_Account, models.Role_User_Account.role_id == models.Role.id)\
                        .filter(models.Role_User_Account.user_account_id == user_account.id)\
                        .all()
            
            role_summary_dto = [role_schemas.RoleSummaryDTO.from_orm(role) for role in roles]
            account_membership = {
               "account_id": user_account.account_id,
               "account_name": account_name,  
               "is_admin": user_account.is_admin,
               "roles": role_summary_dto
            }
         user_data["account_memberships"].append(account_membership)
        
      # Convert dictionary to UserProfileDTO instance
      user_profile_dto = user_schemas.UserProfileDTO(**user_data)
      return user_profile_dto
   
   except HTTPException as e:
      db.rollback()
      pprint(f'API error in GET /users/{user_to_profile.id}/profile service method : {e}')
      raise e
   except SQLAlchemyError as e:
      db.rollback()
      pprint(f'Error in GET /users/{user_to_profile.id}/profile service method : {e}')
      request.state.source_error_msg = str(e)
      raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
   except Exception as e:
      db.rollback()
      pprint(f'Unexpected error in GET /users/{user_to_profile.id}/profile service method : {e}')
      request.state.source_error_msg = str(e)
      raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")

def get_user_accounts(
   request: Request,
   db: Session,
   user_id: UUID,
) -> List[account_schemas.AccountResponseDTO]:
   try:
      user = db.query(models.User).filter(models.User.id == user_id).first()
      if not user:
         raise ApiError.notfound(f"User - '{user_id}' - not found")
      
      query = db.query(models.Account)\
               .join(models.User_Account, models.Account.id == models.User_Account.account_id)\
               .filter(models.User_Account.user_id == user_id)
      
      accounts = query.all()
      return [account_schemas.AccountResponseDTO.from_orm(account) for account in accounts]
   except HTTPException as e:
      db.rollback()
      pprint(f'API error in GET /users/{user_id}/accounts service method : {e}')
      raise e
   except SQLAlchemyError as e:
      db.rollback()
      pprint(f'Error in GET /users/{user_id}/accounts service method : {e}')
      request.state.source_error_msg = str(e)
      raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
   except Exception as e:
      db.rollback()
      pprint(f'Unexpected error in GET /users/{user_id}/accounts service method : {e}')
      request.state.source_error_msg = str(e)
      raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")

def get_user_projects( 
   request: Request,
   db: Session,
   user_id: UUID,
   account_id : UUID
) -> List[project_schemas.ProjectResponseDTO]:
   try:
      user = db.query(models.User).filter(models.User.id == user_id).first()
      if not user:
         raise ApiError.notfound(f"User - '{user_id}' - not found")
      
      query = db.query(models.Project)\
               .join(models.User_Project, models.User_Project.project_id == models.Project.id)\
               .filter(
                  models.Project.account_id == account_id,
                  models.User_Project.user_id == user_id,
               )            

      projects = query.all()
      return [project_schemas.ProjectResponseDTO.from_orm(project) for project in projects]
   except SQLAlchemyError as e:
      db.rollback()
      pprint(f'DB error in GET users/{user_id}/projects/ service method: {e}')
      request.state.source_error_msg = str(e)
      raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
   except Exception as e:
      db.rollback()
      print(f'Unexpected error in GET users/{user_id}/projects/ service method: {e}')
      request.state.source_error_msg = str(e)
      raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
   
def patch_user(
   request: Request,
   user_to_patch: models.User,
   user_patch_payload: user_schemas.UserPatchRequestDTO,
   db: Session
) -> user_schemas.OrgUserListItemDTO:
   try:
      for key, value in vars(user_patch_payload).items():
         setattr(user_to_patch, key, value) if value is not None else None
      user_to_patch.updated_at = datetime.now()
      db.commit()
      db.refresh(user_to_patch)
      return user_schemas.OrgUserListItemDTO.from_orm(user_to_patch)
   except HTTPException as e:
      db.rollback()
      pprint(f'API Error in PATCH /users/{user_to_patch.id} service method: {e}')
      raise e
   except SQLAlchemyError as e:
      db.rollback()
      pprint(f'Error in PATCH /users/{user_to_patch.id} service method: {e}')
      request.state.source_error_msg = str(e)
      raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
   except Exception as e:
      db.rollback()
      pprint(f'Unexpected error in PATCH /users/{user_to_patch.id} service method: {e}')
      request.state.source_error_msg = str(e)
      raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
   
def patch_user_account_roles(
   request: Request,
   user_to_patch: models.User,
   account_id: UUID,
   role_list_dto: role_schemas.RoleListDTO,
   db: Session,
) -> JSONResponse:
   try:
      if user_to_patch.is_superadmin:
         raise ApiError.validationerror(f"Invalid action : cannot patch account roles for superadmin user - {user_to_patch.id}")
         
      # Check User_Account association
      user_to_patch_account_association = db.query(models.User_Account).filter(models.User_Account.user_id == user_to_patch.id, models.User_Account.account_id == account_id).first()
      if not user_to_patch_account_association:
         raise ApiError.validationerror(f"User - '{user_to_patch.id}' - is not assigned to account - '{account_id}'")
      
      if user_to_patch_account_association.is_admin:
         raise ApiError.validationerror(f"Invalid action : cannot patch account roles for admin user - {user_to_patch.id}")
      
      RoleUserAccountAlias = aliased(models.Role_User_Account)
      UserAccountAlias = aliased(models.User_Account)

      # Scalar subquery to count the number of roles found in the database matching the provided role_ids
      roles_count_check = (
         db.query(func.count(models.Role.id))
         .filter(models.Role.id.in_(role_list_dto.role_ids))
         .as_scalar()
      )

      # Check for the count of existing roles in Role_User_Account for the provided role_ids and user_account_id
      existing_roles_check = (
         db.query(func.count(RoleUserAccountAlias.role_id))
         .join(UserAccountAlias, UserAccountAlias.id == RoleUserAccountAlias.user_account_id)
         .filter(RoleUserAccountAlias.role_id.in_(role_list_dto.role_ids),
                  UserAccountAlias.id == user_to_patch_account_association.id)
         .as_scalar()
      )

      # Combine everything into a single query
      result = db.query(
         existing_roles_check.label("count_existing_roles"),
         roles_count_check.label("count_found_roles")
      ).one()

      (count_existing_roles, count_found_roles)  = result
      
      if count_found_roles != len(role_list_dto.role_ids):
         print(f"in PATCH /{user_to_patch.id}/accounts/{account_id}/roles service method: one or more roles not found")
         raise ApiError.notfound("one or more roles not found")
      
      if role_list_dto.action == "Add" and count_existing_roles > 0:
         print(f"in PATCH /{user_to_patch.id}/accounts/{account_id}/roles service method: One or more account-scoped roles are already assigned to the user -'{user_to_patch.id}'- in account -'{account_id}'")
         raise ApiError.conflict(f"One or more account-scoped roles are already assigned to user - '{user_to_patch.id}' - in account - '{account_id}'")
      if role_list_dto.action == "Remove" and count_existing_roles != len(role_list_dto.role_ids):
         print(f"in PATCH /{user_to_patch.id}/accounts/{account_id}/roles service method: One or more roles to remove were not found for the user -'{user_to_patch.id}'- in account -'{account_id}'")
         raise ApiError.notfound(f"One or more roles to remove were not found for the user - '{user_to_patch.id}' - in account - '{account_id}'")      
      if role_list_dto.action == "Add":
         new_role_user_accounts = [
            models.Role_User_Account(user_account_id=user_to_patch_account_association.id, role_id=role_id)
            for role_id in role_list_dto.role_ids
         ]
         db.bulk_save_objects(new_role_user_accounts)
         db.commit()
         return JSONResponse(content = {"message" : f"Successfully added {len(role_list_dto.role_ids)} account-scoped role/(s) to user"}, status_code= status.HTTP_200_OK)
      else: # role_list_dto.action == "Remove":
         db.query(models.Role_User_Account).filter(
         models.Role_User_Account.user_account_id == user_to_patch_account_association.id,
         models.Role_User_Account.role_id.in_(role_list_dto.role_ids)
         ).delete(synchronize_session=False)  
         db.commit()
         return JSONResponse(content = {"message" : f"Successfully removed {len(role_list_dto.role_ids)} account-scoped role/(s) from user"}, status_code= status.HTTP_200_OK)
   
   except HTTPException as e:
      db.rollback()
      pprint(f'API Error in PATCH /users/{user_to_patch.id}/accounts/{account_id}/roles service method: {e}')
      raise e
   except IntegrityError as e : # Database-side uniqueness check 
        db.rollback()
        pprint(f'Error in PATCH /users/{user_to_patch.id}/accounts/{account_id}/roles service method: {e}')
        raise ApiError.conflict(f"One or more account-scoped roles for user already exists in account")
   except SQLAlchemyError as e:
      db.rollback()
      pprint(f'Error in PATCH /users/{user_to_patch.id}/accounts/{account_id}/roles service method: {e}')
      request.state.source_error_msg = str(e)
      raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
   except Exception as e:
      db.rollback()
      pprint(f'Unexpected error in PATCH /users/{user_to_patch.id} : {e}')
      request.state.source_error_msg = str(e)
      raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
   
def update_user_project_permission_overrides(
   request: Request,
   user_id: UUID,
   user_to_patch: models.User,
   account_id: UUID,
   project_id: UUID,
   permission_overrides_payload: permission_schemas.ProjectScopedRBACPermission,
   db: Session,
) -> JSONResponse:
   try:
      user_account_association = db.query(models.User_Account).filter(models.User_Account.user_id == user_id, models.User_Account.account_id == account_id).first()
      if not user_account_association:
         raise ApiError.validationerror(f"user - '{user_id}' - is not assigned to account - '{account_id}")
      
      user_project_association = db.query(models.User_Project).filter(models.User_Project.user_id == user_id, models.User_Project.project_id == project_id).first()
      if not user_project_association:
         raise ApiError.validationerror(f"user - '{user_id}' - is not assigned to project - '{project_id}'")
      
      if user_project_association.is_admin or user_account_association.is_admin or user_to_patch.is_superadmin:
         raise ApiError.validationerror(f"Invalid action - Attempting to update project permission overrides for user - '{user_id}' - who is admin/superadmin/project-admin")

      user_project_association.permission_overrides = permission_overrides_payload.dict(exclude_none=True) # exclude values with None
      db.commit()
      return JSONResponse(content={"message": f"Project permission overrides successfully updated for user"}, status_code=status.HTTP_200_OK)
   except HTTPException as e:
      db.rollback()
      pprint(f'API Error in PUT users/{user_id}/projects/{project_id}/permission-overrides service method: {e}')
      raise e
   except SQLAlchemyError as e:
      db.rollback()
      pprint(f'Error in PUT users/{user_id}/projects/{project_id}/permission-overrides service method: {e}')
      request.state.source_error_msg = str(e)
      raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
   except Exception as e:
      db.rollback()
      pprint(f'Unexpected error in PUT users/{user_id}/projects/{project_id}/permission-overrides service method: {e}')
      request.state.source_error_msg = str(e)
      raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
   
def get_user_project_permission_overrides(
   request: Request,
   user_to_patch: models.User,
   user_id: UUID,
   account_id: UUID,
   project_id: UUID,
   db: Session,
) -> permission_schemas.ProjectScopedRBACPermission:
   try:
      user_account_association = db.query(models.User_Account).filter(models.User_Account.user_id == user_id, models.User_Account.account_id == account_id).first()
      if not user_account_association:
         raise ApiError.validationerror(f"user - '{user_id}' - is not assigned to account - '{account_id}")
      
      user_project_association = db.query(models.User_Project).filter(models.User_Project.user_id == user_id, models.User_Project.project_id == project_id).first()
      if not user_project_association:
         raise ApiError.validationerror(f"user - '{user_id}' - is not assigned to project - '{project_id}'")
      
      if user_project_association.is_admin or user_account_association.is_admin or user_to_patch.is_superadmin:
         raise ApiError.validationerror(f"Invalid action - Attempting to get project permission overrides for user - '{user_id}' - who is admin/superadmin/project-admin")
      
      return permission_schemas.ProjectScopedRBACPermission.parse_obj(user_project_association.permission_overrides)
   except HTTPException as e:
      db.rollback()
      pprint(f'API Error in GET users/{user_id}/projects/{project_id}/permission-overrides service method: {e}')
      raise e
   except SQLAlchemyError as e:
      db.rollback()
      pprint(f'Error in GET users/{user_id}/projects/{project_id}/permission-overrides service method: {e}')
      request.state.source_error_msg = str(e)
      raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
   except Exception as e:
      db.rollback()
      pprint(f'Unexpected error in GET users/{user_id}/projects/{project_id}/permission-overrides service method: {e}')
      request.state.source_error_msg = str(e)
      raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
   
def patch_user_superadmin_status(
   request: Request,
   user_id: UUID,
   superadmin_status_update_dto: user_schemas.SuperadminStatusUpdateDTO,
   db: Session,
   logged_in_user_id: UUID
   )-> JSONResponse:
   try:
      if user_id == logged_in_user_id:
         raise ApiError.validationerror(f"Invalid action - cannot update superadmin status of self")
      
      # Check if user in payload exists
      user_in_payload = db.query(models.User).filter(models.User.id == user_id).first()
      if not user_in_payload:
         raise ApiError.notfound(f"User - '{user_id}' - not found")
      
      ROOT_SUPERADMIN_ID = UUID(os.getenv("ROOT_SUPERADMIN_ID"))
      if ROOT_SUPERADMIN_ID == user_id: # cannot update root superadmin's status
         raise ApiError.forbidden(f"logged-in user - '{logged_in_user_id}' - cannot update superadmin status of root superadmin user - '{user_id}'")
      
      match superadmin_status_update_dto.action:
         case "Grant":
            if not user_in_payload.is_superadmin:
               user_in_payload.is_superadmin = True

         case "Revoke":
            if user_in_payload.is_superadmin:
               top_level_associated_projects_in_non_admin_accounts: List[UUID] = get_top_level_associated_project_ids_for_user_in_all_non_admin_accounts(db, user_id)
               delete_unrooted_user_project_associations_in_all_non_admin_accounts(db,user_id, top_level_associated_projects_in_non_admin_accounts)
               user_in_payload.is_superadmin = False
         case _:
            raise ApiError.validationerror(f"unknown action - '{superadmin_status_update_dto.action}'")

      db.commit()
      return JSONResponse(content={"message": f"superadmin status successfully {'revoked' if superadmin_status_update_dto.action.lower() == 'revoke' else 'granted'}"}, status_code=status.HTTP_200_OK)
   except HTTPException as e:
      db.rollback()
      pprint(f'API error in PATCH /users/{user_id}/superadmin service method: {e}')
      raise e
   except SQLAlchemyError as e:
      db.rollback()
      pprint(f'DB error in PATCH /users/{user_id}/superadmin service method: Error updating superadmin status: {e}')
      request.state.source_error_msg = str(e)
      raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
   except Exception as e:
      db.rollback()
      pprint(f'Unexpected error in PATCH /users/{user_id}/superadmin service method: Error updating superadmin status: {e}')
      request.state.source_error_msg = str(e)
      raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")  
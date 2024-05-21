from fastapi import HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy import func, case, and_, select, exists
from sqlalchemy.orm import Session, aliased
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from typing import List, Optional, cast
from uuid import UUID
from datetime import datetime
from pprint import pprint
import os
from ..errors.api_error import ApiError

from elevaitedb.schemas import (
   account as account_schemas,
   role as role_schemas,
   user as user_schemas
)
from elevaitedb.db import models

from .utils.project_helpers import (
   get_top_level_associated_project_ids_for_user_in_account,
   delete_all_associated_user_projects_in_account
)
from rbac_api.utils.cte import (
   delete_unrooted_user_project_associations_in_account,
)

def create_account(
   account_creation_payload: account_schemas.AccountCreationRequestDTO,
   db: Session,
   logged_in_user_id: UUID 
   ) -> account_schemas.AccountResponseDTO: 
   
   try:
      # Check if the organization exists and if an account with the same name does not exist in the organization
      organization_exists_subquery = select(exists().where(models.Organization.id == account_creation_payload.organization_id))
      account_exists_subquery = select(exists().where(and_(models.Account.organization_id == account_creation_payload.organization_id, models.Account.name == account_creation_payload.name)))

      # Execute the subqueries in 1 db call
      organization_exists, account_exists = db.query(
         organization_exists_subquery.as_scalar(),
         account_exists_subquery.as_scalar()
      ).one()

      if not organization_exists:
         pprint(f"in POST /accounts/ service method : organization - '{account_creation_payload.organization_id}' - not found'")
         raise ApiError.notfound(f"organization - '{account_creation_payload.organization_id}' - not found")

      if account_exists:
         pprint(f"in POST /accounts/ service method : An account with name - '{account_creation_payload.name}' - already exists in organization - '{account_creation_payload.organization_id}'")
         raise ApiError.conflict(f"An account with name - '{account_creation_payload.name}' - already exists in organization - '{account_creation_payload.organization_id}'")
      # Create new account from req body
      new_account = models.Account(
         organization_id=account_creation_payload.organization_id,
         name=account_creation_payload.name,
         description=account_creation_payload.description,
         created_at=datetime.now(),
         updated_at=datetime.now()
      )

      db.add(new_account)
      db.flush()  # Now, new_account.id is available

      # Create the User_Account association with the new account's ID
      new_user_account = models.User_Account(
         user_id=logged_in_user_id,
         account_id=new_account.id
      )

      db.add(new_user_account) # Add the User_Account association to the session

      db.commit() # Commit the transaction to persist both the new account and the association
      db.refresh(new_account)
      return new_account
   except HTTPException as e:
      db.rollback()
      pprint(f'API error in POST /accounts service method : {e}')
      raise e
   except IntegrityError as e: # Database-side uniqueness check : Check if an account with the same name already exists in the organization
      db.rollback()  
      pprint(f'DB error in POST /accounts service method : {e}')
      raise ApiError.conflict(f"An account with name -'{account_creation_payload.name}'- already exists in organization")
   except SQLAlchemyError as e: # group db side error as 503 to not expose actual error to client
      db.rollback()
      pprint(f'DB error in POST /accounts service method : {e}')
      raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
   except Exception as e:
      db.rollback()
      pprint(f'Unexpected error in POST /accounts service method: {e}')
      raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
   
def patch_account(
   account_to_patch: models.Account,
   account_patch_req_dto: account_schemas.AccountPatchRequestDTO,
   db: Session
   ) -> account_schemas.AccountResponseDTO: 
   """
   Patches account based on given account_id path param, and account_patch_req_dto body

   Args:
      account_id (UUID): The account_id pointing to the account that needs to be patched.
      account_patch_req_dto (AccountPatchRequestDTO): Request body containing optional 'name' and 'description' fields that can be patched.
      db (Session): The db session object for db operations.

   Raises: 
      404: Account not found.
      503: Any db related error.

   Returns: 
      AccountResponseDTO : The response containing patched AccountResponseDTO object. 
   
   Notes:
      - logged-in user is assumed to be either admin or superadmin. 
      - the req body has either non-empty 'name' field, or non-empty 'description' field, or both fields are non-empty.
   """
   try:
      for var, value in vars(account_patch_req_dto).items():
         setattr(account_to_patch, var, value) if value is not None else None
      account_to_patch.updated_at = datetime.now()
      db.commit()
      db.refresh(account_to_patch)
      return account_to_patch
   except HTTPException as e:
      db.rollback()
      pprint(f'API error in PATCH /accounts/{account_to_patch.id} service method: {e}')
      raise e
   except SQLAlchemyError as e: # group db side error as 503 to not expose actual error to client
      db.rollback()
      pprint(f'DB error in PATCH /accounts/{account_to_patch.id} service method: {e}')
      raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
   except Exception as e:
      db.rollback()
      pprint(f'Unexpected error in PATCH /accounts/{account_to_patch.id} service method: {e}')
      raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")

def get_accounts( 
   logged_in_user_id: UUID,
   logged_in_user_is_superadmin: bool,
   name: Optional[str],
   db: Session
) -> List[account_schemas.AccountResponseDTO]:

   try:
      # Start with all accounts if the user is superadmin, else filter by user's accounts (so that superadmin can still view accounts if association removed)
      if logged_in_user_is_superadmin: 
         query = db.query(models.Account)
      else:
         # For non-superadmins: get accounts they are associated with
         query = db.query(models.Account)\
                  .join(models.User_Account, models.Account.id == models.User_Account.account_id)\
                  .filter(models.User_Account.user_id == logged_in_user_id)
                  
      # Apply filters based on account name
      if name:
         query = query.filter(models.Account.name.ilike(f"%{name}%"))

      accounts = query.all()
      return cast(List[account_schemas.AccountResponseDTO], accounts)
   except HTTPException as e:
      db.rollback()
      pprint(f'API error in GET /accounts service method: {e}')
      raise e
   except SQLAlchemyError as e: 
      pprint(f'DB error in GET /accounts service method: {e}')
      raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
   except Exception as e:
      pprint(f'Unexpected error in GET /accounts service method: {e}')
      raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")

def get_account_user_profile(
   db: Session,
   account_id: UUID,
   logged_in_user: models.User,
   user_account_association: models.User_Account
) -> user_schemas.AccountUserProfileDTO:
   try:
      if logged_in_user.is_superadmin:
         account_user_with_roles_dto = user_schemas.AccountUserProfileDTO(
            **logged_in_user.__dict__,
            is_account_admin=False,
            roles=[]
         )
      elif user_account_association.is_admin:
         account_user_with_roles_dto = user_schemas.AccountUserProfileDTO(
            **logged_in_user.__dict__,
            is_account_admin=True,
            roles=[]
         )
      else:
         RoleUserAccountAlias = aliased(models.Role_User_Account)
         roles_query = (
            db.query(models.Role)
            .join(RoleUserAccountAlias, RoleUserAccountAlias.role_id == models.Role.id)
            .filter(RoleUserAccountAlias.user_account_id == user_account_association.id)
         )
         roles = roles_query.all()
         roles_dto = cast(List[role_schemas.RoleResponseDTO], roles)

         account_user_with_roles_dto = user_schemas.AccountUserProfileDTO(
            **logged_in_user.__dict__,
            is_account_admin=False,
            roles=roles_dto
         )

      return account_user_with_roles_dto

   except HTTPException as e:
      db.rollback()
      pprint(f'API error in GET /accounts/{account_id}/profile service method: {e}')
      raise e
   except SQLAlchemyError as e:
      db.rollback()
      pprint(f'Error in GET /accounts/{account_id}/profile service method: {e}')
      raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
   except Exception as e:
      db.rollback()
      pprint(f'Unexpected error in GET /accounts/{account_id}/profile service method: {e}')
      raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")

def get_account_user_list(
   db: Session,
   account_id: UUID, 
   firstname: Optional[str],
   lastname: Optional[str],
   email: Optional[str],
   project_id: Optional[UUID],
   assigned: Optional[bool] = True
) -> List[user_schemas.AccountUserListItemDTO]:
   try:
      UserAccountAlias = aliased(models.User_Account)
      RoleUserAccountAlias = aliased(models.Role_User_Account)
      UserProjectAlias = aliased(models.User_Project)

      account_users_query = (
         db.query(models.User, UserAccountAlias.is_admin, UserAccountAlias.id)
         .join(UserAccountAlias, UserAccountAlias.user_id == models.User.id)
         .filter(UserAccountAlias.account_id == account_id)
      )

      if firstname:
         account_users_query = account_users_query.filter(models.User.firstname.ilike(f"%{firstname}%"))
      if lastname:
         account_users_query = account_users_query.filter(models.User.lastname.ilike(f"%{lastname}%"))
      if email:
         account_users_query = account_users_query.filter(models.User.email.ilike(f"%{email}%"))

      if project_id:
         account_users_query = account_users_query.outerjoin(
               UserProjectAlias,
               (UserProjectAlias.user_id == models.User.id) & 
               (UserProjectAlias.project_id == project_id)
         )
         if assigned:
            account_users_query = account_users_query.filter(UserProjectAlias.project_id != None)
         else:
            account_users_query = account_users_query.filter(UserProjectAlias.project_id == None)
            
      account_users = account_users_query.all()
      account_users_with_roles = []

      for user, is_admin, user_account_id in account_users:
         if user.is_superadmin or is_admin:
            account_user_with_roles_dto = user_schemas.AccountUserListItemDTO(
               **user.__dict__,
               is_account_admin = is_admin,
               roles = []
            )
         else:
            roles_query = (
               db.query(models.Role)
               .join(RoleUserAccountAlias, RoleUserAccountAlias.role_id == models.Role.id)
               .filter(
                  RoleUserAccountAlias.user_account_id == user_account_id
               )
            )
            roles = roles_query.all()
            
            # role_summary_dto = [RoleSummaryDTO.model_validate(role) for role in roles]
            role_summary_dto = [role_schemas.RoleSummaryDTO.from_orm(role) for role in roles]

            # Construct AccountUserListItemDTO for each user
            account_user_with_roles_dto = user_schemas.AccountUserListItemDTO(
               **user.__dict__,
               is_account_admin = False,
               roles = role_summary_dto
            )
         account_users_with_roles.append(account_user_with_roles_dto)
      return account_users_with_roles
   except HTTPException as e:
      db.rollback()
      pprint(f'API error in GET /accounts/{account_id}/users service method : {e}')
      raise e
   except SQLAlchemyError as e:
      db.rollback()
      pprint(f'Error in GET /accounts/{account_id}/users service method : {e}')
      raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
   except Exception as e:
      db.rollback()
      pprint(f'Unexpected error in GET /accounts/{account_id}/users service method : {e}')
      raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
   
def assign_users_to_account(
   account_id: UUID,
   user_list_dto: user_schemas.UserListDTO,
   db: Session,
   ) -> JSONResponse:
   try:
      user_ids = user_list_dto.user_ids
      # if action == "Add":
      query_result = db.query(# Check for the existence of all users in the list, and their account association
         func.count(models.User.id).label("total_users_found"),  # Count all users matched by user_ids
         func.count(models.User_Account.user_id).label("total_user_account_associations"),  # Count only non-NULL associations (existing associations)
      ).outerjoin(models.User_Account, and_(models.User.id == models.User_Account.user_id, models.User_Account.account_id == account_id)) \
      .filter(models.User.id.in_(user_ids)) \
      .one() # outerjoin to get User, User_Account counts separately in one query

      # Extracting the results
      (total_users_found, total_user_account_associations) = query_result

      # print(f'total_users_found = {total_users_found},\n'
      #       f'total_user_account_associations = {total_user_account_associations},\n')
   
      if total_users_found != len(user_ids):
         print(f"in PATCH /accounts/{account_id}/users service method: One or more users not found in user table")
         raise ApiError.notfound("One or more users not found")
                                             
      if total_user_account_associations > 0:
         print(f"in PATCH /accounts/{account_id}/users service method: One or more users are already assigned to the account")
         raise ApiError.conflict(f"One or more users are already assigned to account - '{account_id}'")

      # Create new User_Account associations
      new_user_accounts = [
         models.User_Account(user_id=UUID(str(user_id)), account_id=account_id)
         for user_id in user_ids
      ]
      db.bulk_save_objects(new_user_accounts)
      db.commit()
      return JSONResponse(content={"message": f"Successfully assigned {len(new_user_accounts)} user/(s) to account - '{account_id}'"}, status_code= status.HTTP_200_OK)
   except HTTPException as e:
      db.rollback()
      pprint(f'API error in POST /accounts/{account_id}/users service method: {e}')
      raise e
   except SQLAlchemyError as e:
      db.rollback()
      pprint(f'DB Error in POST /accounts/{account_id}/users service method: {e}')
      raise ApiError.serviceunavailable("The server is currently unavailable, please try again later")
   except Exception as e:
      db.rollback()
      pprint(f'Unexpected error in POST /accounts/{account_id}/users service method: {e}')
      raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")

def deassign_user_from_account(
   account_id: UUID,
   user_id: UUID,
   logged_in_user: models.User,
   db: Session,
   ) -> JSONResponse:
   try:
      user_to_deassign = db.query(models.User).filter(models.User.id == user_id).first()
      if not user_to_deassign:
         raise ApiError.notfound(f"User - '{user_id}' - not found")
      
      user_to_deassign_account_association = db.query(models.User_Account).filter(models.User_Account.user_id == user_to_deassign.id, models.User_Account.account_id == account_id).first()
      if not user_to_deassign_account_association:
         raise ApiError.validationerror(f"User - '{user_to_deassign.id}' - is not assigned to account - '{account_id}'")
      
      if logged_in_user.id == user_to_deassign.id:
         if not logged_in_user.is_superadmin:
            raise ApiError.validationerror("Invalid action - cannot deassign self from account")
         # delete associated projects in account
         delete_all_associated_user_projects_in_account(user_id = user_to_deassign.id, account_id=account_id, db=db)
         # delete User_Account association
         user_account_delete_count = db.query(models.User_Account).filter(
               models.User_Account.user_id == user_to_deassign.id,
               models.User_Account.account_id == account_id
         ).delete(synchronize_session=False)
         db.commit()

         return JSONResponse(content={"message": f"Successfully deassigned user - '{user_id}' - from account - '{account_id}'"}, status_code=status.HTTP_200_OK)
      
      if user_to_deassign.is_superadmin: # if user to deassign is superadmin
         ROOT_SUPERADMIN_ID = os.getenv("ROOT_SUPERADMIN_ID", None)
         if ROOT_SUPERADMIN_ID != logged_in_user.id: # only root superadmin user can deassign other superadmins
            raise ApiError.forbidden(f"you do not have root superadmin permissions to deassign superadmin user - '{user_to_deassign.id}' from account - '{account_id}'")
      
      delete_all_associated_user_projects_in_account(user_id = user_to_deassign.id, account_id=account_id, db=db)
      
      # delete User_Account association
      user_account_delete_count = db.query(models.User_Account).filter(
            models.User_Account.user_id == user_to_deassign.id,
            models.User_Account.account_id == account_id
      ).delete(synchronize_session=False)
      db.commit()

      return JSONResponse(content={"message": f"Successfully deassigned user - '{user_id}' - from account - '{account_id}'"}, status_code=status.HTTP_200_OK)
   
   except HTTPException as e:
      db.rollback()
      pprint(f'API error in DELETE /accounts/{account_id}/users/{user_id} service method: {e}')
      raise e
   except SQLAlchemyError as e:
      db.rollback()
      pprint(f'DB Error in DELETE /accounts/{account_id}/users/{user_id} service method: {e}')
      raise ApiError.serviceunavailable("The server is currently unavailable, please try again later")
   except Exception as e:
      db.rollback()
      pprint(f'Unexpected error in DELETE /accounts/{account_id}/users/{user_id} service method: {e}')
      raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
   
def patch_user_account_admin_status(
   account_id: UUID,
   user_id: UUID,
   logged_in_user_is_superadmin: bool,
   account_admin_status_update_dto: account_schemas.AccountAdminStatusUpdateDTO,
   db: Session,
   logged_in_user_id: UUID
   )-> JSONResponse:
   try:
      # Check if user in payload exists
      user_in_payload = db.query(models.User).filter(models.User.id == user_id).first()

      if not user_in_payload:
         raise ApiError.notfound(f"User - '{user_id}' - not found")

      # Fetch the User_Account association if it exists
      user_account_association = db.query(models.User_Account).filter(
         models.User_Account.user_id == user_id,
         models.User_Account.account_id == account_id
      ).first()

      if not user_account_association:
         raise ApiError.validationerror(f"user - '{user_id}' - is not assigned to account - '{account_id}'")

      if user_id == logged_in_user_id:
         if not logged_in_user_is_superadmin:
            raise ApiError.forbidden('you do not have permission to modify account admin status of self')
      
      match account_admin_status_update_dto.action:
         case "Grant":
            if not user_account_association.is_admin:
               user_account_association.is_admin = True

         case "Revoke":
            if user_account_association.is_admin:
               if not user_in_payload.is_superadmin:
                  top_level_associated_projects_in_account: List[UUID] = get_top_level_associated_project_ids_for_user_in_account(db, user_id, account_id)

                  # if top_level_associated_projects_in_account:
                  delete_unrooted_user_project_associations_in_account(db, user_id, top_level_associated_projects_in_account, account_id)
               user_account_association.is_admin = False

         case _:
            raise ApiError.validationerror(f"unknown action - '{account_admin_status_update_dto.action}'")

      db.commit()
      return JSONResponse(content={"message": f"Admin status successfully {'revoked' if account_admin_status_update_dto.action.lower() == 'revoke' else 'granted'}"}, status_code=status.HTTP_200_OK)
   except HTTPException as e:
      db.rollback()
      pprint(f'API error in PATCH /accounts/{account_id}/users/{user_id}/admin service method : {e}')
      raise e
   except SQLAlchemyError as e:
      db.rollback()
      pprint(f'DB error in PATCH /accounts/{account_id}/users/{user_id}/admin service method')
      raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
   except Exception as e:
      db.rollback()
      pprint(f'Unexpected error in PATCH /accounts/{account_id}/users/{user_id}/admin service method')
      raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")  



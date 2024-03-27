from fastapi import HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy import (
   func,
   case,
   and_,
   select,
   exists
)
from sqlalchemy.orm import Session, aliased
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from typing import List, Optional, cast
from uuid import UUID
from datetime import datetime
from elevaitedb.schemas.account_schemas import (
   AccountCreationRequestDTO,
   AccountResponseDTO,
   AccountPatchRequestDTO,
   AccountAdminStatusUpdateDTO,
)
from elevaitedb.schemas.role_schemas import (
   RoleResponseDTO,
   RoleSummaryDTO
)
from elevaitedb.schemas.user_schemas import (
   UserListDTO,
   AccountUserListItemDTO,
   AccountUserProfileDTO 
)
from elevaitedb.db.models import (
   Organization,
   Account,
   Project,
   User_Project,
   User,
   Role,
   User_Account,
   Role_User_Account
) 
from elevaitedb.schemas.common_schemas import (
   ResourceStatusUpdateDTO
)
from app.errors.api_error import ApiError
from pprint import pprint
from app.services.utils.helpers import get_top_level_project_ids_for_user_in_account
from app.utils.cte import delete_unrooted_user_project_associations
def create_account(
   account_creation_payload: AccountCreationRequestDTO,
   db: Session,
   logged_in_user_id: UUID 
   ) -> AccountResponseDTO: 
   """
   Creates an account based on given account_creation_payload body param and validity and permission checks.

   Args:
      account_creation_payload (AccountCreationRequestDTO): The payload containing details of 'organization_id', 'name' and optionally 'description' for account creation
      logged_in_user_id (UUID): logged-in users' id
      db (Session): The db session object for db operations.

   Raises: 
      404: Organization not found.
      409: Account with same name in specified organization already exists.
      503: Any db related error.
   Returns: 
      AccountResponseDTO : The response containing created AccountResponseDTO object. 
   
   Notes:
      - logged-in user is assumed to be either admin or superadmin. 
      - the req body has either non-empty 'name' field, or non-empty 'description' field, or both fields are non-empty.
   """
   try:
      # Check if the organization exists and if an account with the same name does not exist in the organization
      organization_exists_subquery = select(exists().where(Organization.id == account_creation_payload.organization_id))
      account_exists_subquery = select(exists().where(and_(Account.organization_id == account_creation_payload.organization_id, Account.name == account_creation_payload.name)))

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
      new_account = Account(
         organization_id=account_creation_payload.organization_id,
         name=account_creation_payload.name,
         description=account_creation_payload.description,
         created_at=datetime.now(),
         updated_at=datetime.now()
      )

      db.add(new_account)
      db.flush()  # Now, new_account.id is available

      # Create the User_Account association with the new account's ID
      new_user_account = User_Account(
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
   account_to_patch: Account,
   account_patch_req_dto: AccountPatchRequestDTO,
   db: Session
   ) -> AccountResponseDTO: 
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
   org_id: UUID,
   name: Optional[str],
   db: Session
) -> List[AccountResponseDTO]:
   """
   Retrieves accounts for a user with optional name query param based on superadmin or non-superadmin role.

   Args:
      org_id (UUID): The org_id pointing to the organization that the account belongs to.
      name (Optional[str]): Optional query param of account name .
      db (Session): The db session object for db operations.

   Raises: 
      401: If logged-in user is not found in db.
      503: Any db related error.

   Returns: 
      List[AccountResponseDTO] : A list of retrieved AccountResponseDTO objects, which may be empty. 
   
   Notes:
      - Superadmin users can get all the accounts in the specified organization, with optional filtering based on query param 'name'
      - non-superadmin users can get all the accounts that they are associated with in the specified organization, with optional filtering based on query param 'name'
   """
   try:
      # Start with all accounts if the user is superadmin, else filter by user's accounts (so that superadmin can still view accounts if association removed)
      if logged_in_user_is_superadmin: 
         query = db.query(Account).filter(Account.organization_id == org_id)
      else:
         # For non-superadmins: get accounts they are admin of or which are not disabled
         query = (db.query(Account)
                  .join(User_Account, Account.id == User_Account.account_id)
                  .filter(User_Account.user_id == logged_in_user_id,
                           Account.organization_id == org_id)
                  .filter((User_Account.is_admin == True) | (Account.is_disabled == False)))
      # Apply filters based on account name
      if name:
         query = query.filter(Account.name.ilike(f"%{name}%"))

      accounts = query.all()
      return cast(List[AccountResponseDTO], accounts)
   except HTTPException as e:
      db.rollback()
      pprint(f'API error in GET /accounts?org_id={org_id} service method: {e}')
      raise e
   except SQLAlchemyError as e: # group db side error as 503 to not expose actual error to client
      pprint(f'DB error in GET /accounts?org_id={org_id} service method: {e}')
      raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
   except Exception as e:
      pprint(f'Unexpected error in GET /accounts?org_id={org_id} service method: {e}')
      raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")

def get_account_user_profile(
   db: Session,
   account_id: UUID,
   logged_in_user: User,
   user_account_association: User_Account
) -> AccountUserProfileDTO:
   try:
      if logged_in_user.is_superadmin:
         account_user_with_roles_dto = AccountUserProfileDTO(
            **logged_in_user.__dict__,
            is_account_admin=False,
            roles=[]
         )
      elif user_account_association.is_admin:
         account_user_with_roles_dto = AccountUserProfileDTO(
            **logged_in_user.__dict__,
            is_account_admin=True,
            roles=[]
         )
      else:
         RoleUserAccountAlias = aliased(Role_User_Account)
         roles_query = (
            db.query(Role)
            .join(RoleUserAccountAlias, RoleUserAccountAlias.role_id == Role.id)
            .filter(RoleUserAccountAlias.user_account_id == user_account_association.id)
         )
         roles = roles_query.all()
         roles_dto = cast(List[RoleResponseDTO], roles)

         account_user_with_roles_dto = AccountUserProfileDTO(
            **logged_in_user.__dict__,
            is_account_admin=False,
            roles=roles_dto
         )

      return account_user_with_roles_dto

   except HTTPException as e:
      db.rollback()
      pprint(f'API error in GET /accounts/{account_id}/profile : {e}')
      raise e
   except SQLAlchemyError as e:
      db.rollback()
      pprint(f'Error in GET /accounts/{account_id}/profile : {e}')
      raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
   except Exception as e:
      db.rollback()
      pprint(f'Unexpected error in GET /accounts/{account_id}/profile : {e}')
      raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")

def get_account_user_list(
   db: Session,
   account_id: UUID, 
   firstname: Optional[str],
   lastname: Optional[str],
   email: Optional[str]
) -> List[AccountUserListItemDTO]:
   try:
      UserAccountAlias = aliased(User_Account)
      RoleUserAccountAlias = aliased(Role_User_Account)

      account_users_query = (
         db.query(User, UserAccountAlias.is_admin, UserAccountAlias.id)
         .join(UserAccountAlias, UserAccountAlias.user_id == User.id)
         .filter(UserAccountAlias.account_id == account_id)
      )

      if firstname:
         account_users_query = account_users_query.filter(User.firstname.ilike(f"%{firstname}%"))
      if lastname:
         account_users_query = account_users_query.filter(User.lastname.ilike(f"%{lastname}%"))
      if email:
         account_users_query = account_users_query.filter(User.email.ilike(f"%{email}%"))

      account_users = account_users_query.all()
      account_users_with_roles = []

      for user, is_admin, user_account_id in account_users:
         if user.is_superadmin:
            account_user_with_roles_dto = AccountUserListItemDTO(
               **user.__dict__,
               is_account_admin = False,
               roles = []
            )
         elif is_admin:
            account_user_with_roles_dto = AccountUserListItemDTO(
               **user.__dict__,
               is_account_admin = True,
               roles = []
            )
         else:
            roles_query = (
               db.query(Role)
               .join(RoleUserAccountAlias, RoleUserAccountAlias.role_id == Role.id)
               .filter(
                  RoleUserAccountAlias.user_account_id == user_account_id
               )
            )
            roles = roles_query.all()
            
            # role_summary_dto = [RoleSummaryDTO.model_validate(role) for role in roles]
            role_summary_dto = [RoleSummaryDTO.from_orm(role) for role in roles]

            # Construct AccountUserListItemDTO for each user
            account_user_with_roles_dto = AccountUserListItemDTO(
               **user.__dict__,
               is_account_admin = False,
               roles = role_summary_dto
            )
         account_users_with_roles.append(account_user_with_roles_dto)
      return account_users_with_roles
   except HTTPException as e:
      db.rollback()
      pprint(f'API error in GET /users/account-level?account_id={account_id} : {e}')
      raise e
   except SQLAlchemyError as e:
      db.rollback()
      pprint(f'Error in GET /users/account-level?account_id={account_id} : {e}')
      raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
   except Exception as e:
      db.rollback()
      pprint(f'Unexpected error in GET /users/account-level?account_id={account_id} : {e}')
      raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
   
def assign_or_deassign_users_in_account(
   account_id: UUID,
   user_list_dto: UserListDTO,
   db: Session,
   logged_in_user_id: UUID,
   logged_in_user_is_superadmin: bool
   ) -> JSONResponse:
   try:
      user_ids = user_list_dto.user_ids
      action = user_list_dto.action

      if action == "Add":
         query_result = db.query(# Check for the existence of all users in the list, and their account association
            func.count(User.id).label("total_users_found"),  # Count all users matched by user_ids
            func.count(User_Account.user_id).label("total_user_account_associations"),  # Count only non-NULL associations (existing associations)
         ).outerjoin(User_Account, and_(User.id == User_Account.user_id, User_Account.account_id == account_id)) \
         .filter(User.id.in_(user_ids)) \
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
            User_Account(user_id=UUID(str(user_id)), account_id=account_id)
            for user_id in user_ids
         ]
         db.bulk_save_objects(new_user_accounts)
         db.commit()
         return JSONResponse(content={"message": f"Successfully assigned {len(new_user_accounts)} user/(s) to the account"}, status_code= status.HTTP_200_OK)
      else: # action == "Remove"
         query_result = db.query(
         func.count(User.id).label("total_users_found_in_list"),  # Count all users matched by user_ids
         func.count(User_Account.user_id).label("total_user_account_associations_in_list"),  # Count only non-NULL associations
         func.sum(case((User.is_superadmin == True, 1), else_=0)).label("superadmin_count_in_list"),  # count = 0 or 1 : represents if superadmin is present in list 
         # select(User.is_superadmin).where(User.id == logged_in_user_id).as_scalar().label("logged_in_user_is_superadmin"), # boolean flag - logged_in_user is superadmin  | Have logged_in_user_is_superadmin flag avaialable
         func.sum(case((User_Account.user_id == logged_in_user_id, 1), else_=0)).label("logged_in_user_association_count_in_list") # count = 0 or 1 : represents if logged_in_user_id is a part of the list and is associated to account
         ).outerjoin(User_Account, and_(User.id == User_Account.user_id, User_Account.account_id == account_id)) \
         .filter(User.id.in_(user_ids)) \
         .one() # outerjoin to get User, User_Account counts separately in one query

         # Extracting the results
         (total_users_found_in_list,
         total_user_account_associations_in_list,
         superadmin_count_in_list,
         logged_in_user_association_count_in_list) = query_result

         # print(f'total_users_found = {total_users_found},\n'
         #       f'total_user_account_associations = {total_user_account_associations},\n'
         #       f'total_is_superadmin = {total_is_superadmin},\n'
         #       f'logged_in_user_is_superadmin = {logged_in_user_is_superadmin},\n'
         #       f'logged_in_user_association_count_in_list = {logged_in_user_association_count_in_list}')

         if total_users_found_in_list != len(user_ids): # all users in input must exist
            print(f'In PATCH /accounts/{account_id}/users service method : One or more users not found')
            raise ApiError.notfound("One or more users not found")
         
         if total_user_account_associations_in_list != len(user_ids): # all users in input must be associated to account
            print(f"In PATCH /accounts/{account_id}/users service method : Not all users are assigned to the account '{account_id}'")
            raise ApiError.validationerror(f"Not all users are assigned to account - '{account_id}'")

         if logged_in_user_association_count_in_list == 1: # logged-in user cannot deassign self
            print(f"In PATCH /accounts/{account_id}/users service method : user does not have permissions to deassign self from account")
            raise ApiError.validationerror(f"invalid action - you cannot deassign self from account - '{account_id}'")
         
         if superadmin_count_in_list > 0 and not logged_in_user_is_superadmin:
            print(f"In PATCH /accounts/{account_id}/users service method : user does not have permissions to deassign superadmin-user from account")
            raise ApiError.forbidden(f"you do not have permissions to deassign superadmin-user from account - '{account_id}'")
         
         # First obtain all User_Project association id's to delete based on projects under specified account
         user_project_ids_query = db.query(User_Project.id) \
            .join(Project, Project.id == User_Project.project_id) \
            .filter(
               User_Project.user_id.in_(user_ids),
               Project.account_id == account_id
            )

         # Perform the deletion on these user-project association id's
         user_project_delete_count = db.query(User_Project) \
            .filter(User_Project.id.in_(user_project_ids_query)) \
            .delete(synchronize_session=False)
         
         # Log the number of User_Project entries deleted for auditing
         print(f"Deleted {user_project_delete_count} User_Project entries for users in account {account_id}")

         # Then, delete User_Account entries
         user_account_delete_count = db.query(User_Account).filter(
               User_Account.user_id.in_(user_ids),
               User_Account.account_id == account_id
         ).delete(synchronize_session=False)
      

         db.commit()
         return JSONResponse(content={"message": f"Successfully deassigned {user_account_delete_count} user" + ("s" if user_account_delete_count > 1 else "") + " from the account"}, status_code=status.HTTP_200_OK)
   except HTTPException as e:
      db.rollback()
      pprint(f'API error in PATCH /accounts/{account_id}/users : {e}')
      raise e
   except SQLAlchemyError as e:
      db.rollback()
      pprint(f'DB Error in PATCH /accounts/{account_id}/users : {e}')
      raise ApiError.serviceunavailable("The server is currently unavailable, please try again later")
   except Exception as e:
      db.rollback()
      pprint(f'Unexpected error in PATCH /accounts/{account_id}/users : {e}')
      raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")

def patch_account_user_admin_status(
   account_id: UUID,
   logged_in_user_is_superadmin: bool,
   account_admin_status_update_dto: AccountAdminStatusUpdateDTO,
   db: Session,
   logged_in_user_id: UUID
   )-> JSONResponse:
   try:
      # Check if user in payload exists
      user_in_payload = db.query(User).filter(User.id == account_admin_status_update_dto.user_id).first()

      if not user_in_payload:
         print(f'In PATCH /accounts/{account_id}/admin service method - : user with id {account_admin_status_update_dto.user_id} not found')
         raise ApiError.notfound(f"user - '{account_admin_status_update_dto.user_id}' - not found")

      # Fetch the User_Account association if it exists
      user_account_association = db.query(User_Account).filter(
         User_Account.user_id == account_admin_status_update_dto.user_id,
         User_Account.account_id == account_id
      ).first()

      if not user_account_association:
         print(f'In PATCH /accounts/{account_id}/admin service method - : user -"{account_admin_status_update_dto.user_id}"- is not a member of account -"{account_id}"')
         raise ApiError.validationerror(f"user - '{account_admin_status_update_dto.user_id}' - is not assigned to account - '{account_id}'")


      if account_admin_status_update_dto.user_id == logged_in_user_id:
         if not logged_in_user_is_superadmin:
            print(f'In PATCH /accounts/{account_id}/admin service method - : you do not have permission to modify account admin status of self')
            raise ApiError.forbidden('you do not have permission to modify account admin status of self')
      
      if user_in_payload.is_superadmin:
         print(f'In PATCH /accounts/{account_id}/admin service method - : Invalid action - cannot update account admin status of superadmin user')
         raise ApiError.validationerror(f"Invalid action - cannot update account admin status of superadmin user - '{user_in_payload.id}'")
      
      match account_admin_status_update_dto.action:
         case "Grant":
            if user_account_association.is_admin:
               print(f'In PATCH /accounts/{account_id}/admin service method - : User with id {account_admin_status_update_dto.user_id} is already an admin; cannot grant admin status.')
               raise ApiError.conflict(f"user - '{account_admin_status_update_dto.user_id}' - is already an admin of account - '{account_id}'")
            else:
               user_account_association.is_admin = True

         case "Revoke":
            if not user_account_association.is_admin:
               print(f'In PATCH /accounts/{account_id}/admin service method - : User with id {account_admin_status_update_dto.user_id} is not an admin; cannot revoke admin status.')
               raise ApiError.validationerror(f"user - '{account_admin_status_update_dto.user_id}' - is not an admin of account - '{account_id}'")
            else:
               top_level_projects_in_account: List[UUID] = get_top_level_project_ids_for_user_in_account(db, account_admin_status_update_dto.user_id, account_id)
               print(f'top_level_projects_in_account = {top_level_projects_in_account}')
               if top_level_projects_in_account:
                  delete_unrooted_user_project_associations(db, account_admin_status_update_dto.user_id, top_level_projects_in_account, account_id)
               user_account_association.is_admin = False

         case _:
            print(f'In PATCH /accounts/{account_id}/admin - : Unknown action {account_admin_status_update_dto.action}')
            raise ApiError.validationerror(f"unknown action - '{account_admin_status_update_dto.action}'")

      db.commit()
      return JSONResponse(content={"message": f"Admin status successfully {'revoked' if account_admin_status_update_dto.action.lower() == 'revoke' else 'granted'}"}, status_code=status.HTTP_200_OK)
   except HTTPException as e:
      db.rollback()
      pprint(f'API error in PATCH /accounts/{account_id}/users : {e}')
      raise e
   except SQLAlchemyError as e:
      db.rollback()
      pprint(f'DB error in PATCH /accounts/{account_id}/admin : Error updating admin status: {e}')
      raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
   except Exception as e:
      db.rollback()
      pprint(f'Unexpected error in PATCH /accounts/{account_id}/admin : Error updating admin status: {e}')
      raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")  

def patch_account_status(
   account: Account,
   account_disabled_status_update_dto: ResourceStatusUpdateDTO,
   db: Session,
)-> JSONResponse:
   try:
      # Check for redundant status updates
      if (account_disabled_status_update_dto.action == "Disable" and account.is_disabled) or \
         (account_disabled_status_update_dto.action == "Enable" and not account.is_disabled):
         print(f"in PATCH /accounts/{account.id}/status service method: Account - '{account.id}' - is already {'disabled' if account.is_disabled else 'enabled'}.")
         raise ApiError.validationerror(f"account - '{account.id}' - is already {'disabled' if account.is_disabled else 'enabled'}.")

      # Update account status
      account.is_disabled = account_disabled_status_update_dto.action == "Disable"
      db.commit()

      return JSONResponse(content= {"message": f"Account successfully {'disabled' if account.is_disabled else 'enabled'}."} ,status_code=status.HTTP_200_OK)
   except HTTPException as e:
      db.rollback()
      pprint(f'API error in PATCH /accounts/{account.id}/status : {e}')
      raise e
   except SQLAlchemyError as e:
      db.rollback()
      pprint(f'DB error in PATCH /accounts/{account.id}/status : {e}')
      raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
   except Exception as e:
      db.rollback()
      pprint(f'Unexpected error in PATCH /accounts/{account.id}/status : {e}')
      raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")  
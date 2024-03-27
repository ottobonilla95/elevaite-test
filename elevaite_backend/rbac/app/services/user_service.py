from fastapi import status, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy import exists, func
from sqlalchemy.orm import Session, aliased
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from typing import List, Optional, cast, Any
from uuid import UUID
from datetime import datetime
from fastapi.encoders import jsonable_encoder
from elevaitedb.schemas.user_schemas import (
   UserCreationRequestDTO,
   UserPatchRequestDTO,
   UserProfileDTO, 
   OrgUserListItemDTO,
)
from elevaitedb.schemas.role_schemas import (
   RoleListDTO,
   RoleResponseDTO,
   ProjectScopedPermissions
)
from elevaitedb.db.models import (
   Account,
   User,
   Role,
   User_Account,
   Role_User_Account,
)
from pprint import pprint
from app.errors.api_error import ApiError

def create_user(db: Session, 
                user_creation_payload: UserCreationRequestDTO) -> JSONResponse:
   try:
      # Verify that the specified user does not exist already; if so, return existing user
      db_user = db.query(User).filter(User.email == user_creation_payload.email, User.organization_id == user_creation_payload.org_id).first()
      if db_user:
         pprint(f"in POST /auth/register - A user with email - '{user_creation_payload.email}' - already exists in organization - '{user_creation_payload.org_id}'")
         return JSONResponse(content=jsonable_encoder(db_user), status_code=status.HTTP_200_OK)

      # Create the new user instance
      db_user = User(
         firstname=user_creation_payload.firstname,
         lastname=user_creation_payload.lastname,
         email=user_creation_payload.email,
         organization_id=user_creation_payload.org_id,
      )
      db.add(db_user)
      db.commit()
      db.refresh(db_user)

      return JSONResponse(content=jsonable_encoder(db_user), status_code=status.HTTP_201_CREATED)
   except HTTPException as e:
      db.rollback()
      pprint(f'API error in POST /auth/register create_user service method : {e}')
      raise e
   except SQLAlchemyError as e:
      db.rollback()
      pprint(f'Error in POST /auth/register create_user service method : {e}')
      raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
   except Exception as e:
      db.rollback()
      pprint(f'Unexpected error POST /auth/register create_user service method : {e}')
      raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")

def get_user_profile(
   user_to_profile: User,
   logged_in_user: User,
   db: Session
) -> UserProfileDTO:
   try:
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
         User_Account,
         Account.name.label("account_name")
      ).join(
         Account, User_Account.account_id == Account.id
      )

      # Modify the query based on whether the logged-in user is a superadmin
      if logged_in_user.is_superadmin:
         # If logged-in user is a superadmin, fetch all user_accounts where user is a member, since superadmin can see all accounts.
         user_accounts_query = user_accounts_query.filter(
            User_Account.user_id == user_to_profile.id
         )
      else: # if logged-in user is not a superadmin, he should only be able to see common accounts 
         logged_in_user_accounts_subquery = db.query( # Get account IDs associated with the logged-in user
            User_Account.account_id
         ).filter(
            User_Account.user_id == logged_in_user.id
         ).subquery()

         # Use .alias() to reference the column in the subquery for use with .in_()
         logged_in_user_accounts_alias = logged_in_user_accounts_subquery.alias()
         
         # Filter user accounts to include only those where account_id matches
         # both the target user and logged-in user
         user_accounts_query = user_accounts_query.filter(
            User_Account.user_id == user_to_profile.id,
            User_Account.account_id.in_(db.query(logged_in_user_accounts_alias.c.account_id))
         )
         
      user_accounts = user_accounts_query.all()
      
      for user_account, account_name in user_accounts:
         # if user is superadmin, do not fetch roles
         if user_to_profile.is_superadmin:
            account_membership = {
               "account_id": user_account.account_id,
               "account_name": account_name,  
               "is_admin": False,
               "roles": []
            }
         elif user_account.is_admin:
            account_membership = {
               "account_id": user_account.account_id,
               "account_name": account_name,  
               "is_admin": True,
               "roles": []
            }
         else:
            # Fetch Account-Scoped Roles for Each User_Account using user_account.id
            roles = db.query(Role)\
                        .join(Role_User_Account, Role_User_Account.role_id == Role.id)\
                        .filter(Role_User_Account.user_account_id == user_account.id)\
                        .all()
            
            roles_dto = cast(List[RoleResponseDTO], roles)
            account_membership = {
               "account_id": user_account.account_id,
               "account_name": account_name,  
               "is_admin": False,
               "roles": roles_dto
            }
         user_data["account_memberships"].append(account_membership)
        
      # Convert dictionary to UserProfileDTO instance
      user_profile_dto = UserProfileDTO(**user_data)
      return user_profile_dto
   
   except HTTPException as e:
      db.rollback()
      pprint(f'API error in GET /users/{user_to_profile.id}/profile service method : {e}')
      raise e
   except SQLAlchemyError as e:
      db.rollback()
      pprint(f'Error in GET /users/{user_to_profile.id}/profile service method : {e}')
      raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
   except Exception as e:
      db.rollback()
      pprint(f'Unexpected error in GET /users/{user_to_profile.id}/profile service method : {e}')
      raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")

def get_org_users(
   db: Session,
   org_id: UUID,
   firstname: Optional[str],
   lastname: Optional[str],
   email: Optional[str],
) -> List[OrgUserListItemDTO]:
   try:
      query = db.query(User).filter(User.organization_id == org_id)

      if firstname:
         query = query.filter(User.firstname.ilike(f"%{firstname}%"))
      if lastname:
         query = query.filter(User.lastname.ilike(f"%{lastname}%"))
      if email:
         query = query.filter(User.email.ilike(f"%{email}%"))

      users = query.all()
      return cast(List[OrgUserListItemDTO], users)
   except HTTPException as e:
      db.rollback()
      pprint(f'API error in GET /users/ service method : {e}')
      raise e
   except SQLAlchemyError as e:
      db.rollback()
      pprint(f'Error in GET /users/ service method : {e}')
      raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
   except Exception as e:
      db.rollback()
      pprint(f'Unexpected error in GET /users service method: {e}')
      raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
   
def patch_user(
   user_to_patch: User,
   user_patch_payload: UserPatchRequestDTO,
   db: Session
) -> OrgUserListItemDTO:
   try:
      for key, value in vars(user_patch_payload).items():
         setattr(user_to_patch, key, value) if value is not None else None
      user_to_patch.updated_at = datetime.now()
      db.commit()
      db.refresh(user_to_patch)
      return user_to_patch
   except HTTPException as e:
      db.rollback()
      pprint(f'API Error in PATCH /users/{user_to_patch.id} : {e}')
      raise e
   except SQLAlchemyError as e:
      db.rollback()
      pprint(f'Error in PATCH /users/{user_to_patch.id} : {e}')
      raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
   except Exception as e:
      db.rollback()
      pprint(f'Unexpected error in PATCH /users/{user_to_patch.id} : {e}')
      raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
   
def patch_user_account_roles(
   user_to_patch: User,
   user_to_patch_account_association: User_Account,
   account: Account,
   # user_id: UUID,
   # account_id: UUID,
   role_list_dto: RoleListDTO,
   db: Session,
) -> JSONResponse:
   try:
      RoleUserAccountAlias = aliased(Role_User_Account)
      UserAccountAlias = aliased(User_Account)
      # Subquery to check for the existence of a user-account association and retrieve its ID
      # user_account_subquery = (
      #    db.query(User_Account.id.label("user_account_id"))
      #    .filter(User_Account.user_id == user_id, User_Account.account_id == account_id)
      #    .subquery()
      # )

      # Scalar subquery to count the number of roles found in the database matching the provided role_ids
      roles_count_check = (
         db.query(func.count(Role.id))
         .filter(Role.id.in_(role_list_dto.role_ids))
         .as_scalar()
      )

      # # Check for the presence of Project_Scoped roles in the provided role_ids
      # project_scoped_roles_check = (
      #    db.query(func.count(Role.id))
      #    .filter(Role.id.in_(role_list_dto.role_ids), Role.type == "Project_Scoped")
      #    .as_scalar()
      # )

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
         print(f"in PATCH /{user_to_patch.id}/accounts/{account.id}/roles service method: one or more roles not found")
         raise ApiError.notfound("one or more roles not found")
      # if count_project_scoped_roles > 0:
      #    print(f"in PATCH /{user_id}/accounts/{account_id}/roles service method: Project_Scoped roles cannot be added/removed to/from account roles")
      #    raise ApiError.badRequest("Project_Scoped roles cannot be added/removed to/from account roles")
      if role_list_dto.action == "Add" and count_existing_roles > 0:
         print(f"in PATCH /{user_to_patch.id}/accounts/{account.id}/roles service method: One or more account-scoped roles are already assigned to the user -'{user_to_patch.id}'- in account -'{account.id}'")
         raise ApiError.conflict(f"One or more account-scoped roles are already assigned to user - '{user_to_patch.id}' - in account - '{account.id}'")
      if role_list_dto.action == "Remove" and count_existing_roles != len(role_list_dto.role_ids):
         print(f"in PATCH /{user_to_patch.id}/accounts/{account.id}/roles service method: One or more roles to remove were not found for the user -'{user_to_patch.id}'- in account -'{account.id}'")
         raise ApiError.notfound(f"One or more roles to remove were not found for the user - '{user_to_patch.id}' - in account - '{account.id}'")      
      if role_list_dto.action == "Add":
         new_role_user_accounts = [
            Role_User_Account(user_account_id=user_to_patch_account_association.id, role_id=role_id)
            for role_id in role_list_dto.role_ids
         ]
         db.bulk_save_objects(new_role_user_accounts)
         db.commit()
         return JSONResponse(content = {"message" : f"Successfully added {len(role_list_dto.role_ids)} account-scoped role/(s) to user"}, status_code= status.HTTP_200_OK)
      else: # role_list_dto.action == "Remove":
         db.query(Role_User_Account).filter(
         Role_User_Account.user_account_id == user_to_patch_account_association.id,
         Role_User_Account.role_id.in_(role_list_dto.role_ids)
         ).delete(synchronize_session=False)  
         db.commit()
         return JSONResponse(content = {"message" : f"Successfully removed {len(role_list_dto.role_ids)} account-scoped role/(s) from user"}, status_code= status.HTTP_200_OK)
   
   except HTTPException as e:
      db.rollback()
      pprint(f'API Error in PATCH /users/{user_to_patch.id}/accounts/{account.id}/roles : {e}')
      raise e
   except IntegrityError as e : # Database-side uniqueness check 
        db.rollback()
        pprint(f'Error in PATCH /users/{user_to_patch.id}/accounts/{account.id}/roles : {e}')
        raise ApiError.conflict(f"One or more account-scoped roles for user already exists in account")
   except SQLAlchemyError as e:
      db.rollback()
      pprint(f'Error in PATCH /users/{user_to_patch.id}/accounts/{account.id}/roles : {e}')
      raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
   except Exception as e:
      db.rollback()
      pprint(f'Unexpected error in PATCH /users/{user_to_patch.id} : {e}')
      raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
   
def update_user_project_permission_overrides(
    user_id: UUID,
    project_id: UUID,
    permission_overrides_payload: ProjectScopedPermissions,
    db: Session,
    user_project_association: User_Account
) -> JSONResponse:
   try:
      # user_project_association.permission_overrides = permission_overrides_payload.model_dump()
      user_project_association.permission_overrides = permission_overrides_payload.dict()
      db.commit()
      return JSONResponse(content={"message": f"Project permission overrides successfully updated for user"}, status_code=status.HTTP_200_OK)
   except HTTPException as e:
      db.rollback()
      pprint(f'API Error in PUT users/{user_id}/projects/{project_id}/permission-overrides : {e}')
      raise e
   except SQLAlchemyError as e:
      db.rollback()
      pprint(f'Error in PUT users/{user_id}/projects/{project_id}/permission-overrides : {e}')
      raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
   except Exception as e:
      db.rollback()
      pprint(f'Unexpected error in PUT users/{user_id}/projects/{project_id}/permission-overrides : {e}')
      raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
   
def get_user_project_permission_overrides(
    user_id: UUID,
    project_id: UUID,
    db: Session,
    user_project_association: User_Account
) -> ProjectScopedPermissions:
   try:
      return user_project_association.permission_overrides
   except SQLAlchemyError as e:
      db.rollback()
      pprint(f'Error in GET users/{user_id}/projects/{project_id}/permission-overrides : {e}')
      raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
   except Exception as e:
      db.rollback()
      pprint(f'Unexpected error in GET users/{user_id}/projects/{project_id}/permission-overrides : {e}')
      raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
from fastapi import (
   Depends,
   Query,
   Body,
   Path,
   Depends,
   HTTPException
)
from sqlalchemy import exists, and_
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from .header import validate_token
from elevaitedb.db.models import (
   User,
   Account,
   Project,
   Organization,
   User_Project,
   User_Account
)
from elevaitedb.schemas.user_schemas import UserCreationRequestDTO
from app.utils.deps import get_db
from app.utils.cte import is_user_project_association_till_root
from app.errors.api_error import ApiError
from .header import validate_token
from uuid import UUID
from pprint import pprint
from typing import Any

async def validate_post_user(
   user_creation_payload: UserCreationRequestDTO = Body(description= "user creation payload"), 
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
      organization = db.query(Organization).filter(Organization.id == user_creation_payload.org_id).first()
      if not organization:
         print(f"in POST /register - validate_post_user dependency: organization - '{user_creation_payload.org_id}' - not found")
         raise ApiError.notfound(f"organization - '{user_creation_payload.org_id}' - not found")
      return {"db" : db}
   except HTTPException as e:
      db.rollback()
      pprint(f'API error in POST /register - validate_post_user dependency: {e}')
      raise e
   except SQLAlchemyError as e:
      pprint(f'DB error in POST /register - validate_post_user dependency: {e}')
      raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
   except Exception as e:
      db.rollback()
      print(f'Unexpected error in POST /register - validate_post_user dependency: {e}')
      raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")

async def validate_get_user_profile(
    user_email: str = Depends(validate_token), 
    user_id: UUID = Path(..., description="user id of user whose profile is retrieved"),
    account_id: UUID = Query(None, description="account id under which the user's profile is viewed. Must be provided for non-super admin users"),
    db: Session = Depends(get_db)
) -> dict[str, Any]:
   try:
      # Fetch logged-in user by email
      logged_in_user = db.query(User).filter(User.email == user_email).first()
      if not logged_in_user:
         print(f"INSIDE GET /users/{user_id}/profile - validate_get_user_profile dependency: logged_in_user with email - '{user_email}' - not found")
         raise ApiError.unauthorized("user is unauthenticated")
      
      if account_id:
         account = db.query(Account).filter(Account.id == account_id).first()
         if not account:
            print(f'INSIDE GET /users/{user_id}/profile - validate_get_user_profile dependency: Account - "{account_id}" - not found')
            raise ApiError.notfound(f"account - '{account_id}' - not found")
      
      user = db.query(User).filter(User.id == user_id).first()
      if not user:
         print(f'INSIDE GET /users/{user_id}/profile - validate_get_user_profile dependency: user - "{user_id}" - not found')
         raise ApiError.notfound(f"user - '{user_id}' - not found")

      if logged_in_user.is_superadmin:
         return {"logged_in_user": logged_in_user,
                  "user_to_profile": user,
                  "db": db} 
      
      # For non-superadmins, account_id is required
      if not account_id:
         print(f'INSIDE GET /users/{user_id}/profile - validate_get_user_profile dependency: Account ID must be provided for non-superadmin users')
         raise ApiError.forbidden("account id must be provided for non-superadmin users")
      
      logged_in_user_association = db.query(User_Account).filter(User_Account.user_id == logged_in_user.id, User_Account.account_id == account_id).first()
      if not logged_in_user_association:
         print(f'INSIDE GET /users/{user_id}/profile - validate_get_user_profile dependency: logged-in user does not have access to account - "{account_id}"')
         raise ApiError.forbidden(f"you are not assigned to account - '{account_id}'")
      
      if account.is_disabled and not logged_in_user_association.is_admin: # if account is disabled, raise error if logged-in user is not admin
         print(f'INSIDE GET /users/{user_id}/profile - validate_get_user_profile dependency: account - "{account_id}" - is disabled')
         raise ApiError.forbidden(f"account - '{account_id}' - is disabled")
      
      user_association_exists = db.query(exists().where(and_(User_Account.user_id == user_id, User_Account.account_id == account_id))).scalar()
      
      if not user_association_exists: 
         print(f'INSIDE GET /users/{user_id}/profile - validate_get_user_profile dependency: user -"{user_id}"- not found in account -"{account_id}"')
         raise ApiError.validationerror(f"user - '{user_id}' - not assigned to account - '{account_id}'")

      return {"logged_in_user": logged_in_user,
               "user_to_profile": user,
               "db": db}  
   except HTTPException as e:
      db.rollback()
      pprint(f'API error in GET /users/{user_id}/profile - validate_get_user_profile dependency: {e}')
      raise e
   except SQLAlchemyError as e:
      pprint(f'DB error in GET /users/{user_id}/profile - validate_get_user_profile dependency: {e}')
      raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
   except Exception as e:
      db.rollback()
      print(f'Unexpected error in GET /users/{user_id}/profile - validate_get_user_profile dependency: {e}')
      raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")

# async def validate_get_org_users(
#    user_email: str = Depends(validate_token),
#    org_id: UUID = Query(..., description = "id of org that user belongs to"),
#    db: Session = Depends(get_db)
# ) -> dict[str, Any]:
#    try:
#       # Fetch user by email
#       logged_in_user = db.query(User).filter(User.email == user_email).first()
#       if not logged_in_user:
#          print(f"INSIDE GET /users?org_id={org_id} - validate_get_org_user dependency: logged_in_user with email - '{user_email}' - not found")
#          raise ApiError.unauthorized("user is unauthenticated")
      
#       if not db.query(exists().where(Organization.id == org_id)).scalar():
#          print(f"In GET /users?org_id={org_id} - validate_get_org_user dependency: Organization - '{org_id}' - not found in Organization Table")
#          raise ApiError.notfound(f"organization - '{org_id}' - not found")
      
#       # Check if the user is a superadmin
#       if logged_in_user.is_superadmin: 
#          return {"db": db}

#       # Check for any entries in User_Account for the user where is_admin is true, and the account belongs to the org
#       user_admin_accounts_exist = db.query(
#          exists().where(
#             and_(
#                   User_Account.user_id == logged_in_user.id,
#                   User_Account.is_admin == True,
#                   Account.id == User_Account.account_id, 
#                   Account.organization_id == org_id
#             )
#          )
#       ).select_from(User_Account).join(Account, Account.id == User_Account.account_id).scalar()

#       if user_admin_accounts_exist:
#          return {"db": db}
      
#       print(f"INSIDE GET /users?org_id={org_id} - validate_get_org_user dependency: logged-in user does not have superadmin/admin privileges to read organization users")
#       raise ApiError.forbidden(f"you do not have superadmin/admin privileges to read all users in organization - '{org_id}'")
#    except HTTPException as e:
#       db.rollback()
#       pprint(f'API error in GET /users?org_id={org_id} - validate_get_org_user dependency: {e}')
#       raise e
#    except SQLAlchemyError as e:
#       pprint(f'DB error in GET /users?org_id={org_id} - validate_get_org_user dependency: {e}')
#       raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
#    except Exception as e:
#       db.rollback()
#       print(f'Unexpected error in GET /users?org_id={org_id} - validate_get_org_user dependency: {e}')
      # raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
   
async def validate_patch_user(
    user_email: str = Depends(validate_token),
    user_id: UUID = Path(..., description="The ID of the user to patch"),
    db: Session = Depends(get_db)
) -> dict[str, Any]:
   try:
      # Fetch user by email
      logged_in_user = db.query(User).filter(User.email == user_email).first()
      if not logged_in_user:
         print(f"INSIDE PATCH: /users/{user_id} validate_patch_user dependency : logged in user not found")
         raise ApiError.unauthorized("user is unauthenticated")

      user_to_patch = db.query(User).filter(User.id == user_id).first()
      if not user_to_patch:
         print(f"In PATCH: /users/{user_id} validate_patch_user dependency : user -'{user_id}'- not found")
         raise ApiError.notfound(f"user - '{user_id}' - not found")
         
      # Validate if the current user is a superadmin
      if logged_in_user.is_superadmin: 
         return {"user_to_patch" : user_to_patch, "db" : db}

      # Check if the current user is trying to patch their own data
      if logged_in_user.id == user_id: 
         return {"user_to_patch" : user_to_patch, "db" : db}

      # If the flow reaches here, the user does not have superadmin/admin permissions
      print(f"INSIDE PATCH: /users/{user_id} validate_patch_user dependency : logged-in user -'{logged_in_user.id}'- does not have superadmin/admin privileges to patch user -'{user_id}'")
      raise ApiError.forbidden(f"you do not have superadmin/admin privileges to update user - '{user_id}'")
   except HTTPException as e:
      db.rollback()
      pprint(f'API error in PATCH: /users/{user_id} - validate_patch_user dependency : {e}')
      raise e
   except SQLAlchemyError as e:
      pprint(f'DB error in PATCH: /users/{user_id} - validate_patch_user dependency : {e}')
      raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
   except Exception as e:
      db.rollback()
      print(f'Unexpected error in PATCH: /users/{user_id} - validate_patch_user dependency : {e}')
      raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")

async def validate_patch_user_account_roles(
   user_email: str = Depends(validate_token),
   user_id: UUID = Path(..., description="The ID of the user to patch"),
   account_id: UUID = Path(..., description="The ID of the account to scope the user roles to"),
   db: Session = Depends(get_db)
) -> dict[str, Any]:
   try:
      # Check logged-in user existence
      logged_in_user = db.query(User).filter(User.email == user_email).first()
      if not logged_in_user:
         print(f"INSIDE PATCH /users/{user_id}/accounts/{account_id}/roles validate_patch_user_account_roles dependency: logged-in user with email - {user_email} - not found in user table")
         raise ApiError.unauthorized("user is unauthenticated")
      
      # Check existence of user 
      user_to_patch = db.query(User).filter(User.id == user_id).first()
      if not user_to_patch:
         print(f"INSIDE PATCH /users/{user_id}/accounts/{account_id}/roles validate_patch_user_account_roles dependency: user - {user_id} - not found in user table")
         raise ApiError.notfound(f"user - '{user_id}' - not found")
      
      if user_to_patch.is_superadmin:
         print(f"INSIDE PATCH /users/{user_id}/accounts/{account_id}/roles validate_patch_user_account_roles dependency: Invalid action - cannot patch account roles for superadmin user")
         raise ApiError.validationerror(f"Invalid action : cannot patch account roles for superadmin user - {user_to_patch.id}")
      
      # Check existence of account
      account = db.query(Account).filter(Account.id == account_id).first()
      if not account:
         print(f"INSIDE PATCH /users/{user_id}/accounts/{account_id}/roles validate_patch_user_account_roles dependency: account - {account_id} - not found in Account table")
         raise ApiError.notfound(f"account - '{account_id}' - not found")
      
      # Check User_Account association
      user_account_association = db.query(User_Account).filter(User_Account.user_id == user_id, User_Account.account_id == account_id).first()
      if not user_account_association:
         print(f"INSIDE PATCH /users/{user_id}/accounts/{account_id}/roles validate_patch_user_account_roles dependency: user - '{user_id}' - is not assigned to account - '{account_id}'")
         raise ApiError.validationerror(f"user - '{user_id}' - is not assigned to account - '{account_id}' -")
      
      if user_account_association.is_admin:
         print(f"INSIDE PATCH /users/{user_id}/accounts/{account_id}/roles validate_patch_user_account_roles dependency: Invalid action - cannot patch account roles for admin user")
         raise ApiError.validationerror(f"Invalid action : cannot patch account roles for admin user - {user_to_patch.id}")
      
      # Check if account is disabled
      if account.is_disabled:
         print(f"INSIDE PATCH /users/{user_id}/accounts/{account_id}/roles validate_patch_user_account_roles dependency: account - '{account_id}' - is disabled")
         raise ApiError.forbidden(f"account - '{account_id}' - is disabled")
      
      # Check superadmin
      if logged_in_user.is_superadmin:
         return {"user_to_patch": user_to_patch,
               "account" : account,
               "user_to_patch_account_association" : user_account_association,
               "db" : db}

      # Check User_Account association for logged-in user and admin status
      logged_in_user_account_association = db.query(User_Account).filter(User_Account.user_id == logged_in_user.id, User_Account.account_id == account_id).first()
      if not logged_in_user_account_association:
         print(f"INSIDE PATCH /users/{user_id}/accounts/{account_id}/roles validate_patch_user_account_roles dependency: logged-in user -'{logged_in_user.id}'- is not a superadmin or assigned to account - {account_id}")
         raise ApiError.forbidden(f"you are not assigned to account - '{account_id}'")
      if not logged_in_user_account_association.is_admin:
         print(f"INSIDE PATCH /users/{user_id}/accounts/{account_id}/roles validate_patch_user_account_roles dependency: logged-in user -'{logged_in_user.id}'- does not have superadmin/admin privileges to update user-account roles")
         raise ApiError.forbidden(f"you do not have superadmin/admin privileges to update user-account roles in account - '{account_id}'")
      
      return {"user_to_patch": user_to_patch,
               "account" : account,
               "user_to_patch_account_association" : user_account_association,
               "db" : db}

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
   
async def validate_update_project_permission_overrides(
   user_email: str = Depends(validate_token),
   user_id: UUID = Path(..., description="The ID of the user to update project-specific permission-overrides for"),
   project_id: UUID = Path(..., description="The ID of the project to update user-specific permission-overrides on"),
   db: Session = Depends(get_db)
) -> dict[str, Any]:
   try:
      # Check logged-in user existence
      logged_in_user = db.query(User).filter(User.email == user_email).first()
      if not logged_in_user:
         print(f"INSIDE PATCH /users/{user_id}/projects/{project_id} validate_update_project_permission_overrides dependency: logged-in user with email - {user_email} - not found in user table")
         raise ApiError.unauthorized("user is unauthenticated")
      
      # Check existence of user 
      user_to_patch = db.query(User).filter(User.id == user_id).first()
      if not user_to_patch:
         print(f"INSIDE PATCH /users/{user_id}/projects/{project_id} validate_update_project_permission_overrides dependency: user - {user_id} - not found in user table")
         raise ApiError.notfound(f"user - '{user_id}' - not found")
      
      # Check existence of project
      project = db.query(Project).filter(Project.id == project_id).first()
      if not project:
         print(f"INSIDE PATCH /users/{user_id}/projects/{project_id} validate_update_project_permission_overrides dependency: project - {project_id} - not found in Project table")
         raise ApiError.notfound(f"project - '{project_id}' - not found")
      
      # Check User_Project association
      user_project_association = db.query(User_Project).filter(User_Project.user_id == user_id, User_Project.project_id == project_id).first()
      if not user_project_association:
         print(f"INSIDE PATCH /users/{user_id}/projects/{project_id} validate_update_project_permission_overrides dependency: user - '{user_id}' - is not assigned to project - '{project_id}'")
         raise ApiError.validationerror(f"user - '{user_id}' - is not assigned to project - '{project_id}'")
      
      # Check if account is disabled
      account = db.query(Account).filter(Account.id == project.account_id).first()
      if not account:
         print(f"INSIDE PATCH /users/{user_id}/projects/{project_id} validate_update_project_permission_overrides dependency: project's account - '{project.account_id}' - not found")
         raise ApiError.notfound(f"account - '{project.account_id}' - not found")
      if account.is_disabled:
         print(f"INSIDE PATCH /users/{user_id}/projects/{project_id} validate_update_project_permission_overrides dependency: account - '{project.account_id}' - is disabled")
         raise ApiError.forbidden(f"account - '{project.account_id}' - is disabled")
      
      # TODO: Check ancestor projects for disabled status
      
      validation_info: dict[str, Any] = {"user_project_association": user_project_association, "db": db}

      user_account_association = db.query(User_Account).filter(User_Account.user_id == user_to_patch.id, User_Account.account_id == project.account_id).first()
      if not user_account_association:
         print(f"INSIDE PATCH /users/{user_id}/projects/{project_id} - validate_update_project_permission_overrides dependency: user -'{user_to_patch.id}'- not assigned to account - '{project.account_id}'")
         raise ApiError.validationerror(f"user - '{user_to_patch.id}' - is not assigned to account - '{project.account_id}")
      
      if user_to_patch.id == project.project_owner_id or user_account_association.is_admin or user_to_patch.is_superadmin:
         print(f"INSIDE PATCH /users/{user_id}/projects/{project_id} - validate_update_project_permission_overrides dependency: Invalid action - Attempting to update project permission overrides for user - '{user_to_patch.id}' - who is admin/superadmin/project-owner")
         raise ApiError.validationerror(f"Invalid action - Attempting to update project permission overrides for user - '{user_to_patch.id}' - who is admin/superadmin/project-owner")
      
      # Check superadmin
      if logged_in_user.is_superadmin:
         return validation_info

      # Check User_Account association for logged-in user and admin status
      logged_in_user_account_association = db.query(User_Account).filter(User_Account.user_id == logged_in_user.id, User_Account.account_id == project.account_id).first()
      if not logged_in_user_account_association:
         print(f"INSIDE PATCH /users/{user_id}/projects/{project_id} validate_update_project_permission_overrides dependency: logged-in user -'{logged_in_user.id}'- not assigned to account - '{project.account_id}'")
         raise ApiError.forbidden(f"you are not assigned to account - '{project.account_id}")
      
      if logged_in_user_account_association.is_admin:
         return validation_info
      
      if project.project_owner_id == logged_in_user.id:
         if is_user_project_association_till_root(db=db, starting_project_id=project.id, user_id=logged_in_user.id):
            return validation_info
         
         print(f"logged-in user - '{logged_in_user.id}' - is not assigned to all projects in the project hierarchy of project - '{project.id}'")
         raise ApiError.forbidden(f"you are not assigned to all projects in the project hierarchy of project - '{project.id}")
      
      print(f"INSIDE PATCH /users/{user_id}/projects/{project_id} validate_patch_project_permission_overrides dependency: logged-in user -'{logged_in_user.id}'- does not have superadmin,admin or project association with project-owner privileges to update project permission overrides for user - '{user_to_patch.id}' - in project - '{project.id}'")
      raise ApiError.forbidden(f"you do not have superadmin,admin or project association with project-owner privileges to update project permission overrides for user - '{user_to_patch.id}' - in project - '{project.id}'")
   except HTTPException as e:
      db.rollback()
      pprint(f'API error in PATCH /{user_id}/projects/{project_id}/permission-overrides - validate_update_project_permission_overrides dependency: {e}')
      raise e
   except SQLAlchemyError as e:
      db.rollback()
      pprint(f'DB error in PATCH /{user_id}/projects/{project_id}/permission-overrides - validate_update_project_permission_overrides dependency: {e}')
      raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
   except Exception as e:
      db.rollback()
      print(f'Unexpected error in PATCH /{user_id}/projects/{project_id}/permission-overrides - validate_update_project_permission_overrides dependency: {e}')
      raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")

async def validate_get_project_permission_overrides(
   user_email: str = Depends(validate_token),
   user_id: UUID = Path(..., description="The ID of the user to get project-specific permission-overrides for"),
   project_id: UUID = Path(..., description="The ID of the project to get user-specific permission-overrides for"),
   db: Session = Depends(get_db)
) -> dict[str, Any]:
   try:
      # Check logged-in user existence
      logged_in_user = db.query(User).filter(User.email == user_email).first()
      if not logged_in_user:
         print(f"INSIDE GET/users/{user_id}/projects/{project_id} validate_get_project_permission_overrides dependency: logged-in user with email - {user_email} - not found in user table")
         raise ApiError.unauthorized("user is unauthenticated")
      
      # Check existence of user 
      user = db.query(User).filter(User.id == user_id).first()
      if not user:
         print(f"INSIDE GET /users/{user_id}/projects/{project_id} validate_get_project_permission_overrides dependency: user - {user_id} - not found in user table")
         raise ApiError.notfound(f"user - '{user_id}' - not found")
      
      # Check existence of project
      project = db.query(Project).filter(Project.id == project_id).first()
      if not project:
         print(f"INSIDE GET /users/{user_id}/projects/{project_id} validate_get_project_permission_overrides dependency: project - {project_id} - not found in Project table")
         raise ApiError.notfound(f"project - '{project_id}' - not found")
      
      # Check User_Project association
      user_project_association = db.query(User_Project).filter(User_Project.user_id == user_id, User_Project.project_id == project_id).first()
      if not user_project_association:
         print(f"INSIDE GET /users/{user_id}/projects/{project_id} validate_get_project_permission_overrides dependency: user - '{user_id}' - is not assigned to project - '{project_id}'")
         raise ApiError.validationerror(f"user - '{user_id}' - is not assigned to project - '{project_id}'")
      
      # Check if account is disabled
      account = db.query(Account).filter(Account.id == project.account_id).first()
      if not account:
         print(f"INSIDE GET /users/{user_id}/projects/{project_id} validate_get_project_permission_overrides dependency: project's account - '{project.account_id}' - not found")
         raise ApiError.notfound(f"account - '{project.account_id}' - not found")
      if account.is_disabled:
         print(f"INSIDE GET /users/{user_id}/projects/{project_id} validate_get_project_permission_overrides dependency: account - '{project.account_id}' - is disabled")
         raise ApiError.forbidden(f"account - '{project.account_id}' - is disabled")
      
      # TODO: Check ancestor projects for disabled status
      
      validation_info: dict[str, Any] = {"user_project_association": user_project_association, "db": db}
      
      user_account_association = db.query(User_Account).filter(User_Account.user_id == user.id, User_Account.account_id == project.account_id).first()
      if not user_account_association:
         print(f"INSIDE GET /users/{user_id}/projects/{project_id} - validate_get_project_permission_overrides dependency: user -'{user.id}'- not assigned to account - '{project.account_id}'")
         raise ApiError.validationerror(f"user - '{user.id}' - is not assigned to account - '{project.account_id}")
      
      if user.id == project.project_owner_id or user_account_association.is_admin or user.is_superadmin:
         print(f"INSIDE GET /users/{user_id}/projects/{project_id} - validate_get_project_permission_overrides dependency: Invalid action - Attempting to read project permission overrides for user - '{user.id}' - who is admin/superadmin/project-owner")
         raise ApiError.validationerror(f"Invalid action - Attempting to read project permission overrides for user - '{user.id}' - who is admin/superadmin/project-owner")
      
      # Check superadmin
      if logged_in_user.is_superadmin:
         return validation_info

      # Check User_Account association for logged-in user and admin status
      logged_in_user_account_association = db.query(User_Account).filter(User_Account.user_id == logged_in_user.id, User_Account.account_id == project.account_id).first()
      if not logged_in_user_account_association:
         print(f"INSIDE GET /users/{user_id}/projects/{project_id}validate_get_project_permission_overrides dependency: logged-in user -'{logged_in_user.id}'- not assigned to account - '{project.account_id}'")
         raise ApiError.forbidden(f"you are not assigned to account - '{project.account_id}")
      
      if logged_in_user_account_association.is_admin or logged_in_user.id == user.id:
         return validation_info
      
      # Check User_Project association for logged-in user and check project ownership (he should not be able to read resource if he is not part of project but was owner)
      if project.project_owner_id == logged_in_user.id:
         if is_user_project_association_till_root(db=db, starting_project_id=project.id, user_id=logged_in_user.id):
            return validation_info
         
         print(f"logged-in user - '{logged_in_user.id}' - is not assigned to all projects in the project hierarchy of project - '{project.id}'")
         raise ApiError.forbidden(f"you are not assigned to all projects in the project hierarchy of project - '{project.id}")

      print(f"INSIDE GET /users/{user_id}/projects/{project_id} validate_get_project_permission_overrides dependency: logged-in user -'{logged_in_user.id}'- does not have superadmin,admin or project association with project-owner privileges to read project permission overrides for user - '{user.id}' - in project - '{project.id}'")
      raise ApiError.forbidden(f"you do not have superadmin,admin or project association with project-owner privileges to read project permission overrides for user - '{user.id}' - in project - '{project.id}'")
   except HTTPException as e:
      db.rollback()
      pprint(f'API error in GET /{user_id}/projects/{project_id}/permission-overrides - validate_get_project_permission_overrides dependency: {e}')
      raise e
   except SQLAlchemyError as e:
      db.rollback()
      pprint(f'DB error in GET /{user_id}/projects/{project_id}/permission-overrides - validate_get_project_permission_overrides dependency: {e}')
      raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
   except Exception as e:
      db.rollback()
      print(f'Unexpected error in GET /{user_id}/projects/{project_id}/permission-overrides - validate_get_project_permission_overrides dependency: {e}')
      raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
   
# async def validate_update_superadmin_status(
#    user_email: str = Depends(validate_token),
#    db: Session = Depends(get_db)
# ) -> dict[str, Any]:
#    try:
#       # Fetch the logged-in user by email
#       logged_in_user = db.query(User).filter(User.email == user_email).first()

#       # Check if the user exists
#       if not logged_in_user:
#          print(f"INSIDE PATCH validate_update_superadmin_status: logged-in user - '{logged_in_user.id}' - not found")
#          raise ApiError.notfound("user is unauthorized")

#       # Check if the user is a superadmin
#       if logged_in_user.is_superadmin: #type: ignore
#          return {"db" : db}

#       print('INSIDE validate_update_superadmin_status: you do not have superadmin privileges to modify superadmin status of users')
#       raise ApiError.forbidden("User must be a superadmin in order to modify superadmin status")
#    except SQLAlchemyError as e:
#       pprint(f'DB error in validate_update_superadmin_status: {e}')
#       raise ApiError.serviceunavailable("The database is currently unavailable, please try again later.")
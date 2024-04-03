from fastapi import Query, Path, Depends, HTTPException
from uuid import UUID
from .header import validate_token
from sqlalchemy.orm import Session
from sqlalchemy import and_, select, exists
from sqlalchemy.exc import SQLAlchemyError
from pprint import pprint
from typing import Any
from rbac_api.app.errors.api_error import ApiError


from rbac_api.utils.deps import get_db  
from elevaitedb.db import models

async def validate_post_account(
   user_email: str = Depends(validate_token),
   db: Session = Depends(get_db)
) -> dict[str, Any]:
   try:
      # 1. fetch user, and check if he is superadmin for validation

      # Fetch user by email
      logged_in_user = db.query(models.User).filter(models.User.email == user_email).first()
      if not logged_in_user:
         print(f"in POST /accounts/ - validate_post_account dependency : logged in user with email -'{user_email}'- not found in user table")
         raise ApiError.unauthorized("user is unauthenticated") # decide whether to expose user not found

      # Check if user is a superadmin
      if logged_in_user.is_superadmin:
         return {"logged_in_user_id" : logged_in_user.id, "db" : db}

      # If not a superadmin, deny access
      print(f"in POST /accounts/ - validate_post_account dependency : logged in user -'{logged_in_user.id}'- does not have superadmin privileges to create accounts")
      raise ApiError.forbidden("you do not have superadmin privileges to create accounts")
   except HTTPException as e:
      db.rollback()
      pprint(f'API error in POST /accounts/ - validate_post_account dependency : {e}')
      raise e
   except SQLAlchemyError as e:
      pprint(f'DB error in POST /accounts/ - validate_post_account dependency : {e}')
      raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
   except Exception as e:
      db.rollback()
      print(f'Unexpected error in POST /accounts/ - validate_post_account dependency : {e}')
      raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
   
async def validate_patch_account(
    user_email: str = Depends(validate_token),
    account_id: UUID = Path(..., description="The ID of the account to patch"),
    db: Session = Depends(get_db)
) -> dict[str, Any]:
   try:
      # Fetch user, confirm if user exists, and confirm if account exists
      # 1. there are 2 cases for valid users: superadmins and admins
      # 2. account should not be disabled for both, 
      logged_in_user_id_subquery = select(models.User.id).where(models.User.email == user_email).limit(1).as_scalar().label("logged_in_user_id") 
      user_is_superadmin_subquery = select(models.User.is_superadmin).where(models.User.email == user_email).as_scalar().label("user_is_superadmin")
      
      user_is_admin_subquery = select(exists().where(and_( 
         models.User_Account.user_id == logged_in_user_id_subquery,
         models.User_Account.account_id == account_id,
         models.User_Account.is_admin == True
      ))).as_scalar().label("user_is_admin")

      # Execute the combined query in 1 db call
      query_result = db.query(
         logged_in_user_id_subquery,
         user_is_superadmin_subquery,
         user_is_admin_subquery
      ).one()

      # Extract results
      logged_in_user_id, user_is_superadmin, user_is_admin = query_result

      if not logged_in_user_id:
         print(f"in PATCH /accounts/{account_id} - validate_patch_account dependency : logged in user with email -'{user_email}'- not found in user table")
         raise ApiError.unauthorized("user is unauthenticated")  # User not found
      
      account = db.query(models.Account).filter(models.Account.id == account_id).first()
      if not account:
         print(f"in PATCH /accounts/{account_id} - validate_patch_account dependency : account - '{account_id}' - not found in accounts table")
         raise ApiError.notfound(f"account - '{account_id}' - not found")  # Account not found
      
      if account.is_disabled:
         print(f"in PATCH /accounts/{account_id} - validate_patch_account dependency : account - '{account_id}' - not found in accounts table")
         raise ApiError.forbidden(f"account - '{account_id}' - is disabled")  

      if user_is_superadmin:
         return {"account_to_patch" : account, "db" : db}

      if not user_is_admin:
      # User is not an admin for the account
         print(f"in PATCH /accounts/{account_id} - validate_patch_account dependency : user - '{user_email}' - is not a superadmin/admin for account - '{account_id}'")
         raise ApiError.forbidden(f"you do not have superadmin/admin privileges to patch account - '{account_id}'")
         # print(f"in PATCH /accounts/{account_id} - validate_patch_account dependency : logged in user -'{logged_in_user.id}'- does not have superadmin/account-admin permissions to patch account -'{account_id}'")
         # raise ApiError.forbidden("user does not have permissions to perform this action")
      return {"account_to_patch" : account, "db" : db}
   except HTTPException as e:
      db.rollback()
      pprint(f'API error in PATCH /accounts/{account_id} - validate_patch_account dependency : {e}')
      raise e
   except SQLAlchemyError as e:
      pprint(f'DB error in PATCH /accounts/{account_id} - validate_patch_account dependency : {e}')
      raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
   except Exception as e:
      db.rollback()
      print(f'Unexpected error in PATCH /accounts/{account_id} - validate_patch_account dependency : {e}')
      raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")

# async def validate_get_account(
#     user_email: str = Depends(validate_token),
#     account_id: UUID = Path(..., description="The ID of the account to retrieve"),
#     db: Session = Depends(get_db)
# ) -> UUID:
#    try:
#       # Fetch user by email
#       logged_in_user = db.query(User).filter(User.email == user_email).first()
#       if not logged_in_user:
#          print(f'in GET /accounts/{account_id} - validate_patch_account dependency : logged in user with email - {user_email} - not found in user table')
#          raise ApiError.unauthorized("user is unauthorized")
      
#       # Check if user is a superadmin
#       if logged_in_user.is_superadmin: 
#          return logged_in_user.id  # type: ignore # Return the user ID for further use
      
#       # Fetch account to ensure it exists
#       account = db.query(Account).filter(Account.id == account_id).first()
#       if not account:
#          print(f'in validate_get_account: Account - {account_id} - not found')
#          raise ApiError.notfound("account not found")

#       # Check for any association between user and account
#       user_account_association = db.query(User_Account).filter(
#          User_Account.user_id == logged_in_user.id,
#          User_Account.account_id == account_id
#       ).first()

#       if user_account_association:
#          return logged_in_user.id  #type: ignore # Return user ID for further use in the route function
      
#       print(f'in validate_get_account: logged in user - {logged_in_user.id} - does not have permissions to access account - {account_id}')
#       raise ApiError.forbidden("user does not have permissions to perform this action")
#    except HTTPException as e:
#       db.rollback()
#       pprint(f'Error in validate_get_account : {e}')
#       raise e
#    except SQLAlchemyError as e:
#       pprint(f'DB error in validate_get_account: {e}')
#       raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
#    except Exception as e:
#       print(f'Unexpected error in validate_get_account : {e}')
#       raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
async def validate_get_account(
   user_email: str = Depends(validate_token),
   org_id: UUID = Query(description = "org_id under which account is queried"),
   account_id: UUID = Path(description = "id of account to be queried"),
   db: Session = Depends(get_db),
) -> dict[str, Any]:
   try:
      # Fetch user by email
      logged_in_user = db.query(models.User).filter(models.User.email == user_email).first()
      if not logged_in_user:
         print(f"in GET /accounts/{account_id}?org_id={org_id} - validate_get_account dependency : logged in user with email -'{user_email}'- not found in user table")
         raise ApiError.unauthorized("user is unauthenticated")
      
      # Fetch organization
      organization = db.query(models.Organization).filter(models.Organization.id == org_id).first()
      if not organization:
         print(f"in GET /accounts/{account_id}?org_id={org_id} - validate_get_account dependency : organization -'{org_id}'- not found")
         raise ApiError.notfound(f"organization - '{org_id}' - not found")
      
      if logged_in_user.organization_id != org_id:
         print(f"in GET /accounts/{account_id}?org_id={org_id} - validate_get_account dependency : logged-in user -'{logged_in_user.id}'- is not assigned to organization -'{org_id}'")
         raise ApiError.forbidden(f"you are not assigned to organization - '{org_id}'")
      
      account = db.query(models.Account).filter(models.Account.id == account_id).first()
      if not account:
         print(f"in GET /accounts/{account_id}?org_id={org_id} - validate_get_account dependency : account - '{account_id}' - not found")
         raise ApiError.notfound(f"account - '{account_id}' - not found")
      
      if logged_in_user.is_superadmin:
         return {"account": account}
      
      user_account_association_exists = db.query(exists().where(
         models.User_Account.user_id == logged_in_user.id,
         models.User_Account.account_id == account_id
      )).scalar()
      
      if not user_account_association_exists:
         print(f"in GET /accounts/{account_id}?org_id={org_id} - validate_get_account dependency : logged-in user - '{logged_in_user.id}' - is not assigned to account - '{account_id}'")
         raise ApiError.forbidden(f"you are not assigned to account - '{account_id}'")
      
      return {"account": account}
   except HTTPException as e:
      db.rollback()
      pprint(f'API error in GET /accounts/{account_id}?org_id={org_id} - validate_get_account dependency : {e}')
      raise e
   except SQLAlchemyError as e:
      pprint(f'DB error in GET /accounts/{account_id}?org_id={org_id} - validate_get_account dependency : {e}')
      raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
   except Exception as e:
      print(f'Unexpected error in GET /accounts/?org_id={org_id} - validate_get_account dependency : {e}')
      raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
   
async def validate_get_accounts(
   user_email: str = Depends(validate_token),
   org_id: UUID = Query(description = "org_id under which accounts are queried"),
   db: Session = Depends(get_db)
) -> dict[str, Any]:
   try:
      # Fetch user by email
      logged_in_user = db.query(models.User).filter(models.User.email == user_email).first()
      if not logged_in_user:
         print(f"in GET /accounts/?org_id={org_id} - validate_get_accounts dependency : logged in user with email -'{user_email}'- not found in user table")
         raise ApiError.unauthorized("user is unauthenticated")

      # Fetch organization
      organization = db.query(models.Organization).filter(models.Organization.id == org_id).first()
      if not organization:
         print(f"in GET /accounts/?org_id={org_id} - validate_get_accounts dependency : organization -'{org_id}'- not found")
         raise ApiError.notfound(f"organization - '{org_id}' - not found")
      
      if logged_in_user.organization_id != org_id:
         print(f"in GET /accounts/?org_id={org_id} - validate_get_accounts dependency : logged-in user -'{logged_in_user.id}'- is not assigned to organization -'{org_id}'")
         raise ApiError.forbidden(f"you are not assigned to organization - '{org_id}'")
      
      return {"logged_in_user_id" : logged_in_user.id,
               "logged_in_user_is_superadmin" : logged_in_user.is_superadmin,
               "db" : db} 

   except HTTPException as e:
      db.rollback()
      pprint(f'API error in GET /accounts/?org_id={org_id} - validate_get_accounts dependency : {e}')
      raise e
   except SQLAlchemyError as e:
      pprint(f'DB error in GET /accounts/?org_id={org_id} - validate_get_accounts dependency : {e}')
      raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
   except Exception as e:
      print(f'Unexpected error in GET /accounts/?org_id={org_id} - validate_get_accounts dependency : {e}')
      raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")

async def validate_get_account_user_list_or_profile(
    db: Session = Depends(get_db),
    account_id: UUID = Path(..., description="Account id under which users are queried"),
    user_email: str = Depends(validate_token)
) -> dict[str, Any]:
   # logged-in user must exist, account must exist
   # superadmin and admins can get account user profile info regardless of disabled status 
   # regular users can get account user profile info list only if account is not disabled 
   try:
      # Fetch user by email
      logged_in_user = db.query(models.User).filter(models.User.email == user_email).first()
      if not logged_in_user:
         print(f"in GET /accounts/{account_id}/profile - validate_get_account_user_profile dependency : logged-in user with email -'{user_email}'- not found in user table")
         raise ApiError.unauthorized("user is unauthenticated")

      # Check if the account exists
      account = db.query(models.Account).filter(models.Account.id == account_id).first()
      if not account:
         print(f"in GET /accounts/{account_id}/profile - validate_get_account_user_profile dependency : account -'{account_id}'- not found")
         raise ApiError.notfound(f"account - '{account_id}' - not found")

      if logged_in_user.is_superadmin:
         return {"logged_in_user_id": logged_in_user.id,
                  "logged_in_user" : logged_in_user,
                  "user_account_association" : None,
                  "db": db}
      # Check if the logged-in user is associated with the account
      user_account_association = db.query(models.User_Account).filter_by(user_id=logged_in_user.id, account_id=account_id).first()
      if not user_account_association:
         print(f"in GET /accounts/{account_id}/profile - validate_get_account_user_profile dependency : user - '{logged_in_user.id}' is not a member of account -'{account_id}'")
         raise ApiError.forbidden(f"you are not assigned to account - '{account_id}'")

      if account.is_disabled and not user_account_association.is_admin:
         print(f"in GET /accounts/{account_id}/profile - validate_get_account_user_profile dependency : account -'{account_id}' is disabled")
         raise ApiError.forbidden(f"account - '{account_id}' - is disabled")

      return {"logged_in_user_id": logged_in_user.id,
              "logged_in_user" : logged_in_user,
               "user_account_association" : user_account_association,
               "db": db}
   except HTTPException as e:
      db.rollback()
      pprint(f'API error in GET /accounts/{account_id}/profile - validate_get_account_user_profile dependency : {e}')
      raise e
   except SQLAlchemyError as e:
      pprint(f'DB error in GET /accounts/{account_id}/profile - validate_get_account_user_profile dependency : {e}')
      raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
   except Exception as e:
      print(f'Unexpected error in GET /accounts/{account_id}/profile - validate_get_account_user_profile dependency : {e}')
      raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
   
async def validate_assign_or_deassign_users_in_account(
    user_email: str = Depends(validate_token),  # Assuming this dependency extracts and validates the user's email
    account_id: UUID = Path(..., description="The ID of the account"),
    db: Session = Depends(get_db)
) -> dict[str, Any]:
   try:
      # Fetch logged-in user from email, validate existence. Then fetch account from account_id, validate existence.
      # 3 cases for users: superadmin, admin and regular
      # For superadmin, make sure the account is not disabled, and validate
      # For admin, make sure account is not disabled, and check for User_Account association to verify admin, and then validate
      # For regular user, invalidate since no permissions

      # Fetch current user by email
      logged_in_user = db.query(models.User).filter(models.User.email == user_email).first()
      if not logged_in_user:
         print(f"in PATCH /accounts/{account_id}/users - validate_assign_or_deassign_users dependency : logged-in user with email -'{user_email}'- not found in user table")
         raise ApiError.unauthorized("user is unauthenticated")
      
      # Fetch account by ID
      account = db.query(models.Account).filter(models.Account.id == account_id).first()
      if not account:
         print(f"in PATCH /accounts/{account_id}/users - validate_assign_or_deassign_users dependency : account -'{account_id}'- not found")
         raise ApiError.notfound(f"account - '{account_id}' - not found")
      
      if account.is_disabled:
         print(f"in PATCH /accounts/{account_id}/users - validate_assign_or_deassign_users dependency : account -'{account_id}'- is disabled")
         raise ApiError.forbidden(f"account - '{account_id}' - is disabled")
      # Check if the user is superadmin
      if logged_in_user.is_superadmin: 
         return {"logged_in_user_id" : logged_in_user.id,
                  "logged_in_user_is_superadmin" : True,
                  "logged_in_user_is_admin" : None,
                  "db" : db}

      # Check for User_Account association
      user_account = db.query(models.User_Account).filter(
         models.User_Account.user_id == logged_in_user.id,
         models.User_Account.account_id == account_id
      ).first()

      if user_account and user_account.is_admin:
         return {"logged_in_user_id" : logged_in_user.id,
                  "logged_in_user_is_superadmin" : False,
                  "logged_in_user_is_admin" : True,
                  "db": db}
      
      print(f"in PATCH /accounts/{account_id}/users - validate_assign_or_deassign_users dependency : logged-in user -'{logged_in_user.id}'- does not have superadmin/admin privileges to assign or deassign users to this account -'{account_id}'")
      raise ApiError.forbidden(f"you do not have superadmin/admin privileges to assign or deassign users in account - '{account_id}'")
   except HTTPException as e:
      db.rollback()
      pprint(f'API error in PATCH /accounts/{account_id}/users - validate_assign_or_deassign_users dependency : {e}')
      raise e
   except SQLAlchemyError as e:
      pprint(f'DB error in PATCH /accounts/{account_id}/users - validate_assign_or_deassign_users dependency : {e}')
      raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
   except Exception as e:
      print(f'Unexpected error in PATCH /accounts/{account_id}/users - validate_assign_or_deassign_users dependency : {e}')
      raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")

async def validate_patch_account_admin_status(
    user_email: str = Depends(validate_token),
    account_id: UUID = Path(..., description = "The ID of the account"),
    db: Session = Depends(get_db)
) -> dict[str, Any]:
   try:
      # Only Superadmins and admins can patch admin status for any valid non-disabled account

      # Fetch user by email
      logged_in_user = db.query(models.User).filter(models.User.email == user_email).first()
      if not logged_in_user:
         print(f"in PATCH /accounts/{account_id}/admin - validate_patch_account_admin_status dependency : logged-in user with email -'{user_email}'- not found in user table")
         raise ApiError.unauthorized("user is unauthenticated")

      account = db.query(models.Account).filter(models.Account.id == account_id).first()

      if not account:
         print(f"in PATCH /accounts/{account_id}/admin - validate_patch_account_admin_status dependency : account -'{account_id}'- not found")
         raise ApiError.notfound(f"account - '{account_id}' - not found")
      
      if account.is_disabled:
         print(f"in PATCH /accounts/{account_id}/users - validate_assign_or_deassign_users dependency : account -'{account_id}'- is disabled")
         raise ApiError.forbidden(f"account - '{account_id}' - is disabled")
      
      # Check if the user is superadmin
      if logged_in_user.is_superadmin: 
         return {"logged_in_user_id" : logged_in_user.id,
                  "logged_in_user_is_superadmin" : True,
                  "logged_in_user_is_admin" : None,
                  "db": db}


      # Check if there's an association between the logged-in user and the account
      logged_in_user_account_association = db.query(models.User_Account).filter(
         models.User_Account.user_id == logged_in_user.id,
         models.User_Account.account_id == account_id
      ).first()

      if not logged_in_user_account_association:
         print(f"in PATCH /accounts/{account_id}/admin - validate_patch_account_admin_status dependency : logged-in user -'{logged_in_user.id}'- does not have permissions to perform this action as user is not a member of account -'{account_id}'")
         raise ApiError.forbidden(f"you must be assigned to the account - '{account_id}' - to update user admin status in account")

      # Check if the user is an admin of the account
      if logged_in_user_account_association.is_admin: 
         return {"logged_in_user_id" : logged_in_user.id,
                  "logged_in_user_is_superadmin" : False,
                  "logged_in_user_is_admin" : True,
                  "db": db}

      print(f"in PATCH /accounts/{account_id}/admin - validate_patch_account_admin_status dependency : logged-in user -'{logged_in_user.id}'- is a member of account -'{account_id}', but lacks superadmin/admin status to perform action")
      raise ApiError.forbidden(f"you do not have superadmin/admin privileges to update user admin status in account - '{account_id}'")

   except HTTPException as e:
      db.rollback()
      pprint(f'API error in PATCH /accounts/{account_id}/admin - validate_patch_account_admin_status dependency : {e}')
      raise e
   except SQLAlchemyError as e:
      pprint(f'DB error in PATCH /accounts/{account_id}/admin - validate_patch_account_admin_status dependency : {e}')
      raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
   except Exception as e:
      print(f'Unexpected error in PATCH /accounts/{account_id}/admin - validate_patch_account_admin_status dependency : {e}')
      raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
   
async def validate_patch_account_status(
   user_email: str = Depends(validate_token),
   db: Session = Depends(get_db),
   account_id: UUID = Path(..., description="The ID of the account to patch enabled/disabled status")
) -> dict[str, Any]:
   try:
      # Only Superadmins and admins can patch account disabled status
      logged_in_user = db.query(models.User).filter(models.User.email == user_email).first()
      if not logged_in_user:
         print(f"in PATCH /accounts/{account_id}/status - validate_patch_account_status dependency : logged-in user with email -'{user_email}'- not found in user table")
         raise ApiError.unauthorized("user is unauthenticated")

      account = db.query(models.Account).filter(models.Account.id == account_id).first()

      if not account:
         print(f"in PATCH /accounts/{account_id}/status - validate_patch_account_status dependency : account -'{account_id}'- not found")
         raise ApiError.notfound(f"account - '{account_id}' - not found")

      # If logged-in user is a superadmin, return early
      if logged_in_user.is_superadmin:
         return {"account": account, "db" : db}

      # Check for logged-in user's association with the account
      user_account_association = db.query(models.User_Account).filter(
         models.User_Account.user_id == logged_in_user.id,
         models.User_Account.account_id == account_id
      ).first()
      
      if not user_account_association:
         print(f"in PATCH /accounts/{account_id}/status - validate_patch_account_status dependency : logged-in user -'{logged_in_user.id}'- is not assigned to account -'{account_id}'")
         raise ApiError.forbidden(f"you are not assigned to account - '{account_id}'")

      # Check if the user is an admin of the account
      if user_account_association.is_admin:
         return {"account": account, "db" : db}
      
      # If the flow reaches here, the user does not have permission to patch the account status
      print(f"in PATCH /accounts/{account_id}/status - validate_patch_account_status dependency : logged-in user -'{logged_in_user.id}'- does not have superadmin/admin permissions")
      raise ApiError.forbidden(f"you do not have superadmin/admin privileges to update status of account - '{account_id}'")
   except HTTPException as e:
      db.rollback()
      pprint(f'API error in PATCH /accounts/{account_id}/status - validate_patch_account_status dependency : {e}')
      raise e
   except SQLAlchemyError as e:
      pprint(f'DB error in PATCH /accounts/{account_id}/status - validate_patch_account_status dependency : {e}')
      raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
   except Exception as e:
      print(f'Unexpected error in PATCH /accounts/{account_id}/status - validate_patch_account_status dependency : {e}')
      raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
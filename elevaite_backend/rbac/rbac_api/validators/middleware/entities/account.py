from fastapi import Query, Path, Depends, HTTPException
from uuid import UUID
from ..auth.token import validate_token
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
      # Fetch user by email
      logged_in_user = db.query(models.User).filter(models.User.email == user_email).first()
      if not logged_in_user:
         raise ApiError.unauthorized("User is unauthenticated") # decide whether to expose user not found

      # Check if user is a superadmin
      if logged_in_user.is_superadmin:
         return {"logged_in_user" : logged_in_user, "db" : db}

      # If not a superadmin, deny access
      raise ApiError.forbidden("you do not have superadmin privileges to create accounts")
   except HTTPException as e:
      db.rollback()
      pprint(f'API error in POST /accounts/ - validate_post_account middleware : {e}')
      raise e
   except SQLAlchemyError as e:
      pprint(f'DB error in POST /accounts/ - validate_post_account middleware : {e}')
      raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
   except Exception as e:
      db.rollback()
      print(f'Unexpected error in POST /accounts/ - validate_post_account middleware : {e}')
      raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
   
async def validate_patch_account(
    user_email: str = Depends(validate_token),
    account_id: UUID = Path(..., description="The ID of the account to patch"),
    db: Session = Depends(get_db)
) -> dict[str, Any]:
   try: 
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
         raise ApiError.unauthorized("User is unauthenticated")  # User not found
      
      account = db.query(models.Account).filter(models.Account.id == account_id).first()
      if not account:
         raise ApiError.notfound(f"Account - '{account_id}' - not found")  # Account not found

      if user_is_superadmin or user_is_admin:
         return {"Account" : account, "db" : db}

      raise ApiError.forbidden(f"you do not have superadmin/account-admin privileges to patch account - '{account_id}'")
   except HTTPException as e:
      db.rollback()
      pprint(f'API error in PATCH /accounts/{account_id} - validate_patch_account middleware : {e}')
      raise e
   except SQLAlchemyError as e:
      pprint(f'DB error in PATCH /accounts/{account_id} - validate_patch_account middleware : {e}')
      raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
   except Exception as e:
      db.rollback()
      print(f'Unexpected error in PATCH /accounts/{account_id} - validate_patch_account middleware : {e}')
      raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")

async def validate_get_account(
   user_email: str = Depends(validate_token),
   account_id: UUID = Path(description = "id of account to be queried"),
   db: Session = Depends(get_db),
) -> dict[str, Any]:
   try:
      # Fetch user by email
      logged_in_user = db.query(models.User).filter(models.User.email == user_email).first()
      if not logged_in_user:
         raise ApiError.unauthorized("User is unauthenticated")
      
      account = db.query(models.Account).filter(models.Account.id == account_id).first()
      if not account:
         raise ApiError.notfound(f"account - '{account_id}' - not found")
      
      if logged_in_user.is_superadmin:
         return {"Account": account}
      
      user_account_association_exists = db.query(exists().where(
         models.User_Account.user_id == logged_in_user.id,
         models.User_Account.account_id == account_id
      )).scalar()
      
      if not user_account_association_exists:
         raise ApiError.forbidden(f"you are not assigned to account - '{account_id}'")
      
      return {"Account": account}
   except HTTPException as e:
      db.rollback()
      pprint(f'API error in GET /accounts/{account_id} - validate_get_account middleware : {e}')
      raise e
   except SQLAlchemyError as e:
      pprint(f'DB error in GET /accounts/{account_id} - validate_get_account middleware : {e}')
      raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
   except Exception as e:
      print(f'Unexpected error in GET /accounts/{account_id} - validate_get_account middleware : {e}')
      raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
   
async def validate_get_accounts(
   user_email: str = Depends(validate_token),
   db: Session = Depends(get_db)
) -> dict[str, Any]:
   try:
      # Fetch user by email
      logged_in_user = db.query(models.User).filter(models.User.email == user_email).first()
      if not logged_in_user:
         raise ApiError.unauthorized("User is unauthenticated")
      
      return {"logged_in_user" : logged_in_user,
               "db" : db} 

   except HTTPException as e:
      db.rollback()
      pprint(f'API error in GET /accounts/ - validate_get_accounts middleware : {e}')
      raise e
   except SQLAlchemyError as e:
      pprint(f'DB error in GET /accounts/ - validate_get_accounts middleware : {e}')
      raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
   except Exception as e:
      print(f'Unexpected error in GET /accounts/ - validate_get_accounts middleware : {e}')
      raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")

async def validate_get_account_user_list(
   db: Session = Depends(get_db),
   account_id: UUID = Path(..., description="Account id under which users are queried"),
   user_email: str = Depends(validate_token)
) -> dict[str, Any]:
   try:
      # Fetch user by email
      logged_in_user = db.query(models.User).filter(models.User.email == user_email).first()
      if not logged_in_user:
         raise ApiError.unauthorized("User is unauthenticated")

      # Check if the account exists
      account = db.query(models.Account).filter(models.Account.id == account_id).first()
      if not account:
         raise ApiError.notfound(f"Account - '{account_id}' - not found")

      if logged_in_user.is_superadmin:
         return { "logged_in_user" : logged_in_user,
                  "logged_in_user_account_association" : None,
                  "db": db}
      # Check if the logged-in user is associated with the account
      logged_in_user_account_association = db.query(models.User_Account).filter_by(user_id=logged_in_user.id, account_id=account_id).first()
      if not logged_in_user_account_association:
         raise ApiError.forbidden(f"you are not assigned to account - '{account_id}'")

      return {"logged_in_user" : logged_in_user,
               "logged_in_user_account_association" : logged_in_user_account_association,
               "db": db}
   except HTTPException as e:
      db.rollback()
      pprint(f'API error in GET /accounts/{account_id}/users - validate_get_account_user_list middleware : {e}')
      raise e
   except SQLAlchemyError as e:
      pprint(f'DB error in GET /accounts/{account_id}/users - validate_get_account_user_list middleware : {e}')
      raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
   except Exception as e:
      print(f'Unexpected error in GET /accounts/{account_id}/users - validate_get_account_user_list middleware : {e}')
      raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
   
async def validate_assign_users_to_account(
   user_email: str = Depends(validate_token),  # Assuming this dependency extracts and validates the user's email
   account_id: UUID = Path(..., description="The ID of the account"),
   db: Session = Depends(get_db)
) -> dict[str, Any]:
   try:
      # Fetch current user by email
      logged_in_user = db.query(models.User).filter(models.User.email == user_email).first()
      if not logged_in_user:
         raise ApiError.unauthorized("User is unauthenticated")
      
      # Fetch account by ID
      account = db.query(models.Account).filter(models.Account.id == account_id).first()
      if not account:
         raise ApiError.notfound(f"Account - '{account_id}' - not found")
      
      # Check if the user is superadmin
      if logged_in_user.is_superadmin: 
         return {"logged_in_user" : logged_in_user,
                  "db" : db}

      # Check for User_Account association
      logged_in_user_account_association = db.query(models.User_Account).filter(
         models.User_Account.user_id == logged_in_user.id,
         models.User_Account.account_id == account_id
      ).first()

      if logged_in_user_account_association:
         if logged_in_user_account_association.is_admin:
            return {"logged_in_user" : logged_in_user,
                     "db": db}
      
      raise ApiError.forbidden(f"you do not have superadmin/account-admin privileges to assign users to account - '{account_id}'")
   except HTTPException as e:
      db.rollback()
      pprint(f'API error in POST /accounts/{account_id}/users - validate_assign_users_to_account middleware : {e}')
      raise e
   except SQLAlchemyError as e:
      pprint(f'DB error in POST /accounts/{account_id}/users - validate_assign_users_to_account middleware : {e}')
      raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
   except Exception as e:
      print(f'Unexpected error in POST /accounts/{account_id}/users - validate_assign_users_to_account middleware : {e}')
      raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")

async def validate_deassign_user_from_account(
   user_email: str = Depends(validate_token),  
   account_id: UUID = Path(..., description="The ID of the account"),
   user_id: UUID = Path(..., description = "The ID of user to deassign from account"),
   db: Session = Depends(get_db)
) -> dict[str, Any]:
   try:
      # Fetch current user by email
      logged_in_user = db.query(models.User).filter(models.User.email == user_email).first()
      if not logged_in_user:
         raise ApiError.unauthorized("User is unauthenticated")
      
      # Fetch account by ID
      account = db.query(models.Account).filter(models.Account.id == account_id).first()
      if not account:
         raise ApiError.notfound(f"Account - '{account_id}' - not found")
      
      # Check if the user is superadmin
      if logged_in_user.is_superadmin: 
         return {"logged_in_user" : logged_in_user,
                  "db" : db}

      # Check for User_Account association
      logged_in_user_account_association = db.query(models.User_Account).filter(
         models.User_Account.user_id == logged_in_user.id,
         models.User_Account.account_id == account_id
      ).first()

      if logged_in_user_account_association:
         if logged_in_user_account_association.is_admin:
            return {"logged_in_user" : logged_in_user,
                     "db": db}
      
      raise ApiError.forbidden(f"you do not have superadmin/account-admin privileges to deassign user from account - '{account_id}'")
   except HTTPException as e:
      db.rollback()
      pprint(f'API error in DELETE /accounts/{account_id}/users/{user_id} - validate_deassign_user_from_account middleware : {e}')
      raise e
   except SQLAlchemyError as e:
      pprint(f'DB error in DELETE /accounts/{account_id}/users/{user_id} - validate_deassign_user_from_account middleware : {e}')
      raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
   except Exception as e:
      print(f'Unexpected error in DELETE /accounts/{account_id}/users/{user_id} - validate_deassign_user_from_account middleware : {e}')
      raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")

async def validate_patch_account_admin_status(
   user_email: str = Depends(validate_token),
   account_id: UUID = Path(..., description = "The ID of the account"),
   db: Session = Depends(get_db)
) -> dict[str, Any]:
   try:

      # Fetch user by email
      logged_in_user = db.query(models.User).filter(models.User.email == user_email).first()
      if not logged_in_user:
         raise ApiError.unauthorized("User is unauthenticated")

      account = db.query(models.Account).filter(models.Account.id == account_id).first()

      if not account:
         raise ApiError.notfound(f"Account - '{account_id}' - not found")
      
      # Check if the user is superadmin
      if logged_in_user.is_superadmin: 
         return {"logged_in_user" : logged_in_user,
                  "logged_in_user_account_association" : None,
                  "db": db}

      # Check if there's an association between the logged-in user and the account
      logged_in_user_account_association = db.query(models.User_Account).filter(
         models.User_Account.user_id == logged_in_user.id,
         models.User_Account.account_id == account_id
      ).first()

      if not logged_in_user_account_association:
         raise ApiError.forbidden(f"you are not assigned to account - '{account_id}'")

      # Check if the user is an admin of the account
      if logged_in_user_account_association.is_admin: 
         return {"logged_in_user" : logged_in_user,
                  "logged_in_user_account_association" : logged_in_user_account_association,
                  "db": db}

      raise ApiError.forbidden(f"you do not have superadmin/account-admin privileges to update user admin status in account - '{account_id}'")

   except HTTPException as e:
      db.rollback()
      pprint(f'API error in PATCH validate_patch_account_admin_status dependency : {e}')
      raise e
   except SQLAlchemyError as e:
      pprint(f'DB error in PATCH validate_patch_account_admin_status dependency : {e}')
      raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
   except Exception as e:
      print(f'Unexpected error in PATCH validate_patch_account_admin_status dependency : {e}')
      raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
   
from fastapi import Depends, HTTPException
from uuid import UUID
import os
from .header import validate_token
from sqlalchemy import exists
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from rbac_api.app.errors.api_error import ApiError
from typing import Any
from pprint import pprint

from rbac_api.utils.deps import get_db  
from elevaitedb.db import models

# async def validate_post_organization(
#    user_email: str = Depends(validate_token),
#    db: Session = Depends(get_db)
# ) -> dict[str, Any]:
#    try:
#       # Fetch user by email
#       logged_in_user = db.query(User).filter(User.email == user_email).first()
#       if not logged_in_user:
#          print(f'in POST /organizations - validate_post_organization: logged in user with email - {user_email} - not found in user table')
#          raise ApiError.unauthorized("user is unauthenticated")

#       # Validate if the user is a superadmin
#       if logged_in_user.is_superadmin: 
#          return {"db" : db}
      
#       print(f"in POST /organizations - validate_post_organization: logged in user - '{logged_in_user.id}' - does not have superadmin privileges to create an organization")
#       raise ApiError.forbidden("you do not have superadmin privileges to create organizations")
#    except HTTPException as e:
#       db.rollback()
#       pprint(f'Error in POST /organizations - validate_post_organization : {e}')
#       raise e
#    except SQLAlchemyError as e:
#       pprint(f'DB error in POST /organizations - validate_post_organization: {e}')
#       raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
#    except Exception as e:
#       db.rollback()
#       print(f'Unexpected error in POST /organizations - validate_post_organization : {e}')
#       raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
   
async def validate_patch_organization(
   user_email: str = Depends(validate_token),
   # org_id: UUID = Path(..., description="The ID of the organization to update"),
   db: Session = Depends(get_db)
) -> dict[str, Any]:
   try:
      # Fetch user by email
      logged_in_user = db.query(models.User).filter(models.User.email == user_email).first()
      if not logged_in_user:
         print(f"in PATCH /organization - validate_patch_organization dependency : logged-in user with email -'{user_email}'- not found in user table")
         raise ApiError.unauthorized("user is unauthenticated")
      org_id = os.getenv("ORGANIZATION_ID", None)
      print(f'org_id = {org_id}')
      org_to_patch = db.query(models.Organization).filter(models.Organization.id == org_id).first()
      if not org_to_patch:
         print(f"in PATCH /organization validate_patch_organization dependency : Organization - '{org_id}' - not found")
         raise ApiError.notfound(f"organization - '{org_id}' - not found")
      
      if logged_in_user.is_superadmin:  # Validate if the user is a superadmin
         return {"org_to_patch" : org_to_patch, "db" : db}
      print(f"in PATCH /organization - validate_patch_organization dependency : logged in user - '{logged_in_user.id}' - does not have superadmin privileges to patch organization - {org_id}")
      raise ApiError.forbidden(f"you do not have superadmin privileges to patch organization - '{org_id}'")
   except HTTPException as e:
      db.rollback()
      pprint(f'API error in PATCH /organization - validate_patch_organization dependency : {e}')
      raise e
   except SQLAlchemyError as e:
      pprint(f'DB error in in PATCH /organization - validate_patch_organization dependency : {e}')
      raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
   except Exception as e:
      db.rollback()
      print(f'Unexpected error in PATCH /organization - validate_patch_organization dependency : {e}')
      raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")

async def validate_get_organization(
   user_email: str = Depends(validate_token),
   db: Session = Depends(get_db)
) -> dict[str, Any]:
   try:
      # Fetch user by email
      logged_in_user = db.query(models.User).filter(models.User.email == user_email).first()
      if not logged_in_user:
         print(f"in GET /organization - validate_get_organization dependency : logged in user with email -'{user_email}'- not found in user table")
         raise ApiError.unauthorized("user is unauthenticated")
      org_id = os.getenv("ORGANIZATION_ID", None)
      print(f'org_id = {org_id}')
      db_org_exists = db.query(exists().where(models.Organization.id == org_id)).scalar()
      if not db_org_exists:
         print(f"in GET /organization - validate_get_organization dependency : Organization - '{org_id}' - not found")
         raise ApiError.notfound(f"organization - '{org_id}' - not found")

      return {"db": db, "org_id" : org_id}
   except HTTPException as e:
      db.rollback()
      pprint(f'API error in GET /organization - validate_get_organization dependency : {e}')
      raise e
   except SQLAlchemyError as e:
      pprint(f'DB error in GET /organization - validate_get_organization dependency : {e}')
      raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
   except Exception as e:
      db.rollback()
      print(f'Unexpected error in GET /organization - validate_get_organization dependency : {e}')
      raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
   
async def validate_get_org_users(
   user_email: str = Depends(validate_token),
   db: Session = Depends(get_db)
) -> dict[str, Any]:
   try:
      org_id = UUID(os.getenv("ORGANIZATION_ID", None))
      # Fetch user by email
      logged_in_user = db.query(models.User).filter(models.User.email == user_email).first()
      if not logged_in_user:
         print(f"INSIDE GET /users?org_id={org_id} - validate_get_org_user dependency: logged_in_user with email - '{user_email}' - not found")
         raise ApiError.unauthorized("user is unauthenticated")
      
      if not db.query(exists().where(models.Organization.id == org_id)).scalar():
         print(f"In GET /users?org_id={org_id} - validate_get_org_user dependency: Organization - '{org_id}' - not found in Organization Table")
         raise ApiError.notfound(f"organization - '{org_id}' - not found")
      
      # Check if the user is a superadmin
      if logged_in_user.is_superadmin: 
         return {"db": db, "org_id" : org_id}

      # Check for any entries in User_Account for the user where is_admin is true, and the account belongs to the org
      user_admin_accounts_exist = db.query(models.User_Account).join(
         models.Account, models.User_Account.account_id == models.Account.id
      ).filter(
         models.User_Account.user_id == logged_in_user.id,
         models.User_Account.is_admin == True,
         models.Account.organization_id == org_id
      ).first()

      if user_admin_accounts_exist:
         return {"db": db, "org_id" : org_id}
      
      print(f"INSIDE GET /organization/users - validate_get_org_users dependency: logged-in user does not have superadmin/admin privileges to read organization users")
      raise ApiError.forbidden(f"you do not have superadmin/admin privileges to read all users in organization - '{org_id}'")
   except HTTPException as e:
      db.rollback()
      pprint(f'API error in GET /organization/users - validate_get_org_users dependency : {e}')
      raise e
   except SQLAlchemyError as e:
      pprint(f'DB error in GET /users?org_id={org_id} - validate_get_org_user dependency: {e}')
      raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
   except Exception as e:
      db.rollback()
      print(f'Unexpected error in GET /users?org_id={org_id} - validate_get_org_user dependency: {e}')
      raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")

# async def validate_org_user_membership(
#    user_email: str = Depends(validate_token),
#    db: Session = Depends(get_db)
# ) -> dict[str, Any]:
#    try:
#       org_id = os.getenv("ORGANIZATION_ID", None)
#       if not db.query(exists().where(Organization.id == org_id)).scalar():
#          print(f"In GET /organization/users/me - validate_org_user_membership: Organization - '{org_id}' - not found in Organization Table")
#          raise ApiError.notfound(f"organization - '{org_id}' - not found")
      
#       # Check if the user exists with the given email and belongs to the specified organization
#       user_exists = db.query(
#          exists().where(
#                and_(
#                   User.email == user_email,
#                   User.organization_id == org_id
#                )
#          )
#       ).scalar()

#       if not user_exists:
#          print(f"Inside GET /organization/users/me - validate_org_user_membership: User with email - '{user_email}' - not found in organization - '{org_id}'")
#          raise ApiError.notfound(f"user with email - '{user_email}' - not found in organization - '{org_id}'")
      
#       return {"db": db, "user_email" : user_email, "org_id" : org_id}
    
#    except HTTPException as e:
#       db.rollback()
#       pprint(f'API error in GET /organization/users/me validate_org_user_membership: {e}')
#       raise e
#    except SQLAlchemyError as e:
#       db.rollback()
#       pprint(f'DB error in GET /organization/users/me validate_org_user_membership: {e}')
#       raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
#    except Exception as e:
#       db.rollback()
#       print(f'Unexpected error in GET /organization/users/me validate_org_user_membership: {e}')
#       raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
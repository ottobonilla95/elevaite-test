from fastapi import Depends, HTTPException, Request
from uuid import UUID
import os

from ..auth.authenticate.impl import AccessTokenAuthentication
from sqlalchemy import exists
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from rbac_api.app.errors.api_error import ApiError
from typing import Any
from pprint import pprint

from rbac_api.utils.deps import get_db  
from elevaitedb.db import models

async def validate_patch_organization(
   request: Request,
   logged_in_user: models.User = Depends(AccessTokenAuthentication.authenticate), 
) -> dict[str, Any]:
   db: Session = request.state.db
   try:
      org_id = os.getenv("ORGANIZATION_ID")
      
      if not logged_in_user.is_superadmin:
         raise ApiError.forbidden(f"you do not have superadmin privileges to patch organization - '{org_id}'")
      
      org_to_patch = db.query(models.Organization).filter(models.Organization.id == org_id).first()
      if not org_to_patch:
         raise ApiError.notfound(f"Organization - '{org_id}' - not found")
      
      return {"Organization" : org_to_patch}
   except HTTPException as e:
      db.rollback()
      pprint(f'API error in PATCH /organization - validate_patch_organization middleware : {e}')
      raise e
   except SQLAlchemyError as e:
      pprint(f'DB error in in PATCH /organization - validate_patch_organization middleware : {e}')
      raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
   except Exception as e:
      db.rollback()
      print(f'Unexpected error in PATCH /organization - validate_patch_organization middleware : {e}')
      raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")

async def validate_get_organization(
   request: Request,
   logged_in_user: models.User = Depends(AccessTokenAuthentication.authenticate), 
) -> dict[str, Any]:
   db: Session = request.state.db
   try:
      org_id = os.getenv("ORGANIZATION_ID", None)
      
      db_org = db.query(models.Organization).filter(models.Organization.id == org_id).first()
      if not db_org:
         raise ApiError.notfound(f"Organization - '{org_id}' - not found")

      return {"Organization" : db_org}
   except HTTPException as e:
      db.rollback()
      pprint(f'API error in GET /organization - validate_get_organization middleware : {e}')
      raise e
   except SQLAlchemyError as e:
      pprint(f'DB error in GET /organization - validate_get_organization middleware : {e}')
      raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
   except Exception as e:
      db.rollback()
      print(f'Unexpected error in GET /organization - validate_get_organization middleware : {e}')
      raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
   
async def validate_get_org_users(
   request: Request,
   logged_in_user: models.User = Depends(AccessTokenAuthentication.authenticate), 
) -> dict[str, Any]:
   db: Session = request.state.db
   try:
      org_id = UUID(os.getenv("ORGANIZATION_ID", None))
          
      if not db.query(exists().where(models.Organization.id == org_id)).scalar():
         raise ApiError.notfound(f"Organization - '{org_id}' - not found")
      
      # Check if the user is a superadmin
      if logged_in_user.is_superadmin: 
         return {"org_id" : org_id}

      # Check for any entries in User_Account for the user where is_admin is true, and the account belongs to the org
      logged_in_user_admin_accounts_exist = db.query(models.User_Account).join(
         models.Account, models.User_Account.account_id == models.Account.id
      ).filter(
         models.User_Account.user_id == logged_in_user.id,
         models.User_Account.is_admin == True,
         models.Account.organization_id == org_id
      ).first()

      if logged_in_user_admin_accounts_exist:
         return {"org_id" : org_id}
      
      raise ApiError.forbidden(f"you do not have superadmin/account-admin privileges to read all users in organization - '{org_id}'")
   except HTTPException as e:
      db.rollback()
      pprint(f'API error in GET /organization/users - validate_get_org_users middleware : {e}')
      raise e
   except SQLAlchemyError as e:
      pprint(f'DB error in GET /organization/users - validate_get_org_users middleware: {e}')
      raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
   except Exception as e:
      db.rollback()
      print(f'Unexpected error in GET /organization/users - validate_get_org_users middleware: {e}')
      raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")


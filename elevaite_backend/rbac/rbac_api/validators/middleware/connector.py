from fastapi import Path, Depends, Header, HTTPException
from uuid import UUID
from .header import validate_token
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from rbac_api.utils.deps import get_db  
from rbac_api.app.errors.api_error import ApiError
from pprint import pprint
from typing import Any

from elevaitedb.db import models
from elevaitedb.schemas import (
   role_schemas
)
from elevaitedb.schemas import (
   application as connector_schemas
)

async def validate_get_connector(
   user_email: str = Depends(validate_token),
   account_id: UUID = Header(None, alias="X-elevAIte-accountId"),
   application_id: int = Path(..., description="id of application to retrieve"),
   db: Session = Depends(get_db)
) -> dict[str, Any]:
   try:
      if account_id is None:
         print(f"in GET /application/{application_id} - validate_get_connector dependency : Request header must contain account id for this endpoint")
         raise ApiError.validationerror("Request header must contain 'X-elevAIte-accountId' for this endpoint")
      
      # Fetch user by email
      logged_in_user = db.query(models.User).filter(models.User.email == user_email).first()
      if not logged_in_user:
         print(f"in GET /application/{application_id} - validate_get_connector dependency : logged in user with email - '{user_email}' - not found in user table")
         raise ApiError.unauthorized("user is unauthenticated") # decide whether to expose user not found

      account = db.query(models.Account).filter(models.Account.id == account_id).first()
      if not account:
         print(f"in GET /application/{application_id} - validate_get_connector dependency : account - '{account_id}' - not found")
         raise ApiError.notfound(f"account - '{account_id}' - not found")
      
      if account.is_disabled:
         print(f"in GET /application/{application_id} - validate_get_connector dependency : account - '{account_id}' - is disabled")
         raise ApiError.forbidden(f"account - '{account_id}' - is disabled")
      
      application: models.Application = db.query(models.Application).filter(models.Application.id == application_id).first()
      if not application:
         print(f"in GET /application/{application_id} - validate_get_connector dependency : connector - '{application_id}' - not found")
         raise ApiError.notfound(f"connector - '{application_id}' - not found")
      
      validation_info = {"logged_in_user_id" : logged_in_user.id,
                           "account_id" : account_id,
                           "db" : db}
      
      # Check if user is a superadmin and validate early
      if logged_in_user.is_superadmin:
         return validation_info

      logged_in_user_account_association = db.query(models.User_Account).filter(
         models.User_Account.user_id == logged_in_user.id, models.User_Account.account_id == account.id
      ).first()

      if not logged_in_user_account_association:
         print(f"in GET /application/{application_id} - validate_get_connector dependency : logged-in user - '{logged_in_user.id}' - is not assigned to account - '{account_id}'")
         raise ApiError.forbidden(f"you are not assigned to account - '{account_id}'")

      if logged_in_user_account_association.is_admin: # check if user is admin and validate early
         return validation_info
      
      applicationType = application.applicationType
      # print(f'applicationType = {applicationType}')
      if applicationType not in connector_schemas.ApplicationType.__members__.values():
         print(f"In GET /application/{application_id} - validate_get_connector: Unsupported connector type - '{application.applicationType}'")
         raise ApiError.validationerror(f"Unsupported connector type - '{application.applicationType}'")
      
      # print(f'applicationType.lower().capitalize() = {applicationType.lower().capitalize()}')
      applicationType = applicationType.lower().capitalize()
      if applicationType not in role_schemas.AccountScopedPermissions.__fields__.keys():
         print(f"In GET /application/{application_id} - validate_get_connector: RBAC Validation for connector type - '{application.applicationType}' - not implemented.")
         raise ApiError.validationerror(f"RBAC Validation for connector type - '{application.applicationType}' - not implemented.")
      
      role_based_access_exists = db.query(
         db.query(models.Role)
            .join(models.Role_User_Account,
                  (models.Role_User_Account.role_id == models.Role.id) &
            (models.Role_User_Account.user_account_id == logged_in_user_account_association.id))
            .filter(
               models.Role.permissions[applicationType]['READ']['action'].astext == 'Allow'
            )
            .exists()
      ).scalar()

      if not role_based_access_exists:
         print(f"INSIDE GET /application/{application_id} - validate_get_connector: logged-in user - '{logged_in_user.id}' - is not a superadmin/admin and does not have account-specific role-based access permissions to read connector resources in account - '{account.id}'")
         raise ApiError.forbidden(f"you do not have superadmin/admin privileges and you do not have account-specific role-based access permissions to read connector resources in account - '{account.id}'")
      
      return validation_info
   except HTTPException as e:
      db.rollback()
      pprint(f'API error in GET /application/{application_id} - validate_get_connector dependency : {e}')
      raise e
   except SQLAlchemyError as e:
      pprint(f'DB error in GET /application/{application_id} - validate_get_connector dependency : {e}')
      raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
   except Exception as e:
      db.rollback()
      print(f'Unexpected error in GET /application/{application_id} - validate_get_connector dependency : {e}')
      raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
   

async def validate_get_connectors(
   user_email: str = Depends(validate_token),
   account_id: UUID = Header(None, alias="X-elevAIte-accountId"),
   application_id: int = Path(..., description="id of application to retrieve"),
   db: Session = Depends(get_db)
) -> dict[str, Any]:
   try:
      if account_id is None:
         print(f"in GET /application/{application_id} - validate_get_connector dependency : Request header must contain account id for this endpoint")
         raise ApiError.validationerror("Request header must contain 'X-elevAIte-accountId' for this endpoint")
      
      # Fetch user by email
      logged_in_user = db.query(models.User).filter(models.User.email == user_email).first()
      if not logged_in_user:
         print(f"in GET /application/{application_id} - validate_get_connector dependency : logged in user with email - '{user_email}' - not found in user table")
         raise ApiError.unauthorized("user is unauthenticated") # decide whether to expose user not found

      account = db.query(models.Account).filter(models.Account.id == account_id).first()
      if not account:
         print(f"in GET /application/{application_id} - validate_get_connector dependency : account - '{account_id}' - not found")
         raise ApiError.notfound(f"account - '{account_id}' - not found")
      
      if account.is_disabled:
         print(f"in GET /application/{application_id} - validate_get_connector dependency : account - '{account_id}' - is disabled")
         raise ApiError.forbidden(f"account - '{account_id}' - is disabled")
      
      application: models.Application = db.query(models.Application).filter(models.Application.id == id).first()
      if not application:
         print(f"in GET /application/{application_id} - validate_get_connector dependency : application - '{application_id}' - not found")
         raise ApiError.notfound(f"application - '{application_id}' - not found")
      
      validation_info = {"logged_in_user_id" : logged_in_user.id,
                           "account_id" : account_id,
                           "db" : db}
      
      # Check if user is a superadmin and validate early
      if logged_in_user.is_superadmin:
         return validation_info

      logged_in_user_account_association = db.query(models.User_Account).filter(
         models.User_Account.user_id == logged_in_user.id, models.User_Account.account_id == account.id
      ).first()

      if not logged_in_user_account_association:
         print(f"in GET /application/{application_id} - validate_get_connector dependency : logged-in user - '{logged_in_user.id}' - is not assigned to account - '{account_id}'")
         raise ApiError.forbidden(f"you are not assigned to account - '{account_id}'")

      if logged_in_user_account_association.is_admin: # check if user is admin and validate early
         return validation_info
      
      applicationType = application.applicationType
      # print(f'applicationType = {applicationType}')
      if applicationType not in connector_schemas.ApplicationType.__members__.values():
         print(f"In GET /application/{application_id} - validate_get_connector: Unsupported application type - '{application.applicationType}'")
         raise ApiError.validationerror(f"Unsupported application type - '{application.applicationType}'")
      
      print(f'applicationType.lower().capitalize() = {applicationType.lower().capitalize()}')
      applicationType = applicationType.lower().capitalize()
      if applicationType not in role_schemas.AccountScopedPermissions.__fields__.keys():
         print(f"In GET /application/{application_id} - validate_get_connector: RBAC Validation for application type - '{application.applicationType}' - not implemented.")
         raise ApiError.validationerror(f"RBAC Validation for application type - '{application.applicationType}' - not implemented.")
      
      # Checking account-scoped role-based access here for applicationType.READ:
      role_based_access_exists = db.query(
         db.query(models.Role)
            .join(models.Role_User_Account,
                  (models.Role_User_Account.role_id == models.Role.id) &
            (models.Role_User_Account.user_account_id == logged_in_user_account_association.id))
            .filter(
               models.Role.permissions[applicationType]['READ'].astext == 'Allow'
            )
            .exists()
      ).scalar()

      if not role_based_access_exists:
         print(f"INSIDE GET /application/{application_id} - validate_get_connector: logged-in user - '{logged_in_user.id}' - is not a superadmin/admin and does not have account-specific role-based access permissions to read connector resources in account - '{account.id}'")
         raise ApiError.forbidden(f"you do not have superadmin/admin privileges and you do not have account-specific role-based access permissions to read connector resources in account - '{account.id}'")
      
      return validation_info
   except HTTPException as e:
      db.rollback()
      pprint(f'API error in GET /application/{application_id} - validate_get_connector dependency : {e}')
      raise e
   except SQLAlchemyError as e:
      pprint(f'DB error in GET /application/{application_id} - validate_get_connector dependency : {e}')
      raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
   except Exception as e:
      db.rollback()
      print(f'Unexpected error in GET /application/{application_id} - validate_get_connector dependency : {e}')
      raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
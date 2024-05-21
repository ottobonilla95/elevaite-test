from fastapi import status, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy import exists
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from fastapi.encoders import jsonable_encoder
from pprint import pprint
from typing import Optional
from uuid import UUID
from datetime import datetime
from pydantic import EmailStr

from elevaitedb.schemas import (
   auth as auth_schemas,
   permission as permission_schemas
)

from elevaitedb.db import models
from ..errors.api_error import ApiError
from rbac_api import RBACProvider
import os

def register_user(
      db: Session, 
      register_user_payload: auth_schemas.RegisterUserRequestDTO,
      user_email: EmailStr
) -> JSONResponse:
   try:
      org_id = os.getenv("ORGANIZATION_ID")
      USER_ALREADY_EXISTS = True
      # Verify if the specified user exists already
      db_user = db.query(models.User).filter(models.User.email == user_email, models.User.organization_id == org_id).first()
      if not db_user:
         USER_ALREADY_EXISTS = False
         # Create the new user instance
         db_user = models.User(
            firstname=register_user_payload.firstname,
            lastname=register_user_payload.lastname,
            email=user_email,
            organization_id=org_id,
         )
         db.add(db_user)
         db.flush()  # Now, db_user.id is available

      default_account_id = os.getenv("DEFAULT_ACCOUNT_ID")
      default_account = db.query(models.Account).filter(models.Account.id == default_account_id).first()
      if not default_account:
         default_account = models.Account(
            id=default_account_id,
            organization_id=org_id,
            name="elevAIte Default Account",
            description="Iopex Default Account desc",
            created_at=datetime.now(),
            updated_at=datetime.now()
         )
         db.add(default_account)
         db.flush()
      
      db_user_default_account_association = db.query(models.User_Account).filter(
         models.User_Account.account_id == default_account.id,
         models.User_Account.user_id == db_user.id
      ).first()

      if not db_user_default_account_association:
         # Create the User_Account association with default account
         new_user_default_account_association = models.User_Account(
            user_id=db_user.id,
            account_id=default_account.id,
            is_admin=True # for demo purposes so that users can access resources within account and contained projects until UI for roles is developed
         )
         db.add(new_user_default_account_association)
      elif db_user_default_account_association.is_admin == False:
         db_user_default_account_association.is_admin = True

      default_project_id = os.getenv("DEFAULT_PROJECT_ID")
      default_project = db.query(models.Project).filter(models.Project.id == default_project_id).first()
      if not default_project:
        # Create default project
         default_project = models.Project(
            id=default_project_id,
            account_id=default_account.id,
            creator=user_email,
            name="elevAIte Default Project",
            description="elevAIte Default Project desc",
            created_at=datetime.now(),
            updated_at=datetime.now()
         )
         db.add(default_project)
         db.flush()
      
      db_user_default_project_association = db.query(models.User_Project).filter(
         models.User_Project.project_id == default_project.id,
         models.User_Project.user_id == db_user.id,
      ).first()
      
      if not db_user_default_project_association:
         # Create the User_Project association with default  with all allowed project scoped permissions (no overrides)
         new_user_default_project_association = models.User_Project(
            user_id=db_user.id,
            project_id=default_project.id,
            permission_overrides = permission_schemas.ProjectScopedRBACPermission.create("Allow").dict()
         )
         db.add(new_user_default_project_association)

      db.commit()
      db.refresh(db_user)

      if USER_ALREADY_EXISTS:
         return JSONResponse(content=jsonable_encoder(db_user), status_code=status.HTTP_200_OK)
      
      return JSONResponse(content=jsonable_encoder(db_user), status_code=status.HTTP_201_CREATED)
   except HTTPException as e:
      db.rollback()
      pprint(f'API error in POST /auth/register register_user service method : {e}')
      raise e
   except SQLAlchemyError as e:
      db.rollback()
      pprint(f'Error in POST /auth/register register_user service method : {e}')
      raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
   except Exception as e:
      db.rollback()
      pprint(f'Unexpected error in POST /auth/register register_user service method : {e}')
      raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
   
async def evaluate_rbac_permissions(
   account_id: Optional[UUID],
   project_id: Optional[UUID],
   logged_in_user: models.User,
   permissions_evaluation_request: auth_schemas.PermissionsEvaluationRequest,
   db: Session, 
) -> auth_schemas.PermissionsEvaluationResponse:
   try:
      return await RBACProvider.get_instance().evaluate_rbac_permissions(
         logged_in_user=logged_in_user,
         account_id=account_id,
         project_id=project_id,
         permissions_evaluation_request=permissions_evaluation_request,
         db=db
      )
   except HTTPException as e:
      db.rollback()
      pprint(f'API error in POST /auth/rbac-permissions evaluate_rbac_permissions service method : {e}')
      raise e
   except SQLAlchemyError as e:
      db.rollback()
      pprint(f'Error in POST /auth/rbac-permissions evaluate_rbac_permissions service method : {e}')
      raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
   except Exception as e:
      db.rollback()
      pprint(f'Unexpected error in POST /auth/rbac-permissions evaluate_rbac_permissions service method : {e}')
      raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
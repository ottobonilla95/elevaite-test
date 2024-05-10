from fastapi import Depends, Body, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from uuid import UUID
from pprint import pprint
from typing import Any, Optional
from rbac_api.app.errors.api_error import ApiError
from .token import validate_token
from rbac_api.utils.deps import get_db
from elevaitedb.db import models
from elevaitedb.schemas import (
   auth as auth_schemas
)

async def validate_evaluate_rbac_permissions(
   user_email: str = Depends(validate_token),
   # params required for pydantic validation
   account_id: Optional[UUID] = Header(None, alias='X-elevAIte-AccountId', description="account id under which rbac permissions are evaluated"),
   project_id: Optional[UUID] = Header(None, alias='X-elevAIte-ProjectId', description="project id under which rbac permissions are evaluated"),
   permissions_validation_request: auth_schemas.PermissionsValidationRequest = Body(...),
   db: Session = Depends(get_db)
) -> dict[str, Any]:
   try:
      logged_in_user = db.query(models.User).filter(models.User.email == user_email).first()
      if not logged_in_user:
         raise ApiError.unauthorized("User is unauthenticated")
      return {"db": db, "logged_in_user": logged_in_user}
   except HTTPException as e:
      db.rollback()
      pprint(f'API error in POST /auth/permissions - validate_evaluate_rbac_permissions middleware: {e}')
      raise e
   except SQLAlchemyError as e:
      db.rollback()
      print(f'DB error in POST /auth/permissions - validate_evaluate_rbac_permissions middleware: {e}')
      raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
   except Exception as e:
      db.rollback()
      print(f'Unexpected error in POST /auth/permissions - validate_evaluate_rbac_permissions middleware: {e}')
      raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")

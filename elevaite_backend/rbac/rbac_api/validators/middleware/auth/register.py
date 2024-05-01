from fastapi import Depends, Body, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from pprint import pprint
from typing import Any
from rbac_api.app.errors.api_error import ApiError
from .token import validate_token
from rbac_api.utils.deps import get_db
from elevaitedb.db import models
from elevaitedb.schemas import (
   auth as auth_schemas
)

async def validate_register_user(
   register_user_payload: auth_schemas.RegisterUserRequestDTO = Body(description= "user registration payload"),  
   user_email: str = Depends(validate_token), 
   db: Session = Depends(get_db)
) -> dict[str, Any]:
   """
   For now, every user is allowed to register themselves. Include whitelist validation here later.
   Returns the user_email and db session for use in service method
   """
   try:
      if register_user_payload.email != user_email:
         print(f"in POST /auth/register - validate_register_user middleware: logged-in user does not have permissions to register user with email - '{register_user_payload.email}'")
         raise ApiError.forbidden(f"you do not have permissions to register user with email - '{register_user_payload.email}'")
      organization = db.query(models.Organization).filter(models.Organization.id == register_user_payload.org_id).first()
      if not organization:
         print(f"in POST /auth/register - validate_register_user middleware: Organization - '{register_user_payload.org_id}' - not found")
         raise ApiError.notfound(f"Organization - '{register_user_payload.org_id}' - not found")
      return {"db" : db}
   except HTTPException as e:
      db.rollback()
      pprint(f'API error in POST /auth/register - validate_register_user middleware: {e}')
      raise e
   except SQLAlchemyError as e:
      pprint(f'DB error in POST /auth/register - validate_register_user middleware: {e}')
      raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
   except Exception as e:
      db.rollback()
      print(f'Unexpected error in POST /auth/register - validate_register_user middleware: {e}')
      raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")


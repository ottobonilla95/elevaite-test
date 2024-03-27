
from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import  SQLAlchemyError, IntegrityError
from typing import List, Optional, cast
from uuid import UUID
from datetime import datetime
from elevaitedb.schemas.organization_schemas import (
   OrganizationCreationRequestDTO,
    OrganizationResponseDTO,
    OrganizationPatchRequestDTO
)
from elevaitedb.db.models import (
    Organization,
    User
)
from elevaitedb.schemas.user_schemas import (
   OrgUserListItemDTO
)
from app.errors.api_error import ApiError
from pprint import pprint

# def create_organization(
#    organization_creation_payload: OrganizationCreationRequestDTO,
#    db: Session
# ) -> OrganizationResponseDTO :
#    try:
#       existing_organization = db.query(Organization).filter(Organization.name == organization_creation_payload.name).first()
#       if existing_organization: # Application-side uniqueness check : Check if org with same name exists already
#          pprint(f'in POST /organization - An organization with the same name already exists in organizations table')
#          raise ApiError.conflict(f"organization with name - '{organization_creation_payload.name}' - already exists")
#       new_organization = Organization(
#          name=organization_creation_payload.name,
#          description=organization_creation_payload.description
#       )
#       db.add(new_organization)
#       db.commit()
#       db.refresh(new_organization)
#       return new_organization
#    except HTTPException as e:
#       db.rollback()
#       pprint(f'API error in POST /organization service method : {e}')
#       raise e
#    except IntegrityError as e: # Database-side uniqueness check : Check if organization with same name already exists
#       db.rollback()  
#       pprint(f'DB error in POST /organizations service method : {e}')
#       raise ApiError.conflict(f"organization with name - '{organization_creation_payload.name}' - already exists")
#    except SQLAlchemyError as e: # group db side error as 503 to not expose actual error to client
#       db.rollback()
#       pprint(f'DB error in POST /organizations service method : {e}')
#       raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
#    except Exception as e:
#       db.rollback()
#       pprint(f'Unexpected error inPOST /organizations service method : {e}')
#       raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
   
def patch_organization(
   organization_patch_req_payload: OrganizationPatchRequestDTO,
   db: Session,
   org_to_patch: Organization
   ) -> OrganizationResponseDTO:
   """
   Patches an organization based on given org_id path param, and org patch payload

   Args:
      org_id (UUID) : The id of the organization to be patched.
      organization_patch_req_payload (OrganizationPatchRequestDTO): The organization patch payload containing optional details of 'name', and 'description' for patch.
      db (Session): The db session object for db operations.

   Raises: 
      404: Organization not found.
      503: Any db related error.
   Returns: 
      OrganizationResponseDTO : The response containing patched OrganizationResponseDTO object. 
   
   Notes:
      - logged-in user is assumed to be a superadmin. 
      - the req body has either non-empty 'name' field, or non-empty 'description' field, or both fields are non-empty.
   """
   try:
      for var, value in vars(organization_patch_req_payload).items():
         setattr(org_to_patch, var, value) if value is not None else None
      org_to_patch.updated_at = datetime.now()
      db.commit()
      db.refresh(org_to_patch)
      return org_to_patch
   except HTTPException as e:
      db.rollback()
      pprint(f'API error in PATCH /organization service method: {e}')
      raise e
   except SQLAlchemyError as e: # group db side error as 503 to not expose actual error to client
      db.rollback()
      pprint(f'DB error in PATCH /organization service method : {e}')
      raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
   except Exception as e:
      db.rollback()
      pprint(f'Unexpected error in PATCH /organization service method: {e}')
      raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
   
def get_organization(
   org_id: UUID,
   db: Session
   ) -> OrganizationResponseDTO:
   """
   Retrieves an organization based on given org_id path param

   Args:
      org_id (UUID) : The id of the organization to be retrieved.
      db (Session): The db session object for db operations.

   Raises: 
      404: Organization not found.
      503: Any db related error.
   Returns: 
      OrganizationResponseDTO : The response containing retrieved OrganizationResponseDTO object. 
   
   Notes:
      - logged-in user is assumed to exist in user table. 
   """
   try:
      db_org = db.query(Organization).filter(Organization.id == org_id).first() # existence checked in dependency
      return db_org
   except HTTPException as e:
      db.rollback()
      pprint(f'API error in GET /organization service method : {e}')
      raise e
   except SQLAlchemyError as e: # group db side error as 503 to not expose actual error to client
      pprint(f'DB error in GET /organization service method : {e}')
      raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
   except Exception as e:
      pprint(f'Unexpected error in GET /organization service method : {e}')
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

# def get_user_by_email_and_org_id(db: Session, email: str, org_id: UUID) -> OrgUserListItemDTO:
#    """
#    Queries the database for a user by their email and organization ID.

#    Parameters:
#    - db: The SQLAlchemy database session.
#    - email: The user's email address.
#    - org_id: The ID of the organization.

#    Returns:
#    - A OrgUserListItemDTO object
#    """
#    try:
#       user = db.query(User).filter(
#          User.email == email,
#          User.organization_id == org_id
#       ).first()
#       if not user:
#          print(f"in GET /organization/users/me - service method : user with email - '{email}' - not found in organization - '{org_id}'")
#          raise ApiError.notfound(f"user with email - '{email}' - not found in organization - '{org_id}'")
#       return user
#    except SQLAlchemyError as e: # group db side error as 503 to not expose actual error to client
#       db.rollback()
#       pprint(f'DB error in GET /organization/users/me - service method : {e}')
#       raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
#    except Exception as e:
#       db.rollback()
#       pprint(f'Unexpected error in GET /organization/users/me - service method : {e}')
#       raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
   
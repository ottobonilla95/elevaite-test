from fastapi import status, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session, aliased, load_only
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.sql import and_, exists
from sqlalchemy import func, case
from typing import List, Optional, cast
from uuid import UUID
from datetime import datetime
from pprint import pprint
from pydantic import EmailStr
from ..errors.api_error import ApiError
from datetime import UTC
import secrets

from elevaitedb.schemas import (
   project as project_schemas,
   user as user_schemas,
   role as role_schemas,
   permission as permission_schemas,
)
from elevaitedb.db import models

from rbac_api.utils.cte import (
   delete_user_project_associations_for_subprojects_of_user,
   delete_user_project_associations_for_subprojects_of_user_list
)


def create_project(
   project_creation_payload: project_schemas.ProjectCreationRequestDTO,
   account_id: UUID,
   parent_project_id: Optional[UUID],
   db: Session,
   logged_in_user_id: UUID,
) -> project_schemas.ProjectResponseDTO: 
   try:

      project_exists = db.query(exists().where(
        and_(
            models.Project.account_id == account_id,
            models.Project.name == project_creation_payload.name
        )
      )).scalar()
      
      if project_exists: # Application-side uniqueness check : Check if a project with the same name already exists in the specified account
         pprint(f'in POST /projects service method: A project with the same name -"{project_creation_payload.name}"- already exists in the specified account -"{account_id}"')
         raise ApiError.conflict(f"A project with the same name - '{project_creation_payload.name}' - already exists in account - '{account_id}'")
      # Create new project resource from req body
      new_project = models.Project(
         account_id=account_id,
         creator_id=logged_in_user_id,
         parent_project_id=parent_project_id,
         name=project_creation_payload.name,
         description=project_creation_payload.description,
         created_at=datetime.now(),
         updated_at=datetime.now()
      )
      
      db.add(new_project)
      db.flush()  # Now, new_project.id is available

      # Create the User_Project association with the new project's ID, with no project overrides () all Allow'ed permissions)
      new_user_project = models.User_Project(
         user_id=logged_in_user_id,
         project_id=new_project.id,
         is_admin=True,
         permission_overrides=permission_schemas.ProjectScopedRBACPermission.create("Allow").dict()
      )
      
      db.add(new_user_project) # Add the User_Project association to the session
      db.commit() # Commit the transaction to persist both the new project and the association
      
      return new_project
   except HTTPException as e:
      db.rollback()
      pprint(f'API error in POST /projects/ service method: {e}')
      raise e
   except IntegrityError as e : # Database-side uniqueness check : Check if a project with the same name already exists in the specified account
        db.rollback()
        pprint(f'Error in POST /projects service method: {e}')
        raise ApiError.conflict(f"A project with the same name -{project_creation_payload.name}- already exists in the specified account -{account_id}")
   except SQLAlchemyError as e: # group db side error as 503 to not expose actual error to client
        db.rollback()
        pprint(f'Error in POST /projects service method: {e}')
        raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
   except Exception as e:
      db.rollback()
      print(f'Unexpected error in POST /projects/ service method: {e}')
      raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
   
def patch_project(
   project_to_patch: models.Project,
   project_patch_payload: project_schemas.ProjectPatchRequestDTO,
   db: Session,
   ): 
   try:
      for var, value in vars(project_patch_payload).items():
         setattr(project_to_patch, var, value) if value is not None else None
      project_to_patch.updated_at = datetime.now()
      db.commit()
      db.refresh(project_to_patch)
      return project_to_patch
   except SQLAlchemyError as e: # group db side error as 503 to not expose actual error to client
      db.rollback()
      pprint(f'DB error in PATCH /projects/{project_to_patch.id} service method: {e}')
      raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
   except Exception as e:
      db.rollback()
      print(f'Unexpected error in PATCH /projects/{project_to_patch.id} service method: {e}')
      raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")

def get_projects( 
   logged_in_user_id: UUID,
   logged_in_user_is_superadmin: bool,
   logged_in_user_is_admin: bool,
   account_id: UUID,
   parent_project_id: Optional[UUID],
   name: Optional[str],
   db: Session,
   type: Optional[project_schemas.ProjectType] = project_schemas.ProjectType.All,
   view: Optional[project_schemas.ProjectView] = project_schemas.ProjectView.Flat
) -> List[project_schemas.ProjectResponseDTO]:
   try:
      if (not logged_in_user_is_superadmin and not logged_in_user_is_admin) or type == project_schemas.ProjectType.Shared_With_Me: # When type is 'Shared_With_Me' or when user is non account-admin/superadmin:
         query = db.query(models.Project).join(models.User_Project, models.User_Project.project_id == models.Project.id).filter( # base query is to show associated projects in account; can be filtered for view : 'Hierarchical', type: 'Shared_With_Me', type: 'My_Projects' later
            models.Project.account_id == account_id,
            models.User_Project.user_id == logged_in_user_id,
         )            
      else: # When type is not 'Shared_With_Me' and when user is admin/superadmin
         query = db.query(models.Project).filter(models.Project.account_id == account_id) # base query is to see all projects in account regardless of association, can be filtered for view : 'Hierarchical', type: 'Shared_With_Me', type: 'My_Projects' later

      if view == project_schemas.ProjectView.Hierarchical: # consider subset of projects linked to parent_project_id for 'Hierarchical' view 
         query = query.filter(models.Project.parent_project_id == parent_project_id)
      
      if type == project_schemas.ProjectType.My_Projects: 
         query = query.filter(models.Project.creator_id == logged_in_user_id) # show all projects created by user
      elif type == project_schemas.ProjectType.Shared_With_Me:
         query = query.filter(models.Project.creator_id != logged_in_user_id) # show all projects not created by user

      if name:
         query = query.filter(models.Project.name.ilike(f"%{name}%"))

      projects = query.all()
      return cast(List[project_schemas.ProjectResponseDTO], projects)  
   except SQLAlchemyError as e:
      db.rollback()
      pprint(f'DB error in GET /projects/ service method: {e}')
      raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
   except Exception as e:
      db.rollback()
      print(f'Unexpected error in GET /projects/ service method: {e}')
      raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")

def get_project_user_list(
   db: Session,
   project_id: UUID,
   account_id: UUID, 
   firstname: Optional[str],
   lastname: Optional[str],
   email: Optional[str]
) -> List[user_schemas.ProjectUserListItemDTO]:
   try:
      UserAccountAlias = aliased(models.User_Account)
      RoleUserAccountAlias = aliased(models.Role_User_Account)
      UserProjectAlias = aliased(models.User_Project)

      project_users_query = (
      db.query(models.User, UserAccountAlias.is_admin, UserProjectAlias.is_admin, UserAccountAlias.id)
      .join(UserProjectAlias, UserProjectAlias.user_id == models.User.id)
      .join(UserAccountAlias, and_(UserAccountAlias.user_id == models.User.id, UserAccountAlias.account_id == account_id))
      .filter(UserProjectAlias.project_id == project_id)
      )

      if firstname:
         project_users_query = project_users_query.filter(models.User.firstname.ilike(f"%{firstname}%"))
      if lastname:
         project_users_query = project_users_query.filter(models.User.lastname.ilike(f"%{lastname}%"))
      if email:
         project_users_query = project_users_query.filter(models.User.email.ilike(f"%{email}%"))

      project_users = project_users_query.all()
      project_users_with_roles = []

      for user, is_account_admin, is_project_admin, user_account_id in project_users:
         if user.is_superadmin or is_account_admin:
            project_user_with_roles_dto = user_schemas.ProjectUserListItemDTO(
               **user.__dict__,
               is_account_admin=is_account_admin,
               is_project_admin=is_project_admin,
               roles=[]
            )
         else:
            roles_query = (
               db.query(models.Role)
               .join(RoleUserAccountAlias, RoleUserAccountAlias.role_id == models.Role.id)
               .filter(
                  RoleUserAccountAlias.user_account_id == user_account_id
               )
            )
            roles = roles_query.all()
            
            # role_summary_dto = [RoleSummaryDTO.model_validate(role) for role in roles]
            role_summary_dto = [role_schemas.RoleSummaryDTO.from_orm(role) for role in roles]

            # Construct AccountUserListItemDTO for each user
            project_user_with_roles_dto = user_schemas.ProjectUserListItemDTO(
               **user.__dict__,
               is_account_admin=is_account_admin,
               is_project_admin=is_project_admin,
               roles=role_summary_dto
            )
         project_users_with_roles.append(project_user_with_roles_dto)
      return project_users_with_roles
   except HTTPException as e:
      db.rollback()
      pprint(f'API error in GET /projects/{project_id}/users service method: {e}')
      raise e
   except SQLAlchemyError as e:
      db.rollback()
      pprint(f'Error in GET /projects/{project_id}/users service method: {e}')
      raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
   except Exception as e:
      db.rollback()
      pprint(f'Unexpected error in GET /projects/{project_id}/users service method: {e}')
      raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
   
def assign_users_to_project(
   project_assignee_list_dto: project_schemas.ProjectAssigneeListDTO,
   db: Session,
   project : models.Project,
) -> JSONResponse:
   try:
      user_ids = [assignee.user_id for assignee in project_assignee_list_dto.assignees]

      # if action == "Add":
      query_result = db.query(
         func.count(models.User.id).label("total_users_found_in_list"),
         func.count(models.User_Account.user_id).label("total_user_account_associations_in_list"),
         func.count(models.User_Project.user_id).label("total_user_current_project_associations_in_list")
      ).outerjoin(
         models.User_Account, and_(models.User.id == models.User_Account.user_id, models.User_Account.account_id == project.account_id)
      ).outerjoin(
         models.User_Project, and_(models.User.id == models.User_Project.user_id, models.User_Project.project_id == project.id)
      ).filter(
         models.User.id.in_(user_ids)
      ).one()

      # Extracting the results
      (total_users_found_in_list,
      total_user_account_associations_in_list,
      total_user_current_project_associations_in_list) = query_result
      
      print(f'''total_users_found_in_list = {total_users_found_in_list}
            total_user_account_associations_in_list = {total_user_account_associations_in_list}
            total_user_current_project_associations_in_list = {total_user_current_project_associations_in_list}
            ''')
      if total_users_found_in_list != len(user_ids):
         print(f"in PATCH /projects/{project.id}/users service method: One or more users not found in user table")
         raise ApiError.notfound(f"One or more users not found")
      if total_user_account_associations_in_list != len(user_ids):
         print(f"in PATCH /projects/{project.id}/users service method: One or more users are not assigned to project account - {project.account_id}")
         raise ApiError.validationerror(f"One or more users are not assigned to account - '{project.account_id}'")
      
      if project.parent_project_id is not None:
         parent_project_associations_count = db.query(
            func.count(models.User_Project.user_id)
         ).filter(
            models.User_Project.user_id.in_(user_ids),
            models.User_Project.project_id == project.parent_project_id
         ).scalar()
         if parent_project_associations_count != len(user_ids):
            raise ApiError.validationerror(f" One or more users are not assigned to parent project - '{project.parent_project_id}'")
         
      if total_user_current_project_associations_in_list > 0 :
         raise ApiError.conflict(f"One or more users are already assigned to project - '{project.id}'")
      
      new_user_projects = [
         models.User_Project(user_id=assignee.user_id, project_id=project.id, permission_overrides=assignee.permission_overrides.dict())
         for assignee in project_assignee_list_dto.assignees
      ]
      db.bulk_save_objects(new_user_projects)
      db.commit()
      return JSONResponse(content={"message": f"Successfully assigned {len(new_user_projects)} user/(s) to project - '{project.id}'"}, status_code= status.HTTP_200_OK)
   except HTTPException as e:
      db.rollback()
      pprint(f'API error in POST /projects/{project.id}/users service method : {e}')
      raise e
   except SQLAlchemyError as e:
      db.rollback()
      pprint(f'DB Error in POST /projects/{project.id}/users service method : {e}')
      raise ApiError.serviceunavailable("The server is currently unavailable, please try again later")
   except Exception as e:
      db.rollback()
      pprint(f'Unexpected error in POST /projects/{project.id}/users service method : {e}')
      raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")

def deassign_user_from_project(
   user_id: UUID,
   db: Session,
   project : models.Project,
) -> JSONResponse:
   try:
      user_to_deassign = db.query(models.User).filter(models.User.id == user_id).first()
      if not user_to_deassign:
         raise ApiError.notfound(f"User - '{user_id}' - not found")
      
      user_to_deassign_account_association = db.query(models.User_Account).filter(models.User_Account.user_id == user_to_deassign.id, models.User_Account.account_id == project.account_id).first()
      if not user_to_deassign_account_association:
         raise ApiError.validationerror(f"User - '{user_to_deassign.id}' - is not assigned to account - '{project.account_id}'")
      
      user_project_association = db.query(models.User_Project).filter(
          models.User_Project.user_id == user_id, models.User_Project.project_id == project.id
      ).first()

      if not user_project_association:
         raise ApiError.validationerror(f"User - '{user_id}' - is not assigned to project - '{project.id}'")

      delete_user_project_associations_for_subprojects_of_user(db=db, starting_project_id=project.id, user_id=user_id)
      db.commit()
      return JSONResponse(content={"message": f"Successfully deassigned user - '{user_id}' - from project - '{project.id}'"}, status_code=status.HTTP_200_OK)
   except HTTPException as e:
      db.rollback()
      pprint(f'API error in DELETE /projects/{project.id}/users/{user_id} service method : {e}')
      raise e
   except SQLAlchemyError as e:
      db.rollback()
      pprint(f'DB Error in DELETE /projects/{project.id}/users/{user_id} service method : {e}')
      raise ApiError.serviceunavailable("The server is currently unavailable, please try again later")
   except Exception as e:
      db.rollback()
      pprint(f'Unexpected error in DELETE /projects/{project.id}/users/{user_id} service method : {e}')
      raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
   
def patch_user_project_admin_status(
   user_id: UUID,
   account_id: UUID,
   project_id: UUID,
   project_admin_status_update_dto: project_schemas.ProjectAdminStatusUpdateDTO,
   db: Session
   )-> JSONResponse:
   try:
      # Check if user in payload exists
      user_in_payload = db.query(models.User).filter(models.User.id == user_id).first()
      if not user_in_payload:
         raise ApiError.notfound(f"User - '{user_id}' - not found")
      
      # Check if user in payload is associated to account
      user_account_association = db.query(models.User_Account).filter(models.User_Account.user_id == user_id, models.User_Account.account_id == account_id).first()
      if not user_account_association:
         raise ApiError.validationerror(f"User - '{user_id}' - is not assigned to account - '{account_id}'")
      
      # Check if user in payload is associated to project
      user_project_association = db.query(models.User_Project).filter(models.User_Project.user_id == user_id, models.User_Project.project_id == project_id).first()
      if not user_project_association:
         raise ApiError.validationerror(f"User - '{user_id}' - is not assigned to project - '{project_id}'")

      match project_admin_status_update_dto.action:
         case "Grant":
            if not user_project_association.is_admin:
               user_project_association.is_admin = True

         case "Revoke":
            if user_project_association.is_admin:
               user_project_association.is_admin = False
         case _:
            raise ApiError.validationerror(f"unknown action - '{project_admin_status_update_dto.action}'")

      db.commit()
      return JSONResponse(content={"message": f"project-admin status successfully {'revoked' if project_admin_status_update_dto.action.lower() == 'revoke' else 'granted'}"}, status_code=status.HTTP_200_OK)
   except HTTPException as e:
      db.rollback()
      pprint(f'API error in PATCH /projects/{project_id}/users/{user_id}/admin service method: {e}')
      raise e
   except SQLAlchemyError as e:
      db.rollback()
      pprint(f'DB error in PATCH /projects/{project_id}/users/{user_id}/admin service method: Error updating project-admin status: {e}')
      raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
   except Exception as e:
      db.rollback()
      pprint(f'Unexpected error in PATCH /projects/{project_id}/users/{user_id}/admin service method: Error updating project-admin status: {e}')
      raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")  
   
   
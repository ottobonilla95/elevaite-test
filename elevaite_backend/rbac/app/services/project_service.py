from fastapi import status, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session, aliased
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.sql import (
   or_,
   and_,
   exists,
)
from sqlalchemy import func, case
from typing import (
   List,
   Optional,
   Any,
   cast
)
from uuid import UUID
from datetime import datetime
from app.utils.cte import (
   delete_user_project_associations_for_subprojects
)

from elevaitedb.schemas.project_schemas import (
   ProjectCreationRequestDTO,
   ProjectResponseDTO,
   ProjectPatchRequestDTO,
   ProjectType,
   ProjectView
)
from elevaitedb.schemas.user_schemas import (
   UserListDTO, 
   ProjectUserListItemDTO,
)
from elevaitedb.schemas.common_schemas import (
   ResourceStatusUpdateDTO
)
from elevaitedb.schemas.role_schemas import (
   ProjectScopedPermissions,
   RoleSummaryDTO
)
from elevaitedb.db.models import (
   Project,
   User,
   Role,
   User_Project,
   User_Account,
   Project,
   Role_User_Account,
   User_Project
)
from app.errors.api_error import ApiError
from pprint import pprint

def create_project(
   project_creation_payload: ProjectCreationRequestDTO,
   db: Session,
   logged_in_user_id: UUID,
) -> ProjectResponseDTO: 
   try:
      project_exists = db.query(exists().where(
        and_(
            Project.account_id == project_creation_payload.account_id,
            Project.name == project_creation_payload.name
        )
      )).scalar()
      
      if project_exists: # Application-side uniqueness check : Check if a project with the same name already exists in the specified account
         pprint(f'in POST /projects service method: A project with the same name -"{project_creation_payload.name}"- already exists in the specified account -"{project_creation_payload.account_id}"')
         raise ApiError.conflict(f"A project with the same name - '{project_creation_payload.name}' - already exists in account - '{project_creation_payload.account_id}'")
      # Create new project resource from req body
      new_project = Project(
         account_id=project_creation_payload.account_id,
         project_owner_id=logged_in_user_id,
         parent_project_id=project_creation_payload.parent_project_id,
         name=project_creation_payload.name,
         description=project_creation_payload.description,
         created_at=datetime.now(),
         updated_at=datetime.now()
      )
      
      db.add(new_project)
      db.flush()  # Now, new_project.id is available

      # Create the User_Project association with the new project's ID
      new_user_project = User_Project(
         user_id=logged_in_user_id,
         project_id=new_project.id,
      )

      db.add(new_user_project) # Add the User_Project association to the session
      db.commit() # Commit the transaction to persist both the new project and the association
      
      return new_project
   except HTTPException as e:
      db.rollback()
      pprint(f'API error in POST /projects/ : {e}')
      raise e
   except IntegrityError as e : # Database-side uniqueness check : Check if a project with the same name already exists in the specified account
        db.rollback()
        pprint(f'Error in POST /projects : {e}')
        raise ApiError.conflict(f"A project with the same name -{project_creation_payload.name}- already exists in the specified account -{project_creation_payload.account_id}")
   except SQLAlchemyError as e: # group db side error as 503 to not expose actual error to client
        db.rollback()
        pprint(f'Error in POST /projects : {e}')
        raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
   except Exception as e:
      db.rollback()
      print(f'Unexpected error in POST /projects/ : {e}')
      raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
   
def patch_project(
   project_to_patch: Project,
   project_patch_payload: ProjectPatchRequestDTO,
   db: Session,
   ): 
   try:
      for var, value in vars(project_patch_payload).items():
         setattr(project_to_patch, var, value) if value is not None else None
      project_to_patch.updated_at = datetime.now()
      db.commit()
      db.refresh(project_to_patch)
      return project_to_patch
   except HTTPException as e:
      db.rollback()
      pprint(f'API error in PATCH /projects/{project_to_patch.id} : {e}')
      raise e
   except SQLAlchemyError as e: # group db side error as 503 to not expose actual error to client
      db.rollback()
      pprint(f'DB error in PATCH /projects/{project_to_patch.id} : {e}')
      raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
   except Exception as e:
      db.rollback()
      print(f'Unexpected error in PATCH /projects/{project_to_patch.id} : {e}')
      raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")

def get_projects( 
   logged_in_user_id: UUID,
   logged_in_user_is_superadmin: bool,
   logged_in_user_is_admin: bool,
   account_id: UUID,
   parent_project_id: Optional[UUID],
   project_owner_email: Optional[str],
   name: Optional[str],
   db: Session,
   type: Optional[ProjectType] = ProjectType.All,
   view: Optional[ProjectView] = ProjectView.Flat
) -> List[ProjectResponseDTO]:
   try:
      if (not logged_in_user_is_superadmin and not logged_in_user_is_admin) or type == ProjectType.Shared_With_Me: # When type is 'Shared_With_Me' or when user is non admin/superadmin:
         query = db.query(Project).join(User_Project, User_Project.project_id == Project.id).filter( # base query is to show associated projects in account; can be filtered for view : 'Hierarchical', type: 'Shared_With_Me', type: 'My_Projects' later
            Project.account_id == account_id,
            User_Project.user_id == logged_in_user_id,
         )            
      else: # When type is not 'Shared_With_Me' and when user is admin/superadmin
         query = db.query(Project).filter(Project.account_id == account_id) # base query is to see all projects in account regardless of association, can be filtered for view : 'Hierarchical', type: 'Shared_With_Me', type: 'My_Projects' later

      if view == ProjectView.Hierarchical: # consider subset of projects linked to parent_project_id for 'Hierarchical' view 
         query = query.filter(Project.parent_project_id == parent_project_id)
      
      if type == ProjectType.My_Projects: 
          query = query.filter(Project.project_owner_id == logged_in_user_id) # show all projects created by user
      elif type == ProjectType.Shared_With_Me:
          query = query.filter(Project.project_owner_id != logged_in_user_id) # show all projects not created by user

      if project_owner_email:
          user_alias = aliased(User)
          query = query.join(user_alias, Project.project_owner_id == user_alias.id).filter(user_alias.email.ilike(f"%{project_owner_email}%"))
      if name:
          query = query.filter(Project.name.ilike(f"%{name}%"))

      projects = query.all()
      return cast(List[ProjectResponseDTO], projects)  
   except SQLAlchemyError as e:
      db.rollback()
      pprint(f'DB error in GET /projects/ : {e}')
      raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
   except Exception as e:
      db.rollback()
      print(f'Unexpected error in GET /projects/ : {e}')
      raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")

def get_project_user_list(
   db: Session,
   project_id: UUID,
   account_id: UUID, 
   firstname: Optional[str],
   lastname: Optional[str],
   email: Optional[str]
) -> List[ProjectUserListItemDTO]:
   try:
      UserAccountAlias = aliased(User_Account)
      RoleUserAccountAlias = aliased(Role_User_Account)
      UserProjectAlias = aliased(User_Project)

      project_users_query = (
      db.query(User, UserAccountAlias.is_admin, UserAccountAlias.id)
      .join(UserProjectAlias, UserProjectAlias.user_id == User.id)
      .join(UserAccountAlias, and_(UserAccountAlias.user_id == User.id, UserAccountAlias.account_id == account_id))
      .filter(UserProjectAlias.project_id == project_id)
      )

      if firstname:
         project_users_query = project_users_query.filter(User.firstname.ilike(f"%{firstname}%"))
      if lastname:
         project_users_query = project_users_query.filter(User.lastname.ilike(f"%{lastname}%"))
      if email:
         project_users_query = project_users_query.filter(User.email.ilike(f"%{email}%"))

      project_users = project_users_query.all()
      project_users_with_roles = []

      for user, is_admin, user_account_id in project_users:
         if user.is_superadmin:
            project_user_with_roles_dto = ProjectUserListItemDTO(
               **user.__dict__,
               is_account_admin=False,
               roles=[]
            )
         elif is_admin:
            project_user_with_roles_dto = ProjectUserListItemDTO(
               **user.__dict__,
               is_account_admin=True,
               roles=[]
            )
         else:
            roles_query = (
               db.query(Role)
               .join(RoleUserAccountAlias, RoleUserAccountAlias.role_id == Role.id)
               .filter(
                  RoleUserAccountAlias.user_account_id == user_account_id
               )
            )
            roles = roles_query.all()
            
            # role_summary_dto = [RoleSummaryDTO.model_validate(role) for role in roles]
            role_summary_dto = [RoleSummaryDTO.from_orm(role) for role in roles]

            # Construct AccountUserListItemDTO for each user
            project_user_with_roles_dto = ProjectUserListItemDTO(
               **user.__dict__,
               is_account_admin=False,
               roles=role_summary_dto
            )
         project_users_with_roles.append(project_user_with_roles_dto)
      return project_users_with_roles
   except HTTPException as e:
      db.rollback()
      pprint(f'API error in GET /projects/{project_id}/users : {e}')
      raise e
   except SQLAlchemyError as e:
      db.rollback()
      pprint(f'Error in GET /projects/{project_id}/users : {e}')
      raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
   except Exception as e:
      db.rollback()
      pprint(f'Unexpected error in GET /projects/{project_id}/users : {e}')
      raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
   
def assign_or_deassign_users_in_project(
   user_list_dto: UserListDTO,
   db: Session,
   project : Project,
   logged_in_user_id: UUID,
   logged_in_user_is_superadmin: bool,
   logged_in_user_is_admin: bool,
) -> JSONResponse:
   try:
      user_ids = user_list_dto.user_ids
      action = user_list_dto.action

      if action == "Add":
         query_result = db.query(
            func.count(User.id).label("total_users_found_in_list"),
            func.count(User_Account.user_id).label("total_user_account_associations_in_list"),
            func.count(User_Project.user_id).label("total_user_current_project_associations_in_list")
         ).outerjoin(
            User_Account, and_(User.id == User_Account.user_id, User_Account.account_id == project.account_id)
         ).outerjoin(
            User_Project, and_(User.id == User_Project.user_id, User_Project.project_id == project.id)
         ).filter(
            User.id.in_(user_list_dto.user_ids)
         ).one()


         # #Start building the base query
         # query = db.query(
         #    func.count(User.id).label("total_users_found_in_list"),
         #    func.count(User_Account.user_id).label("total_user_account_associations_in_list"),
         # ).outerjoin(
         #    User_Account, and_(User.id == User_Account.user_id, User_Account.account_id == project.account_id)
         # )

         # # Conditionally modify the query based on the presence of a parent project
         # if project.parent_project_id is not None:
         #    query = query.add_columns( 
         #       func.sum(
         #             case(
         #                (User_Project.project_id == project.id, 1),
         #                else_=0
         #             )
         #       ).label("total_user_current_project_associations_in_list"),
         #       func.sum(
         #             case(
         #                (User_Project.project_id == project.parent_project_id, 1),
         #                else_=0
         #             )
         #       ).label("total_user_parent_project_associations_in_list"),
         #    ).outerjoin(
         #       User_Project, and_(User.id == User_Project.user_id, or_(User_Project.project_id == project.id, User_Project.project_id == project.parent_project_id))
         #    )
         # else:
         #    query = query.add_columns(
         #       func.count(User_Project.user_id).label("total_user_current_project_associations_in_list")
         #    ).outerjoin(
         #       User_Project, and_(User.id == User_Project.user_id, User_Project.project_id == project.id)
         #    )

         # # # Apply filter for user_ids and execute the query
         # query_result = query.filter(
         #    User.id.in_(user_list_dto.user_ids)
         # ).one()

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
               func.count(User_Project.user_id)
            ).filter(
               User_Project.user_id.in_(user_list_dto.user_ids),
               User_Project.project_id == project.parent_project_id
            ).scalar()
            print(f'parent_project_association_count = {parent_project_associations_count}')
            if parent_project_associations_count != len(user_ids):
               print(f"in PATCH /projects/{project.id}/users service method: One or more users are not assigned to parent project - {project.parent_project_id}")
               raise ApiError.validationerror(f" One or more users are not assigned to parent project - '{project.parent_project_id}'")
            
         if total_user_current_project_associations_in_list > 0 :
            print(f"in PATCH /projects/{project.id}/users service method: One or more users are already assigned to project - {project.id}")
            raise ApiError.conflict(f"One or more users are already assigned to project - '{project.id}'")
         
         new_user_projects = [
            User_Project(user_id=user_id, project_id=project.id)
            for user_id in user_ids
         ]
         db.bulk_save_objects(new_user_projects)
         db.commit()
         return JSONResponse(content={"message": f"Successfully assigned {len(new_user_projects)} user/(s) to project"}, status_code= status.HTTP_200_OK)
      else: # action == "Remove"
         query_result = db.query(
         func.count(User.id).label("total_users_found_in_list"),
         func.count(User_Account.user_id).label("total_user_account_associations_in_list"),
         func.count(User_Project.user_id).label("total_user_project_associations_in_list"),
         func.sum(case((User.is_superadmin == True, 1), else_=0)).label("superadmin_in_list"),
         func.sum(case((User.id == logged_in_user_id, 1), else_=0)).label("logged_in_user_in_list"),
         func.sum(case((User_Account.is_admin == True, 1), else_=0)).label("total_admins_in_list")
            ).outerjoin(
               User_Account, and_(User.id == User_Account.user_id, User_Account.account_id == project.account_id)
            ).outerjoin(
               User_Project, and_(User.id == User_Project.user_id, User_Project.project_id == project.id)
            ).filter(
               User.id.in_(user_list_dto.user_ids)
            ).one()
         
         # Extracting the results
         (total_users_found_in_list,
         total_user_account_associations_in_list,
         total_user_project_associations_in_list,
         superadmin_in_list,
         logged_in_user_in_list,
         total_admins_in_list) = query_result

         if total_users_found_in_list != len(user_ids): # all users in input must exist
            print(f'In PATCH /projects/{project.id}/users service method : One or more users to deassign from project -{project.id}- not found')
            raise ApiError.notfound(f"One or more users not found")
         
         if total_user_account_associations_in_list != len(user_ids): # all users in input must be associated to account
            print(f"In PATCH /projects/{project.id}/users service method : One or more users are not assigned to project account - {project.account_id}")
            raise ApiError.validationerror(f"One or more users are not assigned to account - '{project.account_id}'")
         
         if total_user_project_associations_in_list != len(user_ids): # all users in input must be associated to account
            print(f"In PATCH /projects/{project.id}/users service method : One or more users are not assigned to project - '{project.id}'")
            raise ApiError.validationerror(f"One or more users are not assigned to project - '{project.id}'")

         if logged_in_user_in_list == 1: # logged in user cannot deassign self using this endpoint
            print(f"In PATCH /accounts/{project.account_id}/users service method : invalid operation - user cannot include self in deassignment list for project -'{project.id}'")
            raise ApiError.forbidden(f"you cannot include self in deassignment list for project - '{project.id}'")
         
         # Admin, Superadmin or project-owner may deassign anyone from project, so code commented out below:

         # if superadmin_in_list > 0 and not logged_in_user_is_superadmin:
         #    print(f"In PATCH /projects/{project.id}/users service method : user does not have permissions to deassign superadmin-user from project -'{project.id}'")
         #    raise ApiError.forbidden(f"you do not have permissions to deassign superadmin-user from project - '{project.id}'")
         
         # if total_admins_in_list > 0:
         #    if not logged_in_user_is_superadmin and not logged_in_user_is_admin:
         #       print(f"In PATCH /projects/{project.id}/users service method : user does not have permissions to deassign admin-users from project -'{project.id}'")
         #       raise ApiError.forbidden(f"you do not have permissions to deassign admin-users from project - '{project.id}'")
         
         delete_user_project_associations_for_subprojects(db=db, starting_project_id=project.id, user_id_or_user_ids=user_ids)

         db.commit()
         return JSONResponse(content={"message": f"Successfully deassigned {len(user_ids)} user/(s) from project"}, status_code=status.HTTP_200_OK)
   except HTTPException as e:
      db.rollback()
      pprint(f'API error in PATCH /projects/{project.id}/users service method : {e}')
      raise e
   except SQLAlchemyError as e:
      db.rollback()
      pprint(f'DB Error in PATCH /projects/{project.id}/users service method : {e}')
      raise ApiError.serviceunavailable("The server is currently unavailable, please try again later")
   except Exception as e:
      db.rollback()
      pprint(f'Unexpected error in PATCH /projects/{project.id}/users service method : {e}')
      raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
   
# def assign_self_to_project(
#    logged_in_user_id: UUID,
#    project_exists: bool,
#    project_id: UUID,
#    db: Session
# ) -> JSONResponse:
#    try:
#       if project_exists is None:
#          project_exists = db.query(exists().where(
#             Project.id == project_id
#          )).scalar()

#       if not project_exists:
#          print(f'INSIDE POST /projects/{project_id}/users/self - validate_astsign_self_to_project dependency : project - "{project_id}" - not found')
#          raise ApiError.notfound(f"project - '{project_id}' - not found")
      
#       user_project_association_exists = db.query(exists().where(
#          User_Project.user_id == logged_in_user_id,
#          User_Project.project_id == project_id
#       )).scalar()

#       if user_project_association_exists:
#          print(f'INSIDE POST /projects/{project_id}/users/self - service method : logged-in user is already assigned to project - "{project_id}"')
#          raise ApiError.conflict(f"you are already assigned to project - '{project_id}'")
#       # Create a new User_Project association
#       new_association = User_Project(user_id=logged_in_user_id, project_id=project_id)
#       db.add(new_association)
#       db.commit()
#       return JSONResponse(status_code= status.HTTP_200_OK, content={"message": f"Successfully assigned self to project - '{project_id}'"})
#    except HTTPException as e:
#       db.rollback()
#       pprint(f'API error in POST /projects/{project_id}/users/self service method : {e}')
#       raise e
#    except SQLAlchemyError as e:
#       db.rollback()
#       pprint(f'DB Error in POST /projects/{project_id}/users/self service method : {e}')
#       raise ApiError.serviceunavailable("The server is currently unavailable, please try again later")
#    except Exception as e:
#       db.rollback()
#       pprint(f'Unexpected error in POST /projects/{project_id}/users/self service method : {e}')
#       raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
   
def deassign_self_from_project(
   db: Session,
   project_id: UUID,
   logged_in_user_id: UUID
) -> JSONResponse:
   try:
      delete_user_project_associations_for_subprojects(db=db, starting_project_id=project_id, user_id_or_user_ids=logged_in_user_id)
      db.commit()
      return JSONResponse(status_code= status.HTTP_200_OK, content={"message": f"Successfully deassigned self from project - '{project_id}'"})
   except SQLAlchemyError as e:
      db.rollback()
      pprint(f'DB Error in DELETE /projects/{project_id}/users/self service method : {e}')
      raise ApiError.serviceunavailable("The server is currently unavailable, please try again later")
   except Exception as e:
      db.rollback()
      pprint(f'Unexpected error in DELETE /projects/{project_id}/users/self service method : {e}')
      raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
   
# def patch_project_status(
#    project_id: UUID,
#    project_disabled_status_update_dto: ResourceStatusUpdateDTO,
#    db: Session,
# )-> JSONResponse:
#    try:
#       project = db.query(Project).filter(Project.id == project_id).first()
#       if not project:
#          print(f"in PATCH /projects/{project_id}/status service method: Project -'{project_id}'- not found")
#          raise ApiError.notfound(f"Project -'{project_id}'- not found")

#       # Check for redundant status updates
#       if (project_disabled_status_update_dto.action == "Disable" and project.is_disabled) or \
#          (project_disabled_status_update_dto.action == "Enable" and not project.is_disabled):
#          print(f"in PATCH /projects/{project_id}/status service method: Project - '{project_id}' - is already {'disabled' if project.is_disabled else 'enabled'}.")
#          raise ApiError.validationerror(f"Project - '{project_id}' - is already {'disabled' if project.is_disabled else 'enabled'}.")

#       # Update project status
#       project.is_disabled = project_disabled_status_update_dto.action == "Disable"
#       db.commit()

#       return JSONResponse(content= {"message": f"Project successfully {'disabled' if project.is_disabled else 'enabled'}."} ,status_code=status.HTTP_200_OK)
#    except HTTPException as e:
#       db.rollback()
#       pprint(f'API error in PATCH /projects/{project_id}/status : {e}')
#       raise e
#    except SQLAlchemyError as e:
#       db.rollback()
#       pprint(f'DB error in PATCH /projects/{project_id}/status : {e}')
#       raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
#    except Exception as e:
#       db.rollback()
#       pprint(f'Unexpected error in PATCH /projects/{project_id}/status : {e}')
#       raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")  
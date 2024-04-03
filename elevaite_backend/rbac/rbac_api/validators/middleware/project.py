from fastapi import Query, Path, Depends, Body, HTTPException
from uuid import UUID
from .header import validate_token
from sqlalchemy import exists
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from pprint import pprint
from typing import Optional, Any
from rbac_api.app.errors.api_error import ApiError

from rbac_api.utils.deps import get_db 
from elevaitedb.db import models
from elevaitedb.schemas import (
   role_schemas,
   project_schemas,
)

from rbac_api.utils.cte import (
   is_user_project_association_till_root,
)

async def validate_get_project(
      user_email: str = Depends(validate_token),
      project_id: UUID = Path(..., description="The ID of the project to retrieve"),
      db: Session = Depends(get_db)
   ) -> dict[str, Any]:
   try:
      # Fetch user by email
      logged_in_user = db.query(models.User).filter(models.User.email == user_email).first()
      if not logged_in_user:
         print(f'INSIDE GET /projects/{project_id} validate_get_project: logged-in user not found in db')
         raise ApiError.unauthorized("user is unauthenticated")

      # Fetch project to get account_id
      project = db.query(models.Project).filter(models.Project.id == project_id).first()
      if not project:
         print(f"INSIDE GET /projects/{project_id} validate_get_project: project - '{project_id}' - not found")
         raise ApiError.notfound(f"project - '{project_id}' - not found")

      account_id = project.account_id
      account = db.query(models.Account).filter(models.Account.id == account_id).first()
      if not account:
         print(f"INSIDE GET /projects/{project_id} validate_get_project: account - '{account_id}' - not found")
         raise ApiError.notfound(f"project's associated account - '{account_id}' - not found")
      
      if logged_in_user.is_superadmin:
         return {"project" : project}
      
      logged_in_user_account_association = db.query(models.User_Account).filter(
         models.User_Account.user_id == logged_in_user.id,
         models.User_Account.account_id == account_id,
      ).first()

      # invalidate if logged-in user is not a member of the account the project belongs to
      if not logged_in_user_account_association: 
         print(f"INSIDE GET /projects/{project_id} validate_get_project: logged-in user - '{logged_in_user.id}' - is not assigned to account - '{account_id}'")
         raise ApiError.forbidden(f"you are not assigned to account - '{account_id}'")
      
      # validate user if he is an account admin of the account the project belongs to
      if logged_in_user_account_association.is_admin: 
         return {"project" : project}
      
      if account.is_disabled:
         print(f"INSIDE validate_get_project: account - '{account_id}' - is disabled")
         raise ApiError.forbidden(f"account - '{account_id}' - is disabled")
      
      # need to check account based role permission here
      role_based_project_read_access_exists = db.query(
         db.query(models.Role)
         .join(models.Role_User_Account, 
               (models.Role_User_Account.role_id == models.Role.id) &
            (models.Role_User_Account.user_account_id == logged_in_user_account_association.id))
         .filter(
            models.Role.permissions['Project']['READ']['action'].astext == 'Allow'
         )
         .exists()
      ).scalar()

      if not role_based_project_read_access_exists:
         print(f"INSIDE GET /projects/{project_id} - validate_get_project dependency : logged-in user - '{logged_in_user.id}' - is not a superadmin/admin and does not have account-specific role-based access permissions to perform actions on or within project resources due to denied Project - 'READ' permissions in account - '{account.id}'")
         raise ApiError.forbidden(f"you are not a superadmin/admin and you do not have account-specific role-based access permissions to perform actions on or within project resources due to denied Project - 'READ' permissions in account - '{account.id}'")
      
      # Check user-project association:
      user_project_association = db.query(models.User_Project).filter(
         models.User_Project.user_id == logged_in_user.id,
         models.User_Project.project_id == project_id
      ).first()
      
      if not user_project_association:
         print(f"INSIDE GET /projects/{project_id} validate_get_project: logged-in user - '{logged_in_user.id}' - is not assigned to project - '{project_id}'")
         raise ApiError.forbidden(f"you are not assigned to project - '{project_id}'")
      
      # Check user-project association and project-specific read permissions for all projects in current project parent's hierarchy
      if project.parent_project_id and not is_user_project_association_till_root(db=db, starting_project_id=project.parent_project_id, user_id=logged_in_user.id):
         print(f"logged-in user - '{logged_in_user.id}' - is not assigned to one or more projects in the project hierarchy of parent project - '{project.parent_project_id}'")
         raise ApiError.forbidden(f"you are not assigned to one or more projects in the project hierarchy of parent project - '{project.parent_project_id}'")
      
      return {"project" : project}
   except HTTPException as e:
      db.rollback()
      pprint(f'API error in GET /projects/{project_id}- validate_get_project: {e}')
      raise e
   except SQLAlchemyError as e:
      db.rollback()
      print(f'DB error in GET /projects/{project_id} - validate_get_project: {e}')
      raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
   except Exception as e:
      db.rollback()
      print(f'Unexpected error in GET /projects/{project_id} - validate_get_project: {e}')
      raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
   
async def validate_get_projects( # When associations cascade deleted, this will perform as expected. When project is disabled, can still see them, but cant perform actions.
      user_email: str = Depends(validate_token),
      account_id: UUID = Query(description = "account id that the project belongs to"), 
      parent_project_id: Optional[UUID] = Query(None, description = "parent project id under which projects are queried"),
      view: Optional[project_schemas.ProjectView] = Query(None, description = "view style to display projects"),
      db: Session = Depends(get_db)
   ) -> dict[str,Any]:
   try:
      # 1. First need to check existence of logged_in_user, account_id, and parent_project if provided
      # 2. Three cases for users : superadmin, admin and regular user
      #    superadmin should be validated regardless.
      #    admin needs to exist in account to be verified as admin, and can then be validated.
      #    regular user needs to exist in account, and account should not be disabled, and ancestory chain of projects given by parent_project_id should not be disabled.
      # Fetch user by email
      logged_in_user = db.query(models.User).filter(models.User.email == user_email).first()
      if not logged_in_user:
         print(f'INSIDE validate_get_projects: logged-in user with email -{user_email}- not found in user table')
         raise ApiError.unauthorized("user is unauthenticated")

      # Check for account existence
      account = db.query(models.Account).filter(models.Account.id == account_id).first()
      if not account:
         print(f'INSIDE validate_get_projects: account -{account_id}- not found')
         raise ApiError.notfound(f"Account - '{account_id}' - not found")

      # If parent_project_id is provided and view is 'Hierarchical', check for parent project existence
      if parent_project_id and view == project_schemas.ProjectView.Hierarchical:
         parent_project_exists = db.query(exists().where(models.Project.id == parent_project_id)).scalar()
         if not parent_project_exists:
            print(f'INSIDE validate_get_projects: parent project -{parent_project_id}- not found')
            raise ApiError.notfound(f"Parent project - '{parent_project_id}' - not found")

      # Validate user if is a superadmin regardless of account-association, account-disabled or parent-project ancestory disabled somewhere
      if logged_in_user.is_superadmin:
         return {"logged_in_user_id": logged_in_user.id,
                  "logged_in_user_is_superadmin" : True,
                  "logged_in_user_is_admin" : None,
                  "db": db}

      # Fetch User_Account association entry for admin and regular user validations ahead
      logged_in_user_account_association = db.query(models.User_Account).filter(
         models.User_Account.user_id == logged_in_user.id,
         models.User_Account.account_id == account_id
      ).first()

      # Invalidate user if not a member of the account
      if not logged_in_user_account_association:
         print(f'INSIDE validate_get_projects: logged-in user -{logged_in_user.id}- is not assigned to account -{account_id}')
         raise ApiError.forbidden(f"you are not assigned to account - '{account_id}'")

      # Validate user if is an account admin
      if logged_in_user_account_association.is_admin:
         return {"logged_in_user_id": logged_in_user.id,
                  "logged_in_user_is_superadmin" : False,
                  "logged_in_user_is_admin" : True,
                  "db": db}
      
      # regular-user case:
      if account.is_disabled:
         print(f"INSIDE validate_get_projects: account - '{account_id}' - is disabled")
         raise ApiError.forbidden(f"account - '{account_id}' - is disabled")

      # need to check account based role permission here
      role_based_project_read_access_exists = db.query(
         db.query(models.Role)
         .join(models.Role_User_Account, 
               (models.Role_User_Account.role_id == models.Role.id) &
            (models.Role_User_Account.user_account_id == logged_in_user_account_association.id))
         .filter(
            models.Role.permissions['Project']['READ']['action'].astext == 'Allow'
         )
         .exists()
      ).scalar()

      if not role_based_project_read_access_exists:
         print(f"INSIDE GET /projects/ - validate_get_projects dependency : logged-in user - '{logged_in_user.id}' - is not a superadmin/admin and does not have account-specific role-based access permissions to perform actions on or within project resources due to denied project 'READ' permissions in account - '{account.id}'")
         raise ApiError.forbidden(f"you are not a superadmin/admin and you do not have account-specific role-based access permissions to perform actions on or within project resources due to denied Project - 'READ' permissions in account - '{account.id}'")
            
      # Check accessibility for non-admin users only if parent_project_id is provided by checking association  with parent_project_id and all its ancestors
      if parent_project_id and view == project_schemas.ProjectView.Hierarchical:
         if not is_user_project_association_till_root(db=db, starting_project_id=parent_project_id, user_id=logged_in_user.id):
            print(f"logged-in user - '{logged_in_user.id}' - is not assigned to one or more projects in the project hierarchy of parent project - '{parent_project_id}'")
            raise ApiError.forbidden(f"you are not assigned to one or more projects in the project hierarchy of parent project - '{parent_project_id}'")
         
      return {"logged_in_user_id": logged_in_user.id,
               "logged_in_user_is_superadmin" : False,
               "logged_in_user_is_admin" : False,
               "db": db}
   except HTTPException as e:
      db.rollback()
      pprint(f'API error in GET /projects/ validate_get_projects : {e}')
      raise e
   except SQLAlchemyError as e:
      db.rollback()
      pprint(f'DB error in GET /projects/ validate_get_projects: {e}')
      raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
   except Exception as e:
      db.rollback()
      print(f'Unexpected error in GET /projects/ - validate_get_projects: {e}')
      raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
      
async def validate_get_project_user_list(
    db: Session = Depends(get_db),
    project_id: UUID = Path(..., description="Project id under which users are queried"),
    user_email: str = Depends(validate_token)
) -> dict[str, Any]:
   # logged-in user must exist, project must exist, account corresponding to project.account_id must exist
   # superadmin and admins of account can get all project user list regardless of disabled account or project status 
   # regular users can get all account user list only if account is not disabled, and they are associated with project as well (including owner of project) 
   # in total, first existence of logged in user, project, account and is_superadmin and User_Account.is_admin can be checked. Then account.is_disabled, then User_Project, then project ancestory is disabled check and then finally return.
   try:
      # Check for existence of logged-in user
      logged_in_user = db.query(models.User).filter(models.User.email == user_email).first()
      if not logged_in_user:
         print(f"in GET /projects/{project_id}/users - validate_get_project_user_list dependency : logged-in user with email -'{user_email}'- not found in users table")
         raise ApiError.unauthorized("user is unauthenticated")

      # Check for existence of project
      project = db.query(models.Project).filter(models.Project.id == project_id).first()
      if not project:
         print(f"in GET /projects/{project_id}/users - validate_get_project_user_list dependency : project -'{project_id}'- not found in projects table")
         raise ApiError.notfound(f"project - '{project_id}' - not found")

      # Check for existence of account related to the project
      account = db.query(models.Account).filter(models.Account.id == project.account_id).first()
      if not account:
         print(f"in GET /projects/{project_id}/users - validate_get_project_user_list dependency : account -'{project.account_id}'- not found in account table")
         raise ApiError.notfound(f"account - '{project.account_id}' - not found")

      # Check if the account is disabled
      if account.is_disabled:
         print(f"in GET /projects/{project_id}/users - validate_get_project_user_list dependency : account -'{project.account_id}'- is disabled")
         raise ApiError.forbidden(f"account - '{project.account_id}' - is disabled")
      
      validation_info = {"account_id": account.id, "db": db}

      # Check if logged-in user is a superadmin, and return the account_id if this is the case regardless of account being disabled or any ancestor project being disabled
      if logged_in_user.is_superadmin:
         return validation_info

      # Check for user-account association
      logged_in_user_account_association = db.query(models.User_Account).filter(
         models.User_Account.user_id == logged_in_user.id, models.User_Account.account_id == account.id
      ).first()
      if not logged_in_user_account_association:
         print(f"in GET /projects/{project_id}/users - validate_get_project_user_list dependency : logged-in user - '{logged_in_user.id}' - is not assigned to account - '{project.account_id}'")
         raise ApiError.forbidden(f"you are not assigned to account - '{project.account_id}'")
         
      # Check if the user is an admin in the account, and return the account_id if this is the case regardless of account being disabled or any ancestor project being disabled
      if logged_in_user_account_association.is_admin:
         return validation_info

      # need to check account based role permission for project 'READ' here
      role_based_project_read_access_exists = db.query(
         db.query(models.Role)
         .join(models.Role_User_Account, 
               (models.Role_User_Account.role_id == models.Role.id) &
            (models.Role_User_Account.user_account_id == logged_in_user_account_association.id))
         .filter(
            models.Role.permissions['Project']['READ']['action'].astext == 'Allow'
         )
         .exists()
      ).scalar()

      if not role_based_project_read_access_exists:
         print(f"INSIDE GET /projects/{project_id}/users - validate_get_project_user_list dependency : logged-in user - '{logged_in_user.id}' - is not a superadmin/admin and does not have account-specific role-based access permissions to perform actions on or within project resources due to denied project 'READ' permissions in account - '{account.id}'")
         raise ApiError.forbidden(f"you are not a superadmin/admin and you do not have account-specific role-based access permissions to perform actions on or within project resources due to denied Project - 'READ' permissions in account - '{account.id}'")
      
      # Check for user-project association
      user_project_association = db.query(models.User_Project).filter(
         models.User_Project.project_id == project_id,
         models.User_Project.user_id == logged_in_user.id
      ).first()

      if not user_project_association:
         print(f"in GET /projects/{project_id}/users - validate_get_project_user_list dependency : logged-in user - '{logged_in_user.id}' - is not assigned to project - '{project_id}'")
         raise ApiError.forbidden(f"you are not assigned to project - '{project_id}'")
      
      parent_project_id = project.parent_project_id
      # Check user-project association and project-specific read permissions for all projects in current project parent's hierarchy
      if parent_project_id and not is_user_project_association_till_root(db=db, starting_project_id=parent_project_id, user_id=logged_in_user.id):
         print(f"logged-in user - '{logged_in_user.id}' - is not assigned to one or more projects in the project hierarchy of parent project - '{parent_project_id}'")
         raise ApiError.forbidden(f"you are not assigned to one or more projects in the project hierarchy of parent project - '{parent_project_id}'")
         
      return validation_info
   except HTTPException as e:
         db.rollback()
         pprint(f'API error in GET /projects/{project_id}/users - validate_get_project_user_list dependency : {e}')
         raise e
   except SQLAlchemyError as e:
      pprint(f'DB error in GET /projects/{project_id}/users - validate_get_project_user_list dependency : {e}')
      raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
   except Exception as e:
      print(f'Unexpected error in GET /projects/{project_id}/users - validate_get_project_user_list dependency : {e}')
      raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
 
async def validate_patch_project(
      user_email: str = Depends(validate_token),
      project_id: UUID = Path(..., description="The ID of the project to patch"),
      db: Session = Depends(get_db)
   ) -> dict[str, Any]:
   try:
      # 1. logged-in user and project existence must be verified, and account within it extracted from query
      # 2. split users into 2 cases : superadmin and admin
      # 3. for superadmin, account should not be disabled, and none in parent project ancestory must be disabled.
      #    for admin, logged-in user User_Account association must be verified, and account should not be disabled, and none in parent project ancestory must be disabled.
      #    for regular user, logged-in user User_Account association must be verified, and account should not be disabled, User_Project association must exist, and he must be owner, and none in parent project ancestory must be disabled.
      #    So in total, logged-in user check, project existence,  account not disabled, and none in project ancestory disabled can all be done in common at the top, but project recursion done specifically so that unecessary computation avoided
      # Fetch user by email
      logged_in_user = db.query(models.User).filter(models.User.email == user_email).first()
      if not logged_in_user:
         print(f"INSIDE PATCH /projects/{project_id} validate_patch_project: logged-in user with email -'{user_email}'- not found in user table")
         raise ApiError.unauthorized("user is unauthenticated")
      
      project = db.query(models.Project).filter(models.Project.id == project_id).first()
      if not project:
         print(f'INSIDE PATCH /projects/{project_id} validate_patch_project: project -{project_id}- not found')
         raise ApiError.notfound(f"project - '{project_id}' - not found")
      
      account = db.query(models.Account).filter(models.Account.id == project.account_id).first()
      if not account:
         print(f'INSIDE PATCH /projects/{project_id} validate_patch_project: account -{project.account_id}- not found')
         raise ApiError.notfound(f"account - '{project.account_id}' - not found")
      
      if account.is_disabled:  
         print(f'INSIDE PATCH /projects/{project_id} validate_patch_project: account -{project.account_id}- is disabled')
         raise ApiError.forbidden(f"account - '{project.account_id}' - is disabled")

      if logged_in_user.is_superadmin: 
         # if project.is_disabled: # needs to be a cte check here, and can be common at the top
         #    print(f'INSIDE PATCH /projects/{project_id} validate_patch_project: project -{project_id}- is disabled')
         #    raise ApiError.forbidden(f'project -{project_id}- is disabled')
         return {"logged_in_user_id" : logged_in_user.id,
                  "is_superadmin" : True,
                  "is_admin" : None,
                  "is_owner" : None,
                  "project_to_patch" : project,
                  "db" : db}

      logged_in_user_account_association = db.query(models.User_Account).filter(
         models.User_Account.user_id == logged_in_user.id,
         models.User_Account.account_id == account.id,
      ).first()

      # validate if logged_in_user is associated to account, and if account admin or project-owner
      if not logged_in_user_account_association:
         print(f"INSIDE PATCH /projects/{project_id} validate_patch_project: logged-in user - '{logged_in_user.id}' - is not assigned to account - '{account.id}' - and does not have superadmin privileges to patch project - '{project_id}'")
         raise ApiError.forbidden(f"you are not assigned to account - '{account.id}' - and you dont have superadmin privileges to patch project - '{project_id}'")
      
      if logged_in_user_account_association.is_admin: 
         return {"logged_in_user_id" : logged_in_user.id,
                  "is_superadmin" : False,
                  "is_admin" : True,
                  "is_owner" : None,
                  "project_to_patch" : project,
                  "db" : db}
      
      # need to check account based role permission for project 'READ' here
      role_based_project_read_access_exists = db.query(
         db.query(models.Role)
         .join(models.Role_User_Account, 
               (models.Role_User_Account.role_id == models.Role.id) &
            (models.Role_User_Account.user_account_id == logged_in_user_account_association.id))
         .filter(
            models.Role.permissions['Project']['READ']['action'].astext == 'Allow'
         )
         .exists()
      ).scalar()

      if not role_based_project_read_access_exists:
         print(f"INSIDE PATCH /projects/{project_id} validate_patch_project: logged-in user - '{logged_in_user.id}' - is not a superadmin/admin and does not have account-specific role-based access permissions to perform actions on or within project resources due to denied project 'READ' permissions in account - '{account.id}'")
         raise ApiError.forbidden(f"you are not a superadmin/admin and you do not have account-specific role-based access permissions to perform actions on or within project resources due to denied Project - 'READ' permissions in account - '{account.id}'")
      
      if logged_in_user.id == project.project_owner_id: 
         # Check user-project association:
         user_project_association = db.query(models.User_Project).filter(
            models.User_Project.user_id == logged_in_user.id,
            models.User_Project.project_id == project_id
         ).first()
         if not user_project_association:
            print(f"INSIDE PATCH /projects/{project_id} validate_patch_project: logged-in user - '{logged_in_user.id}' - is not assigned to project - '{project_id}'")
            raise ApiError.forbidden(f"you are not assigned to project - '{project_id}'")
         
         parent_project_id = project.parent_project_id
         if parent_project_id and not is_user_project_association_till_root(db=db, starting_project_id=parent_project_id, user_id=logged_in_user.id):
            print(f"INSIDE PATCH /projects/{project_id} - validate_patch_project dependency: logged-in user - '{logged_in_user.id}' - is not assigned to one or more projects in the project hierarchy of parent project - '{parent_project_id}'")
            raise ApiError.forbidden(f"you are not assigned to one or more projects in the project hierarchy of parent project - '{parent_project_id}'")
               
         return {"logged_in_user_id" : logged_in_user.id,
                  "is_superadmin" : False,
                  "is_admin" : False,
                  "is_owner" : True,
                  "project_to_patch" : project,
                  "db" : db}

      print(f"INSIDE PATCH /projects/{project_id} validate_patch_project: logged-in user - '{logged_in_user.id}' - does not have superadmin/admin or owner permissions to patch project - '{project_id}'")
      raise ApiError.forbidden(f"you do not have superadmin/admin or project-owner permissions to update project - '{project_id}'")
      
   except HTTPException as e:
      db.rollback()
      pprint(f'API error in PATCH /projects/{project_id} validate_patch_project : {e}')
      raise e
   except SQLAlchemyError as e:
      db.rollback()
      pprint(f'DB error in PATCH /projects/{project_id} validate_patch_project: {e}')
      raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
   except Exception as e:
      db.rollback()
      print(f'Unexpected error in PATCH /projects/{project_id} - validate_patch_project dependency : {e}')
      raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")

async def extract_and_validate_post_project_data(project_creation_payload: project_schemas.ProjectCreationRequestDTO = Body(...),
                                                 user_email: str = Depends(validate_token),
                                                 db: Session = Depends(get_db)):
    account_id = project_creation_payload.account_id
    parent_project_id = project_creation_payload.parent_project_id
    return await validate_post_project(account_id, parent_project_id, user_email, db)

async def validate_post_project( # cascade delete on associations will make this work as intended. disabled status of account and projects need to be checked
   account_id: UUID,
   parent_project_id: Optional[UUID],
   user_email: str = Depends(validate_token),
   db: Session = Depends(get_db)
) -> dict[str, Any]:
   try: 
      # 1. First validate existence of logged-in user, and account within project
      # 2. Split access for user into 3 cases - user is : superadmin, admin, or neither.
      # 3. For superadmin case, if parent-project-id provided, then must exist, and any ancestor project in parent chain should not be disabled, and account must not be disabled.
      #    For admin case, logged-in user and account association must exist for admin check, and if so, same checks of if parent-project-id provided, then must exist, and any ancestor project in parent chain should not be disabled, and account must not be disabled.
      #    For regular users, account-association must exist, account must not be disabled, parent-project-id if present must exist, association must exist, and any ancestor project in parent chain should not be disabled, and account must not be disabled. and role-based and project-based permissions must be checked 
      # which means the logged-in user check, account check, and account.is_disabled checks can be common at the top
      
      # Fetch user by email
      logged_in_user = db.query(models.User).filter(models.User.email == user_email).first()
      if not logged_in_user:
         print(f"INSIDE POST /projects validate_post_project: logged-in user with email -'{user_email}'- not found in user table")
         raise ApiError.unauthorized("user is unauthenticated")

      # Fetch account and validate existence
      account = db.query(models.Account).filter(models.Account.id == account_id).first()
      if not account:
         print(f"INSIDE POST /projects validate_post_project: account -'{account_id}'- not found") 
         raise ApiError.notfound(f"account - '{account_id}' - not found")

      if account.is_disabled:  
         print(f"INSIDE POST /projects validate_post_project: account - '{account_id}' - is disabled")
         raise ApiError.forbidden(f"account - '{account_id}' - is disabled")
      
      if parent_project_id:
         parent_project = db.query(models.Project).filter(models.Project.id == parent_project_id).first()
         if not parent_project:
            print(f'INSIDE POST /projects validate_post_project: parent project - "{parent_project_id}" - not found')
            raise ApiError.notfound(f"parent project - '{parent_project_id}' - not found")
      
      # superadmin case
      if logged_in_user.is_superadmin: 
         # if project.parent_project_id: # and parent_project.is_disabled: # needs to be replaced by recursive cte on parent_project , and this can be done on top since required below as well
         #    print(f'INSIDE POST /projects validate_post_project: parent-project -"{parent_project.id}"- is disabled')
         #    raise ApiError.forbidden(f'parent-project is disabled')
         return {"logged_in_user_id" : logged_in_user.id,
                  "is_superadmin" : True,
                  "is_admin" : None,
                  "db": db}
      
      # Fetch logged-in user User_Account association for is_admin check
      logged_in_user_account_association = db.query(models.User_Account).filter(
         models.User_Account.user_id == logged_in_user.id,
         models.User_Account.account_id == account_id
      ).first()

      # Validate logged-in user's membership in the account
      if not logged_in_user_account_association:
         print(f"INSIDE POST /projects validate_post_project: logged-in user -{logged_in_user.id}- is not assigned to account -{account_id}")
         raise ApiError.forbidden(f"you are not assigned to account - '{account_id}'")

      # account admin case
      if logged_in_user_account_association.is_admin:
         # if project.parent_project_id: # and parent_project.is_disabled: # needs to be replaced with cte check flag obtained above
         #    print(f'INSIDE POST /projects validate_post_project: parent-project -"{parent_project.id}"- is disabled')
         #    raise ApiError.forbidden(f'parent-project -"{parent_project.id}"- is disabled')
         return {"logged_in_user_id" : logged_in_user.id,
                  "is_superadmin" : False,
                  "is_admin" : True,
                  "db": db}

      # need to check account based role permission for project 'READ' here
      role_based_project_read_access_exists = db.query(
         db.query(models.Role)
         .join(models.Role_User_Account, 
               (models.Role_User_Account.role_id == models.Role.id) &
            (models.Role_User_Account.user_account_id == logged_in_user_account_association.id))
         .filter(
            models.Role.permissions['Project']['READ']['action'].astext == 'Allow'
         )
         .exists()
      ).scalar()

      if not role_based_project_read_access_exists:
         print(f"INSIDE POST /projects validate_post_project dependency : logged-in user - '{logged_in_user.id}' - is not a superadmin/admin and does not have account-specific role-based access permissions to perform actions on or within project resources due to denied project 'READ' permissions in account - '{account.id}'")
         raise ApiError.forbidden(f"you are not a superadmin/admin and you do not have account-specific role-based access permissions to perform actions on or within project resources due to denied Project - 'READ' permissions in account - '{account.id}'")
         
      # check account based role permissions for "CREATE":
      role_based_project_create_access_exists = db.query(
         db.query(models.Role)
         .join(models.Role_User_Account, 
               (models.Role_User_Account.role_id == models.Role.id) &
            (models.Role_User_Account.user_account_id == logged_in_user_account_association.id))
         .filter(
            models.Role.permissions['Project']['CREATE']['action'].astext == 'Allow'
         )
         .exists()
      ).scalar()
      if not role_based_project_create_access_exists:
         print(f"INSIDE POST /projects validate_post_project dependency : logged-in user - '{logged_in_user.id}' - is not a superadmin/admin and does not have account-specific role-based access permissions to create projects in account - '{account.id}'")
         raise ApiError.forbidden(f"you do not have superadmin/admin privileges and you do not have account-specific role-based access permissions to create projects in account - '{account.id}'")
      
      if parent_project_id:
         parent_project_association = db.query(models.User_Project).filter(
            models.User_Project.user_id == logged_in_user.id,
            models.User_Project.project_id == parent_project_id
         ).first()

         if not parent_project_association:
            print(f"INSIDE POST /projects - validate_post_project dependency: logged-in user - '{logged_in_user.id}' - is not assigned to parent project - '{parent_project_id}'")
            raise ApiError.forbidden(f"you are not assigned to parent project - '{parent_project_id}'")
         if not is_user_project_association_till_root(db=db, starting_project_id=parent_project_id, user_id=logged_in_user.id):
            print(f"INSIDE POST /projects - validate_post_project dependency: logged-in user - '{logged_in_user.id}' - is not assigned to one or more projects in the project hierarchy of parent project - '{parent_project_id}'")
            raise ApiError.forbidden(f"you are not assigned to one or more projects in the project hierarchy of parent project - '{parent_project_id}'")
         
         if not parent_project.project_owner_id == logged_in_user.id:
            # Fetch permission overrides for the parent project
            user_project_overrides = role_schemas.ProjectScopedPermissions.parse_obj(parent_project_association.permission_overrides)
            if user_project_overrides and user_project_overrides.Project.CREATE.action == 'Deny': 
               print(f"INSIDE POST /projects validate_post_project: logged-in user - '{logged_in_user.id}' - has project-specific permission overrides which restrict creation of subprojects under parent project - '{parent_project_id}' ")
               raise ApiError.forbidden(f"you are denied project create permissions due to project-specific permission overrides under parent project - '{parent_project_id}'")
      
      return {"logged_in_user_id" : logged_in_user.id,
               "is_superadmin" : False,
               "is_admin" : False,
               "db": db}
   except HTTPException as e:
      db.rollback()
      pprint(f'API error in POST /projects/ - validate_post_project dependency : {e}')
      raise e
   except SQLAlchemyError as e:
      db.rollback()
      pprint(f'DB error in POST /projects validate_post_project: {e}')
      raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
   except Exception as e:
      db.rollback()
      print(f'Unexpected error in POST /projects - validate_post_projects dependency : {e}')
      raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")

# async def validate_assign_self_to_project(
#    email: str = Depends(validate_token), 
#    project_id: UUID = Path(..., description ="The ID of the project"),
#    db: Session = Depends(get_db)  
# ) -> dict[str, Any]:
#    # Authorization only concerned with logged-in user, superadmin, and admin checks
#    # other details obtained as by-product can be sent to service as well
#    try:
#       logged_in_user = db.query(User).filter(User.email == email).first()
#       if not logged_in_user:
#          print(f'INSIDE POST /projects/{project_id}/users/self - validate_assign_self_to_project dependency : logged-in user with email - "{email}" - not found')
#          raise ApiError.unauthorized("user is unauthenticated")
      
#       # authorize superadmin early
#       if logged_in_user.is_superadmin:
#          return {
#             "logged_in_user_id" : logged_in_user.id,
#             "project_exists": None,
#             "db" : db
#          }
      
#       # Find out if account admin
#       project = db.query(Project).filter(Project.id == project_id).first()
#       if not project:
#          print(f'INSIDE POST /projects/{project_id}/users/self - validate_assign_self_to_project dependency : project - "{project_id}" - not found')
#          raise ApiError.notfound(f"project - '{project_id}' - not found")
      
#       logged_in_user_account_association = db.query(User_Account).filter(User_Account.account_id == project.account_id,
#                                                                          User_Account.user_id == logged_in_user.id).first()
#       if not logged_in_user_account_association:
#          print(f'INSIDE POST /projects/{project_id}/users/self - validate_assign_self_to_project dependency : logged-in user is not assigned to account - "{project.account_id}"')
#          raise ApiError.forbidden(f"you are not assigned to account - '{project.account_id}'")
      
#       if not logged_in_user_account_association.is_admin:
#          print(f'INSIDE POST /projects/{project_id}/users/self - validate_assign_self_to_project dependency : logged-in user - "{logged_in_user.id}" - does not have superadmin/admin privileges to assign self to project - "{project.id}"')
#          raise ApiError.forbidden(f"you do not have superadmin/admin privileges to assign self to project - '{project.id}'")
#       return {
#             "logged_in_user_id" : logged_in_user.id,
#             "project_exists": True,
#             "db" : db
#          }
#    except HTTPException as e:
#       db.rollback()
#       pprint(f'API error in POST /projects/{project_id}/users/self - validate_assign_self_to_project dependency : {e}')
#       raise e
#    except SQLAlchemyError as e:
#       # Handle SQLAlchemy errors
#       db.rollback()
#       pprint(f'DB error in POST /projects/{project_id}/users/self - validate_assign_self_to_project dependency : {e}')
#       raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
#    except Exception as e:
#       db.rollback()
#       print(f'Unexpected error in POST /projects/{project_id}/users/self - validate_assign_self_to_project dependency : {e}')
#       raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
   
async def validate_deassign_self_from_project(
   email: str = Depends(validate_token), 
   project_id: UUID = Path(..., description ="The ID of the project"),
   db: Session = Depends(get_db) 
) -> dict[str, Any]:
   # Authorization only concerned with existence of user and project in db; user must be authenticated and part of project
   try:
      logged_in_user = db.query(models.User).filter(models.User.email == email).first()
      if not logged_in_user:
         print(f'INSIDE DELETE /projects/{project_id}/users/self - validate_deassign_self_from_project dependency : logged-in user with email - "{email}" - not found')
         raise ApiError.unauthorized("user is unauthenticated")
         
      project = db.query(models.Project).filter(models.Project.id == project_id).first()

      if not project:
         print(f'INSIDE DELETE /projects/{project_id}/users/self - validate_deassign_self_from_project dependency : project - "{project_id}" - not found')
         raise ApiError.notfound(f"project - '{project_id}' - not found")
      
      # Fetch account associated with the project
      account = db.query(models.Account).filter(models.Account.id == project.account_id).first()
      if not account:
         print(f'INSIDE DELETE /projects/{project_id}/users/self - validate_deassign_self_from_project dependency : associated account - "{project.account_id}" - for project - "{project_id}" - not found')
         raise ApiError.notfound(f"account - '{project.account_id}' - not found")

      if account.is_disabled:
         print(f'DELETE /projects/{project_id}/users/self - validate_deassign_self_from_project dependency : associated account - "{project.account_id}" - is disabled')
         raise ApiError.forbidden(f"account - '{project.account_id}' - is disabled")
      
      user_project_association_exists = db.query(exists().where(
         models.User_Project.user_id == logged_in_user.id,
         models.User_Project.project_id == project_id
         )).scalar()
      
      if not user_project_association_exists:
         print(f'INSIDE DELETE /projects/{project_id}/users/self - validate_deassign_self_from_project dependency : logged-in user is not assigned to project - "{project_id}"')
         raise ApiError.forbidden(f"you are not assigned to project - '{project_id}'")
      
      if logged_in_user.is_superadmin:
         return {"db" : db, "logged_in_user_id": logged_in_user.id}
      
      logged_in_user_account_association = db.query(models.User_Account).filter(
         models.User_Account.user_id == logged_in_user.id,
         models.User_Account.account_id == account.id
      ).first()

      if not logged_in_user_account_association:
         print(f'INSIDE DELETE /projects/{project_id}/users/self - validate_deassign_self_from_project dependency : logged-in user is not assigned to account - "{account.id}"')
         raise ApiError.forbidden(f"you are not assigned to account - '{account.id}'")
      
      if logged_in_user_account_association.is_admin:
         return {"db" : db, "logged_in_user_id": logged_in_user.id}
      
      # need to check account based role permission for project 'READ' here
      role_based_project_read_access_exists = db.query(
         db.query(models.Role)
         .join(models.Role_User_Account, 
               (models.Role_User_Account.role_id == models.Role.id) &
            (models.Role_User_Account.user_account_id == logged_in_user_account_association.id))
         .filter(
            models.Role.permissions['Project']['READ']['action'].astext == 'Allow'
         )
         .exists()
      ).scalar()

      if not role_based_project_read_access_exists:
         print(f"INSIDE DELETE /projects/{project_id}/users/self - validate_deassign_self_from_project dependency : logged-in user - '{logged_in_user.id}' - is not a superadmin/admin and does not have account-specific role-based access permissions to perform actions on or within project resources due to denied project 'READ' permissions in account - '{account.id}'")
         raise ApiError.forbidden(f"you are not a superadmin/admin and you do not have account-specific role-based access permissions to perform actions on or within project resources due to denied Project - 'READ' permissions in account - '{account.id}'")
         
      if project.parent_project_id and not is_user_project_association_till_root(db=db, starting_project_id=project.parent_project_id, user_id=logged_in_user.id):
         print(f"INSIDE DELETE /projects/{project_id}/users/self - validate_deassign_self_from_project dependency : logged-in user - '{logged_in_user.id}' - is not assigned to one or more projects in the project hierarchy of parent project - '{project.parent_project_id}'")
         raise ApiError.forbidden(f"you are not assigned to one or more projects in the project hierarchy of parent project - '{project.parent_project_id}'")
      
      return {"db" : db, "logged_in_user_id": logged_in_user.id}
   
   except HTTPException as e:
      db.rollback()
      pprint(f'API error in DELETE /projects/{project_id}/users/self - validate_deassign_self_from_project dependency : {e}')
      raise e
   except SQLAlchemyError as e:
      # Handle SQLAlchemy errors
      db.rollback()
      pprint(f'DB error in DELETE /projects/{project_id}/users/self - validate_deassign_self_from_project dependency : {e}')
      raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
   except Exception as e:
      db.rollback()
      print(f'Unexpected error in DELETE /projects/{project_id}/users/self - validate_deassign_self_from_project dependency : {e}')
      raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
   
async def validate_assign_or_deassign_users_in_project(
    email: str = Depends(validate_token), 
    project_id: UUID = Path(..., description ="The ID of the project"),
    db: Session = Depends(get_db)
) -> dict[str, Any]:
   try:
      # 1. Check for logged-in user exists, project given by project_id exists
      # 2. Split into 3 cases for users - superadmin, admin, or neither
      # 3. For superadmin case, check if account given by project.account_id exists, and account is not disabled, and if any ancestor project not disabled
      #    For admin case, check if logged-in-user-account association exists to check for admin, and then account is not disabled, and if any ancestor project not disabled
      #    For regular case, check if account association exists, check if user-project association exists, and if user is owner, and if any ancestor project is not disabled
      # which means checking logged-in user, account, account_disabled and ancestor_project_disabled can all be done in common at the top
      # Fetch current user by email
      logged_in_user = db.query(models.User).filter(models.User.email == email).first()
      if not logged_in_user:
         print(f'INSIDE PATCH /projects/{project_id}/users - validate_assign_or_deassign_users_in_project: logged-in user with email - "{email}" - not found')
         raise ApiError.unauthorized("user is unauthenticated")
      
      # Fetch project by project_id
      project = db.query(models.Project).filter(models.Project.id == project_id).first()
      if not project:
         print(f'INSIDE PATCH /projects/{project_id}/users - validate_assign_or_deassign_users_in_project: Project - "{project_id}" - not found.')
         raise ApiError.notfound(f"project - '{project_id}' - not found")
      
      # Fetch account associated with the project
      account = db.query(models.Account).filter(models.Account.id == project.account_id).first()
      if not account:
         print(f'INSIDE PATCH /projects/{project_id}/users - validate_assign_or_deassign_users_in_project: associated account - "{project.account_id}" - for project - "{project_id}" - not found')
         raise ApiError.notfound(f"account - '{project.account_id}' - not found")

      if account.is_disabled:
         print(f'INSIDE PATCH /projects/{project_id}/users - validate_assign_or_deassign_users_in_project: associated account - "{project.account_id}" - is disabled')
         raise ApiError.forbidden(f"account - '{project.account_id}' - is disabled")
      
      # If current_user is the project owner or superadmin, return early
      if logged_in_user.is_superadmin: 
         return {"logged_in_user_id": logged_in_user.id,
                  "project": project,
                  "logged_in_user_is_superadmin" : True,
                  "logged_in_user_is_admin" : False,
                  "db": db}

      # Check for User_Account entry and if logged-in user is an account admin
      logged_in_user_account_association = db.query(models.User_Account).filter(
         models.User_Account.user_id == logged_in_user.id,
         models.User_Account.account_id == project.account_id
      ).first()

      if not logged_in_user_account_association:
         print(f'INSIDE PATCH /projects/{project_id}/users - validate_assign_or_deassign_users_in_project: logged-in user -"{logged_in_user.id}"- is not assigned to project account - {project.account_id}')
         raise ApiError.forbidden(f"you are not assigned to account - '{project.account_id}'")
      
      if logged_in_user_account_association.is_admin: 
         return {"logged_in_user_id": logged_in_user.id,
                  "project": project,
                  "logged_in_user_is_superadmin" : False,
                  "logged_in_user_is_admin" : True,
                  "db" : db}
      
      # need to check account based role permission for project 'READ' here
      role_based_project_read_access_exists = db.query(
         db.query(models.Role)
         .join(models.Role_User_Account, 
               (models.Role_User_Account.role_id == models.Role.id) &
            (models.Role_User_Account.user_account_id == logged_in_user_account_association.id))
         .filter(
            models.Role.permissions['Project']['READ']['action'].astext == 'Allow'
         )
         .exists()
      ).scalar()

      if not role_based_project_read_access_exists:
         print(f"INSIDE PATCH /projects/{project_id}/users - validate_assign_or_deassign_project: logged-in user - '{logged_in_user.id}' - is not a superadmin/admin and does not have account-specific role-based access permissions to perform actions on or within project resources due to denied project 'READ' permissions in account - '{account.id}'")
         raise ApiError.forbidden(f"you are not a superadmin/admin and you do not have account-specific role-based access permissions to perform actions on or within project resources due to denied Project - 'READ' permissions in account - '{account.id}'")
      
      if project.project_owner_id == logged_in_user.id:
         # Check user-project association:
         user_project_association = db.query(models.User_Project).filter(
            models.User_Project.user_id == logged_in_user.id,
            models.User_Project.project_id == project_id
         ).first()
         if not user_project_association:
            print(f"INSIDE PATCH /projects/{project_id}/users - validate_assign_or_deassign_project: logged-in user - '{logged_in_user.id}' - is not assigned to project - '{project_id}'")
            raise ApiError.forbidden(f"you are not assigned to project - '{project_id}'")
         
         parent_project_id = project.parent_project_id
         if parent_project_id and not is_user_project_association_till_root(db=db, starting_project_id=parent_project_id, user_id=logged_in_user.id):
            print(f"INSIDE PATCH /projects/{project_id}/users - validate_assign_or_deassign_project: logged-in user - '{logged_in_user.id}' - is not assigned to one or more projects in the project hierarchy of parent project - '{parent_project_id}'")
            raise ApiError.forbidden(f"you are not assigned to one or more projects in the project hierarchy of parent project - '{parent_project_id}'")
         
         return {"logged_in_user_id": logged_in_user.id,
               "project": project,
               "logged_in_user_is_superadmin" : False,
               "logged_in_user_is_admin" : False,
               "db": db}
         
      # If flow reaches here, user does not have required permissions
      print('INSIDE validate_assign_project: User does not have superadmin/admin/project-owner permission to assign/deassign users to/from this project')
      raise ApiError.forbidden(f"you do not have superadmin,admin or project-owner privileges to assign or deassign users in project - '{project_id}'")
   except HTTPException as e:
      db.rollback()
      pprint(f'API error in PATCH /projects/{project_id}/users - validate_assign_project dependency : {e}')
      raise e
   except SQLAlchemyError as e:
      # Handle SQLAlchemy errors
      db.rollback()
      pprint(f'DB error in PATCH /projects/{project_id}/users - validate_assign_project dependency: {e}')
      raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
   except Exception as e:
      db.rollback()
      print(f'Unexpected error in PATCH /projects/{project_id}/users - validate_assign_project dependency: {e}')
      raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
   
# async def validate_patch_project_status(
#    user_email: str = Depends(validate_token),
#    db: Session = Depends(get_db),
#    project_id: UUID = Path(..., description="The ID of the project to patch enabled/disabled status")
# ) -> dict[str, Any]:
#    try:
#       # Only Superadmins, account admins, and project owners who are still associated to project, can patch project disabled status
#       logged_in_user = db.query(User).filter(User.email == user_email).first()
#       if not logged_in_user:
#          print(f"in PATCH /projects/{project_id}/status - validate_patch_project_status dependency : logged-in user with email -'{user_email}'- not found in user table")
#          raise ApiError.unauthorized()

#       project = db.query(Project).filter(Project.id == project_id).first()
#       if not project:
#          print(f"in PATCH /projects/{project_id}/status - validate_patch_project_status dependency : project -'{project}'- not found")
#          raise ApiError.notfound(f"project -'{project_id}'- not found")
      
#       account = db.query(Account).filter(Account.id == project.account_id).first()
#       if not account:
#          print(f"in PATCH /projects/{project_id}/status - validate_patch_project_status dependency : account -'{project.account_id}'- not found")
#          raise ApiError.notfound(f"account -'{project.account_id}'- not found")

#       # If logged-in user is a superadmin, return early
#       if logged_in_user.is_superadmin:
#          return {"logged_in_user_id": logged_in_user.id}

#       # Check for logged-in user's association with the account
#       user_account_association = db.query(User_Account).filter(
#          User_Account.user_id == logged_in_user.id,
#          User_Account.account_id == account.id
#       ).first()
      
#       if not user_account_association:
#          print(f"in PATCH /projects/{project_id}/status - validate_patch_project_status dependency : logged-in user -'{logged_in_user.id}'- does not have permissions to perform this action")
#          raise ApiError.forbidden(f"logged-in user -'{logged_in_user.id}'- does not have permissions to perform this action")

#       # Check if the user is an admin of the account
#       if user_account_association.is_admin:
#          return {"logged_in_user_id": logged_in_user.id}
      
#       if logged_in_user.id == project.project_owner_id: # Check if project owner and is still associated to all projects in hierarchy
#          # do cte check here
#          return {"logged_in_user_id": logged_in_user.id}
      
#       # If the flow reaches here, the user does not have permission to patch the account status
#       print(f"in PATCH /projects/{project_id}/status - validate_patch_project_status dependency : logged-in user -'{logged_in_user.id}'- does not have permissions to perform this action")
#       raise ApiError.forbidden(f"logged-in user -'{logged_in_user.id}'- does not have permissions to perform this action")
#    except HTTPException as e:
#       db.rollback()
#       pprint(f'API error in PATCH /projects/{project_id}/status - validate_patch_project_status dependency : {e}')
#       raise e
#    except SQLAlchemyError as e:
#       pprint(f'DB error in PATCH /projects/{project_id}/status - validate_patch_project_status dependency : {e}')
#       raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
#    except Exception as e:
#       print(f'Unexpected error in PATCH /projects/{project_id}/status - validate_patch_project_status dependency : {e}')
#       raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
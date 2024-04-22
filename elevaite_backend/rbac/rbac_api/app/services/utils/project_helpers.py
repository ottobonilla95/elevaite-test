from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from elevaitedb.db.models import User_Project, User_Account, Project 

def get_top_level_associated_project_ids_for_user_in_account(db: Session, user_id: UUID, account_id: UUID) -> List[UUID]:
    # Query User_Project and Project to find top-level projects for the logged-in user within a specific account
    query = (
        db.query(Project.id)
        .join(User_Project, User_Project.project_id == Project.id)  # Join User_Project to Project
        .filter(User_Project.user_id == user_id)  # Where User_Project matches the user ID
        .filter(Project.account_id == account_id)  # Where Project belongs to the specified account
        .filter(Project.parent_project_id == None)  # Where Project is a top-level project
    )

    # Execute the query and extract project IDs
    result = query.all()
    project_ids = [id for (id,) in result]  # Extract IDs from the result tuples
    # print(f'top_level_associated_project_ids_for_user_in_account - "{account_id}" = {project_ids}')
    return project_ids

# need to define this for the superadmin revoke endpoint
def get_top_level_associated_project_ids_for_user_in_all_non_admin_accounts(db: Session, user_id: UUID):
    query = (
        db.query(Project.id)
        .join(User_Project, User_Project.project_id == Project.id)# Join with User_Project on project_id; ensures 1 to 1 mapping after join for each row
        .join(User_Account, ((User_Account.user_id == User_Project.user_id) & (User_Account.account_id == Project.account_id))) # join User_Account on account_id from Project table, and user_id from User_Project table; ensures 1-1 mapping for each row after join
        .filter(User_Project.user_id == user_id)  # Where User_Project matches the user ID
        .filter(User_Account.is_admin == False) # where user is not account admin
        .filter(Project.parent_project_id == None)  # Where Project is a top-level project
    )

    # Execute the query and extract project IDs
    result = query.all()
    project_ids = [id for (id,) in result]  # Extract IDs from the result tuples
    # print(f'top_level_associated_project_ids_for_user_in_all_non_admin_accounts = {project_ids}')
    return project_ids

def delete_all_associated_user_projects_in_account(user_id: UUID, account_id: UUID, db: Session):
    # First obtain all User_Project association id's to delete based on projects under specified account
    user_project_ids_query = db.query(User_Project.id) \
        .join(Project, Project.id == User_Project.project_id) \
        .filter(
        User_Project.user_id == user_id,
        Project.account_id == account_id
    )

    # Perform the deletion on these user-project association id's
    user_project_delete_count = db.query(User_Project) \
        .filter(User_Project.id.in_(user_project_ids_query)) \
        .delete(synchronize_session=False)
      
    # Log the number of User_Project entries deleted for auditing
    # print(f"Deleted {user_project_delete_count} User_Project entries for user - '{user_id}' - in account {account_id}")
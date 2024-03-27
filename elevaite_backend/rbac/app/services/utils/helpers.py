from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from elevaitedb.db.models import User_Project, Project  # Assuming these are your ORM models

def get_top_level_project_ids_for_user_in_account(db: Session, logged_in_user_id: UUID, account_id: UUID) -> List[UUID]:
    # Query User_Project and Project to find top-level projects for the logged-in user within a specific account
    query = (
        db.query(Project.id)
        .join(User_Project, User_Project.project_id == Project.id)  # Join User_Project to Project
        .filter(User_Project.user_id == logged_in_user_id)  # Where User_Project matches the logged-in user ID
        .filter(Project.account_id == account_id)  # Where Project belongs to the specified account
        .filter(Project.parent_project_id == None)  # Where Project is a top-level project
    )

    # Execute the query and extract project IDs
    result = query.all()
    project_ids = [id for (id,) in result]  # Extract IDs from the result tuples

    return project_ids
from sqlalchemy import text
import uuid
import os
from sqlalchemy.orm import Session
from fastapi import Depends
from sqlalchemy import update
from dotenv import load_dotenv
from uuid import UUID
from elevaitedb.db.models import (
   Base,
   Organization,
   User,
   Account,
   User_Account,
   Project,
   User_Project,
   Role,
   Role_User_Account
   )
from elevaitedb.schemas.role_schemas import (
    AccountScopedPermissions,
    ProjectScopedPermissions
)

from app.utils.deps import get_db

def seed_db(db: Session):
    ORG_ID = os.getenv("ORGANIZATION_ID")
    SUPERADMIN_EMAIL_1 = os.getenv("SUPERADMIN_EMAIL_1")
    SUPERADMIN_EMAIL_2 = os.getenv("SUPERADMIN_EMAIL_2")
    
    # Truncate existing tables
    tables = ['role_user_account', 'roles', 'user_project', 'user_account', 'users', 'accounts', 'projects', 'organizations']
    for table in tables:
        db.execute(text(f"TRUNCATE TABLE {table} RESTART IDENTITY CASCADE;"))
    db.commit()

    # Insert Organization
    organization = Organization(id=UUID(str(ORG_ID)), name="Seed Org", description="Seeded Organization")
    db.add(organization)
    db.commit()
    
    # Insert Users including Superadmins
    superadmin_1 = User(id=uuid.uuid4(), organization_id=UUID(str(ORG_ID)), email=SUPERADMIN_EMAIL_1, firstname='Akash', is_superadmin=True)
    superadmin_2 = User(id=uuid.uuid4(), organization_id=UUID(str(ORG_ID)), email=SUPERADMIN_EMAIL_2, firstname='John', is_superadmin=True)
    regular_users = [User(id=uuid.uuid4(), organization_id=UUID(str(ORG_ID)), email=f"user{i}@example.com", firstname = f'user-{i}') for i in range(3)]
    db.add_all([superadmin_1, superadmin_2] + regular_users)
    db.commit()
    db.refresh(superadmin_1)
    db.refresh(superadmin_2)
    db.refresh(regular_users[0])
    db.refresh(regular_users[1])
    db.refresh(regular_users[2])
    # Create Accounts and tie them to users
    account_1 = Account(id=uuid.uuid4(), organization_id=UUID(str(ORG_ID)), name="Account 1")
    account_2 = Account(id=uuid.uuid4(), organization_id=UUID(str(ORG_ID)), name="Account 2")
    account_3 = Account(id=uuid.uuid4(), organization_id=UUID(str(ORG_ID)), name="Account 3")
    db.add_all([account_1, account_2, account_3])
    db.commit()
    db.refresh(account_1)
    db.refresh(account_2)
    db.refresh(account_3)

    user_account_1_for_superadmin_1 = User_Account(user_id=superadmin_1.id, account_id=account_1.id)
    db.add(user_account_1_for_superadmin_1)
    db.commit()

    user_account_2_for_superadmin_1 = User_Account(user_id=superadmin_1.id, account_id=account_2.id)
    db.add(user_account_2_for_superadmin_1)
    db.commit()

    user_account_3_for_superadmin_1 = User_Account(user_id=superadmin_1.id, account_id=account_3.id)
    db.add(user_account_3_for_superadmin_1)
    db.commit()

    user_account_1_for_superadmin_2 = User_Account(user_id=superadmin_2.id, account_id=account_1.id)
    db.add(user_account_1_for_superadmin_2)
    db.commit()

    user_account_2_for_superadmin_2 = User_Account(user_id=superadmin_2.id, account_id=account_2.id)
    db.add(user_account_2_for_superadmin_2)
    db.commit()

    user_account_3_for_superadmin_2 = User_Account(user_id=superadmin_2.id, account_id=account_3.id)
    db.add(user_account_3_for_superadmin_2)
    db.commit()

    user_account_3_for_admin = User_Account(user_id=regular_users[2].id, account_id=account_3.id, is_admin=True)
    db.add(user_account_3_for_admin)
    db.commit()

    # Add other users as members of Account 3
    user_account_3_for_user0 = User_Account(user_id=regular_users[0].id, account_id=account_3.id)
    db.add(user_account_3_for_user0)
    db.commit()

    user_account_3_for_user1 = User_Account(user_id=regular_users[1].id, account_id=account_3.id)
    db.add(user_account_3_for_user1)
    db.commit()


    # Create Projects and tie them to accounts and owners
    project_1 = Project(id=uuid.uuid4(), account_id=account_1.id, project_owner_id=superadmin_1.id, name="Project 1")
    project_2 = Project(id=uuid.uuid4(), account_id=account_2.id, project_owner_id=superadmin_2.id, name="Project 2")
    project_3 = Project(id=uuid.uuid4(), account_id=account_3.id, project_owner_id=regular_users[2].id, name="Project 3")
    project_1_child1 = Project(id=uuid.uuid4(), account_id=account_1.id, project_owner_id=superadmin_1.id, parent_project_id = project_1.id, name="Project-1_Child-1")
    project_1_child2 = Project(id=uuid.uuid4(), account_id=account_1.id, project_owner_id=superadmin_1.id, parent_project_id = project_1.id, name="Project-1_Child-2")
    project_2_child1 = Project(id=uuid.uuid4(), account_id=account_2.id, project_owner_id=superadmin_2.id, parent_project_id = project_2.id, name="Project-2_Child-1")
    project_2_child2 = Project(id=uuid.uuid4(), account_id=account_2.id, project_owner_id=superadmin_2.id, parent_project_id = project_2.id, name="Project-2_Child-2")
    project_3_child1 = Project(id=uuid.uuid4(), account_id=account_3.id, project_owner_id=regular_users[0].id, parent_project_id = project_3.id, name="Project-3_Child-1")
    project_3_child2 = Project(id=uuid.uuid4(), account_id=account_3.id, project_owner_id=regular_users[1].id, parent_project_id = project_3.id, name="Project-3_Child-2")
    project_3_child3 = Project(id=uuid.uuid4(), account_id=account_3.id, project_owner_id=regular_users[1].id, parent_project_id = project_3.id, name="Project-3_Child-3")

    db.add(project_1)
    db.commit()
    db.refresh(project_1)

    db.add(project_2)
    db.commit()
    db.refresh(project_2)

    db.add(project_3)
    db.commit()
    db.refresh(project_3)

    db.add(project_1_child1)
    db.commit()
    db.refresh(project_1_child1)

    db.add(project_1_child2)
    db.commit()
    db.refresh(project_1_child2)

    db.add(project_2_child1)
    db.commit()
    db.refresh(project_2_child1)

    db.add(project_2_child2)
    db.commit()
    db.refresh(project_2_child2)

    db.add(project_3_child1)
    db.commit()
    db.refresh(project_3_child1)

    db.add(project_3_child2)
    db.commit()
    db.refresh(project_3_child2)

    db.add(project_3_child3)
    db.commit()
    db.refresh(project_3_child3)

    # # User_Project entries
    user_project_1 = User_Project(user_id=superadmin_1.id, project_id=project_1.id, )
    user_project_1_child1 = User_Project(user_id=superadmin_1.id, project_id=project_1_child1.id)
    user_project_1_child2 = User_Project(user_id=superadmin_1.id, project_id=project_1_child2.id)

    user_project_2 = User_Project(user_id=superadmin_2.id, project_id=project_2.id)
    user_project_2_child1 = User_Project(user_id=superadmin_2.id, project_id=project_2_child1.id)
    user_project_2_child2 = User_Project(user_id=superadmin_2.id, project_id=project_2_child2.id)

    user_project_3 = User_Project(user_id=regular_users[2].id, project_id=project_3.id)
    user_project_3_for_user_0 = User_Project(user_id=regular_users[0].id, project_id=project_3.id)
    user_project_3_child1_for_user_0 = User_Project(user_id=regular_users[0].id, project_id=project_3_child1.id)
    user_project_3_child2_for_user_0 = User_Project(user_id=regular_users[0].id, project_id=project_3_child2.id)

    user_project_3_for_user_1 = User_Project(user_id=regular_users[1].id, project_id=project_3.id)
    user_project_3_child1_for_user_1 = User_Project(user_id=regular_users[1].id, project_id=project_3_child1.id)
    user_project_3_child2_for_user_1 = User_Project(user_id=regular_users[1].id, project_id=project_3_child2.id)
    user_project_3_child3_for_user_1 = User_Project(user_id=regular_users[1].id, project_id=project_3_child3.id)

    user_projects = [
        user_project_1, user_project_1_child1, user_project_1_child2,
        user_project_2, user_project_2_child1, user_project_2_child2,
        user_project_3, user_project_3_for_user_0, user_project_3_child1_for_user_0, user_project_3_child2_for_user_0,
        user_project_3_for_user_1, user_project_3_child1_for_user_1, user_project_3_child2_for_user_1, user_project_3_child3_for_user_1,
    ]

    for user_project in user_projects:
        db.add(user_project)
        db.commit()
        db.refresh(user_project)
        
    # # Permissions setup :

    # # Data scientist account-scoped permissions:
    data_scientist_permissions = AccountScopedPermissions()

    data_scientist_permissions.Project.READ.action = 'Allow'
    data_scientist_permissions.Project.CREATE.action = 'Allow'

    data_scientist_permissions.Ingest.READ.action = 'Allow'
    data_scientist_permissions.Ingest.CONFIGURE.READ.action = 'Allow'
    data_scientist_permissions.Ingest.CONFIGURE.CREATE.action = 'Allow'
    data_scientist_permissions.Ingest.CONFIGURE.RUN.action = 'Allow'

    data_scientist_permissions.Preprocess.READ.action = 'Allow'
    data_scientist_permissions.Preprocess.CONFIGURE.READ.action = 'Allow'
    data_scientist_permissions.Preprocess.CONFIGURE.CREATE.action = 'Allow'
    data_scientist_permissions.Preprocess.CONFIGURE.RUN.action = 'Allow'

    # ML Engineer account-scoped permissions:
    ml_engineer_permissions = AccountScopedPermissions()

    ml_engineer_permissions.Project.READ.action = 'Allow'
    ml_engineer_permissions.Project.CREATE.action = 'Allow'

    ml_engineer_permissions.Train.READ.action = 'Allow'
    ml_engineer_permissions.Train.DOWNLOAD.READ.action = 'Allow'
    ml_engineer_permissions.Train.DOWNLOAD.CREATE.action = 'Allow'
    ml_engineer_permissions.Train.DOWNLOAD.RUN.action = 'Allow'
    ml_engineer_permissions.Train.EVALUATE.READ.action = 'Allow'
    ml_engineer_permissions.Train.EVALUATE.CREATE.action = 'Allow'
    ml_engineer_permissions.Train.EVALUATE.RUN.action = 'Allow'
    ml_engineer_permissions.Train.FINE_TUNING.READ.action = 'Allow'
    ml_engineer_permissions.Train.FINE_TUNING.CREATE.action = 'Allow'

    # ML OPS account-scoped permissions:
    ml_ops_permissions = AccountScopedPermissions()

    ml_ops_permissions.Project.READ.action = 'Allow'
    ml_ops_permissions.Project.CREATE.action = 'Allow'

    ml_ops_permissions.Deploy.READ.action = 'Allow'
    ml_ops_permissions.Deploy.RUN.action = 'Allow'
    ml_ops_permissions.Deploy.CREATE.action = 'Allow'
    ml_ops_permissions.Deploy.CONFIGURE.READ.action = 'Allow'
    ml_ops_permissions.Deploy.CONFIGURE.CREATE.action = 'Allow'
    ml_ops_permissions.Deploy.CONFIGURE.RUN.action = 'Allow'

    # # Create Roles
    data_scientist_role = Role(name="Data Scientist", permissions=data_scientist_permissions.dict())
    ml_engineer_role = Role(name="ML Engineer", permissions=ml_engineer_permissions.dict())
    ml_ops_role = Role(name="ML OPS", permissions=ml_ops_permissions.dict())

    account_scoped_roles = [data_scientist_role, ml_engineer_role, ml_ops_role]
    for role in account_scoped_roles:
        db.add(role)
        db.commit()
        db.refresh(role)
    
    # # Role-User_Account Association
    role_user_account_1 = Role_User_Account(role_id=data_scientist_role.id, user_account_id=user_account_3_for_user0.id)
    role_user_account_2 = Role_User_Account(role_id=ml_engineer_role.id, user_account_id=user_account_3_for_user0.id)
    role_user_account_3 = Role_User_Account(role_id=ml_ops_role.id, user_account_id=user_account_3_for_user1.id)

    role_user_account_associations = [role_user_account_1, role_user_account_2, role_user_account_3]
    for role_user_account_association in role_user_account_associations:
        db.add(role_user_account_association)
        db.commit()
        db.refresh(role_user_account_association)

    # # Adding Project-specific permission overrides:

    project_permissions_overrides = ProjectScopedPermissions()
    project_permissions_overrides.Project.READ.action = 'Allow'
    project_permissions_overrides.Project.CREATE.action = 'Allow'

    project_permissions_overrides.Ingest.READ.action = 'Deny'
    project_permissions_overrides.Ingest.CONFIGURE.READ.action = 'Deny'
    project_permissions_overrides.Ingest.CONFIGURE.CREATE.action = 'Deny'
    project_permissions_overrides.Ingest.CONFIGURE.RUN.action = 'Deny'

    project_permissions_overrides.Preprocess.READ.action = 'Allow'
    project_permissions_overrides.Preprocess.CONFIGURE.READ.action = 'Allow'
    project_permissions_overrides.Preprocess.CONFIGURE.CREATE.action = 'Allow'
    project_permissions_overrides.Preprocess.CONFIGURE.RUN.action = 'Allow'

    user_project_id_to_update = user_project_3_for_user_0.id

    # # Perform the update
    db.execute(
        update(User_Project).
        where(User_Project.id == user_project_id_to_update).
        values(permission_overrides= project_permissions_overrides.dict())
    )
    db.commit()

    


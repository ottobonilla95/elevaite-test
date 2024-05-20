from sqlalchemy import text
import uuid
import os
from sqlalchemy.orm import Session
from sqlalchemy import update
from uuid import UUID
from elevaitedb.util.func import get_utc_datetime

from elevaitedb.schemas import (
    permission as permission_schemas,
    application as connector_schemas,
    instance as instance_schemas,
)
from elevaitedb.db import models


def seed_db(db: Session):
    ORG_ID = os.getenv("ORGANIZATION_ID")
    SUPERADMIN_EMAIL_1 = os.getenv("SUPERADMIN_EMAIL_1")
    SUPERADMIN_EMAIL_2 = os.getenv("SUPERADMIN_EMAIL_2")
    
    # Truncate existing tables
    # tables = ['role_user_account', 'roles', 'user_project', 'user_account', 'users', 'accounts', 'projects', 'organizations']
    # for table in tables:
    #     db.execute(text(f"TRUNCATE TABLE {table} RESTART IDENTITY CASCADE;"))
    # db.commit()

    db.execute(
        text(
            "TRUNCATE {} RESTART IDENTITY;".format(
                ", ".join(
                    table.name for table in reversed(models.Base.metadata.sorted_tables)
                )
            )
        )
    )

    db.commit()

    # Insert Organization
    organization = models.Organization(id=UUID(str(ORG_ID)), name="Seed Org", description="Seeded Organization")
    db.add(organization)
    db.commit()
    
    # Insert Users including Superadmins
    superadmin_1 = models.User(id=uuid.uuid4(), organization_id=UUID(str(ORG_ID)), email=SUPERADMIN_EMAIL_1, firstname='Akash', is_superadmin=True)
    superadmin_2 = models.User(id=uuid.uuid4(), organization_id=UUID(str(ORG_ID)), email=SUPERADMIN_EMAIL_2, firstname='John', is_superadmin=True)
    regular_users = [models.User(id=uuid.uuid4(), organization_id=UUID(str(ORG_ID)), email=f"user{i}@example.com", firstname = f'user-{i}') for i in range(3)]
    db.add_all([superadmin_1, superadmin_2] + regular_users)
    db.commit()
    db.refresh(superadmin_1)
    db.refresh(superadmin_2)
    db.refresh(regular_users[0])
    db.refresh(regular_users[1])
    db.refresh(regular_users[2])
    # Create Accounts and tie them to users
    account_1 = models.Account(id=uuid.uuid4(), organization_id=UUID(str(ORG_ID)), name="Account 1")
    account_2 = models.Account(id=uuid.uuid4(), organization_id=UUID(str(ORG_ID)), name="Account 2")
    account_3 = models.Account(id=uuid.uuid4(), organization_id=UUID(str(ORG_ID)), name="Account 3")
    db.add_all([account_1, account_2, account_3])
    db.commit()
    db.refresh(account_1)
    db.refresh(account_2)
    db.refresh(account_3)

    user_account_1_for_superadmin_1 = models.User_Account(user_id=superadmin_1.id, account_id=account_1.id)
    db.add(user_account_1_for_superadmin_1)
    db.commit()

    user_account_2_for_superadmin_1 = models.User_Account(user_id=superadmin_1.id, account_id=account_2.id)
    db.add(user_account_2_for_superadmin_1)
    db.commit()

    user_account_3_for_superadmin_1 = models.User_Account(user_id=superadmin_1.id, account_id=account_3.id)
    db.add(user_account_3_for_superadmin_1)
    db.commit()

    user_account_1_for_superadmin_2 = models.User_Account(user_id=superadmin_2.id, account_id=account_1.id)
    db.add(user_account_1_for_superadmin_2)
    db.commit()

    user_account_2_for_superadmin_2 = models.User_Account(user_id=superadmin_2.id, account_id=account_2.id)
    db.add(user_account_2_for_superadmin_2)
    db.commit()

    user_account_3_for_superadmin_2 = models.User_Account(user_id=superadmin_2.id, account_id=account_3.id)
    db.add(user_account_3_for_superadmin_2)
    db.commit()

    user_account_3_for_admin = models.User_Account(user_id=regular_users[2].id, account_id=account_3.id, is_admin=True)
    db.add(user_account_3_for_admin)
    db.commit()

    # Add other users as members of Account 3
    user_account_3_for_user0 = models.User_Account(user_id=regular_users[0].id, account_id=account_3.id)
    db.add(user_account_3_for_user0)
    db.commit()

    user_account_3_for_user1 = models.User_Account(user_id=regular_users[1].id, account_id=account_3.id)
    db.add(user_account_3_for_user1)
    db.commit()


    # Create Projects and tie them to accounts and owners
    project_1 = models.Project(id=uuid.uuid4(), account_id=account_1.id, creator=superadmin_1.email, name="Project 1")
    project_2 = models.Project(id=uuid.uuid4(), account_id=account_2.id, creator=superadmin_2.email, name="Project 2")
    project_3 = models.Project(id=uuid.uuid4(), account_id=account_3.id, creator=regular_users[2].email, name="Project 3")
    project_1_child1 = models.Project(id=uuid.uuid4(), account_id=account_1.id, creator=superadmin_1.email, parent_project_id = project_1.id, name="Project-1_Child-1")
    project_1_child2 = models.Project(id=uuid.uuid4(), account_id=account_1.id, creator=superadmin_1.email, parent_project_id = project_1.id, name="Project-1_Child-2")
    project_2_child1 = models.Project(id=uuid.uuid4(), account_id=account_2.id, creator=superadmin_2.email, parent_project_id = project_2.id, name="Project-2_Child-1")
    project_2_child2 = models.Project(id=uuid.uuid4(), account_id=account_2.id, creator=superadmin_2.email, parent_project_id = project_2.id, name="Project-2_Child-2")
    project_3_child1 = models.Project(id=uuid.uuid4(), account_id=account_3.id, creator=regular_users[0].email, parent_project_id = project_3.id, name="Project-3_Child-1")
    project_3_child2 = models.Project(id=uuid.uuid4(), account_id=account_3.id, creator=regular_users[1].email, parent_project_id = project_3.id, name="Project-3_Child-2")
    project_3_child3 = models.Project(id=uuid.uuid4(), account_id=account_3.id, creator=regular_users[1].email, parent_project_id = project_3.id, name="Project-3_Child-3")

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
    user_project_1 = models.User_Project(user_id=superadmin_1.id, project_id=project_1.id, is_admin=True, permission_overrides = permission_schemas.ProjectScopedRBACPermission.create("Deny").dict())
    user_project_1_child1 = models.User_Project(user_id=superadmin_1.id, project_id=project_1_child1.id, is_admin=True, permission_overrides = permission_schemas.ProjectScopedRBACPermission.create("Deny").dict())
    user_project_1_child2 = models.User_Project(user_id=superadmin_1.id, project_id=project_1_child2.id, is_admin=True, permission_overrides = permission_schemas.ProjectScopedRBACPermission.create("Deny").dict())

    user_project_2 = models.User_Project(user_id=superadmin_2.id, project_id=project_2.id, is_admin=True, permission_overrides = permission_schemas.ProjectScopedRBACPermission.create("Deny").dict())
    user_project_2_child1 = models.User_Project(user_id=superadmin_2.id, project_id=project_2_child1.id, is_admin=True, permission_overrides = permission_schemas.ProjectScopedRBACPermission.create("Deny").dict())
    user_project_2_child2 = models.User_Project(user_id=superadmin_2.id, project_id=project_2_child2.id, is_admin=True, permission_overrides = permission_schemas.ProjectScopedRBACPermission.create("Deny").dict())

    user_project_3 = models.User_Project(user_id=regular_users[2].id, project_id=project_3.id, is_admin=True, permission_overrides = permission_schemas.ProjectScopedRBACPermission.create("Deny").dict())
    user_project_3_for_user_0 = models.User_Project(user_id=regular_users[0].id, project_id=project_3.id, permission_overrides = permission_schemas.ProjectScopedRBACPermission.create("Deny").dict())
    user_project_3_child1_for_user_0 = models.User_Project(user_id=regular_users[0].id, project_id=project_3_child1.id, permission_overrides = permission_schemas.ProjectScopedRBACPermission.create("Deny").dict())
    user_project_3_child2_for_user_0 = models.User_Project(user_id=regular_users[0].id, project_id=project_3_child2.id, permission_overrides = permission_schemas.ProjectScopedRBACPermission.create("Deny").dict())

    user_project_3_for_user_1 = models.User_Project(user_id=regular_users[1].id, project_id=project_3.id, permission_overrides = permission_schemas.ProjectScopedRBACPermission.create("Deny").dict())
    user_project_3_child1_for_user_1 = models.User_Project(user_id=regular_users[1].id, project_id=project_3_child1.id, permission_overrides = permission_schemas.ProjectScopedRBACPermission.create("Deny").dict())
    user_project_3_child2_for_user_1 = models.User_Project(user_id=regular_users[1].id, project_id=project_3_child2.id, permission_overrides = permission_schemas.ProjectScopedRBACPermission.create("Deny").dict())
    user_project_3_child3_for_user_1 = models.User_Project(user_id=regular_users[1].id, project_id=project_3_child3.id, permission_overrides = permission_schemas.ProjectScopedRBACPermission.create("Deny").dict())

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
    data_scientist_permissions = permission_schemas.AccountScopedRBACPermission.create("Deny") # create with all denied permissions

    data_scientist_permissions.ENTITY_Project.ACTION_CREATE = 'Allow'

    data_scientist_permissions.ENTITY_Application.TYPENAMES_applicationType.TYPEVALUES_ingest.ACTION_READ = 'Allow'
    data_scientist_permissions.ENTITY_Application.TYPENAMES_applicationType.TYPEVALUES_ingest.ENTITY_Configuration.ACTION_READ = 'Allow'
    data_scientist_permissions.ENTITY_Application.TYPENAMES_applicationType.TYPEVALUES_ingest.ENTITY_Configuration.ACTION_CREATE = 'Allow'
    data_scientist_permissions.ENTITY_Application.TYPENAMES_applicationType.TYPEVALUES_ingest.ENTITY_Configuration.ACTION_UPDATE = 'Allow'

    data_scientist_permissions.ENTITY_Application.TYPENAMES_applicationType.TYPEVALUES_preprocess.ACTION_READ = 'Allow'
    data_scientist_permissions.ENTITY_Application.TYPENAMES_applicationType.TYPEVALUES_preprocess.ENTITY_Configuration.ACTION_READ = 'Allow'
    data_scientist_permissions.ENTITY_Application.TYPENAMES_applicationType.TYPEVALUES_preprocess.ENTITY_Configuration.ACTION_CREATE = 'Allow'
    data_scientist_permissions.ENTITY_Application.TYPENAMES_applicationType.TYPEVALUES_preprocess.ENTITY_Configuration.ACTION_UPDATE = 'Allow'

    # ML Engineer account-scoped permissions:
    ml_engineer_permissions = permission_schemas.AccountScopedRBACPermission.create("Deny")

    ml_engineer_permissions.ENTITY_Project.ACTION_READ = 'Allow'
    ml_engineer_permissions.ENTITY_Project.ACTION_CREATE = 'Allow'

    ml_engineer_permissions.ENTITY_Application.TYPENAMES_applicationType.TYPEVALUES_ingest.ACTION_READ = 'Allow'
    ml_engineer_permissions.ENTITY_Application.TYPENAMES_applicationType.TYPEVALUES_ingest.ENTITY_Configuration.ACTION_READ = 'Allow'
    ml_engineer_permissions.ENTITY_Application.TYPENAMES_applicationType.TYPEVALUES_ingest.ENTITY_Configuration.ACTION_CREATE = 'Allow'
    ml_engineer_permissions.ENTITY_Application.TYPENAMES_applicationType.TYPEVALUES_ingest.ENTITY_Configuration.ACTION_UPDATE = 'Allow'

    ml_engineer_permissions.ENTITY_Application.TYPENAMES_applicationType.TYPEVALUES_preprocess.ACTION_READ = 'Allow'
    ml_engineer_permissions.ENTITY_Application.TYPENAMES_applicationType.TYPEVALUES_preprocess.ENTITY_Configuration.ACTION_READ = 'Allow'
    ml_engineer_permissions.ENTITY_Application.TYPENAMES_applicationType.TYPEVALUES_preprocess.ENTITY_Configuration.ACTION_CREATE = 'Allow'
    ml_engineer_permissions.ENTITY_Application.TYPENAMES_applicationType.TYPEVALUES_preprocess.ENTITY_Configuration.ACTION_UPDATE = 'Allow'

    # ML OPS account-scoped permissions:
    ml_ops_permissions = permission_schemas.AccountScopedRBACPermission.create("Deny")

    ml_engineer_permissions.ENTITY_Project.ACTION_READ = 'Allow'
    ml_engineer_permissions.ENTITY_Project.ACTION_CREATE = 'Allow'

    ml_engineer_permissions.ENTITY_Application.TYPENAMES_applicationType.TYPEVALUES_ingest.ACTION_READ = 'Allow'
    ml_engineer_permissions.ENTITY_Application.TYPENAMES_applicationType.TYPEVALUES_ingest.ENTITY_Configuration.ACTION_READ = 'Allow'
    ml_engineer_permissions.ENTITY_Application.TYPENAMES_applicationType.TYPEVALUES_ingest.ENTITY_Configuration.ACTION_CREATE = 'Allow'
    ml_engineer_permissions.ENTITY_Application.TYPENAMES_applicationType.TYPEVALUES_ingest.ENTITY_Configuration.ACTION_UPDATE = 'Allow'

    ml_engineer_permissions.ENTITY_Application.TYPENAMES_applicationType.TYPEVALUES_preprocess.ACTION_READ = 'Allow'
    ml_engineer_permissions.ENTITY_Application.TYPENAMES_applicationType.TYPEVALUES_preprocess.ENTITY_Configuration.ACTION_READ = 'Allow'
    ml_engineer_permissions.ENTITY_Application.TYPENAMES_applicationType.TYPEVALUES_preprocess.ENTITY_Configuration.ACTION_CREATE = 'Allow'
    ml_engineer_permissions.ENTITY_Application.TYPENAMES_applicationType.TYPEVALUES_preprocess.ENTITY_Configuration.ACTION_UPDATE = 'Allow'

    # # Create Roles
    data_scientist_role = models.Role(name="Data Scientist", permissions=data_scientist_permissions.dict())
    ml_engineer_role = models.Role(name="ML Engineer", permissions=ml_engineer_permissions.dict())
    ml_ops_role = models.Role(name="ML OPS", permissions=ml_ops_permissions.dict())

    account_scoped_roles = [data_scientist_role, ml_engineer_role, ml_ops_role]
    for role in account_scoped_roles:
        db.add(role)
        db.commit()
        db.refresh(role)
    
    # # Role-User_Account Association
    role_user_account_1 = models.Role_User_Account(role_id=data_scientist_role.id, user_account_id=user_account_3_for_user0.id)
    role_user_account_2 = models.Role_User_Account(role_id=ml_engineer_role.id, user_account_id=user_account_3_for_user0.id)
    role_user_account_3 = models.Role_User_Account(role_id=ml_ops_role.id, user_account_id=user_account_3_for_user1.id)

    role_user_account_associations = [role_user_account_1, role_user_account_2, role_user_account_3]
    for role_user_account_association in role_user_account_associations:
        db.add(role_user_account_association)
        db.commit()
        db.refresh(role_user_account_association)

    # # Adding Project-specific permission overrides:

    project_permissions_overrides = permission_schemas.ProjectScopedRBACPermission.create("Deny") # all denied permissions
    project_permissions_overrides.ENTITY_Project.ACTION_CREATE = 'Allow'

    user_project_id_to_update = user_project_3_for_user_0.id

    # # Perform the update
    db.execute(
        update(models.User_Project). 
        where(models.User_Project.id == user_project_id_to_update).
        values(permission_overrides= project_permissions_overrides.dict())
    )
    db.commit()
    
    #---------------------

    pre_process_pipeline_step_1 = models.PipelineStep(
        title="Dataset Configuration",
        data=[],
        _dependsOn=[],
        id="14fc347b-aa19-4a2a-9d9b-3b3a630c9d5c",
    )
    db.add(pre_process_pipeline_step_1)

    pre_process_pipeline_step_2 = models.PipelineStep(
        title="Document Segmentation",
        data=[],
        _dependsOn=[],
        id="647427ef-2654-4585-8aaa-e03c66915c91",
    )
    pre_process_pipeline_step_2._dependsOn.append(pre_process_pipeline_step_1)
    db.add(pre_process_pipeline_step_2)

    pre_process_pipeline_step_3 = models.PipelineStep(
        title="Document Vectorization",
        data=[],
        _dependsOn=[],
        id="19feed33-c233-44c4-83ea-8d5dd54e7ec1",
    )
    pre_process_pipeline_step_3._dependsOn.append(pre_process_pipeline_step_2)
    db.add(pre_process_pipeline_step_3)

    pre_process_pipeline_step_4 = models.PipelineStep(
        title="Vector DB",
        data=[],
        _dependsOn=[],
        id="547b4b9d-7ea5-414a-a2bf-a691c3e97954",
    )
    pre_process_pipeline_step_4._dependsOn.append(pre_process_pipeline_step_3)
    db.add(pre_process_pipeline_step_4)

    ingest_pipeline_step_1 = models.PipelineStep(
        title="Data Source Configuration",
        data=[],
        _dependsOn=[],
        id="9966b76c-5a5a-4eeb-924f-bd5983b4610a",
    )
    db.add(ingest_pipeline_step_1)

    ingest_pipeline_step_2 = models.PipelineStep(
        title="Worker Process",
        data=[],
        _dependsOn=[],
        id="9fb4ebe8-a679-40a7-90a7-e14f26e6f397",
    )
    ingest_pipeline_step_2._dependsOn.append(ingest_pipeline_step_1)
    db.add(ingest_pipeline_step_2)

    ingest_pipeline_step_3 = models.PipelineStep(
        title="Data Lake Storage",
        data=[],
        _dependsOn=[],
        id="f3427f14-ac54-4bb8-b681-5e2d3e9bbad8",
    )
    ingest_pipeline_step_3._dependsOn.append(ingest_pipeline_step_2)
    db.add(ingest_pipeline_step_3)

    db.commit()
    db.refresh(pre_process_pipeline_step_1)
    db.refresh(pre_process_pipeline_step_2)
    db.refresh(pre_process_pipeline_step_3)
    db.refresh(pre_process_pipeline_step_4)
    db.refresh(ingest_pipeline_step_1)
    db.refresh(ingest_pipeline_step_2)
    db.refresh(ingest_pipeline_step_3)

    pre_process_pipeline_1 = models.Pipeline(
        label="Documents",
        id="8470d675-6752-4446-8f07-fe7a99949e42",
        entry=pre_process_pipeline_step_1.id,
        exit=pre_process_pipeline_step_4.id,
        steps=[
            pre_process_pipeline_step_1,
            pre_process_pipeline_step_2,
            pre_process_pipeline_step_3,
            pre_process_pipeline_step_4,
        ],
    )
    db.add(pre_process_pipeline_1)

    ingest_pipeline_1 = models.Pipeline(
        label="S3 Ingest",
        id="a141911b-7430-44a5-915e-4a4e469799ae",
        entry=ingest_pipeline_step_1.id,
        exit=ingest_pipeline_step_3.id,
        steps=[
            ingest_pipeline_step_1,
            ingest_pipeline_step_2,
            ingest_pipeline_step_3,
        ],
    )
    db.add(ingest_pipeline_1)

    db.commit()
    db.refresh(pre_process_pipeline_1)
    db.refresh(ingest_pipeline_1)

    pre_process_application_1 = models.Application(
        id="2",
        title="Preprocess Pipelines",
        creator="elevAIte",
        applicationType= connector_schemas.ApplicationType.PREPROCESS,
        description="Preprocess ingested data",
        version="1.0",
        icon="",
        instances=[],
        pipelines=[pre_process_pipeline_1],
    )
    db.add(pre_process_application_1)

    ingest_application_1 = models.Application(
        id="1",
        title="S3 Connector",
        creator="elevAIte 2",
        applicationType=connector_schemas.ApplicationType.INGEST,
        description="Ingest data from an S3 bucket",
        version="1.0",
        icon="",
        instances=[],
        pipelines=[ingest_pipeline_1],
    )
    db.add(ingest_application_1)

    db.commit()
    db.refresh(pre_process_application_1)
    db.refresh(ingest_application_1)

    _source = models.DatasetTag(name="Source")
    db.add(_source)
    _evaluation = models.DatasetTag(name="Evaluation")
    db.add(_evaluation)
    _training = models.DatasetTag(name="Training")
    db.add(_training)
    db.commit()

    config_ingest = models.Configuration(
        applicationId="1", 
        name="Ingest Configuration Example",
        isTemplate=False,
        raw={"key": "value", "purpose": "Demonstrate ingest configuration"}
    )

    config_preprocess = models.Configuration(
        applicationId="2",  
        name="Preprocess Configuration Example",
        isTemplate=False,
        raw={"key": "value", "purpose": "Demonstrate preprocess configuration"}
    )

    db.add(config_ingest)
    db.add(config_preprocess)
    db.commit()

    db.refresh(config_ingest)
    db.refresh(config_preprocess)

    # Create datasets, each linked to one of the projects
    dataset_1 = models.Dataset(
        id=uuid.uuid4(),
        name="Dataset 1",
        projectId=project_1.id
    )

    dataset_2 = models.Dataset(
        id=uuid.uuid4(),
        name="Dataset 2",
        projectId=project_2.id
    )

    dataset_3 = models.Dataset(
        id=uuid.uuid4(),
        name="Dataset 3",
        projectId=project_3.id
    )

    db.add(dataset_1)
    db.add(dataset_2)
    db.add(dataset_3)
    db.commit()

    db.refresh(dataset_1)
    db.refresh(dataset_2)
    db.refresh(dataset_3)

    instance_1 = models.Instance(
        id="2aaa0c19-53a0-4f13-94d3-0e6845f36ccd",
        creator="User One",
        name="Instance 1 Name",
        comment="This is a comment for Instance 1",
        startTime=str(get_utc_datetime()),
        endTime=None,  
        status=instance_schemas.InstanceStatus.RUNNING,  
        datasetId=dataset_1.id, 
        selectedPipelineId=ingest_pipeline_1.id,  
        applicationId=ingest_application_1.id,  
        configurationId=config_ingest.id, 
        projectId=project_1.id,  
        configurationRaw={"key": "value"}  
    )

    instance_2 = models.Instance(
        id="2aaa0c19-53a0-4f13-94d3-0e6845f36cce",
        creator="User Two",
        name="Instance 2 Name",
        comment=None,  
        startTime=None,
        endTime=None, 
        status=instance_schemas.InstanceStatus.COMPLETED,
        datasetId=dataset_2.id,
        selectedPipelineId=pre_process_pipeline_1.id,
        applicationId=pre_process_application_1.id,
        configurationId=config_preprocess.id,
        projectId=project_2.id,
        configurationRaw={"anotherKey": "anotherValue"}
    )

    # Add instances to the session and commit
    db.add(instance_1)
    db.add(instance_2)
    db.commit()

    # Optional: refresh from the DB to confirm
    db.refresh(instance_1)
    db.refresh(instance_2)

    chart_data_1 = models.InstanceChartData(
        instanceId=instance_1.id, 
        totalItems=100,  
        ingestedItems=80,
        avgSize=150,
        totalSize=15000,
        ingestedSize=12000,
        ingestedChunks=40
    )

    chart_data_2 = models.InstanceChartData(
        instanceId=instance_2.id,  
        totalItems=200,  
        ingestedItems=150,
        avgSize=120,
        totalSize=24000,
        ingestedSize=18000,
        ingestedChunks=60
    )

    db.add(chart_data_1)
    db.add(chart_data_2)
    db.commit()

    db.refresh(chart_data_1)
    db.refresh(chart_data_2)


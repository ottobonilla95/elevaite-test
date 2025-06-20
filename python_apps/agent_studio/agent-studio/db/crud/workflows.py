
import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy.orm import Session

from ..models import Workflow, WorkflowAgent, WorkflowConnection, WorkflowDeployment
from ..schemas import (
    WorkflowCreate, 
    WorkflowUpdate,
    WorkflowAgentCreate,
    WorkflowAgentUpdate,
    WorkflowConnectionCreate,
    WorkflowConnectionUpdate,
    WorkflowDeploymentCreate,
    WorkflowDeploymentUpdate,
)

def create_workflow(db: Session, workflow: WorkflowCreate) -> Workflow:
    db_workflow = Workflow(
        name=workflow.name,
        description=workflow.description,
        version=workflow.version,
        configuration=workflow.configuration,
        created_by=workflow.created_by,
        is_active=workflow.is_active,
        tags=workflow.tags,
    )
    db.add(db_workflow)
    db.commit()
    db.refresh(db_workflow)
    return db_workflow

def get_workflow(db: Session, workflow_id: uuid.UUID) -> Optional[Workflow]:
    return db.query(Workflow).filter(Workflow.workflow_id == workflow_id).first()

def get_workflow_by_id(db: Session, workflow_id: uuid.UUID) -> Optional[Workflow]:
    return get_workflow(db, workflow_id)

def get_workflow_by_name(db: Session, name: str, version: Optional[str] = None) -> Optional[Workflow]:
    query = db.query(Workflow).filter(Workflow.name == name)
    if version:
        query = query.filter(Workflow.version == version)
    return query.first()

def get_workflows(db: Session, skip: int = 0, limit: int = 100, is_active: Optional[bool] = None) -> List[Workflow]:
    query = db.query(Workflow)
    if is_active is not None:
        query = query.filter(Workflow.is_active == is_active)
    return query.offset(skip).limit(limit).all()

def get_deployed_workflows(db: Session) -> List[Workflow]:
    return db.query(Workflow).filter(Workflow.is_deployed == True).all()

def update_workflow(db: Session, workflow_id: uuid.UUID, workflow_update: WorkflowUpdate) -> Optional[Workflow]:
    db_workflow = get_workflow(db, workflow_id)
    if not db_workflow:
        return None

    update_data = workflow_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_workflow, key, value)

    db_workflow.updated_at = datetime.now()
    db.commit()
    db.refresh(db_workflow)
    return db_workflow

def delete_workflow(db: Session, workflow_id: uuid.UUID) -> bool:
    db_workflow = get_workflow(db, workflow_id)
    if not db_workflow:
        return False

    db.delete(db_workflow)
    db.commit()
    return True

def create_workflow_agent(db: Session, workflow_agent: WorkflowAgentCreate) -> WorkflowAgent:
    db_workflow_agent = WorkflowAgent(
        workflow_id=workflow_agent.workflow_id,
        agent_id=workflow_agent.agent_id,
        position_x=workflow_agent.position_x,
        position_y=workflow_agent.position_y,
        node_id=workflow_agent.node_id,
        agent_config=workflow_agent.agent_config,
    )
    db.add(db_workflow_agent)
    db.commit()
    db.refresh(db_workflow_agent)
    return db_workflow_agent

def get_workflow_agents(db: Session, workflow_id: uuid.UUID) -> List[WorkflowAgent]:
    return db.query(WorkflowAgent).filter(WorkflowAgent.workflow_id == workflow_id).all()

def get_workflow_agent(db: Session, workflow_id: uuid.UUID, agent_id: uuid.UUID) -> Optional[WorkflowAgent]:
    return db.query(WorkflowAgent).filter(
        WorkflowAgent.workflow_id == workflow_id,
        WorkflowAgent.agent_id == agent_id
    ).first()

def update_workflow_agent(db: Session, workflow_id: uuid.UUID, agent_id: uuid.UUID, update_data: WorkflowAgentUpdate) -> Optional[WorkflowAgent]:
    db_workflow_agent = get_workflow_agent(db, workflow_id, agent_id)
    if not db_workflow_agent:
        return None

    update_dict = update_data.model_dump(exclude_unset=True)
    for key, value in update_dict.items():
        setattr(db_workflow_agent, key, value)

    db.commit()
    db.refresh(db_workflow_agent)
    return db_workflow_agent

def delete_workflow_agent(db: Session, workflow_id: uuid.UUID, agent_id: uuid.UUID) -> bool:
    db_workflow_agent = get_workflow_agent(db, workflow_id, agent_id)
    if not db_workflow_agent:
        return False

    db.delete(db_workflow_agent)
    db.commit()
    return True

def create_workflow_connection(db: Session, connection: WorkflowConnectionCreate) -> WorkflowConnection:
    db_connection = WorkflowConnection(
        workflow_id=connection.workflow_id,
        source_agent_id=connection.source_agent_id,
        target_agent_id=connection.target_agent_id,
        connection_type=connection.connection_type,
        conditions=connection.conditions,
        priority=connection.priority,
        source_handle=connection.source_handle,
        target_handle=connection.target_handle,
    )
    db.add(db_connection)
    db.commit()
    db.refresh(db_connection)
    return db_connection

def get_workflow_connections(db: Session, workflow_id: uuid.UUID) -> List[WorkflowConnection]:
    return db.query(WorkflowConnection).filter(WorkflowConnection.workflow_id == workflow_id).all()

def get_workflow_connection(db: Session, workflow_id: uuid.UUID, source_agent_id: uuid.UUID, target_agent_id: uuid.UUID) -> Optional[WorkflowConnection]:
    return db.query(WorkflowConnection).filter(
        WorkflowConnection.workflow_id == workflow_id,
        WorkflowConnection.source_agent_id == source_agent_id,
        WorkflowConnection.target_agent_id == target_agent_id
    ).first()

def update_workflow_connection(db: Session, connection_id: int, update_data: WorkflowConnectionUpdate) -> Optional[WorkflowConnection]:
    db_connection = db.query(WorkflowConnection).filter(WorkflowConnection.id == connection_id).first()
    if not db_connection:
        return None

    update_dict = update_data.model_dump(exclude_unset=True)
    for key, value in update_dict.items():
        setattr(db_connection, key, value)

    db.commit()
    db.refresh(db_connection)
    return db_connection

def delete_workflow_connection(db: Session, workflow_id: uuid.UUID, source_agent_id: uuid.UUID, target_agent_id: uuid.UUID) -> bool:
    db_connection = get_workflow_connection(db, workflow_id, source_agent_id, target_agent_id)
    if not db_connection:
        return False

    db.delete(db_connection)
    db.commit()
    return True

def create_workflow_deployment(db: Session, deployment: WorkflowDeploymentCreate) -> WorkflowDeployment:
    db_deployment = WorkflowDeployment(
        workflow_id=deployment.workflow_id,
        environment=deployment.environment,
        deployment_name=deployment.deployment_name,
        deployed_by=deployment.deployed_by,
        runtime_config=deployment.runtime_config,
    )
    db.add(db_deployment)
    db.commit()
    db.refresh(db_deployment)
    return db_deployment

def get_workflow_deployment(db: Session, deployment_id: uuid.UUID) -> Optional[WorkflowDeployment]:
    return db.query(WorkflowDeployment).filter(WorkflowDeployment.deployment_id == deployment_id).first()

def get_workflow_deployment_by_name(db: Session, deployment_name: str, environment: str = "production") -> Optional[WorkflowDeployment]:
    return db.query(WorkflowDeployment).filter(
        WorkflowDeployment.deployment_name == deployment_name,
        WorkflowDeployment.environment == environment
    ).first()

def get_workflow_deployments(db: Session, workflow_id: Optional[uuid.UUID] = None, environment: Optional[str] = None, status: Optional[str] = None) -> List[WorkflowDeployment]:
    query = db.query(WorkflowDeployment)
    if workflow_id:
        query = query.filter(WorkflowDeployment.workflow_id == workflow_id)
    if environment:
        query = query.filter(WorkflowDeployment.environment == environment)
    if status:
        query = query.filter(WorkflowDeployment.status == status)
    return query.all()

def get_active_workflow_deployments(db: Session) -> List[WorkflowDeployment]:
    return db.query(WorkflowDeployment).filter(WorkflowDeployment.status == "active").all()

def update_workflow_deployment(db: Session, deployment_id: uuid.UUID, update_data: WorkflowDeploymentUpdate) -> Optional[WorkflowDeployment]:
    db_deployment = get_workflow_deployment(db, deployment_id)
    if not db_deployment:
        return None

    update_dict = update_data.model_dump(exclude_unset=True)
    for key, value in update_dict.items():
        setattr(db_deployment, key, value)

    db.commit()
    db.refresh(db_deployment)
    return db_deployment

def delete_workflow_deployment(db: Session, deployment_id: uuid.UUID) -> bool:
    db_deployment = get_workflow_deployment(db, deployment_id)
    if not db_deployment:
        return False

    db.delete(db_deployment)
    db.commit()
    return True

def stop_workflow_deployment(db: Session, deployment_id: uuid.UUID) -> Optional[WorkflowDeployment]:
    db_deployment = get_workflow_deployment(db, deployment_id)
    if not db_deployment:
        return None

    db_deployment.status = "inactive"
    db_deployment.stopped_at = datetime.now()
    db.commit()
    db.refresh(db_deployment)
    return db_deployment

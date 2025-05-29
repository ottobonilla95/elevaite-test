import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from db.database import get_db
from db import crud, schemas
from agents.command_agent import CommandAgent
from agents import agent_schemas
from prompts import command_agent_system_prompt
from datetime import datetime

router = APIRouter(prefix="/workflows", tags=["workflows"])

# Global variable to store active workflow deployments
ACTIVE_WORKFLOWS = {}


@router.post("/", response_model=schemas.WorkflowResponse)
def create_workflow(
    workflow: schemas.WorkflowCreate,
    db: Session = Depends(get_db)
):
    """Create a new workflow"""
    try:
        # Check if workflow with same name and version already exists
        existing = crud.get_workflow_by_name(db, workflow.name, workflow.version)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Workflow '{workflow.name}' version '{workflow.version}' already exists"
            )
        
        db_workflow = crud.create_workflow(db, workflow)
        return db_workflow
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating workflow: {str(e)}"
        )


@router.get("/", response_model=List[schemas.WorkflowResponse])
def list_workflows(
    skip: int = 0,
    limit: int = 100,
    is_active: Optional[bool] = None,
    is_deployed: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    """List all workflows with optional filters"""
    workflows = crud.get_workflows(db, skip=skip, limit=limit, is_active=is_active, is_deployed=is_deployed)
    return workflows


@router.get("/{workflow_id}", response_model=schemas.WorkflowResponse)
def get_workflow(
    workflow_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    """Get a specific workflow by ID"""
    workflow = crud.get_workflow(db, workflow_id)
    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow not found"
        )
    return workflow


@router.put("/{workflow_id}", response_model=schemas.WorkflowResponse)
def update_workflow(
    workflow_id: uuid.UUID,
    workflow_update: schemas.WorkflowUpdate,
    db: Session = Depends(get_db)
):
    """Update a workflow"""
    workflow = crud.update_workflow(db, workflow_id, workflow_update)
    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow not found"
        )
    return workflow


@router.delete("/{workflow_id}")
def delete_workflow(
    workflow_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    """Delete a workflow"""
    success = crud.delete_workflow(db, workflow_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow not found"
        )
    return {"message": "Workflow deleted successfully"}


@router.post("/{workflow_id}/agents", response_model=schemas.WorkflowAgentResponse)
def add_agent_to_workflow(
    workflow_id: uuid.UUID,
    workflow_agent: schemas.WorkflowAgentCreate,
    db: Session = Depends(get_db)
):
    """Add an agent to a workflow"""
    # Verify workflow exists
    workflow = crud.get_workflow(db, workflow_id)
    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow not found"
        )
    
    # Verify agent exists
    agent = crud.get_agent(db, workflow_agent.agent_id)
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found"
        )
    
    # Set workflow_id
    workflow_agent.workflow_id = workflow_id
    
    try:
        db_workflow_agent = crud.create_workflow_agent(db, workflow_agent)
        return db_workflow_agent
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error adding agent to workflow: {str(e)}"
        )


@router.post("/{workflow_id}/connections", response_model=schemas.WorkflowConnectionResponse)
def add_connection_to_workflow(
    workflow_id: uuid.UUID,
    connection: schemas.WorkflowConnectionCreate,
    db: Session = Depends(get_db)
):
    """Add a connection between agents in a workflow"""
    # Verify workflow exists
    workflow = crud.get_workflow(db, workflow_id)
    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow not found"
        )
    
    # Set workflow_id
    connection.workflow_id = workflow_id
    
    try:
        db_connection = crud.create_workflow_connection(db, connection)
        return db_connection
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error adding connection to workflow: {str(e)}"
        )


@router.post("/{workflow_id}/deploy", response_model=schemas.WorkflowDeploymentResponse)
def deploy_workflow(
    workflow_id: uuid.UUID,
    deployment: schemas.WorkflowDeploymentCreate,
    db: Session = Depends(get_db)
):
    """Deploy a workflow"""
    # Verify workflow exists
    workflow = crud.get_workflow(db, workflow_id)
    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow not found"
        )
    
    # Set workflow_id
    deployment.workflow_id = workflow_id
    
    try:
        # Create deployment record
        db_deployment = crud.create_workflow_deployment(db, deployment)
        
        # Build and store the CommandAgent for this deployment
        command_agent = _build_command_agent_from_workflow(db, workflow)
        ACTIVE_WORKFLOWS[deployment.deployment_name] = {
            "command_agent": command_agent,
            "deployment": db_deployment,
            "workflow": workflow
        }
        
        return db_deployment
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deploying workflow: {str(e)}"
        )


@router.get("/deployments/active", response_model=List[schemas.WorkflowDeploymentResponse])
def list_active_deployments(db: Session = Depends(get_db)):
    """List all active workflow deployments"""
    deployments = crud.get_active_workflow_deployments(db)
    return deployments


@router.post("/execute", response_model=schemas.WorkflowExecutionResponse)
def execute_workflow(
    execution_request: schemas.WorkflowExecutionRequest,
    db: Session = Depends(get_db)
):
    """Execute a deployed workflow"""
    deployment = None
    
    if execution_request.deployment_name:
        # Find by deployment name
        if execution_request.deployment_name not in ACTIVE_WORKFLOWS:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No active deployment found with name '{execution_request.deployment_name}'"
            )
        deployment_info = ACTIVE_WORKFLOWS[execution_request.deployment_name]
        command_agent = deployment_info["command_agent"]
        deployment = deployment_info["deployment"]
    
    elif execution_request.workflow_id:
        # Find by workflow ID - get the latest active deployment
        deployment = crud.get_workflow_deployment_by_name(db, f"workflow_{execution_request.workflow_id}", "production")
        if not deployment or deployment.status != "active":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No active deployment found for this workflow"
            )
        
        # Build command agent if not in memory
        workflow = crud.get_workflow(db, execution_request.workflow_id)
        command_agent = _build_command_agent_from_workflow(db, workflow)
    
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either workflow_id or deployment_name must be provided"
        )
    
    try:
        # Execute the workflow
        result = command_agent.execute(query=execution_request.query)
        
        # Update deployment statistics
        deployment.execution_count += 1
        deployment.last_executed = datetime.now()
        db.commit()
        
        return schemas.WorkflowExecutionResponse(
            status="success",
            response=result,
            workflow_id=deployment.workflow_id,
            deployment_id=deployment.deployment_id
        )
    
    except Exception as e:
        # Update error statistics
        deployment.error_count += 1
        deployment.last_error = str(e)
        db.commit()
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error executing workflow: {str(e)}"
        )


def _build_command_agent_from_workflow(db: Session, workflow) -> CommandAgent:
    """Build a CommandAgent from a workflow configuration"""
    # Get workflow agents and connections
    workflow_agents = crud.get_workflow_agents(db, workflow.workflow_id)
    workflow_connections = crud.get_workflow_connections(db, workflow.workflow_id)
    
    # Build functions list for CommandAgent
    functions = []
    for connection in workflow_connections:
        source_agent = crud.get_agent(db, connection.source_agent_id)
        target_agent = crud.get_agent(db, connection.target_agent_id)
        
        if source_agent and source_agent.name == "CommandAgent":
            if target_agent.name in agent_schemas:
                functions.append(agent_schemas[target_agent.name])
    
    # Create CommandAgent
    command_agent = CommandAgent(
        name=f"WorkflowCommandAgent_{workflow.name}",
        agent_id=uuid.uuid4(),
        system_prompt=command_agent_system_prompt,
        persona="Command Agent",
        functions=functions,
        routing_options={
            "continue": "If you think you can't answer the query, you can continue to the next tool or do some reasoning.",
            "respond": "If you think you have the answer, you can stop here.",
            "give_up": "If you think you can't answer the query, you can give up and let the user know.",
        },
        short_term_memory=True,
        long_term_memory=False,
        reasoning=False,
        input_type=["text", "voice"],
        output_type=["text", "voice"],
        response_type="json",
        max_retries=5,
        timeout=None,
        deployed=True,
        status="active",
        priority=None,
        failure_strategies=["retry", "escalate"],
        session_id=None,
        last_active=datetime.now(),
        collaboration_mode="single",
    )
    
    return command_agent

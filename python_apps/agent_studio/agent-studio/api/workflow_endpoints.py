import uuid
import json
import asyncio
import time
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from db.database import get_db
from db import crud, schemas, models
from agents.command_agent import CommandAgent
from agents.agent_base import Agent

# from agents import agent_schemas  # Commented out - Redis dependent
from prompts import command_agent_system_prompt
from services.workflow_service import workflow_service
from datetime import datetime

# from utils import agent_schema
import inspect
from typing import Any, Callable, Dict, List, Protocol, Union, cast, get_type_hints

router = APIRouter(prefix="/api/workflows", tags=["workflows"])

# Global variable to store active workflow deployments
ACTIVE_WORKFLOWS = {}


@router.post("/", response_model=schemas.WorkflowResponse)
def create_workflow(workflow: schemas.WorkflowCreate, db: Session = Depends(get_db)):
    """Create a new workflow with agents and connections"""
    try:
        # Check if workflow with same name and version already exists
        existing = crud.workflows.get_workflow_by_name(
            db, workflow.name, workflow.version
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Workflow '{workflow.name}' version '{workflow.version}' already exists",
            )

        # Create the workflow
        db_workflow = crud.create_workflow(db, workflow)

        # Process agents from configuration
        agents_config = workflow.configuration.get("agents", [])
        for agent_config in agents_config:
            agent_type = agent_config.get("agent_type", "")

            # Find the agent by type/name
            if agent_type == "ToshibaAgent":
                agent = crud.get_agent_by_name(db, "ToshibaAgent")
            elif agent_type == "CommandAgent":
                agent = crud.get_agent_by_name(db, "CommandAgent")
            elif agent_type == "WebAgent":
                agent = crud.get_agent_by_name(db, "WebAgent")
            elif agent_type == "DataAgent":
                agent = crud.get_agent_by_name(db, "DataAgent")
            elif agent_type == "APIAgent":
                agent = crud.get_agent_by_name(db, "APIAgent")
            else:
                # Try to find by agent_id if provided
                agent_id = agent_config.get("agent_id")
                if agent_id:
                    try:
                        agent = crud.get_agent(db, uuid.UUID(agent_id))
                    except (ValueError, TypeError):
                        agent = None
                else:
                    agent = None

            if agent:
                # Create workflow_agent entry
                position = agent_config.get("position", {})
                workflow_agent_data = schemas.WorkflowAgentCreate(
                    workflow_id=db_workflow.workflow_id,
                    agent_id=agent.agent_id,
                    position_x=position.get("x", 0),
                    position_y=position.get("y", 0),
                    node_id=agent_config.get("agent_id", str(agent.agent_id)),
                    agent_config=agent_config.get("config", {}),
                )
                crud.create_workflow_agent(db, workflow_agent_data)

        # Process connections from configuration
        connections_config = workflow.configuration.get("connections", [])
        for connection_config in connections_config:
            source_agent_id = connection_config.get("source_agent_id")
            target_agent_id = connection_config.get("target_agent_id")

            if source_agent_id and target_agent_id:
                try:
                    connection_data = schemas.WorkflowConnectionCreate(
                        workflow_id=db_workflow.workflow_id,
                        source_agent_id=uuid.UUID(source_agent_id),
                        target_agent_id=uuid.UUID(target_agent_id),
                        connection_type=connection_config.get(
                            "connection_type", "default"
                        ),
                        conditions=connection_config.get("conditions"),
                        priority=connection_config.get("priority", 0),
                        source_handle=connection_config.get("source_handle"),
                        target_handle=connection_config.get("target_handle"),
                    )
                    crud.create_workflow_connection(db, connection_data)
                except (ValueError, TypeError) as e:
                    # Skip invalid connections
                    continue

        # Return the workflow with populated relationships
        return get_workflow(db_workflow.workflow_id, db)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating workflow: {str(e)}",
        )


@router.get("/", response_model=List[schemas.WorkflowResponse])
def list_workflows(
    skip: int = 0,
    limit: int = 100,
    is_active: Optional[bool] = None,
    is_deployed: Optional[bool] = None,
    db: Session = Depends(get_db),
):
    """List all workflows with optional filters"""
    workflows = crud.get_workflows(
        db, skip=skip, limit=limit, is_active=is_active, is_deployed=is_deployed
    )
    return workflows


@router.get("/{workflow_id}", response_model=schemas.WorkflowResponse)
def get_workflow(workflow_id: uuid.UUID, db: Session = Depends(get_db)):
    """Get a specific workflow by ID with all related data"""
    workflow = crud.get_workflow(db, workflow_id)
    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Workflow not found"
        )

    # Load related data
    workflow_agents = crud.get_workflow_agents(db, workflow_id)
    workflow_connections = crud.get_workflow_connections(db, workflow_id)

    # Convert to response format with relationships
    workflow_dict = {
        **workflow.__dict__,
        "workflow_agents": workflow_agents,
        "workflow_connections": workflow_connections,
        "workflow_deployments": [],  # Add deployments if needed
    }

    return workflow_dict


@router.put("/{workflow_id}", response_model=schemas.WorkflowResponse)
def update_workflow(
    workflow_id: uuid.UUID,
    workflow_update: schemas.WorkflowUpdate,
    db: Session = Depends(get_db),
):
    """Update a workflow"""
    workflow = crud.update_workflow(db, workflow_id, workflow_update)
    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Workflow not found"
        )
    return workflow


@router.delete("/{workflow_id}")
def delete_workflow(workflow_id: uuid.UUID, db: Session = Depends(get_db)):
    """Delete a workflow"""
    success = crud.delete_workflow(db, workflow_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Workflow not found"
        )
    return {"message": "Workflow deleted successfully"}


@router.post("/{workflow_id}/agents", response_model=schemas.WorkflowAgentResponse)
def add_agent_to_workflow(
    workflow_id: uuid.UUID,
    workflow_agent: schemas.WorkflowAgentCreate,
    db: Session = Depends(get_db),
):
    """Add an agent to a workflow"""
    # Verify workflow exists
    workflow = crud.get_workflow(db, workflow_id)
    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Workflow not found"
        )

    # Verify agent exists
    agent = crud.get_agent(db, workflow_agent.agent_id)
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found"
        )

    # Set workflow_id
    workflow_agent.workflow_id = workflow_id

    try:
        db_workflow_agent = crud.create_workflow_agent(db, workflow_agent)
        return db_workflow_agent
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error adding agent to workflow: {str(e)}",
        )


@router.post(
    "/{workflow_id}/connections", response_model=schemas.WorkflowConnectionResponse
)
def add_connection_to_workflow(
    workflow_id: uuid.UUID,
    connection: schemas.WorkflowConnectionCreate,
    db: Session = Depends(get_db),
):
    """Add a connection between agents in a workflow"""
    # Verify workflow exists
    workflow = crud.get_workflow(db, workflow_id)
    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Workflow not found"
        )

    # Set workflow_id
    connection.workflow_id = workflow_id

    try:
        db_connection = crud.create_workflow_connection(db, connection)
        return db_connection
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error adding connection to workflow: {str(e)}",
        )


@router.post("/{workflow_id}/deploy", response_model=schemas.WorkflowDeploymentResponse)
def deploy_workflow(
    workflow_id: uuid.UUID,
    deployment_request: schemas.WorkflowDeploymentRequest,
    db: Session = Depends(get_db),
):
    """Deploy a workflow"""
    # Verify workflow exists
    workflow = crud.get_workflow(db, workflow_id)
    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Workflow not found"
        )

    # Create deployment data with workflow_id
    deployment_data = schemas.WorkflowDeploymentCreate(
        workflow_id=workflow_id,
        environment=deployment_request.environment,
        deployment_name=deployment_request.deployment_name,
        deployed_by=deployment_request.deployed_by,
        runtime_config=deployment_request.runtime_config,
    )

    try:
        # Create deployment record
        db_deployment = crud.create_workflow_deployment(db, deployment_data)

        # Update workflow's is_deployed flag and deployed_at timestamp
        workflow_update = schemas.WorkflowUpdate(
            is_deployed=True, deployed_at=db_deployment.deployed_at
        )
        crud.update_workflow(db, workflow_id, workflow_update)

        # Build and store the CommandAgent for this deployment
        command_agent = _build_command_agent_from_workflow(db, workflow)
        ACTIVE_WORKFLOWS[deployment_request.deployment_name] = {
            "command_agent": command_agent,
            "deployment": db_deployment,
            "workflow": workflow,
        }

        return db_deployment
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deploying workflow: {str(e)}",
        )


@router.get(
    "/deployments/active", response_model=List[schemas.WorkflowDeploymentResponse]
)
def list_active_deployments(db: Session = Depends(get_db)):
    """List all active workflow deployments"""
    deployments = crud.workflows.get_active_workflow_deployments(db)
    return deployments


@router.post("/deployments/{deployment_name}/stop")
def stop_workflow_deployment(deployment_name: str, db: Session = Depends(get_db)):
    """Stop/undeploy a workflow deployment by name"""
    try:
        # Find the deployment by name (try development first, then production)
        deployment = crud.workflows.get_workflow_deployment_by_name(
            db, deployment_name, "development"
        )
        if not deployment:
            deployment = crud.workflows.get_workflow_deployment_by_name(
                db, deployment_name, "production"
            )

        if not deployment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Deployment '{deployment_name}' not found in development or production environment",
            )

        # Update deployment status to inactive
        deployment_update = schemas.WorkflowDeploymentUpdate(status="inactive")
        updated_deployment = crud.update_workflow_deployment(
            db, deployment.deployment_id, deployment_update
        )

        if not updated_deployment:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update deployment '{deployment_name}'",
            )

        # Check if there are any other active deployments for this workflow
        active_deployments = crud.workflows.get_active_workflow_deployments(
            db, deployment.workflow_id
        )
        if not active_deployments:
            # No more active deployments, update workflow's is_deployed flag
            workflow_update = schemas.WorkflowUpdate(is_deployed=False)
            crud.update_workflow(db, deployment.workflow_id, workflow_update)

        # Remove from active workflows memory
        if deployment_name in ACTIVE_WORKFLOWS:
            del ACTIVE_WORKFLOWS[deployment_name]

        return {
            "message": f"Deployment '{deployment_name}' stopped successfully",
            "deployment_id": str(updated_deployment.deployment_id),
            "status": updated_deployment.status,
            "stopped_at": (
                updated_deployment.stopped_at.isoformat()
                if updated_deployment.stopped_at
                else None
            ),
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error stopping deployment: {str(e)}",
        )


# @router.delete("/deployments/{deployment_name}")
# def delete_workflow_deployment_by_name(
#     deployment_name: str, db: Session = Depends(get_db)
# ):
#     """Completely delete a workflow deployment by name"""
#     try:
#         # Find the deployment by name (try development first, then production)
#         deployment = crud.get_workflow_deployment_by_name(
#             db, deployment_name, "development"
#         )
#         if not deployment:
#             deployment = crud.get_workflow_deployment_by_name(
#                 db, deployment_name, "production"
#             )

#         if not deployment:
#             raise HTTPException(
#                 status_code=status.HTTP_404_NOT_FOUND,
#                 detail=f"Deployment '{deployment_name}' not found in development or production environment",
#             )

#         deployment_id = deployment.deployment_id
#         workflow_id = deployment.workflow_id

#         # Remove from active workflows memory first
#         if deployment_name in ACTIVE_WORKFLOWS:
#             del ACTIVE_WORKFLOWS[deployment_name]
#             print(f"Removed '{deployment_name}' from active workflows")

#         # Delete from database
#         success = crud.delete_workflow_deployment(db, deployment_id)
#         if not success:
#             raise HTTPException(
#                 status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#                 detail=f"Failed to delete deployment '{deployment_name}'",
#             )

#         # Check if there are any other active deployments for this workflow
#         active_deployments = crud.workflows.get_active_workflow_deployments(
#             db, workflow_id
#         )
#         if not active_deployments:
#             # No more active deployments, update workflow's is_deployed flag
#             workflow_update = schemas.WorkflowUpdate(is_deployed=False)
#             crud.update_workflow(db, workflow_id, workflow_update)

#         return {
#             "message": f"Deployment '{deployment_name}' deleted successfully",
#             "deployment_id": str(deployment_id),
#         }

#     except Exception as e:
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail=f"Error deleting deployment: {str(e)}",
#         )


@router.post("/{workflow_id}/execute", response_model=schemas.WorkflowExecutionResponse)
def execute_workflow(
    workflow_id: uuid.UUID,
    execution_request: schemas.WorkflowExecutionRequest,
    db: Session = Depends(get_db),
):
    """Execute a workflow by workflow ID (supports both single and multi-agent workflows)"""
    # Verify workflow exists
    workflow = crud.get_workflow(db, workflow_id)
    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Workflow not found"
        )

    try:
        # Determine if this is a single-agent or multi-agent workflow
        agents = workflow.configuration.get("agents", [])
        is_single_agent = len(agents) == 1

        if is_single_agent:
            # Single-agent workflow - execute agent directly with its own prompt
            agent_config = agents[0]
            agent_type = agent_config.get("agent_type", "CommandAgent")

            if agent_type == "ToshibaAgent":
                # Build ToshibaAgent directly
                agent = _build_toshiba_agent_from_workflow(db, workflow, agent_config)
            else:
                # Build other single agents directly
                agent = _build_single_agent_from_workflow(db, workflow, agent_config)

            # Build dynamic agent store for inter-agent communication
            dynamic_agent_store = _build_dynamic_agent_store(db, workflow)

            # Add timeout to agent execution using concurrent.futures (thread-safe)
            import concurrent.futures

            # Execute with timeout using ThreadPoolExecutor
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                # Submit the agent execution to the thread pool
                future = executor.submit(
                    agent.execute,
                    query=execution_request.query,
                    chat_history=execution_request.chat_history,
                    enable_analytics=False,  # Disable analytics to avoid potential issues
                    dynamic_agent_store=dynamic_agent_store,  # Pass dynamic agent store
                )

                try:
                    # Wait for result with 60 second timeout
                    result = future.result(timeout=60)
                except concurrent.futures.TimeoutError:
                    # Cancel the future
                    future.cancel()
                    raise HTTPException(
                        status_code=504,
                        detail="Agent execution timed out after 60 seconds",
                    )
                except Exception as e:
                    raise
        else:
            # Multi-agent workflow - use CommandAgent for orchestration
            command_agent = _build_command_agent_from_workflow(db, workflow)

            # Build dynamic agent store for inter-agent communication
            dynamic_agent_store = _build_dynamic_agent_store(db, workflow)

            # Add timeout to CommandAgent execution using concurrent.futures (thread-safe)
            import concurrent.futures

            # Execute with timeout using ThreadPoolExecutor
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                # Submit the CommandAgent execution to the thread pool
                if execution_request.chat_history:
                    future = executor.submit(
                        command_agent.execute_stream,
                        execution_request.query,
                        execution_request.chat_history,
                        dynamic_agent_store,  # Pass dynamic agent store to execute_stream
                    )
                else:
                    # Use provided session_id or generate one
                    session_id = (
                        execution_request.session_id
                        or f"workflow_{workflow_id}_{int(time.time())}"
                    )
                    user_id = execution_request.user_id or "workflow_user"
                    future = executor.submit(
                        command_agent.execute,
                        query=execution_request.query,
                        enable_analytics=True,  # Enable analytics to track executions
                        session_id=session_id,
                        user_id=user_id,
                        dynamic_agent_store=dynamic_agent_store,  # Pass dynamic agent store
                    )

                try:
                    # Wait for result with 60 second timeout
                    result = future.result(timeout=60)
                except concurrent.futures.TimeoutError:
                    # Cancel the future
                    future.cancel()
                    raise HTTPException(
                        status_code=504,
                        detail="CommandAgent execution timed out after 60 seconds",
                    )
                except Exception as e:
                    raise

        # Ensure response is in JSON format expected by frontend
        import json

        def safe_json_serialize(obj):
            """Safely serialize object to JSON, handling generators and other non-serializable types"""
            try:
                if isinstance(obj, str):
                    return json.dumps({"content": obj})
                elif isinstance(obj, (dict, list, int, float, bool)) or obj is None:
                    return json.dumps(obj)
                elif hasattr(obj, "__iter__") and not isinstance(obj, str):
                    # Handle generators and other iterables
                    return json.dumps({"content": str(list(obj))})
                else:
                    return json.dumps({"content": str(obj)})
            except (TypeError, ValueError) as e:
                # Fallback for any remaining serialization issues
                return json.dumps({"content": str(obj), "serialization_error": str(e)})

        formatted_response = safe_json_serialize(result)

        return schemas.WorkflowExecutionResponse(
            status="success",
            response=formatted_response,
            workflow_id=str(workflow_id),
            deployment_id="",  # Empty string instead of None
            timestamp=datetime.now().isoformat(),
        )

    except Exception as e:
        print(str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error executing workflow: {str(e)}",
        )


@router.post("/{workflow_id}/stream")
async def execute_workflow_stream(
    workflow_id: uuid.UUID,
    execution_request: schemas.WorkflowStreamExecutionRequest,
    db: Session = Depends(get_db),
):
    """Execute a workflow with streaming responses by workflow ID (supports both single and multi-agent workflows)"""
    # Verify workflow exists
    workflow = crud.get_workflow(db, workflow_id)
    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Workflow not found"
        )

    async def stream_generator():
        """Generate streaming response chunks"""
        try:
            # Send initial status
            yield f"data: {json.dumps({'status': 'started', 'workflow_id': str(workflow_id), 'timestamp': datetime.now().isoformat()})}\n\n"

            # Determine if this is a single-agent or multi-agent workflow
            agents = workflow.configuration.get("agents", [])
            is_single_agent = len(agents) == 1

            if is_single_agent:
                # Single-agent workflow - execute agent directly with its own prompt
                agent_config = agents[0]
                agent_type = agent_config.get("agent_type", "CommandAgent")

                if agent_type == "ToshibaAgent":
                    # Build ToshibaAgent directly
                    agent = _build_toshiba_agent_from_workflow(
                        db, workflow, agent_config
                    )
                else:
                    # Build other single agents directly
                    agent = _build_single_agent_from_workflow(
                        db, workflow, agent_config
                    )

                # Check if agent has streaming capability
                if hasattr(agent, "execute_stream") and callable(
                    getattr(agent, "execute_stream")
                ):
                    # Use agent's streaming execution (note: streaming doesn't support analytics yet)
                    for chunk in agent.execute_stream(
                        execution_request.query, execution_request.chat_history
                    ):
                        if chunk:
                            yield f"data: {json.dumps({'type': 'content', 'data': chunk, 'timestamp': datetime.now().isoformat()})}\n\n"
                            await asyncio.sleep(0.01)
                else:
                    # Fallback to regular execution with analytics
                    session_id = (
                        execution_request.session_id
                        or f"workflow_{workflow_id}_{int(time.time())}"
                    )
                    user_id = execution_request.user_id or "workflow_user"
                    result = agent.execute(
                        query=execution_request.query,
                        chat_history=execution_request.chat_history,
                        session_id=session_id,
                        user_id=user_id,
                        enable_analytics=True,
                    )
                    yield f"data: {json.dumps({'type': 'content', 'data': result, 'timestamp': datetime.now().isoformat()})}\n\n"
            else:
                # Multi-agent workflow - use CommandAgent for orchestration
                command_agent = _build_command_agent_from_workflow(db, workflow)

                # Build dynamic agent store for inter-agent communication
                dynamic_agent_store = _build_dynamic_agent_store(db, workflow)

                # Execute with streaming (note: streaming doesn't support analytics yet)
                if execution_request.chat_history:
                    # Use streaming execution with chat history
                    for chunk in command_agent.execute_stream(
                        execution_request.query,
                        execution_request.chat_history,
                        dynamic_agent_store,
                    ):
                        if chunk:
                            yield f"data: {json.dumps({'type': 'content', 'data': chunk, 'timestamp': datetime.now().isoformat()})}\n\n"
                            await asyncio.sleep(0.01)
                else:
                    # For non-streaming execution, simulate streaming by chunking the response
                    session_id = (
                        execution_request.session_id
                        or f"workflow_{workflow_id}_{int(time.time())}"
                    )
                    user_id = execution_request.user_id or "workflow_user"
                    result = command_agent.execute(
                        query=execution_request.query,
                        session_id=session_id,
                        user_id=user_id,
                        enable_analytics=True,
                        dynamic_agent_store=dynamic_agent_store,
                    )
                    yield f"data: {json.dumps({'type': 'content', 'data': result, 'timestamp': datetime.now().isoformat()})}\n\n"

            # Send completion status
            yield f"data: {json.dumps({'status': 'completed', 'workflow_id': str(workflow_id), 'timestamp': datetime.now().isoformat()})}\n\n"

        except Exception as e:
            # Send error as final chunk
            error_chunk = {
                "status": "error",
                "error": str(e),
                "workflow_id": str(workflow_id),
                "timestamp": datetime.now().isoformat(),
            }
            yield f"data: {json.dumps(error_chunk)}\n\n"

    return StreamingResponse(
        stream_generator(),
        media_type="text/event-stream",
        headers={
            "Content-Type": "text/event-stream",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


def _execute_workflow_background(
    execution_id: str,
    workflow_id: uuid.UUID,
    execution_request: schemas.WorkflowExecutionRequest,
):
    """
    Background task to execute a workflow asynchronously with detailed tracing.
    Updates execution status and workflow trace throughout the process.
    """
    from services.analytics_service import analytics_service, WorkflowStep

    try:
        # Update status to running and initialize tracing
        analytics_service.update_execution(
            execution_id, status="running", current_step="Initializing workflow"
        )

        # Get database session for background task
        from db.database import SessionLocal

        db = SessionLocal()

        try:
            # Get the workflow from database
            workflow = crud.get_workflow(db=db, workflow_id=workflow_id)
            if workflow is None:
                analytics_service.update_execution(
                    execution_id, status="failed", error="Workflow not found"
                )
                return

            # Initialize workflow tracing
            agents = workflow.configuration.get("agents", [])
            connections = workflow.configuration.get("connections", [])
            estimated_steps = (
                len(agents) + len(connections) + 2
            )  # agents + connections + init + finalize

            analytics_service.init_workflow_trace(
                execution_id, str(workflow_id), estimated_steps
            )

            # Add initial step
            init_step = WorkflowStep(
                step_id=f"init_{execution_id}",
                step_type="data_processing",
                status="running",
                step_metadata={"description": "Initializing workflow execution"},
            )
            analytics_service.add_workflow_step(execution_id, init_step)
            analytics_service.update_execution(
                execution_id, current_step="Analyzing workflow structure", progress=0.1
            )

            # Determine workflow type and find root agent
            is_single_agent = len(agents) == 1

            # Find the root agent (entry point) - agent with no incoming connections
            root_agent_id = None
            if connections:
                # Get all target agent IDs (agents that have incoming connections)
                target_agent_ids = {conn.get("target_agent_id") for conn in connections}
                # Find agents that are not targets (no incoming connections)
                for agent in agents:
                    agent_id = agent.get("agent_id")
                    if agent_id and agent_id not in target_agent_ids:
                        root_agent_id = agent_id
                        break
            elif agents:
                # If no connections, use the first agent as root
                root_agent_id = agents[0].get("agent_id")

            if is_single_agent:
                # Single-agent workflow execution with tracing
                agent_config = agents[0]
                agent_type = agent_config.get("agent_type", "CommandAgent")

                # Add agent execution step
                agent_step = WorkflowStep(
                    step_id=f"agent_{agent_config.get('agent_id', 'unknown')}",
                    step_type="agent_execution",
                    agent_id=agent_config.get("agent_id"),
                    agent_name=agent_type,
                    status="pending",
                    input_data={"query": execution_request.query},
                    step_metadata={"agent_type": agent_type},
                )
                analytics_service.add_workflow_step(execution_id, agent_step)
                analytics_service.add_execution_path(execution_id, agent_type)

                analytics_service.update_execution(
                    execution_id, current_step=f"Executing {agent_type}", progress=0.3
                )
                analytics_service.update_workflow_step(
                    execution_id, agent_step.step_id, status="running"
                )

                try:
                    if agent_type == "ToshibaAgent":
                        agent = _build_toshiba_agent_from_workflow(
                            db, workflow, agent_config
                        )
                    else:
                        agent = _build_single_agent_from_workflow(
                            db, workflow, agent_config
                        )

                    # Build dynamic agent store for inter-agent communication
                    dynamic_agent_store = _build_dynamic_agent_store(db, workflow)

                    result = agent.execute(
                        query=execution_request.query,
                        chat_history=execution_request.chat_history,
                        enable_analytics=False,
                        dynamic_agent_store=dynamic_agent_store,
                    )

                    # Update agent step as completed
                    analytics_service.update_workflow_step(
                        execution_id,
                        agent_step.step_id,
                        status="completed",
                        output_data={"result": str(result)},
                    )

                except Exception as agent_error:
                    analytics_service.update_workflow_step(
                        execution_id,
                        agent_step.step_id,
                        status="failed",
                        error=str(agent_error),
                    )
                    raise agent_error

            else:
                # Multi-agent workflow execution using root agent as entry point
                if root_agent_id:
                    # Use the root agent as the entry point
                    analytics_service.update_execution(
                        execution_id,
                        current_step="Executing root agent",
                        progress=0.2,
                    )

                    # Get the root agent from database
                    root_agent = crud.get_agent(db, uuid.UUID(root_agent_id))
                    if root_agent:
                        # Add root agent step
                        # Create root agent step with proper UUID to avoid conflicts
                        root_step = WorkflowStep(
                            step_id=str(uuid.uuid4()),  # Use proper UUID for step_id
                            step_type="agent_execution",
                            agent_id=root_agent_id,
                            agent_name=root_agent.name,
                            status="pending",
                            input_data={
                                "query": execution_request.query,
                                "agent_count": len(agents),
                            },
                            step_metadata={
                                "workflow_type": "multi_agent",
                                "root_agent": True,
                                "agent_type": root_agent.agent_type,
                            },
                        )
                        analytics_service.add_workflow_step(execution_id, root_step)
                        analytics_service.add_execution_path(
                            execution_id, root_agent.name
                        )

                        # Use the root agent with workflow functions
                        command_agent = _build_root_agent_with_workflow_functions(
                            db, workflow
                        )
                    else:
                        analytics_service.update_execution(
                            execution_id,
                            status="failed",
                            error=f"Root agent {root_agent_id} not found",
                        )
                        return
                else:
                    # Fallback to CommandAgent orchestrator if no root agent found
                    analytics_service.update_execution(
                        execution_id,
                        current_step="Building CommandAgent orchestrator",
                        progress=0.2,
                    )

                    # Add orchestrator step
                    orchestrator_step = WorkflowStep(
                        step_id=f"orchestrator_{execution_id}",
                        step_type="agent_execution",
                        agent_name="CommandAgent",
                        status="pending",
                        input_data={
                            "query": execution_request.query,
                            "agent_count": len(agents),
                        },
                        step_metadata={
                            "workflow_type": "multi_agent",
                            "orchestrator": True,
                        },
                    )
                    analytics_service.add_workflow_step(execution_id, orchestrator_step)
                    analytics_service.add_execution_path(execution_id, "CommandAgent")

                    command_agent = _build_root_agent_with_workflow_functions(
                        db, workflow
                    )
                dynamic_agent_store = _build_dynamic_agent_store(db, workflow)

                analytics_service.update_execution(
                    execution_id,
                    current_step="Orchestrating workflow execution",
                    progress=0.4,
                )
                # Update the appropriate step as running
                if root_agent_id:
                    analytics_service.update_workflow_step(
                        execution_id, root_step.step_id, status="running"
                    )
                else:
                    analytics_service.update_workflow_step(
                        execution_id, orchestrator_step.step_id, status="running"
                    )

                # Note: Individual tool calls will be tracked by CommandAgent analytics
                # We don't create placeholder steps here - real tool calls will be captured

                try:
                    if execution_request.chat_history:
                        result = command_agent.execute_stream(
                            execution_request.query,
                            execution_request.chat_history,
                            dynamic_agent_store,
                        )
                        # Convert generator to string for storage
                        result = "".join(str(chunk) for chunk in result if chunk)
                    else:
                        session_id = (
                            execution_request.session_id
                            or f"workflow_{workflow_id}_{int(time.time())}"
                        )
                        user_id = execution_request.user_id or "workflow_user"
                        # Enable analytics with proper execution_id to track tool calls
                        result = command_agent.execute(
                            query=execution_request.query,
                            enable_analytics=True,
                            session_id=session_id,
                            user_id=user_id,
                            dynamic_agent_store=dynamic_agent_store,
                            execution_id=execution_id,  # Pass workflow execution_id
                        )

                    # Update the appropriate step as completed
                    if root_agent_id:
                        analytics_service.update_workflow_step(
                            execution_id,
                            root_step.step_id,
                            status="completed",
                            output_data={"result": str(result)},
                        )
                    else:
                        analytics_service.update_workflow_step(
                            execution_id,
                            orchestrator_step.step_id,
                            status="completed",
                            output_data={"result": str(result)},
                        )

                    # Mark sub-agent steps as completed (simplified for now)
                    for agent_config in agents:
                        agent_id = agent_config.get(
                            "agent_id", f"agent_{agents.index(agent_config)}"
                        )
                        analytics_service.update_workflow_step(
                            execution_id, f"sub_agent_{agent_id}", status="completed"
                        )
                        analytics_service.add_execution_path(
                            execution_id, agent_config.get("agent_type", "Unknown")
                        )

                except Exception as orchestrator_error:
                    # Update the appropriate step as failed
                    if root_agent_id:
                        analytics_service.update_workflow_step(
                            execution_id,
                            root_step.step_id,
                            status="failed",
                            error=str(orchestrator_error),
                        )
                    else:
                        analytics_service.update_workflow_step(
                            execution_id,
                            orchestrator_step.step_id,
                            status="failed",
                            error=str(orchestrator_error),
                        )
                    raise orchestrator_error

            # Add finalization step
            final_step = WorkflowStep(
                step_id=f"finalize_{execution_id}",
                step_type="data_processing",
                status="running",
                step_metadata={"description": "Finalizing workflow execution"},
            )
            analytics_service.add_workflow_step(execution_id, final_step)
            analytics_service.update_execution(
                execution_id, current_step="Finalizing results", progress=0.9
            )

            # Format the final response
            import json

            def safe_json_serialize(obj):
                try:
                    if isinstance(obj, str):
                        return json.dumps({"content": obj})
                    elif isinstance(obj, (dict, list, int, float, bool)) or obj is None:
                        return json.dumps(obj)
                    elif hasattr(obj, "__iter__") and not isinstance(obj, str):
                        return json.dumps({"content": str(list(obj))})
                    else:
                        return json.dumps({"content": str(obj)})
                except (TypeError, ValueError) as e:
                    return json.dumps(
                        {"content": str(obj), "serialization_error": str(e)}
                    )

            formatted_response = safe_json_serialize(result)
            response_data = {
                "status": "success",
                "response": formatted_response,
                "workflow_id": str(workflow_id),
                "execution_id": execution_id,
                "timestamp": datetime.now().isoformat(),
            }

            # Complete finalization step
            analytics_service.update_workflow_step(
                execution_id,
                final_step.step_id,
                status="completed",
                output_data=response_data,
            )

            # Update execution as completed
            analytics_service.update_execution(
                execution_id,
                status="completed",
                progress=1.0,
                current_step="Completed",
                result=response_data,
                db=db,
            )

        finally:
            db.close()

    except Exception as e:
        # Update execution as failed
        analytics_service.update_execution(execution_id, status="failed", error=str(e))


@router.post("/{workflow_id}/execute/async", status_code=status.HTTP_202_ACCEPTED)
async def execute_workflow_async(
    workflow_id: uuid.UUID,
    execution_request: schemas.WorkflowExecutionRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """
    Execute a workflow asynchronously with detailed tracing.
    Returns immediately with execution_id for status polling and tracing.
    """
    from services.analytics_service import analytics_service, AsyncExecutionResponse
    from datetime import datetime, timedelta
    import logging

    logger = logging.getLogger(__name__)
    logger.info(f"🚀 Starting async workflow execution for {workflow_id}")

    try:
        # Create execution record
        logger.info("📝 Creating execution record...")
        execution_id = analytics_service.create_execution(
            execution_type="workflow",
            workflow_id=str(workflow_id),
            session_id=execution_request.session_id,
            user_id=execution_request.user_id,
            query=execution_request.query,
            estimated_duration=30,  # Rough estimate for workflows (longer than agents)
        )
        logger.info(f"✅ Created execution record: {execution_id}")

        # Queue the background task
        logger.info("🔄 Queuing background task...")
        background_tasks.add_task(
            _execute_workflow_background,
            execution_id=execution_id,
            workflow_id=workflow_id,
            execution_request=execution_request,
        )
        logger.info("✅ Background task queued successfully")

        logger.info(f"🎯 Creating response object for execution {execution_id}")
        response_obj = AsyncExecutionResponse(
            execution_id=execution_id,
            status="accepted",
            type="workflow",
            estimated_completion_time=datetime.now() + timedelta(seconds=30),
            status_url=f"/api/executions/{execution_id}/status",
            timestamp=datetime.now(),
        )
        logger.info(f"✅ Response object created: {response_obj}")
        logger.info("🚀 About to return response...")
        return response_obj
    except Exception as e:
        logger.error(f"❌ Error in async workflow execution: {e}")
        raise


def _build_toshiba_agent_from_workflow(db: Session, workflow, agent_config):
    """Build ToshibaAgent from workflow configuration"""
    from agents.toshiba_agent import create_toshiba_agent
    from prompts import toshiba_agent_system_prompt
    from agents.tools import tool_schemas

    # Get ToshibaAgent-specific configuration
    functions = (
        [tool_schemas.get("query_retriever2")]
        if "query_retriever2" in tool_schemas
        else []
    )

    return create_toshiba_agent(
        system_prompt=toshiba_agent_system_prompt, functions=functions
    )


def _build_single_agent_from_workflow(
    db: Session, workflow: models.Workflow, agent_config
):
    """Build a single agent from workflow configuration using its configured prompt and tools"""
    from agents.agent_base import Agent

    # Get agent type and ID from config
    agent_type = agent_config.get("agent_type", "CommandAgent")
    agent_id = agent_config.get("agent_id")
    # Try to get the agent from database if agent_id is provided
    db_agent = None
    if agent_id:
        try:
            import uuid

            db_agent = crud.get_agent(db, uuid.UUID(agent_id))
        except (ValueError, TypeError) as e:
            # If agent_id is invalid, try to find by name
            db_agent = crud.get_agent_by_name(db, agent_type)
    else:
        # Find agent by type/name
        db_agent = crud.get_agent_by_name(db, agent_type)

    if not db_agent:
        # Fallback to CommandAgent if agent not found
        return _build_command_agent_from_workflow(db, workflow)

    from typing import cast
    from openai.types.chat.chat_completion_tool_param import ChatCompletionToolParam
    from data_classes import PromptObject

    try:
        # Check if system_prompt exists and has required attributes
        if not hasattr(db_agent, "system_prompt") or db_agent.system_prompt is None:
            # Use a simple fallback
            system_prompt = db_agent.system_prompt
        else:
            from datetime import datetime
            import uuid

            system_prompt = PromptObject(
                appName="",
                createdTime=getattr(
                    db_agent.system_prompt, "created_time", datetime.now()
                ),
                prompt=getattr(db_agent.system_prompt, "prompt", ""),
                uniqueLabel=getattr(db_agent.system_prompt, "unique_label", ""),
                pid=getattr(db_agent.system_prompt, "pid", uuid.uuid4()),
                last_deployed=getattr(db_agent.system_prompt, "last_deployed", None),
                deployedTime=getattr(db_agent.system_prompt, "deployed_time", None),
                isDeployed=getattr(db_agent.system_prompt, "is_deployed", False),
                modelProvider=getattr(db_agent.system_prompt, "ai_model_provider", ""),
                modelName=getattr(db_agent.system_prompt, "ai_model_name", ""),
                sha_hash=getattr(db_agent.system_prompt, "sha_hash", ""),
                tags=getattr(db_agent.system_prompt, "tags", []),
                version=getattr(db_agent.system_prompt, "version", ""),
                variables=getattr(db_agent.system_prompt, "variables", {}),
                hyper_parameters=getattr(
                    db_agent.system_prompt, "hyper_parameters", {}
                ),
                prompt_label=getattr(db_agent.system_prompt, "prompt_label", ""),
            )
    except Exception as e:
        # Fallback to original system_prompt if PromptObject construction fails
        system_prompt = db_agent.system_prompt

    return Agent(
        name=db_agent.name,
        agent_id=db_agent.agent_id,
        system_prompt=system_prompt,
        persona=db_agent.persona,
        functions=cast(List[ChatCompletionToolParam], db_agent.functions or []),
        routing_options=db_agent.routing_options or {},
        model="gpt-4o-mini",
        temperature=0.7,
        short_term_memory=db_agent.short_term_memory or False,
        long_term_memory=db_agent.long_term_memory or False,
        reasoning=db_agent.reasoning or False,
        input_type=["text", "voice"],
        output_type=["text", "voice"],
        response_type="json",
        max_retries=db_agent.max_retries or 3,
        timeout=db_agent.timeout,
        deployed=True,
        status="active",
        priority=db_agent.priority,
        failure_strategies=db_agent.failure_strategies or [],
        session_id=None,
        last_active=datetime.now(),
        collaboration_mode="single",
    )


def _sanitize_function_name(name: str) -> str:
    """Convert agent name to valid OpenAI function name"""
    # Remove spaces and special characters, convert to camelCase
    import re

    # Replace spaces and special chars with underscores, then remove multiple underscores
    sanitized = re.sub(r"[^a-zA-Z0-9_]", "_", name)
    sanitized = re.sub(r"_+", "_", sanitized)  # Remove multiple underscores
    sanitized = sanitized.strip("_")  # Remove leading/trailing underscores

    # Ensure it starts with a letter
    if sanitized and not sanitized[0].isalpha():
        sanitized = f"agent_{sanitized}"

    return sanitized or "unknown_agent"


def _build_openai_schema_from_db_agent(db_agent: models.Agent):
    """Build OpenAI function schema from database agent"""
    try:
        # Sanitize the agent name for use as function name
        function_name = _sanitize_function_name(db_agent.name)

        def python_function_to_openai_schema(agent_cls: models.Agent) -> Dict[str, Any]:
            """Converts an agent class into an OpenAI JSON schema based on its `execute` method."""
            execute_method = getattr(Agent, "execute", None)
            if execute_method is None:
                raise ValueError(f"{agent_cls.name} must have an 'execute' method.")

            signature = inspect.signature(execute_method)
            type_hints = get_type_hints(execute_method)

            schema = {
                "type": "function",
                "function": {
                    "name": _sanitize_function_name(
                        agent_cls.name
                    ),  # Tool name = Class name
                    "description": execute_method.__doc__
                    or f"Agent {agent_cls.name} execution function",
                    "parameters": {"type": "object", "properties": {}, "required": []},
                },
            }

            for param_name, param in signature.parameters.items():
                if param_name == "self":
                    continue  # Skip 'self' parameter

                param_type = type_hints.get(param_name, Any)
                openai_type, is_optional = python_type_to_openai_type(param_type)

                schema["function"]["parameters"]["properties"][param_name] = {
                    "type": openai_type,
                    "description": f"{param_name} parameter",
                }
                if openai_type == "array":
                    schema["function"]["parameters"]["properties"][param_name][
                        "items"
                    ] = {"type": "string"}

                if not is_optional and param.default is inspect.Parameter.empty:
                    schema["function"]["parameters"]["required"].append(param_name)

            return schema

        def python_type_to_openai_type(py_type) -> tuple[str, bool]:
            """Maps Python types to OpenAI JSON schema types, handling Optional and List types."""
            from typing import get_origin, get_args

            if get_origin(py_type) is Union:
                args = get_args(py_type)
                non_none_types = [t for t in args if t is not type(None)]
                if len(non_none_types) == 1:
                    openai_type, _ = python_type_to_openai_type(non_none_types[0])
                    return openai_type, True  # It's Optional

            if get_origin(py_type) is list or get_origin(py_type) is List:
                return "array", False

            mapping = {
                int: "integer",
                float: "number",
                str: "string",
                bool: "boolean",
                dict: "object",
            }

            return mapping.get(py_type, "string"), False  # Default to string

        # Use the sophisticated schema generation, but fall back to simple schema if it fails
        try:
            return python_function_to_openai_schema(db_agent)
        except Exception as schema_error:
            # Fallback to simple schema if advanced generation fails
            pass

            # Fallback to simple, reliable schema that matches base Agent.execute signature
            return {
                "type": "function",
                "function": {
                    "name": function_name,
                    "description": db_agent.description
                    or f"Execute {db_agent.name} agent - {db_agent.agent_type} type agent",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "The query or task to send to the agent",
                            },
                            "session_id": {
                                "type": "string",
                                "description": "Optional session ID for the agent execution",
                            },
                            "user_id": {
                                "type": "string",
                                "description": "Optional user ID for the agent execution",
                            },
                            "chat_history": {
                                "type": "array",
                                "description": "Optional chat history for the agent execution",
                                "items": {"type": "object"},
                            },
                            "enable_analytics": {
                                "type": "boolean",
                                "description": "Whether to enable analytics for this execution",
                            },
                        },
                        "required": ["query"],
                    },
                },
            }

    except Exception as e:
        # Return None if schema generation fails completely
        return None


def _build_dynamic_agent_store(db: Session, workflow):
    """Build agent store dynamically from database agents in the workflow"""
    agent_store = {}

    try:
        # Get all agents in this workflow
        workflow_agents = crud.get_workflow_agents(db, workflow.workflow_id)

        for workflow_agent in workflow_agents:
            db_agent = crud.get_agent(db, workflow_agent.agent_id)
            if db_agent:
                # Create a callable function for this agent
                def create_agent_executor(agent_id):
                    def execute_agent(
                        query: str,
                        session_id: Optional[str] = None,
                        user_id: Optional[str] = None,
                        chat_history: Optional[list] = None,
                        enable_analytics: bool = False,
                        **kwargs,
                    ):
                        # Build the agent dynamically and execute
                        try:
                            agent = _build_single_agent_from_workflow(
                                db, workflow, {"agent_id": str(agent_id)}
                            )
                            result = agent.execute(
                                query=query,
                                session_id=session_id,
                                user_id=user_id,
                                chat_history=chat_history,
                                enable_analytics=enable_analytics,
                                **kwargs,
                            )

                            # Ensure result is JSON serializable
                            if isinstance(result, (dict, list)):
                                import json

                                return json.dumps(result)
                            elif hasattr(result, "__iter__") and not isinstance(
                                result, str
                            ):
                                # Handle generators and other iterables
                                return str(list(result))
                            else:
                                return str(result)
                        except Exception as e:
                            return f"Error executing agent: {str(e)}"

                    return execute_agent

                # Use sanitized function name to match OpenAI schema
                function_name = _sanitize_function_name(db_agent.name)
                agent_store[function_name] = create_agent_executor(db_agent.agent_id)

        return agent_store

    except Exception as e:
        # Return empty store if building fails
        return {}


def _find_root_agent(db: Session, workflow):
    """Find the true root agent by analyzing workflow connections"""
    workflow_agents = crud.get_workflow_agents(db, workflow.workflow_id)
    workflow_connections = crud.get_workflow_connections(db, workflow.workflow_id)

    # Get all agent IDs that appear as targets (have incoming connections)
    target_agent_ids = {conn.target_agent_id for conn in workflow_connections}

    # Get all agent IDs that appear as sources (have outgoing connections)
    source_agent_ids = {conn.source_agent_id for conn in workflow_connections}

    # Root agent is one that is a source but never a target
    root_agent_ids = source_agent_ids - target_agent_ids

    if len(root_agent_ids) == 1:
        root_agent_id = list(root_agent_ids)[0]
        return crud.get_agent(db, root_agent_id)
    elif len(root_agent_ids) == 0:
        # No clear root - might be a single agent workflow
        if len(workflow_agents) == 1:
            return crud.get_agent(db, workflow_agents[0].agent_id)

    # Multiple roots or unclear structure - fallback to None
    return None


def _build_root_agent_with_workflow_functions(db: Session, workflow):
    """Build the root agent with workflow functions instead of creating a temporary CommandAgent"""
    # Find the true root agent
    root_agent = _find_root_agent(db, workflow)

    if not root_agent:
        # Fallback to creating a temporary CommandAgent if no root found
        return _build_command_agent_from_workflow(db, workflow)

    # Get workflow connections to build functions list
    workflow_connections = crud.get_workflow_connections(db, workflow.workflow_id)

    # Build functions list from target agents that the root agent can call
    workflow_functions = []

    for connection in workflow_connections:
        # Only include connections where the root agent is the source
        if connection.source_agent_id == root_agent.agent_id:
            target_agent = crud.get_agent(db, connection.target_agent_id)
            if target_agent:
                dynamic_schema = _build_openai_schema_from_db_agent(target_agent)
                if dynamic_schema:
                    workflow_functions.append(dynamic_schema)

    # Create a CommandAgent using the root agent's properties but with workflow functions
    from agents.command_agent import CommandAgent
    from data_classes import PromptObject

    # Create a PromptObject from the database prompt
    if root_agent.system_prompt:
        system_prompt_obj = PromptObject(
            pid=root_agent.system_prompt.pid,
            prompt_label=root_agent.system_prompt.prompt_label,
            prompt=root_agent.system_prompt.prompt,
            sha_hash=root_agent.system_prompt.sha_hash or "default_hash",
            uniqueLabel=root_agent.system_prompt.unique_label,
            appName=root_agent.system_prompt.app_name,
            version=root_agent.system_prompt.version,
            createdTime=root_agent.system_prompt.created_time,
            deployedTime=root_agent.system_prompt.deployed_time,
            last_deployed=root_agent.system_prompt.last_deployed,
            modelProvider=root_agent.system_prompt.ai_model_provider,
            modelName=root_agent.system_prompt.ai_model_name,
            isDeployed=root_agent.system_prompt.is_deployed,
            tags=root_agent.system_prompt.tags,
            hyper_parameters=root_agent.system_prompt.hyper_parameters,
            variables=root_agent.system_prompt.variables,
        )
    else:
        # Fallback to default prompt
        system_prompt_obj = PromptObject(
            pid=uuid.uuid4(),
            prompt_label="Default Workflow Agent",
            prompt="You are a workflow orchestrator agent.",
            sha_hash="default_hash",
            uniqueLabel="DefaultWorkflowAgent",
            appName="agent_studio",
            version="1.0",
            createdTime=datetime.now(),
            deployedTime=None,
            last_deployed=None,
            modelProvider="OpenAI",
            modelName="gpt-4o",
            isDeployed=False,
            tags=[],
            hyper_parameters={},
            variables={},
        )

    command_agent = CommandAgent(
        name=root_agent.name,
        agent_id=root_agent.agent_id,  # Use the real agent_id from database
        system_prompt=system_prompt_obj,  # Use proper PromptObject
        persona=root_agent.persona,
        functions=workflow_functions,  # Use workflow-specific functions
        routing_options={
            "continue": "If you think you can't answer the query, you can continue to the next tool or do some reasoning.",
            "respond": "If you think you have the answer, you can stop here.",
            "give_up": "If you think you can't answer the query, you can give up and let the user know.",
        },
        model="gpt-4o",
        temperature=0.7,
        short_term_memory=root_agent.short_term_memory,
        long_term_memory=root_agent.long_term_memory,
        reasoning=root_agent.reasoning,
        input_type=["text", "voice"],  # Use default values to avoid type issues
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


def _build_command_agent_from_workflow(db: Session, workflow) -> CommandAgent:
    """Build a CommandAgent from a workflow configuration"""
    # Get workflow agents and connections
    workflow_agents = crud.get_workflow_agents(db, workflow.workflow_id)
    workflow_connections = crud.get_workflow_connections(db, workflow.workflow_id)

    # Build functions list for CommandAgent
    functions = []
    for connection in workflow_connections:
        target_agent = crud.get_agent(db, connection.target_agent_id)

        # Build OpenAI schema dynamically from database agent
        if target_agent:
            dynamic_schema = _build_openai_schema_from_db_agent(target_agent)
            if dynamic_schema:
                functions.append(dynamic_schema)

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
        model="gpt-4o",
        temperature=0.7,
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

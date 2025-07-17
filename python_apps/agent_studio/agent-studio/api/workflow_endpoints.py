import uuid
import json
import asyncio
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from db.database import get_db
from db import crud, schemas, models
from agents.command_agent import CommandAgent
from agents import agent_schemas
from prompts import command_agent_system_prompt
from services.workflow_service import workflow_service
from datetime import datetime

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
        print(workflow)
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
                    print(f"Error creating connection: {e}")
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
            print(f"Removed '{deployment_name}' from active workflows")

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


@router.delete("/deployments/{deployment_name}")
def delete_workflow_deployment_by_name(
    deployment_name: str, db: Session = Depends(get_db)
):
    """Completely delete a workflow deployment by name"""
    try:
        # Find the deployment by name (try development first, then production)
        deployment = crud.get_workflow_deployment_by_name(
            db, deployment_name, "development"
        )
        if not deployment:
            deployment = crud.get_workflow_deployment_by_name(
                db, deployment_name, "production"
            )

        if not deployment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Deployment '{deployment_name}' not found in development or production environment",
            )

        deployment_id = deployment.deployment_id
        workflow_id = deployment.workflow_id

        # Remove from active workflows memory first
        if deployment_name in ACTIVE_WORKFLOWS:
            del ACTIVE_WORKFLOWS[deployment_name]
            print(f"Removed '{deployment_name}' from active workflows")

        # Delete from database
        success = crud.delete_workflow_deployment(db, deployment_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete deployment '{deployment_name}'",
            )

        # Check if there are any other active deployments for this workflow
        active_deployments = crud.workflows.get_active_workflow_deployments(
            db, workflow_id
        )
        if not active_deployments:
            # No more active deployments, update workflow's is_deployed flag
            workflow_update = schemas.WorkflowUpdate(is_deployed=False)
            crud.update_workflow(db, workflow_id, workflow_update)

        return {
            "message": f"Deployment '{deployment_name}' deleted successfully",
            "deployment_id": str(deployment_id),
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting deployment: {str(e)}",
        )


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
        print(f"🔍 DEBUG: Starting workflow execution for {workflow_id}")

        # Determine if this is a single-agent or multi-agent workflow
        agents = workflow.configuration.get("agents", [])
        is_single_agent = len(agents) == 1
        print(
            f"🔍 DEBUG: Found {len(agents)} agents, is_single_agent: {is_single_agent}"
        )

        if is_single_agent:
            # Single-agent workflow - execute agent directly with its own prompt
            agent_config = agents[0]
            agent_type = agent_config.get("agent_type", "CommandAgent")
            print(f"🔍 DEBUG: Building single agent of type: {agent_type}")

            if agent_type == "ToshibaAgent":
                # Build ToshibaAgent directly
                print("🔍 DEBUG: Building ToshibaAgent")
                agent = _build_toshiba_agent_from_workflow(db, workflow, agent_config)
            else:
                # Build other single agents directly
                print(f"🔍 DEBUG: Building generic agent for type: {agent_type}")
                agent = _build_single_agent_from_workflow(db, workflow, agent_config)

            print(f"🔍 DEBUG: Agent built successfully: {agent.name}")
            print(f"🔍 DEBUG: Starting agent execution...")
            print(f"🔍 DEBUG: Query: {execution_request.query[:100]}...")
            print(
                f"🔍 DEBUG: Chat history length: {len(execution_request.chat_history) if execution_request.chat_history else 0}"
            )

            # Add timeout to agent execution
            import signal
            import time

            def timeout_handler(signum, frame):
                print("🔍 DEBUG: Agent execution TIMED OUT after 60 seconds!")
                raise TimeoutError("Agent execution timed out after 60 seconds")

            # Set up timeout
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(60)  # 60 second timeout

            start_time = time.time()
            try:
                print("🔍 DEBUG: About to call agent.execute()...")
                print(
                    f"🔍 DEBUG: Agent functions: {len(agent.functions) if agent.functions else 0}"
                )
                print(f"🔍 DEBUG: Agent max_retries: {agent.max_retries}")

                # Execute the agent directly (preserves agent's own prompt)
                # Add enable_analytics=False to avoid potential analytics issues
                result = agent.execute(
                    query=execution_request.query,
                    chat_history=execution_request.chat_history,
                    enable_analytics=False,  # Disable analytics to avoid potential issues
                )
                execution_time = time.time() - start_time
                print(
                    f"🔍 DEBUG: Agent execution completed in {execution_time:.2f} seconds"
                )
                print(
                    f"🔍 DEBUG: Result type: {type(result)}, length: {len(str(result)) if result else 0}"
                )
            except TimeoutError as e:
                print(f"🔍 DEBUG: Timeout error: {e}")
                raise HTTPException(status_code=504, detail="Agent execution timed out")
            except Exception as e:
                execution_time = time.time() - start_time
                print(
                    f"🔍 DEBUG: Agent execution failed after {execution_time:.2f} seconds: {e}"
                )
                raise
            finally:
                signal.alarm(0)  # Cancel timeout
        else:
            # Multi-agent workflow - use CommandAgent for orchestration
            print("🔍 DEBUG: Building CommandAgent for multi-agent workflow")
            command_agent = _build_command_agent_from_workflow(db, workflow)

            print("🔍 DEBUG: Starting CommandAgent execution")
            print(
                f"🔍 DEBUG: CommandAgent functions: {len(command_agent.functions) if command_agent.functions else 0}"
            )
            print(f"🔍 DEBUG: CommandAgent max_retries: {command_agent.max_retries}")

            # Add timeout to CommandAgent execution
            import signal
            import time

            def timeout_handler(signum, frame):
                print("🔍 DEBUG: CommandAgent execution TIMED OUT after 60 seconds!")
                raise TimeoutError("CommandAgent execution timed out after 60 seconds")

            # Set up timeout
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(60)  # 60 second timeout

            start_time = time.time()
            try:
                # Execute via CommandAgent
                if execution_request.chat_history:
                    print("🔍 DEBUG: Using execute_stream with chat history")
                    result = command_agent.execute_stream(
                        execution_request.query, execution_request.chat_history
                    )
                else:
                    print("🔍 DEBUG: Using regular execute without chat history")
                    result = command_agent.execute(
                        query=execution_request.query,
                        enable_analytics=False,  # Disable analytics to avoid potential issues
                    )
                execution_time = time.time() - start_time
                print(
                    f"🔍 DEBUG: CommandAgent execution completed in {execution_time:.2f} seconds"
                )
            except TimeoutError as e:
                print(f"🔍 DEBUG: Timeout error: {e}")
                raise HTTPException(
                    status_code=504, detail="CommandAgent execution timed out"
                )
            except Exception as e:
                execution_time = time.time() - start_time
                print(
                    f"🔍 DEBUG: CommandAgent execution failed after {execution_time:.2f} seconds: {e}"
                )
                raise
            finally:
                signal.alarm(0)  # Cancel timeout

        # Ensure response is in JSON format expected by frontend
        import json

        if isinstance(result, str):
            # Wrap plain text response in JSON format
            formatted_response = json.dumps({"content": result})
        else:
            # If already a dict/object, convert to JSON string
            formatted_response = (
                json.dumps(result) if not isinstance(result, str) else result
            )

        return schemas.WorkflowExecutionResponse(
            status="success",
            response=formatted_response,
            workflow_id=str(workflow_id),
            deployment_id="",  # Empty string instead of None
            timestamp=datetime.now().isoformat(),
        )

    except Exception as e:
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
                    # Use agent's streaming execution
                    for chunk in agent.execute_stream(
                        execution_request.query, execution_request.chat_history
                    ):
                        if chunk:
                            yield f"data: {json.dumps({'type': 'content', 'data': chunk, 'timestamp': datetime.now().isoformat()})}\n\n"
                            await asyncio.sleep(0.01)
                else:
                    # Fallback to regular execution
                    result = agent.execute(
                        query=execution_request.query,
                        chat_history=execution_request.chat_history,
                    )
                    yield f"data: {json.dumps({'type': 'content', 'data': result, 'timestamp': datetime.now().isoformat()})}\n\n"
            else:
                # Multi-agent workflow - use CommandAgent for orchestration
                command_agent = _build_command_agent_from_workflow(db, workflow)

                # Execute with streaming
                if execution_request.chat_history:
                    # Use streaming execution with chat history
                    for chunk in command_agent.execute_stream(
                        execution_request.query, execution_request.chat_history
                    ):
                        if chunk:
                            yield f"data: {json.dumps({'type': 'content', 'data': chunk, 'timestamp': datetime.now().isoformat()})}\n\n"
                            await asyncio.sleep(0.01)
                else:
                    # For non-streaming execution, simulate streaming by chunking the response
                    result = command_agent.execute(query=execution_request.query)
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

    print(
        f"🔍 DEBUG: _build_single_agent_from_workflow called with agent_config: {agent_config}"
    )

    # Get agent type and ID from config
    agent_type = agent_config.get("agent_type", "CommandAgent")
    agent_id = agent_config.get("agent_id")
    print(f"🔍 DEBUG: agent_type: {agent_type}, agent_id: {agent_id}")

    # Try to get the agent from database if agent_id is provided
    db_agent = None
    if agent_id:
        try:
            print(f"🔍 DEBUG: Looking up agent by ID: {agent_id}")
            db_agent = crud.get_agent(db, uuid.UUID(agent_id))
            print(
                f"🔍 DEBUG: Found agent by ID: {db_agent.name if db_agent else 'None'}"
            )
        except (ValueError, TypeError) as e:
            print(f"🔍 DEBUG: Error looking up by ID: {e}, trying by name")
            # If agent_id is invalid, try to find by name
            db_agent = crud.get_agent_by_name(db, agent_type)
            print(
                f"🔍 DEBUG: Found agent by name: {db_agent.name if db_agent else 'None'}"
            )
    else:
        # Find agent by type/name
        print(f"🔍 DEBUG: Looking up agent by name: {agent_type}")
        db_agent = crud.get_agent_by_name(db, agent_type)
        print(f"🔍 DEBUG: Found agent by name: {db_agent.name if db_agent else 'None'}")

    if not db_agent:
        print("🔍 DEBUG: No agent found, falling back to CommandAgent")
        # Fallback to CommandAgent if agent not found
        return _build_command_agent_from_workflow(db, workflow)

    from typing import cast
    from openai.types.chat.chat_completion_tool_param import ChatCompletionToolParam
    from data_classes import PromptObject

    print("🔍 DEBUG: Starting PromptObject construction")
    print(f"🔍 DEBUG: db_agent.system_prompt type: {type(db_agent.system_prompt)}")

    try:
        # Check if system_prompt exists and has required attributes
        if not hasattr(db_agent, "system_prompt") or db_agent.system_prompt is None:
            print("🔍 DEBUG: No system_prompt found, using fallback")
            # Use a simple fallback
            system_prompt = db_agent.system_prompt
        else:
            print("🔍 DEBUG: Constructing PromptObject with all fields")
            system_prompt = PromptObject(
                appName="",
                createdTime=getattr(db_agent.system_prompt, "created_time", None),
                prompt=getattr(db_agent.system_prompt, "prompt", ""),
                uniqueLabel=getattr(db_agent.system_prompt, "unique_label", ""),
                pid=getattr(db_agent.system_prompt, "pid", None),
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
        print("🔍 DEBUG: PromptObject constructed successfully")
    except Exception as e:
        print(f"🔍 DEBUG: Error constructing PromptObject: {e}")
        print("🔍 DEBUG: Using original system_prompt as fallback")
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
            if target_agent and target_agent.name in agent_schemas:
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

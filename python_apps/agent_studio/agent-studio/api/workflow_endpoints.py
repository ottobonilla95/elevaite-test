import uuid
import json
import asyncio
import time
from typing import List, Optional, Dict, Any
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
    BackgroundTasks,
    UploadFile,
    File,
    Form,
)
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from db.database import get_db
from db import crud, schemas, models
from agents.command_agent import CommandAgent
from agents.agent_base import Agent

# from agents import agent_schemas  # Commented out - Redis dependent
from services.workflow_execution_context import WorkflowExecutionContext
from services.workflow_execution_handlers import (
    execute_deterministic_workflow,
    execute_hybrid_workflow,
    execute_workflow_background,
)
from services.workflow_execution_utils import (
    is_deterministic_workflow,
    is_hybrid_workflow,
)
from services.workflow_agent_builders import (
    build_dynamic_agent_store,
    build_single_agent_from_workflow,
    build_toshiba_agent_from_workflow,
    build_command_agent_from_workflow,
)
from schemas.deterministic_workflow import (
    WorkflowExecutionRequest as DetWorkflowExecutionRequest,
)
from datetime import datetime
import json
import time

# from utils import agent_schema
from typing import List

router = APIRouter(prefix="/api/workflows", tags=["workflows"])

# Global variable to store active workflow deployments
ACTIVE_WORKFLOWS = {}


async def process_file_through_vectorizer(
    file_path: str,
    file_name: str,
    workflow_config: Dict[str, Any],
    execution_context: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Process an uploaded file through the vectorization pipeline.

    This function runs the file through the tokenizer steps:
    1. File reading with enhanced parsing
    2. Text chunking with intelligent segmentation
    3. Embedding generation
    4. Vector storage in Qdrant

    Returns processing results and metadata.
    """
    import logging

    logger = logging.getLogger(__name__)

    try:
        # Import tokenizer steps
        from services.tokenizer_steps_registry import tokenizer_steps_registry

        # Get workflow steps to find vectorizer configuration
        steps = workflow_config.get("steps", [])
        vectorizer_steps = [
            step
            for step in steps
            if step.get("step_type")
            in [
                "file_reader",
                "text_chunking",
                "embedding_generation",
                "vector_storage",
            ]
        ]

        if not vectorizer_steps:
            return {"status": "error", "error": "No vectorizer steps found in workflow"}

        logger.info(f"🔄 Processing {file_name} through {len(vectorizer_steps)} vectorizer steps")

        # Initialize processing context
        processing_data = {
            "file_path": file_path,
            "file_name": file_name,
            "execution_context": execution_context,
        }

        # Step 1: File reading
        file_reader_impl = tokenizer_steps_registry.get_step_implementation("file_reader")
        if file_reader_impl:
            logger.info("📖 Running file reader step...")
            file_reader_config = {
                "step_id": "file_upload_reader",
                "step_name": "File Upload Reader",
                "config": {
                    "file_path": file_path,
                    "enhanced_parsing": True,
                    "extract_metadata": True,
                },
            }
            file_result = await file_reader_impl(file_reader_config, processing_data, execution_context)
            processing_data.update(file_result)
            logger.info(f"✅ File reading completed: {len(file_result.get('content', ''))} characters")

        # Step 2: Text chunking
        text_chunking_impl = tokenizer_steps_registry.get_step_implementation("text_chunking")
        if text_chunking_impl:
            logger.info("✂️ Running text chunking step...")
            chunking_config = {
                "step_id": "file_upload_chunking",
                "step_name": "File Upload Chunking",
                "config": {
                    "chunk_size": 1000,
                    "chunk_overlap": 200,
                    "chunking_strategy": "intelligent",
                    "preserve_structure": True,
                },
            }
            chunk_result = await text_chunking_impl(chunking_config, processing_data, execution_context)
            processing_data.update(chunk_result)
            chunks = chunk_result.get("chunks", [])
            logger.info(f"✅ Text chunking completed: {len(chunks)} chunks created")

        # Step 3: Embedding generation
        embedding_impl = tokenizer_steps_registry.get_step_implementation("embedding_generation")
        if embedding_impl:
            logger.info("🧠 Running embedding generation step...")
            embedding_config = {
                "step_id": "file_upload_embeddings",
                "step_name": "File Upload Embeddings",
                "config": {
                    "embedding_model": "text-embedding-3-small",
                    "batch_size": 50,
                },
            }
            embedding_result = await embedding_impl(embedding_config, processing_data, execution_context)
            processing_data.update(embedding_result)
            embeddings = embedding_result.get("embeddings", [])
            logger.info(f"✅ Embedding generation completed: {len(embeddings)} embeddings created")

        # Step 4: Vector storage
        vector_storage_impl = tokenizer_steps_registry.get_step_implementation("vector_storage")
        if vector_storage_impl:
            logger.info("💾 Running vector storage step...")
            # Use session-specific collection name
            collection_name = f"uploaded_docs_{execution_context.get('session_id', 'default')}"
            storage_config = {
                "step_id": "file_upload_storage",
                "step_name": "File Upload Storage",
                "config": {
                    "collection_name": collection_name,
                    "vector_size": 1536,  # text-embedding-3-small dimension
                    "create_collection": True,
                },
            }
            storage_result = await vector_storage_impl(storage_config, processing_data, execution_context)
            processing_data.update(storage_result)
            logger.info(f"✅ Vector storage completed: stored in collection '{collection_name}'")

        # Return processing summary
        return {
            "status": "success",
            "file_name": file_name,
            "collection_name": collection_name,
            "chunks_count": len(chunks),
            "embeddings_count": len(embeddings),
            "processing_time": processing_data.get("processing_time"),
            "metadata": processing_data.get("metadata", {}),
            "message": f"Successfully processed '{file_name}' into {len(chunks)} chunks and stored in collection '{collection_name}'",
        }

    except Exception as e:
        logger.error(f"❌ File vectorization failed: {e}")
        return {"status": "error", "error": str(e), "file_name": file_name}


@router.post("/", response_model=schemas.WorkflowResponse)
def create_workflow(workflow: schemas.WorkflowCreate, db: Session = Depends(get_db)):
    """Create a new workflow with agents and connections"""
    try:
        # Check if workflow with same name and version already exists
        existing = crud.workflows.get_workflow_by_name(db, workflow.name, workflow.version)
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
                        connection_type=connection_config.get("connection_type", "default"),
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
    workflows = crud.get_workflows(db, skip=skip, limit=limit, is_active=is_active, is_deployed=is_deployed)
    return workflows


@router.get("/{workflow_id}", response_model=schemas.WorkflowResponse)
def get_workflow(workflow_id: uuid.UUID, db: Session = Depends(get_db)):
    """Get a specific workflow by ID with all related data"""
    workflow = crud.get_workflow(db, workflow_id)
    if not workflow:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workflow not found")

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
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workflow not found")
    return workflow


@router.delete("/{workflow_id}")
def delete_workflow(workflow_id: uuid.UUID, db: Session = Depends(get_db)):
    """Delete a workflow"""
    success = crud.delete_workflow(db, workflow_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workflow not found")
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
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workflow not found")

    # Verify agent exists
    agent = crud.get_agent(db, workflow_agent.agent_id)
    if not agent:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")

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


@router.post("/{workflow_id}/connections", response_model=schemas.WorkflowConnectionResponse)
def add_connection_to_workflow(
    workflow_id: uuid.UUID,
    connection: schemas.WorkflowConnectionCreate,
    db: Session = Depends(get_db),
):
    """Add a connection between agents in a workflow"""
    # Verify workflow exists
    workflow = crud.get_workflow(db, workflow_id)
    if not workflow:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workflow not found")

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
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workflow not found")

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
        workflow_update = schemas.WorkflowUpdate(is_deployed=True, deployed_at=db_deployment.deployed_at)
        crud.update_workflow(db, workflow_id, workflow_update)

        # Build and store the CommandAgent for this deployment
        command_agent = build_command_agent_from_workflow(db, workflow)
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


@router.get("/deployments/active", response_model=List[schemas.WorkflowDeploymentResponse])
def list_active_deployments(db: Session = Depends(get_db)):
    """List all active workflow deployments"""
    deployments = crud.workflows.get_active_workflow_deployments(db)
    return deployments


@router.post("/deployments/{deployment_name}/stop")
def stop_workflow_deployment(deployment_name: str, db: Session = Depends(get_db)):
    """Stop/undeploy a workflow deployment by name"""
    try:
        # Find the deployment by name (try development first, then production)
        deployment = crud.workflows.get_workflow_deployment_by_name(db, deployment_name, "development")
        if not deployment:
            deployment = crud.workflows.get_workflow_deployment_by_name(db, deployment_name, "production")

        if not deployment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Deployment '{deployment_name}' not found in development or production environment",
            )

        # Update deployment status to inactive
        deployment_update = schemas.WorkflowDeploymentUpdate(status="inactive")
        updated_deployment = crud.update_workflow_deployment(db, deployment.deployment_id, deployment_update)

        if not updated_deployment:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update deployment '{deployment_name}'",
            )

        # Check if there are any other active deployments for this workflow
        active_deployments = crud.workflows.get_active_workflow_deployments(db, deployment.workflow_id)
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
            "stopped_at": (updated_deployment.stopped_at.isoformat() if updated_deployment.stopped_at else None),
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
    """Execute a workflow by workflow ID (supports single-agent, multi-agent, and deterministic workflows)"""
    # Verify workflow exists
    workflow = crud.get_workflow(db, workflow_id)
    if not workflow:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workflow not found")

    try:
        # Check if this is a pure deterministic workflow
        if is_deterministic_workflow(workflow.configuration):
            import asyncio

            return asyncio.run(execute_deterministic_workflow(workflow, execution_request, db))

        # Check if this is a hybrid workflow with conditional execution
        if is_hybrid_workflow(workflow.configuration):
            return execute_hybrid_workflow(workflow, execution_request, db)

        # Determine if this is a single-agent or multi-agent workflow
        agents = workflow.configuration.get("agents", [])
        is_single_agent = len(agents) == 1

        if is_single_agent:
            # Single-agent workflow - execute agent directly with its own prompt
            agent_config = agents[0]
            agent_type = agent_config.get("agent_type", "CommandAgent")

            if agent_type == "ToshibaAgent":
                # Build ToshibaAgent directly
                agent = build_toshiba_agent_from_workflow(db, workflow, agent_config)
            else:
                # Build other single agents directly
                agent = build_single_agent_from_workflow(db, workflow, agent_config)

            # Build dynamic agent store for inter-agent communication
            dynamic_agent_store = build_dynamic_agent_store(db, workflow)

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
                    # Wait for result with 90 second timeout
                    result = future.result(timeout=90)
                except concurrent.futures.TimeoutError:
                    # Cancel the future
                    future.cancel()
                    raise HTTPException(
                        status_code=504,
                        detail="Agent execution timed out after 90 seconds",
                    )
                except Exception as e:
                    raise
        else:
            # Multi-agent workflow - use CommandAgent for orchestration
            command_agent = build_command_agent_from_workflow(db, workflow)

            # Build dynamic agent store for inter-agent communication
            dynamic_agent_store = build_dynamic_agent_store(db, workflow)

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
                    session_id = execution_request.session_id or f"workflow_{workflow_id}_{int(time.time())}"
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
                    # Wait for result with 90 second timeout
                    result = future.result(timeout=90)
                except concurrent.futures.TimeoutError:
                    # Cancel the future
                    future.cancel()
                    raise HTTPException(
                        status_code=504,
                        detail="CommandAgent execution timed out after 90 seconds",
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
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workflow not found")

    # Check if this is a pure deterministic workflow before starting the stream
    if is_deterministic_workflow(workflow.configuration):
        raise HTTPException(
            status_code=400,
            detail="Deterministic workflows do not support streaming execution. Use the regular execute endpoint instead.",
        )

    async def stream_generator():
        """Generate streaming response chunks"""
        try:
            # Send initial status
            yield f"data: {json.dumps({'status': 'started', 'workflow_id': str(workflow_id), 'timestamp': datetime.now().isoformat()})}\n\n"

            # Check if this is a hybrid workflow with conditional execution
            if is_hybrid_workflow(workflow.configuration):
                # Hybrid workflows support streaming - route to hybrid execution with streaming
                yield f"data: {json.dumps({'status': 'routing', 'message': 'Executing hybrid workflow with streaming support', 'timestamp': datetime.now().isoformat()})}\n\n"

                # TODO: Implement hybrid workflow streaming execution
                # For now, return a placeholder response
                yield f"data: {json.dumps({'status': 'error', 'message': 'Hybrid workflow streaming not yet implemented. Use the regular execute endpoint.', 'timestamp': datetime.now().isoformat()})}\n\n"
                return

            # Determine if this is a single-agent or multi-agent workflow
            agents = workflow.configuration.get("agents", [])
            is_single_agent = len(agents) == 1

            if is_single_agent:
                # Single-agent workflow - execute agent directly with its own prompt
                agent_config = agents[0]
                agent_type = agent_config.get("agent_type", "CommandAgent")

                if agent_type == "ToshibaAgent":
                    # Build ToshibaAgent directly
                    agent = build_toshiba_agent_from_workflow(db, workflow, agent_config)
                else:
                    # Build other single agents directly
                    agent = build_single_agent_from_workflow(db, workflow, agent_config)

                # Check if agent has streaming capability
                if hasattr(agent, "execute_stream") and callable(getattr(agent, "execute_stream")):
                    # Use agent's streaming execution (note: streaming doesn't support analytics yet)
                    for chunk in agent.execute_stream(execution_request.query, execution_request.chat_history):
                        if chunk:
                            yield f"data: {json.dumps({'type': chunk.type, 'data': chunk.message, 'timestamp': datetime.now().isoformat()})}\n\n"
                            await asyncio.sleep(0.01)
                else:
                    # Fallback to regular execution with analytics
                    session_id = execution_request.session_id or f"workflow_{workflow_id}_{int(time.time())}"
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
                command_agent = build_command_agent_from_workflow(db, workflow)

                # Build dynamic agent store for inter-agent communication
                dynamic_agent_store = build_dynamic_agent_store(db, workflow)

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
                    session_id = execution_request.session_id or f"workflow_{workflow_id}_{int(time.time())}"
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


@router.post("/{workflow_id}/execute/async", status_code=status.HTTP_202_ACCEPTED)
async def execute_workflow_async(
    workflow_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    # Support both JSON body (backward compatibility) and form data (with file uploads)
    query: Optional[str] = Form(None),
    chat_history: Optional[str] = Form(None),  # JSON string
    runtime_overrides: Optional[str] = Form(None),  # JSON string
    session_id: Optional[str] = Form(None),
    user_id: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
    # Also support JSON body for backward compatibility
    execution_request: Optional[schemas.WorkflowExecutionRequest] = None,
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
        # Handle both form data (with file) and JSON body (backward compatibility)
        if execution_request is None:
            # Build execution request from form data
            parsed_chat_history = None
            if chat_history:
                try:
                    parsed_chat_history = json.loads(chat_history)
                except json.JSONDecodeError:
                    logger.warning(f"Invalid chat_history JSON: {chat_history}")

            parsed_runtime_overrides = None
            if runtime_overrides:
                try:
                    parsed_runtime_overrides = json.loads(runtime_overrides)
                except json.JSONDecodeError:
                    logger.warning(f"Invalid runtime_overrides JSON: {runtime_overrides}")

            execution_request = schemas.WorkflowExecutionRequest(
                query=query or "",
                chat_history=parsed_chat_history,
                runtime_overrides=parsed_runtime_overrides,
                session_id=session_id,
                user_id=user_id,
            )

        # Get workflow to check if it's hybrid with vectorizer steps
        workflow = crud.get_workflow(db=db, workflow_id=workflow_id)
        if not workflow:
            raise HTTPException(status_code=404, detail="Workflow not found")

        # Check if this is a hybrid workflow with vectorizer capabilities
        is_hybrid = is_hybrid_workflow(workflow.configuration)
        has_vectorizer_steps = False
        file_processing_result = None

        # Check for vectorizer steps in workflow configuration (for both hybrid and deterministic workflows)
        steps = workflow.configuration.get("steps", [])
        vectorizer_step_types = [
            "file_reader",
            "text_chunking",
            "embedding_generation",
            "vector_storage",
        ]
        has_vectorizer_steps = any(
            step.get("step_type") in vectorizer_step_types
            or step.get("config", {}).get("tokenizer_step") in vectorizer_step_types
            for step in steps
        )

        logger.info(
            f"Workflow analysis - Hybrid: {is_hybrid}, Has vectorizer: {has_vectorizer_steps}, File provided: {file is not None}"
        )

        # Process file if provided and workflow supports it
        temp_file_path = None
        if file and has_vectorizer_steps:
            logger.info(f"🔄 Preparing uploaded file for workflow: {file.filename}")

            # Save uploaded file temporarily for workflow to process
            import tempfile
            import os

            try:
                # Create temporary file
                temp_dir = tempfile.mkdtemp()
                temp_file_path = os.path.join(temp_dir, file.filename or "uploaded_file")

                # Save uploaded file
                content = await file.read()
                with open(temp_file_path, "wb") as f:
                    f.write(content)

                logger.info(f"📁 Saved file for workflow processing: {temp_file_path}")

                # Add file context to chat history
                file_context = {
                    "role": "system",
                    "content": f"A file named '{file.filename}' has been uploaded and will be processed by the workflow.",
                }

                if execution_request.chat_history is None:
                    execution_request.chat_history = []
                execution_request.chat_history.insert(0, file_context)

                file_processing_result = {
                    "status": "uploaded",
                    "file_path": temp_file_path,
                    "file_name": file.filename,
                }

            except Exception as file_error:
                logger.error(f"❌ File upload failed: {file_error}")
                file_processing_result = {"status": "error", "error": str(file_error)}

        elif file and not has_vectorizer_steps:
            logger.warning("🚨 File uploaded but workflow does not contain vectorizer steps - file will be ignored")

        elif not file and has_vectorizer_steps:
            logger.info("ℹ️ Workflow has vectorizer capabilities but no file was uploaded")

        # Store file processing result in runtime overrides for the workflow
        if file_processing_result:
            if execution_request.runtime_overrides is None:
                execution_request.runtime_overrides = {}
            execution_request.runtime_overrides["file_processing_result"] = file_processing_result

        # If we have an uploaded file and vectorizer steps, modify workflow config directly
        if temp_file_path and has_vectorizer_steps:
            logger.info(f"🔧 Injecting uploaded file path into workflow step configurations")

            # Directly modify the workflow configuration to use uploaded file
            # This ensures the file_reader step gets the file_path in its config
            modified_steps = []
            for step in workflow.configuration.get("steps", []):
                if step.get("step_type") == "file_reader":
                    # Create a modified step with the uploaded file path
                    modified_step = step.copy()
                    if "config" not in modified_step:
                        modified_step["config"] = {}

                    modified_step["config"]["file_path"] = temp_file_path
                    modified_step["config"]["file_name"] = file.filename or "uploaded_file"
                    modified_steps.append(modified_step)
                    logger.info(f"✅ Injected file path into file_reader step config: {temp_file_path}")
                else:
                    modified_steps.append(step)

            # Store the modified workflow configuration in runtime overrides
            # so the workflow execution can use it instead of the original
            if execution_request.runtime_overrides is None:
                execution_request.runtime_overrides = {}

            modified_workflow_config = workflow.configuration.copy()
            modified_workflow_config["steps"] = modified_steps
            execution_request.runtime_overrides["modified_workflow_config"] = modified_workflow_config

            # Also store cleanup info
            execution_request.runtime_overrides["uploaded_file"] = {
                "file_path": temp_file_path,
                "file_name": file.filename or "uploaded_file",
                "temp_cleanup_required": True,
            }

            logger.info(f"✅ Modified workflow configuration to use uploaded file")
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
            execute_workflow_background,
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

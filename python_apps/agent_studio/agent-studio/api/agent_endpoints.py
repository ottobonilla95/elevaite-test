import os
import sys
import json
import asyncio
from typing import List, Optional, Dict, Any
import uuid
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime

# Add the parent directory to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

# Use absolute imports
from db.database import get_db
from db import crud, schemas, models

router = APIRouter(prefix="/api/agents", tags=["agents"])


def _create_agent_instance_from_db(db: Session, db_agent: models.Agent):
    """
    Helper function to create an Agent instance from a database record with proper type casting.
    """
    from agents.agent_base import Agent
    from typing import cast, Literal

    # Safely cast input_type and output_type
    valid_io_types = ["text", "voice", "image"]
    input_type = (
        [t for t in db_agent.input_type if t in valid_io_types]
        if db_agent.input_type
        else ["text"]
    )
    output_type = (
        [t for t in db_agent.output_type if t in valid_io_types]
        if db_agent.output_type
        else ["text"]
    )

    # Safely cast response_type
    valid_response_types = ["json", "yaml", "markdown", "HTML", "None"]
    response_type = (
        db_agent.response_type
        if db_agent.response_type in valid_response_types
        else "json"
    )

    # Safely cast status
    valid_statuses = ["active", "paused", "terminated"]
    status = db_agent.status if db_agent.status in valid_statuses else "active"

    # Safely cast collaboration_mode
    valid_collaboration_modes = ["single", "team", "parallel", "sequential"]
    collaboration_mode = (
        db_agent.collaboration_mode
        if db_agent.collaboration_mode in valid_collaboration_modes
        else "single"
    )

    system_prompt = crud.get_prompt(db, db_agent.system_prompt_id)

    return Agent(
        name=db_agent.name,
        agent_id=db_agent.agent_id,
        system_prompt=system_prompt,
        persona=db_agent.persona,
        functions=cast(
            List[Any], db_agent.functions
        ),  # Cast to List[Any] for compatibility
        routing_options=db_agent.routing_options,
        short_term_memory=db_agent.short_term_memory,
        long_term_memory=db_agent.long_term_memory,
        reasoning=db_agent.reasoning,
        input_type=cast(List[Literal["text", "voice", "image"]], input_type),
        output_type=cast(List[Literal["text", "voice", "image"]], output_type),
        response_type=cast(
            Literal["json", "yaml", "markdown", "HTML", "None"], response_type
        ),
        max_retries=db_agent.max_retries,
        timeout=db_agent.timeout,
        deployed=db_agent.deployed,
        status=cast(Literal["active", "paused", "terminated"], status),
        priority=db_agent.priority,
        failure_strategies=db_agent.failure_strategies,
        collaboration_mode=cast(
            Literal["single", "team", "parallel", "sequential"], collaboration_mode
        ),
    )


class DeploymentCodeUpdate(BaseModel):
    deployment_code: str


class DeploymentStatusUpdate(BaseModel):
    available_for_deployment: bool


class AgentExecutionRequest(BaseModel):
    query: str
    session_id: Optional[str] = None
    user_id: Optional[str] = None
    chat_history: Optional[List[Dict[str, Any]]] = None
    enable_analytics: bool = False


class AgentExecutionResponse(BaseModel):
    status: str
    response: str
    agent_id: str
    execution_time: Optional[float] = None
    timestamp: str


class AgentStreamExecutionRequest(BaseModel):
    query: str
    chat_history: Optional[List[Dict[str, Any]]] = None


@router.post("/", response_model=schemas.AgentResponse)
def create_agent(agent: schemas.AgentCreate, db: Session = Depends(get_db)):
    """
    Create a new agent.
    """
    return crud.create_agent(db=db, agent=agent)


@router.get("/", response_model=List[schemas.AgentResponse])
def read_agents(
    skip: int = 0,
    limit: int = 100,
    deployed: Optional[bool] = None,
    db: Session = Depends(get_db),
):
    """
    Get a list of agents with optional filtering by deployment status.
    """
    return crud.get_agents(db=db, skip=skip, limit=limit, deployed=deployed)


@router.get("/{agent_id}", response_model=schemas.AgentResponse)
def read_agent(agent_id: uuid.UUID, db: Session = Depends(get_db)):
    """
    Get an agent by ID.
    """
    db_agent = crud.get_agent(db=db, agent_id=agent_id)
    if db_agent is None:
        raise HTTPException(status_code=404, detail="Agent not found")
    return db_agent


@router.get("/name/{name}", response_model=schemas.AgentResponse)
def read_agent_by_name(name: str, db: Session = Depends(get_db)):
    """
    Get an agent by name.
    """
    db_agent = crud.get_agent_by_name(db=db, name=name)
    if db_agent is None:
        raise HTTPException(status_code=404, detail="Agent not found")
    return db_agent


@router.put("/{agent_id}", response_model=schemas.AgentResponse)
def update_agent(
    agent_id: uuid.UUID,
    agent_update: schemas.AgentUpdate,
    db: Session = Depends(get_db),
):
    """
    Update an agent.
    """
    db_agent = crud.update_agent(db=db, agent_id=agent_id, agent_update=agent_update)
    if db_agent is None:
        raise HTTPException(status_code=404, detail="Agent not found")
    return db_agent


@router.delete("/{agent_id}", response_model=bool)
def delete_agent(agent_id: uuid.UUID, db: Session = Depends(get_db)):
    """
    Delete an agent.
    """
    success = crud.delete_agent(db=db, agent_id=agent_id)
    if not success:
        raise HTTPException(status_code=404, detail="Agent not found")
    return success


# @router.get("/deployment/available", response_model=List[schemas.AgentResponse])
# def get_available_agents(db: Session = Depends(get_db)):
#     """
#     Get all agents that are available for deployment.
#     """
#     return crud.get(db=db)


# @router.get("/deployment/codes", response_model=Dict[str, str])
# def get_deployment_codes(db: Session = Depends(get_db)):
#     """
#     Get a mapping of deployment codes to agent names.
#     """
#     agents = crud.get_available_agents(db=db)
#     code_map = {}
#     for agent in agents:
#         deployment_code = getattr(agent, "deployment_code", None)
#         if deployment_code is not None and str(deployment_code).strip() != "":
#             code_map[str(deployment_code)] = str(agent.name)
#     return code_map


# @router.put("/{agent_id}/deployment/code", response_model=schemas.AgentResponse)
# def update_deployment_code(
#     agent_id: uuid.UUID,
#     code_update: DeploymentCodeUpdate,
#     db: Session = Depends(get_db),
# ):
#     """
#     Update an agent's deployment code.
#     """
#     agents = crud.get_available_agents(db=db)
#     for agent in agents:
#         agent_deployment_code = getattr(agent, "deployment_code", None)
#         agent_id_str = str(getattr(agent, "agent_id", ""))
#         if (
#             agent_deployment_code is not None
#             and str(agent_deployment_code) == code_update.deployment_code
#             and agent_id_str != str(agent_id)
#         ):
#             raise HTTPException(
#                 status_code=400,
#                 detail=f"Deployment code '{code_update.deployment_code}' is already in use by agent '{agent.name}'",
#             )

#     agent_update = schemas.AgentUpdate(deployment_code=code_update.deployment_code)
#     db_agent = crud.update_agent(db=db, agent_id=agent_id, agent_update=agent_update)
#     if db_agent is None:
#         raise HTTPException(status_code=404, detail="Agent not found")
#     return db_agent


@router.put("/{agent_id}/deployment/status", response_model=schemas.AgentResponse)
def update_deployment_status(
    agent_id: uuid.UUID,
    status_update: DeploymentStatusUpdate,
    db: Session = Depends(get_db),
):
    """
    Update whether an agent is available for deployment.
    """
    agent_update = schemas.AgentUpdate(
        available_for_deployment=status_update.available_for_deployment
    )
    db_agent = crud.update_agent(db=db, agent_id=agent_id, agent_update=agent_update)
    if db_agent is None:
        raise HTTPException(status_code=404, detail="Agent not found")
    return db_agent


@router.post("/{agent_id}/execute", response_model=AgentExecutionResponse)
def execute_agent(
    agent_id: uuid.UUID,
    execution_request: AgentExecutionRequest,
    db: Session = Depends(get_db),
):
    """
    Execute a specific agent with the given query.
    """
    # Get the agent from database
    db_agent = crud.get_agent(db=db, agent_id=agent_id)
    if db_agent is None:
        raise HTTPException(status_code=404, detail="Agent not found")

    # Check if agent is available for execution
    if not db_agent.available_for_deployment:
        raise HTTPException(
            status_code=400, detail="Agent is not available for execution"
        )

    try:
        # Create an agent instance from the database record with proper type casting
        agent_instance = _create_agent_instance_from_db(db, db_agent)

        # Record start time
        start_time = datetime.now()

        # Execute the agent
        result = agent_instance.execute(
            query=execution_request.query,
            session_id=execution_request.session_id,
            user_id=execution_request.user_id,
            chat_history=execution_request.chat_history,
            enable_analytics=execution_request.enable_analytics,
        )

        # Calculate execution time
        end_time = datetime.now()
        execution_time = (end_time - start_time).total_seconds()

        return AgentExecutionResponse(
            status="success",
            response=result,
            agent_id=str(agent_id),
            execution_time=execution_time,
            timestamp=end_time.isoformat(),
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error executing agent: {str(e)}")


@router.post("/{agent_id}/execute/stream")
async def execute_agent_stream(
    agent_id: uuid.UUID,
    execution_request: AgentStreamExecutionRequest,
    db: Session = Depends(get_db),
):
    """
    Execute a specific agent with streaming response.
    """
    # Get the agent from database
    db_agent = crud.get_agent(db=db, agent_id=agent_id)
    if db_agent is None:
        raise HTTPException(status_code=404, detail="Agent not found")

    # Check if agent is available for execution
    if not db_agent.available_for_deployment:
        raise HTTPException(
            status_code=400, detail="Agent is not available for execution"
        )

    async def stream_generator():
        """Generate streaming response chunks"""
        try:
            # Send initial status
            yield f"data: {json.dumps({'status': 'started', 'agent_id': str(agent_id), 'agent_name': db_agent.name, 'timestamp': datetime.now().isoformat()})}\n\n"

            # Create an agent instance from the database record with proper type casting
            agent_instance = _create_agent_instance_from_db(db, db_agent)

            # Check if agent has execute_stream method
            if hasattr(agent_instance, "execute_stream") and callable(
                getattr(agent_instance, "execute_stream")
            ):
                # Use streaming execution
                execute_stream_method = getattr(agent_instance, "execute_stream")
                for chunk in execute_stream_method(
                    execution_request.query, execution_request.chat_history
                ):
                    if chunk:
                        # Wrap each chunk in a structured format
                        yield f"data: {json.dumps({'type': 'content', 'data': chunk, 'timestamp': datetime.now().isoformat()})}\n\n"
                        # Small delay to prevent overwhelming the client
                        await asyncio.sleep(0.01)
            else:
                # Fallback to regular execution and simulate streaming
                result = agent_instance.execute(
                    query=execution_request.query,
                    chat_history=execution_request.chat_history,
                )

                # Send the result as a single chunk
                yield f"data: {json.dumps({'type': 'content', 'data': result, 'timestamp': datetime.now().isoformat()})}\n\n"

            # Send completion status
            yield f"data: {json.dumps({'status': 'completed', 'agent_id': str(agent_id), 'timestamp': datetime.now().isoformat()})}\n\n"

        except Exception as e:
            # Send error as final chunk
            error_chunk = {
                "status": "error",
                "error": str(e),
                "agent_id": str(agent_id),
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

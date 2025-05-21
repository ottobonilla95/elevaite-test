import os
import sys
from typing import List, Optional, Dict
import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

# Add the parent directory to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

# Use absolute imports
from db.database import get_db
from db import crud, schemas

router = APIRouter(prefix="/api/agents", tags=["agents"])


class DeploymentCodeUpdate(BaseModel):
    deployment_code: str


class DeploymentStatusUpdate(BaseModel):
    available_for_deployment: bool


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


@router.get("/deployment/available", response_model=List[schemas.AgentResponse])
def get_available_agents(db: Session = Depends(get_db)):
    """
    Get all agents that are available for deployment.
    """
    return crud.get_available_agents(db=db)


@router.get("/deployment/codes", response_model=Dict[str, str])
def get_deployment_codes(db: Session = Depends(get_db)):
    """
    Get a mapping of deployment codes to agent names.
    """
    agents = crud.get_available_agents(db=db)
    code_map = {}
    for agent in agents:
        deployment_code = getattr(agent, "deployment_code", None)
        if deployment_code is not None and str(deployment_code).strip() != "":
            code_map[str(deployment_code)] = str(agent.name)
    return code_map


@router.put("/{agent_id}/deployment/code", response_model=schemas.AgentResponse)
def update_deployment_code(
    agent_id: uuid.UUID,
    code_update: DeploymentCodeUpdate,
    db: Session = Depends(get_db),
):
    """
    Update an agent's deployment code.
    """
    agents = crud.get_available_agents(db=db)
    for agent in agents:
        agent_deployment_code = getattr(agent, "deployment_code", None)
        agent_id_str = str(getattr(agent, "agent_id", ""))
        if (
            agent_deployment_code is not None
            and str(agent_deployment_code) == code_update.deployment_code
            and agent_id_str != str(agent_id)
        ):
            raise HTTPException(
                status_code=400,
                detail=f"Deployment code '{code_update.deployment_code}' is already in use by agent '{agent.name}'",
            )

    agent_update = schemas.AgentUpdate(deployment_code=code_update.deployment_code)
    db_agent = crud.update_agent(db=db, agent_id=agent_id, agent_update=agent_update)
    if db_agent is None:
        raise HTTPException(status_code=404, detail="Agent not found")
    return db_agent


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

import os
import sys
from typing import List, Optional
import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

# Add the parent directory to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

# Use absolute imports
from db.database import get_db
from db import crud, schemas

router = APIRouter(prefix="/api/agents", tags=["agents"])


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

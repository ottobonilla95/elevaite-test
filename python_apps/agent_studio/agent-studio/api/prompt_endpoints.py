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

router = APIRouter(prefix="/api/prompts", tags=["prompts"])


@router.post("/", response_model=schemas.PromptResponse)
def create_prompt(prompt: schemas.PromptCreate, db: Session = Depends(get_db)):
    """
    Create a new prompt.
    """
    return crud.create_prompt(db=db, prompt=prompt)


@router.get("/", response_model=List[schemas.PromptResponse])
def read_prompts(
    skip: int = 0,
    limit: int = 100,
    app_name: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """
    Get a list of prompts with optional filtering by app name.
    """
    return crud.get_prompts(db=db, skip=skip, limit=limit, app_name=app_name)


@router.get("/{prompt_id}", response_model=schemas.PromptResponse)
def read_prompt(prompt_id: uuid.UUID, db: Session = Depends(get_db)):
    """
    Get a prompt by ID.
    """
    db_prompt = crud.get_prompt(db=db, prompt_id=prompt_id)
    if db_prompt is None:
        raise HTTPException(status_code=404, detail="Prompt not found")
    return db_prompt


@router.get(
    "/app/{app_name}/label/{prompt_label}", response_model=List[schemas.PromptResponse]
)
def read_prompts_by_app_and_label(
    app_name: str, prompt_label: str, db: Session = Depends(get_db)
):
    """
    Get prompts by application name and label.
    """
    return crud.get_prompt_by_app_and_label(
        db=db, app_name=app_name, prompt_label=prompt_label
    )


@router.get(
    "/app/{app_name}/label/{prompt_label}/deployed",
    response_model=schemas.PromptResponse,
)
def read_deployed_prompt(
    app_name: str, prompt_label: str, db: Session = Depends(get_db)
):
    """
    Get the deployed prompt for an application and label.
    """
    db_prompt = crud.get_deployed_prompt(
        db=db, app_name=app_name, prompt_label=prompt_label
    )
    if db_prompt is None:
        raise HTTPException(status_code=404, detail="Deployed prompt not found")
    return db_prompt


@router.put("/{prompt_id}", response_model=schemas.PromptResponse)
def update_prompt(
    prompt_id: uuid.UUID,
    prompt_update: schemas.PromptUpdate,
    db: Session = Depends(get_db),
):
    """
    Update a prompt.
    """
    db_prompt = crud.update_prompt(
        db=db, prompt_id=prompt_id, prompt_update=prompt_update
    )
    if db_prompt is None:
        raise HTTPException(status_code=404, detail="Prompt not found")
    return db_prompt


@router.post("/deploy", response_model=schemas.PromptResponse)
def deploy_prompt(
    deploy_request: schemas.PromptDeployRequest, db: Session = Depends(get_db)
):
    """
    Deploy a prompt.
    """
    db_prompt = crud.deploy_prompt(
        db=db,
        prompt_id=deploy_request.pid,
        app_name=deploy_request.app_name,
        environment=deploy_request.environment,
    )
    if db_prompt is None:
        raise HTTPException(
            status_code=404, detail="Prompt not found or app name mismatch"
        )
    return db_prompt


@router.delete("/{prompt_id}", response_model=bool)
def delete_prompt(prompt_id: uuid.UUID, db: Session = Depends(get_db)):
    """
    Delete a prompt.
    """
    success = crud.delete_prompt(db=db, prompt_id=prompt_id)
    if not success:
        raise HTTPException(status_code=404, detail="Prompt not found")
    return success

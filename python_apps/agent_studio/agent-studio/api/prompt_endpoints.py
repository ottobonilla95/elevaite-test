"""
Prompt template endpoints for Agent Studio.

✅ FULLY MIGRATED TO SDK.
All endpoints use workflow-core-sdk PromptsService.
"""

from typing import List
import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

# SDK imports
from workflow_core_sdk import PromptsService
from workflow_core_sdk.services.prompts_service import PromptsQuery
from workflow_core_sdk.db.models import PromptCreate as SDKPromptCreate, PromptUpdate as SDKPromptUpdate, Prompt as SDKPrompt

# Database
from db.database import get_db
from db import schemas

router = APIRouter(prefix="/api/prompts", tags=["prompts"])


# Adapter: Convert SDK Prompt to Agent Studio PromptResponse
def sdk_prompt_to_response(sdk_prompt: SDKPrompt) -> schemas.PromptResponse:
    """
    Convert SDK Prompt model to Agent Studio PromptResponse schema.

    SDK Prompt has: id (UUID), created_time, updated_time
    AS PromptResponse expects: id (int), pid (UUID), sha_hash, is_deployed, version, created_time, deployed_time, last_deployed
    """
    # Generate a deterministic integer ID from UUID for backwards compatibility
    # Use the first 8 bytes of UUID as integer
    int_id = int(str(sdk_prompt.id).replace("-", "")[:16], 16) % (2**31)

    return schemas.PromptResponse(
        # Required AS fields
        id=int_id,  # Convert UUID to int for backwards compatibility
        pid=sdk_prompt.id,  # Use SDK id as pid (UUID)
        sha_hash="",  # Not in SDK, use empty string
        is_deployed=False,  # Not in SDK, default to False
        version="1.0",  # Not in SDK, use default
        # Common fields
        prompt_label=sdk_prompt.prompt_label,
        prompt=sdk_prompt.prompt,
        unique_label=sdk_prompt.unique_label,
        app_name=sdk_prompt.app_name,
        ai_model_provider=sdk_prompt.ai_model_provider,
        ai_model_name=sdk_prompt.ai_model_name,
        tags=sdk_prompt.tags or [],
        hyper_parameters=sdk_prompt.hyper_parameters or {},
        variables=sdk_prompt.variables or {},
        # Timestamps
        created_time=sdk_prompt.created_time,
        deployed_time=None,  # Not in SDK
        last_deployed=None,  # Not in SDK
    )


@router.post("/", response_model=schemas.PromptResponse)
def create_prompt(prompt: schemas.PromptCreate, db: Session = Depends(get_db)):
    """
    Create a new prompt template.

    ✅ MIGRATED TO SDK.
    """
    # Convert to SDK format (exclude sha_hash and version as they're not in SDK)
    prompt_data = prompt.model_dump()
    prompt_data.pop("sha_hash", None)  # Remove sha_hash if present
    prompt_data.pop("version", None)  # Remove version (AS-specific field)

    # Convert None to empty list/dict for SDK compatibility
    if prompt_data.get("tags") is None:
        prompt_data["tags"] = []
    if prompt_data.get("hyper_parameters") is None:
        prompt_data["hyper_parameters"] = {}
    if prompt_data.get("variables") is None:
        prompt_data["variables"] = {}

    sdk_prompt_create = SDKPromptCreate(**prompt_data)

    # Create prompt via SDK
    try:
        sdk_prompt = PromptsService.create_prompt(db, sdk_prompt_create)
    except ValueError as e:
        # Handle duplicate unique_label
        if "already exists" in str(e):
            raise HTTPException(status_code=409, detail=str(e))
        raise HTTPException(status_code=400, detail=str(e))

    # Convert to response format using adapter
    return sdk_prompt_to_response(sdk_prompt)


@router.get("/", response_model=List[schemas.PromptResponse])
def list_prompts(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    """
    List all prompt templates.

    ✅ MIGRATED TO SDK.
    """
    # Get prompts from SDK
    query = PromptsQuery(offset=skip, limit=limit)
    sdk_prompts = PromptsService.list_prompts(db, query)

    # Convert to response format using adapter
    return [sdk_prompt_to_response(prompt) for prompt in sdk_prompts]


@router.get("/{prompt_id}", response_model=schemas.PromptResponse)
def get_prompt(prompt_id: uuid.UUID, db: Session = Depends(get_db)):
    """
    Get a specific prompt template by ID.

    ✅ MIGRATED TO SDK.
    """
    # Get prompt from SDK
    sdk_prompt = PromptsService.get_prompt(db, str(prompt_id))

    if not sdk_prompt:
        raise HTTPException(status_code=404, detail="Prompt not found")

    # Convert to response format using adapter
    return sdk_prompt_to_response(sdk_prompt)


@router.put("/{prompt_id}", response_model=schemas.PromptResponse)
def update_prompt(
    prompt_id: uuid.UUID,
    prompt_update: schemas.PromptUpdate,
    db: Session = Depends(get_db),
):
    """
    Update a prompt template.

    ✅ MIGRATED TO SDK.
    """
    # Convert to SDK format (exclude AS-only fields)
    update_data = prompt_update.model_dump(exclude_unset=True)
    update_data.pop("is_deployed", None)  # Remove is_deployed if present (not in SDK)
    update_data.pop("version", None)  # Remove version (AS-specific field)
    sdk_update = SDKPromptUpdate(**update_data)

    # Update prompt via SDK
    try:
        sdk_prompt = PromptsService.update_prompt(db, str(prompt_id), sdk_update)
    except ValueError as e:
        if "not found" in str(e).lower():
            raise HTTPException(status_code=404, detail="Prompt not found")
        raise HTTPException(status_code=400, detail=str(e))

    if not sdk_prompt:
        raise HTTPException(status_code=404, detail="Prompt not found")

    # Convert to response format using adapter
    return sdk_prompt_to_response(sdk_prompt)


@router.delete("/{prompt_id}")
def delete_prompt(prompt_id: uuid.UUID, db: Session = Depends(get_db)):
    """
    Delete a prompt template.

    ✅ MIGRATED TO SDK.
    """
    # Delete prompt via SDK
    success = PromptsService.delete_prompt(db, str(prompt_id))

    if not success:
        raise HTTPException(status_code=404, detail="Prompt not found")

    return {"message": "Prompt deleted successfully", "prompt_id": str(prompt_id)}

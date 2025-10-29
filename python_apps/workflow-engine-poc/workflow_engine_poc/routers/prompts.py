"""
Prompts API router: CRUD for Prompts (top-level)
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session

from ..db.database import get_db_session
from ..db.models import PromptCreate, PromptRead, PromptUpdate
from ..services.prompts_service import PromptsService, PromptsQuery
from ..util import api_key_or_user_guard

router = APIRouter(prefix="/prompts", tags=["prompts"])


@router.post("/", response_model=PromptRead)
async def create_prompt(
    prompt: PromptCreate,
    session: Session = Depends(get_db_session),
    _principal: str = Depends(api_key_or_user_guard("create_prompt")),
):
    try:
        return PromptsService.create_prompt(session, prompt)
    except ValueError as ve:
        # duplicate unique_label within org
        raise HTTPException(status_code=409, detail=str(ve))


@router.get("/", response_model=List[PromptRead])
async def list_prompts(
    session: Session = Depends(get_db_session),
    organization_id: Optional[str] = Query(default=None),
    app_name: Optional[str] = Query(default=None),
    provider: Optional[str] = Query(default=None),
    model: Optional[str] = Query(default=None),
    tag: Optional[str] = Query(default=None),
    q: Optional[str] = Query(default=None),
    limit: int = 100,
    offset: int = 0,
    _principal: str = Depends(api_key_or_user_guard("view_prompt")),
):
    params = PromptsQuery(
        organization_id=organization_id,
        app_name=app_name,
        provider=provider,
        model=model,
        tag=tag,
        q=q,
        limit=limit,
        offset=offset,
    )
    return PromptsService.list_prompts(session, params)


@router.get("/{prompt_id}", response_model=PromptRead)
async def get_prompt(
    prompt_id: str,
    session: Session = Depends(get_db_session),
    _principal: str = Depends(api_key_or_user_guard("view_prompt")),
):
    prompt = PromptsService.get_prompt(session, prompt_id)
    if not prompt:
        raise HTTPException(status_code=404, detail="Prompt not found")
    return prompt


@router.patch("/{prompt_id}", response_model=PromptRead)
async def update_prompt(
    prompt_id: str,
    payload: PromptUpdate,
    session: Session = Depends(get_db_session),
    _principal: str = Depends(api_key_or_user_guard("edit_prompt")),
):
    try:
        return PromptsService.update_prompt(session, prompt_id, payload)
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))


@router.delete("/{prompt_id}")
async def delete_prompt(
    prompt_id: str,
    session: Session = Depends(get_db_session),
    _principal: str = Depends(api_key_or_user_guard("delete_prompt")),
):
    deleted = PromptsService.delete_prompt(session, prompt_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Prompt not found")
    return {"deleted": True}

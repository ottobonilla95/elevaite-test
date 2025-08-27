"""
Prompts API router: CRUD for Prompts (top-level)
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select

from ..db.database import get_db_session
from ..db.models import Prompt, PromptCreate, PromptRead, PromptUpdate

router = APIRouter(prefix="/prompts", tags=["prompts"])


@router.post("/", response_model=PromptRead)
async def create_prompt(prompt: PromptCreate, session: Session = Depends(get_db_session)):
    # uniqueness by unique_label within org
    if prompt.organization_id:
        existing = session.exec(
            select(Prompt).where(
                Prompt.unique_label == prompt.unique_label,
                Prompt.organization_id == prompt.organization_id,
            )
        ).first()
    else:
        existing = session.exec(select(Prompt).where(Prompt.unique_label == prompt.unique_label)).first()

    if existing:
        raise HTTPException(status_code=409, detail="Prompt with this unique_label already exists")

    db_prompt = Prompt(**prompt.model_dump())
    session.add(db_prompt)
    session.commit()
    session.refresh(db_prompt)

    return db_prompt


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
):
    query = select(Prompt)
    if organization_id:
        query = query.where(Prompt.organization_id == organization_id)
    if app_name:
        query = query.where(Prompt.app_name == app_name)
    if provider:
        query = query.where(Prompt.ai_model_provider == provider)
    if model:
        query = query.where(Prompt.ai_model_name == model)
    if tag:
        query = query.where(Prompt.tags.contains([tag]))
    if q:
        query = query.where(Prompt.prompt_label.contains(q))

    prompts = session.exec(query.offset(offset).limit(limit)).all()

    return prompts


@router.get("/{prompt_id}", response_model=PromptRead)
async def get_prompt(prompt_id: str, session: Session = Depends(get_db_session)):
    from uuid import UUID

    prompt = session.exec(select(Prompt).where(Prompt.id == UUID(prompt_id))).first()
    if not prompt:
        raise HTTPException(status_code=404, detail="Prompt not found")

    return prompt


@router.patch("/{prompt_id}", response_model=PromptRead)
async def update_prompt(prompt_id: str, payload: PromptUpdate, session: Session = Depends(get_db_session)):
    from uuid import UUID

    db_prompt = session.exec(select(Prompt).where(Prompt.id == UUID(prompt_id))).first()
    if not db_prompt:
        raise HTTPException(status_code=404, detail="Prompt not found")

    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(db_prompt, k, v)

    session.add(db_prompt)
    session.commit()
    session.refresh(db_prompt)

    return db_prompt


@router.delete("/{prompt_id}")
async def delete_prompt(prompt_id: str, session: Session = Depends(get_db_session)):
    from uuid import UUID

    db_prompt = session.exec(select(Prompt).where(Prompt.id == UUID(prompt_id))).first()
    if not db_prompt:
        raise HTTPException(status_code=404, detail="Prompt not found")

    session.delete(db_prompt)
    session.commit()
    return {"deleted": True}

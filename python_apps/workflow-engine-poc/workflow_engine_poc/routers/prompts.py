"""
Prompts API router: CRUD for Prompts (top-level)
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session
from rbac_sdk.fastapi_helpers import require_permission_async, resource_builders, principal_resolvers

from ..db.database import get_db_session
from ..db.models import PromptCreate, PromptRead, PromptUpdate
from ..services.prompts_service import PromptsService, PromptsQuery

# RBAC header constants
HDR_PROJECT_ID = "X-elevAIte-ProjectId"
HDR_ACCOUNT_ID = "X-elevAIte-AccountId"
HDR_ORG_ID = "X-elevAIte-OrganizationId"

router = APIRouter(prefix="/prompts", tags=["prompts"])

# RBAC guards: view_project (read-only) and edit_project (create/update/delete)
_guard_view_project = require_permission_async(
    action="view_project",
    resource_builder=resource_builders.project_from_headers(
        project_header=HDR_PROJECT_ID,
        account_header=HDR_ACCOUNT_ID,
        org_header=HDR_ORG_ID,
    ),
    principal_resolver=principal_resolvers.api_key_or_user(),
)

_guard_edit_project = require_permission_async(
    action="edit_project",
    resource_builder=resource_builders.project_from_headers(
        project_header=HDR_PROJECT_ID,
        account_header=HDR_ACCOUNT_ID,
        org_header=HDR_ORG_ID,
    ),
    principal_resolver=principal_resolvers.api_key_or_user(),
)


@router.post("/", response_model=PromptRead)
async def create_prompt(
    prompt: PromptCreate,
    session: Session = Depends(get_db_session),
    _principal: str = Depends(_guard_edit_project),
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
    _principal: str = Depends(_guard_view_project),
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
    _principal: str = Depends(_guard_view_project),
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
    _principal: str = Depends(_guard_edit_project),
):
    try:
        return PromptsService.update_prompt(session, prompt_id, payload)
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))


@router.delete("/{prompt_id}")
async def delete_prompt(
    prompt_id: str,
    session: Session = Depends(get_db_session),
    _principal: str = Depends(_guard_edit_project),
):
    deleted = PromptsService.delete_prompt(session, prompt_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Prompt not found")
    return {"deleted": True}

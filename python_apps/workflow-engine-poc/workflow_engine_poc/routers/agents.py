"""
Agents API router: CRUD for Agents, and Tool bindings
"""

from typing import List, Optional, Dict, Any
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form, Security, Header
from fastapi.security.api_key import APIKeyHeader
from sqlmodel import Session, select

# Provider config validation models
from pydantic import BaseModel, ValidationError
from enum import Enum

from workflow_engine_poc.util import api_key_or_user_guard

from ..db.database import get_db_session
from ..db.models import (
    Agent,
    AgentCreate,
    AgentRead,
    AgentUpdate,
    AgentToolBinding,
    Prompt,
)
from ..services.agents_service import AgentsService, AgentsListQuery

from rbac_sdk import (
    HDR_API_KEY,
    HDR_USER_ID,
    HDR_ORG_ID,
    HDR_ACCOUNT_ID,
    HDR_PROJECT_ID,
)


class ProviderType(str, Enum):
    openai_textgen = "openai_textgen"
    gemini_textgen = "gemini_textgen"
    bedrock_textgen = "bedrock_textgen"
    on_prem_textgen = "on-prem_textgen"


class OpenAIConfig(BaseModel):
    provider_type: ProviderType = ProviderType.openai_textgen
    model_name: Optional[str] = None
    temperature: Optional[float] = 0.5
    max_tokens: Optional[int] = 100


class GeminiConfig(BaseModel):
    provider_type: ProviderType = ProviderType.gemini_textgen
    model_name: Optional[str] = None
    temperature: Optional[float] = 0.5
    max_tokens: Optional[int] = 100


class BedrockConfig(BaseModel):
    provider_type: ProviderType = ProviderType.bedrock_textgen
    model_name: Optional[str] = None
    temperature: Optional[float] = 0.5
    max_tokens: Optional[int] = 100


class OnPremConfig(BaseModel):
    provider_type: ProviderType = ProviderType.on_prem_textgen
    model_name: Optional[str] = None
    temperature: Optional[float] = 0.5
    max_tokens: Optional[int] = 100


ProviderConfigUnion = OpenAIConfig | GeminiConfig | BedrockConfig | OnPremConfig


def validate_provider_config(provider_type: str, config: Dict[str, Any]) -> Dict[str, Any]:
    try:
        if provider_type == ProviderType.openai_textgen:
            parsed = OpenAIConfig(**config)
        elif provider_type == ProviderType.gemini_textgen:
            parsed = GeminiConfig(**config)
        elif provider_type == ProviderType.bedrock_textgen:
            parsed = BedrockConfig(**config)
        elif provider_type == ProviderType.on_prem_textgen:
            parsed = OnPremConfig(**config)
        else:
            raise HTTPException(status_code=400, detail=f"Unknown provider_type: {provider_type}")
        return parsed.model_dump()
    except ValidationError as ve:
        raise HTTPException(status_code=422, detail=ve.errors())


# Swagger/OpenAPI: expose API key header for testing in docs
api_key_header = APIKeyHeader(name=HDR_API_KEY, auto_error=False)

router = APIRouter(prefix="/agents", tags=["agents"])


# ---------- Agents CRUD ----------
@router.post("/", response_model=AgentRead, dependencies=[Depends(api_key_or_user_guard("create_agent"))])
async def create_agent(
    agent: AgentCreate,
    session: Session = Depends(get_db_session),
    # RBAC headers for Swagger UI testing
    api_key: Optional[str] = Security(api_key_header),
    user_id: Optional[str] = Header(default=None, alias=HDR_USER_ID),
    org_id: Optional[str] = Header(default=None, alias=HDR_ORG_ID),
    project_id: Optional[str] = Header(default=None, alias=HDR_PROJECT_ID),
    account_id: Optional[str] = Header(default=None, alias=HDR_ACCOUNT_ID),
):
    agent_data = agent.model_dump()
    agent_data["provider_config"] = validate_provider_config(agent.provider_type, agent.provider_config or {})
    try:
        return AgentsService.create_agent(session, agent_data)
    except ValueError as ve:
        raise HTTPException(status_code=409, detail=str(ve))


@router.get("/", response_model=List[AgentRead], dependencies=[Depends(api_key_or_user_guard("view_agent"))])
async def list_agents(
    session: Session = Depends(get_db_session),
    organization_id: Optional[str] = Query(default=None),
    status: Optional[str] = Query(default=None),
    tag: Optional[str] = Query(default=None),
    q: Optional[str] = Query(default=None),
    limit: int = 100,
    offset: int = 0,
    # RBAC headers for Swagger UI testing
    api_key: Optional[str] = Security(api_key_header),
    user_id: Optional[str] = Header(default=None, alias=HDR_USER_ID),
    org_id: Optional[str] = Header(default=None, alias=HDR_ORG_ID),
    project_id: Optional[str] = Header(default=None, alias=HDR_PROJECT_ID),
    account_id: Optional[str] = Header(default=None, alias=HDR_ACCOUNT_ID),
):
    params = AgentsListQuery(
        organization_id=organization_id,
        status=status,
        q=q,
        limit=limit,
        offset=offset,
    )
    agents = AgentsService.list_agents(session, params)

    # Apply Python-level tag filter for portability across DBs
    if tag:
        agents = [a for a in agents if tag in (a.tags or [])]

    return agents


@router.get("/{agent_id}", response_model=AgentRead, dependencies=[Depends(api_key_or_user_guard("view_agent"))])
async def get_agent(
    agent_id: str,
    session: Session = Depends(get_db_session),
    # RBAC headers for Swagger UI testing
    api_key: Optional[str] = Security(api_key_header),
    user_id: Optional[str] = Header(default=None, alias=HDR_USER_ID),
    org_id: Optional[str] = Header(default=None, alias=HDR_ORG_ID),
    project_id: Optional[str] = Header(default=None, alias=HDR_PROJECT_ID),
    account_id: Optional[str] = Header(default=None, alias=HDR_ACCOUNT_ID),
):
    agent = AgentsService.get_agent(session, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent


@router.patch("/{agent_id}", response_model=AgentRead, dependencies=[Depends(api_key_or_user_guard("edit_agent"))])
async def update_agent(
    agent_id: str,
    payload: AgentUpdate,
    session: Session = Depends(get_db_session),
    # RBAC headers for Swagger UI testing
    api_key: Optional[str] = Security(api_key_header),
    user_id: Optional[str] = Header(default=None, alias=HDR_USER_ID),
    org_id: Optional[str] = Header(default=None, alias=HDR_ORG_ID),
    project_id: Optional[str] = Header(default=None, alias=HDR_PROJECT_ID),
    account_id: Optional[str] = Header(default=None, alias=HDR_ACCOUNT_ID),
):
    try:
        return AgentsService.update_agent(session, agent_id, payload)
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))


@router.delete("/{agent_id}", dependencies=[Depends(api_key_or_user_guard("delete_agent"))])
async def delete_agent(
    agent_id: str,
    session: Session = Depends(get_db_session),
    # RBAC headers for Swagger UI testing
    api_key: Optional[str] = Security(api_key_header),
    user_id: Optional[str] = Header(default=None, alias=HDR_USER_ID),
    org_id: Optional[str] = Header(default=None, alias=HDR_ORG_ID),
    project_id: Optional[str] = Header(default=None, alias=HDR_PROJECT_ID),
    account_id: Optional[str] = Header(default=None, alias=HDR_ACCOUNT_ID),
):
    deleted = AgentsService.delete_agent(session, agent_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Agent not found")
    return {"deleted": True}


# ---------- Agent Tool Bindings ----------
@router.get(
    "/{agent_id}/tools", response_model=List[AgentToolBinding], dependencies=[Depends(api_key_or_user_guard("view_agent"))]
)
async def list_agent_tools(
    agent_id: str,
    session: Session = Depends(get_db_session),
    # RBAC headers for Swagger UI testing
    api_key: Optional[str] = Security(api_key_header),
    user_id: Optional[str] = Header(default=None, alias=HDR_USER_ID),
    org_id: Optional[str] = Header(default=None, alias=HDR_ORG_ID),
    project_id: Optional[str] = Header(default=None, alias=HDR_PROJECT_ID),
    account_id: Optional[str] = Header(default=None, alias=HDR_ACCOUNT_ID),
):
    return AgentsService.list_agent_tools(session, agent_id)


@router.post("/{agent_id}/tools", response_model=AgentToolBinding, dependencies=[Depends(api_key_or_user_guard("edit_agent"))])
async def attach_tool_to_agent(
    agent_id: str,
    body: Dict[str, Any],
    session: Session = Depends(get_db_session),
    # RBAC headers for Swagger UI testing
    api_key: Optional[str] = Security(api_key_header),
    user_id: Optional[str] = Header(default=None, alias=HDR_USER_ID),
    org_id: Optional[str] = Header(default=None, alias=HDR_ORG_ID),
    project_id: Optional[str] = Header(default=None, alias=HDR_PROJECT_ID),
    account_id: Optional[str] = Header(default=None, alias=HDR_ACCOUNT_ID),
):
    try:
        return AgentsService.attach_tool_to_agent(
            session,
            agent_id,
            tool_id=body.get("tool_id"),
            local_tool_name=body.get("local_tool_name"),
            override_parameters=body.get("override_parameters", {}),
            is_active=bool(body.get("is_active", True)),
        )
    except ValueError as ve:
        msg = str(ve)
        if msg == "Agent not found":
            raise HTTPException(status_code=404, detail=msg)
        elif msg in {"Provide tool_id or local_tool_name", "Agent/binding mismatch", "Local tool not found in registry"}:
            raise HTTPException(status_code=400, detail=msg)
        else:
            raise HTTPException(status_code=400, detail=msg)


@router.patch(
    "/{agent_id}/tools/{binding_id}",
    response_model=AgentToolBinding,
    dependencies=[Depends(api_key_or_user_guard("edit_agent"))],
)
async def update_agent_tool_binding(
    agent_id: str,
    binding_id: int,
    body: Dict[str, Any],
    session: Session = Depends(get_db_session),
    # RBAC headers for Swagger UI testing
    api_key: Optional[str] = Security(api_key_header),
    user_id: Optional[str] = Header(default=None, alias=HDR_USER_ID),
    org_id: Optional[str] = Header(default=None, alias=HDR_ORG_ID),
    project_id: Optional[str] = Header(default=None, alias=HDR_PROJECT_ID),
    account_id: Optional[str] = Header(default=None, alias=HDR_ACCOUNT_ID),
):
    try:
        return AgentsService.update_agent_tool_binding(session, agent_id, binding_id, body)
    except ValueError as ve:
        msg = str(ve)
        if msg in {"Binding not found"}:
            raise HTTPException(status_code=404, detail=msg)
        else:
            raise HTTPException(status_code=400, detail=msg)


@router.delete("/{agent_id}/tools/{binding_id}", dependencies=[Depends(api_key_or_user_guard("edit_agent"))])
async def detach_tool_from_agent(
    agent_id: str,
    binding_id: int,
    session: Session = Depends(get_db_session),
    # RBAC headers for Swagger UI testing
    api_key: Optional[str] = Security(api_key_header),
    user_id: Optional[str] = Header(default=None, alias=HDR_USER_ID),
    org_id: Optional[str] = Header(default=None, alias=HDR_ORG_ID),
    project_id: Optional[str] = Header(default=None, alias=HDR_PROJECT_ID),
    account_id: Optional[str] = Header(default=None, alias=HDR_ACCOUNT_ID),
):
    try:
        deleted = AgentsService.detach_tool_from_agent(session, agent_id, binding_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Binding not found")
        return {"deleted": True}
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))


# ---------- Available Tools ----------
@router.get("/available-tools", response_model=List[Dict[str, Any]])
async def available_tools():
    # For now, read from step_registry definitions in memory
    # A more advanced version could expose the database StepType table
    from ..step_registry import StepRegistry

    # The running app holds a single registry; import-only fallback here
    registry = StepRegistry()
    await registry.register_builtin_steps()
    steps = await registry.get_registered_steps()

    # Only return summaries
    return [
        {
            "step_type": s["step_type"],
            "name": s["name"],
            "description": s.get("description", ""),
            "execution_type": s["execution_type"],
            "tags": s.get("tags", []),
        }
        for s in steps
    ]


# ---------- Agent Execution ----------
@router.post("/{agent_id}/execute")
async def execute_agent(
    agent_id: str,
    session: Session = Depends(get_db_session),
    payload: Optional[str] = Form(None),
    files: Optional[list[UploadFile]] = File(None),
):
    """Execute a single agent directly.

    Accepts JSON or multipart/form-data. For multipart:
    - payload: JSON string with { query: str, context?: dict }
    - files[]: optional attachments (images/docs/audio). Audio will be flagged for transcription.
    """
    import json

    from ..steps.ai_steps import AgentStep

    # Resolve agent by id
    from uuid import UUID

    db_agent = session.exec(select(Agent).where(Agent.id == UUID(agent_id))).first()
    if not db_agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    # Parse body
    body: Dict[str, Any] = {}
    if payload is not None or files is not None:
        if payload is None:
            raise HTTPException(status_code=400, detail="Missing 'payload' form field")
        try:
            body = json.loads(payload)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid JSON in 'payload' form field")
    else:
        # JSON request body unsupported in this endpoint signature; require multipart form
        raise HTTPException(status_code=400, detail="This endpoint expects multipart form with 'payload'.")

    query = body.get("query")
    if not query:
        raise HTTPException(status_code=400, detail="'query' is required")
    context = body.get("context", {})

    # Handle optional attachments
    attachments = []
    if files:
        upload_root = Path("uploads/agents")
        upload_root.mkdir(parents=True, exist_ok=True)
        import uuid as uuid_module

        run_dir = upload_root / str(uuid_module.uuid4())
        run_dir.mkdir(exist_ok=True)
        total_size = 0
        for up in files:
            mime = up.content_type or "application/octet-stream"
            content = await up.read()
            size = len(content)
            total_size += size
            dest = run_dir / (up.filename or "upload.bin")
            with open(dest, "wb") as f:
                f.write(content)
            att = {
                "name": up.filename,
                "mime": mime,
                "size_bytes": size,
                "path": str(dest),
            }
            if mime.startswith("audio/"):
                att["needs_transcription"] = True
            attachments.append(att)
        context["attachments"] = attachments

    # Load system prompt text from Prompt table
    prompt = session.exec(select(Prompt).where(Prompt.id == db_agent.system_prompt_id)).first()
    system_prompt_text = prompt.prompt if prompt else "You are a helpful assistant."

    # Prepare tools (schemas handled by llm-gateway-compatible structure in SimpleAgent)
    # For now, we don't resolve AgentToolBinding -> Tool set; leaving as empty list
    agent = AgentStep(
        name=db_agent.name,
        system_prompt=system_prompt_text,
        tools=[],
        force_real_llm=False,
    )

    # Execute
    result = await agent.execute(query, context)
    return result

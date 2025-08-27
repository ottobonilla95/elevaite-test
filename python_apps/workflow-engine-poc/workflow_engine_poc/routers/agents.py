"""
Agents API router: CRUD for Agents, Prompts, and Tool bindings
"""

from typing import List, Optional, Dict, Any, cast
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, Query, Request, UploadFile, File, Form
from sqlmodel import Session, select

from ..db.database import get_db_session
from ..db.models import (
    Agent,
    AgentCreate,
    AgentRead,
    AgentUpdate,
    AgentToolBinding,
    Prompt,
    PromptCreate,
    PromptRead,
    PromptUpdate,
)

# Provider config validation models
from pydantic import BaseModel, Field as PydField, ValidationError
from enum import Enum


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


router = APIRouter(prefix="/agents", tags=["agents"])


# ---------- Agents CRUD ----------
@router.post("/", response_model=AgentRead)
async def create_agent(agent: AgentCreate, session: Session = Depends(get_db_session)):
    # Basic uniqueness within org by name
    if agent.organization_id:
        existing = session.exec(
            select(Agent).where(Agent.name == agent.name, Agent.organization_id == agent.organization_id)
        ).first()
    else:
        existing = session.exec(select(Agent).where(Agent.name == agent.name)).first()
    if existing:
        raise HTTPException(status_code=409, detail="Agent with this name already exists")

    # Validate provider_config
    agent_data = agent.model_dump()
    agent_data["provider_config"] = validate_provider_config(agent.provider_type, agent.provider_config or {})

    db_agent = Agent(**agent_data)
    session.add(db_agent)
    session.commit()
    session.refresh(db_agent)

    return db_agent


@router.get("/", response_model=List[AgentRead])
async def list_agents(
    session: Session = Depends(get_db_session),
    organization_id: Optional[str] = Query(default=None),
    status: Optional[str] = Query(default=None),
    tag: Optional[str] = Query(default=None),
    q: Optional[str] = Query(default=None),
    limit: int = 100,
    offset: int = 0,
):
    query = select(Agent)
    if organization_id:
        query = query.where(Agent.organization_id == organization_id)
    if status:
        query = query.where(Agent.status == status)

    agents = session.exec(query.offset(offset).limit(limit)).all()

    # Apply Python-level filters for portability across DBs
    if tag:
        agents = [a for a in agents if tag in (a.tags or [])]
    if q:
        agents = [a for a in agents if q.lower() in (a.name or "").lower()]

    return agents


@router.get("/{agent_id}", response_model=AgentRead)
async def get_agent(agent_id: str, session: Session = Depends(get_db_session)):
    from uuid import UUID

    agent = session.exec(select(Agent).where(Agent.id == UUID(agent_id))).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    return agent


@router.patch("/{agent_id}", response_model=AgentRead)
async def update_agent(
    agent_id: str,
    payload: AgentUpdate,
    session: Session = Depends(get_db_session),
):
    from uuid import UUID

    db_agent = session.exec(select(Agent).where(Agent.id == UUID(agent_id))).first()
    if not db_agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(db_agent, k, v)

    session.add(db_agent)
    session.commit()
    session.refresh(db_agent)

    return db_agent


@router.delete("/{agent_id}")
async def delete_agent(agent_id: str, session: Session = Depends(get_db_session)):
    from uuid import UUID

    db_agent = session.exec(select(Agent).where(Agent.id == UUID(agent_id))).first()
    if not db_agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    session.delete(db_agent)
    session.commit()
    return {"deleted": True}


# ---------- Prompts CRUD ----------
@router.post("/prompts", response_model=PromptRead)
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


@router.get("/prompts", response_model=List[PromptRead])
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


@router.get("/prompts/{prompt_id}", response_model=PromptRead)
async def get_prompt(prompt_id: str, session: Session = Depends(get_db_session)):
    from uuid import UUID

    prompt = session.exec(select(Prompt).where(Prompt.pid == UUID(prompt_id))).first()
    if not prompt:
        raise HTTPException(status_code=404, detail="Prompt not found")

    return prompt


@router.patch("/prompts/{prompt_id}", response_model=PromptRead)
async def update_prompt(prompt_id: str, payload: PromptUpdate, session: Session = Depends(get_db_session)):
    from uuid import UUID

    db_prompt = session.exec(select(Prompt).where(Prompt.pid == UUID(prompt_id))).first()
    if not db_prompt:
        raise HTTPException(status_code=404, detail="Prompt not found")

    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(db_prompt, k, v)

    session.add(db_prompt)
    session.commit()
    session.refresh(db_prompt)

    return db_prompt


@router.delete("/prompts/{prompt_id}")
async def delete_prompt(prompt_id: str, session: Session = Depends(get_db_session)):
    from uuid import UUID

    db_prompt = session.exec(select(Prompt).where(Prompt.pid == UUID(prompt_id))).first()
    if not db_prompt:
        raise HTTPException(status_code=404, detail="Prompt not found")

    session.delete(db_prompt)
    session.commit()
    return {"deleted": True}


# ---------- Agent Tool Bindings ----------
@router.get("/{agent_id}/tools", response_model=List[AgentToolBinding])
async def list_agent_tools(agent_id: str, session: Session = Depends(get_db_session)):
    from uuid import UUID

    bindings = session.exec(select(AgentToolBinding).where(AgentToolBinding.agent_id == UUID(agent_id))).all()

    return bindings


@router.post("/{agent_id}/tools", response_model=AgentToolBinding)
async def attach_tool_to_agent(
    agent_id: str,
    body: Dict[str, Any],
    session: Session = Depends(get_db_session),
):
    from uuid import UUID

    # Validate agent exists
    db_agent = session.exec(select(Agent).where(Agent.id == UUID(agent_id))).first()
    if not db_agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    tool_id = body.get("tool_id")
    if not tool_id:
        raise HTTPException(status_code=400, detail="tool_id is required")

    binding = AgentToolBinding(
        agent_id=db_agent.id,
        tool_id=UUID(tool_id),
        override_parameters=body.get("override_parameters", {}),
        is_active=bool(body.get("is_active", True)),
        organization_id=db_agent.organization_id,
        created_by=db_agent.created_by,
    )

    session.add(binding)
    session.commit()
    session.refresh(binding)

    return binding


@router.patch("/{agent_id}/tools/{binding_id}", response_model=AgentToolBinding)
async def update_agent_tool_binding(
    agent_id: str,
    binding_id: int,
    body: Dict[str, Any],
    session: Session = Depends(get_db_session),
):
    from uuid import UUID

    binding = session.get(AgentToolBinding, binding_id)
    if not binding:
        raise HTTPException(status_code=404, detail="Binding not found")

    # Optional: validate binding.agent_id matches URL
    if str(binding.agent_id) != str(UUID(agent_id)):
        raise HTTPException(status_code=400, detail="Agent/binding mismatch")

    for k in ["override_parameters", "is_active"]:
        if k in body:
            setattr(binding, k, body[k])

    session.add(binding)
    session.commit()
    session.refresh(binding)

    return binding


@router.delete("/{agent_id}/tools/{binding_id}")
async def detach_tool_from_agent(agent_id: str, binding_id: int, session: Session = Depends(get_db_session)):
    from uuid import UUID

    binding = session.get(AgentToolBinding, binding_id)
    if not binding:
        raise HTTPException(status_code=404, detail="Binding not found")

    if str(binding.agent_id) != str(UUID(agent_id)):
        raise HTTPException(status_code=400, detail="Agent/binding mismatch")

    session.delete(binding)
    session.commit()
    return {"deleted": True}


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
        # JSON request body
        from fastapi import Request as FastAPIRequest  # alias to avoid shadowing

        req: FastAPIRequest
        try:
            # Injected via FastAPI if present in signature; we don't have it here, so this path should not be used in practice for now
            raise RuntimeError("Non-multipart path requires multipart form with 'payload'.")
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

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

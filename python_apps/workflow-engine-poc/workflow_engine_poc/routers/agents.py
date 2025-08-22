"""
Agents API router: CRUD for Agents, Prompts, and Tool bindings
"""

from typing import List, Optional, Dict, Any, cast
from fastapi import APIRouter, Depends, HTTPException, Query, Request
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


def validate_provider_config(
    provider_type: str, config: Dict[str, Any]
) -> Dict[str, Any]:
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
            raise HTTPException(
                status_code=400, detail=f"Unknown provider_type: {provider_type}"
            )
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
            select(Agent).where(
                Agent.name == agent.name, Agent.organization_id == agent.organization_id
            )
        ).first()
    else:
        existing = session.exec(select(Agent).where(Agent.name == agent.name)).first()
    if existing:
        raise HTTPException(
            status_code=409, detail="Agent with this name already exists"
        )

    # Validate provider_config
    agent_data = agent.model_dump()
    agent_data["provider_config"] = validate_provider_config(
        agent.provider_type, agent.provider_config or {}
    )

    db_agent = Agent(**agent_data)
    session.add(db_agent)
    session.commit()
    session.refresh(db_agent)

    return AgentRead(
        id=db_agent.id or 0,
        uuid=db_agent.uuid,
        agent_id=db_agent.agent_id,
        name=db_agent.name,
        description=db_agent.description,
        system_prompt_id=db_agent.system_prompt_id,
        provider_type=db_agent.provider_type,
        provider_config=db_agent.provider_config,
        tags=db_agent.tags,
        status=db_agent.status,  # type: ignore[arg-type]
        organization_id=db_agent.organization_id,
        created_by=db_agent.created_by,
        created_at=str(db_agent.created_at),
        updated_at=str(db_agent.updated_at) if db_agent.updated_at else None,
    )


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

    return [
        AgentRead(
            id=a.id or 0,
            uuid=a.uuid,
            agent_id=a.agent_id,
            name=a.name,
            description=a.description,
            system_prompt_id=a.system_prompt_id,
            provider_type=a.provider_type,
            provider_config=a.provider_config,
            tags=a.tags,
            status=a.status,  # type: ignore[arg-type]
            organization_id=a.organization_id,
            created_by=a.created_by,
            created_at=str(a.created_at),
            updated_at=str(a.updated_at) if a.updated_at else None,
        )
        for a in agents
    ]


@router.get("/{agent_id}", response_model=AgentRead)
async def get_agent(agent_id: str, session: Session = Depends(get_db_session)):
    from uuid import UUID

    agent = session.exec(select(Agent).where(Agent.agent_id == UUID(agent_id))).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    return AgentRead(
        id=agent.id or 0,
        uuid=agent.uuid,
        agent_id=agent.agent_id,
        name=agent.name,
        description=agent.description,
        system_prompt_id=agent.system_prompt_id,
        provider_type=agent.provider_type,
        provider_config=agent.provider_config,
        tags=agent.tags,
        status=agent.status,  # type: ignore[arg-type]
        organization_id=agent.organization_id,
        created_by=agent.created_by,
        created_at=str(agent.created_at),
        updated_at=str(agent.updated_at) if agent.updated_at else None,
    )


@router.patch("/{agent_id}", response_model=AgentRead)
async def update_agent(
    agent_id: str,
    payload: AgentUpdate,
    session: Session = Depends(get_db_session),
):
    from uuid import UUID

    db_agent = session.exec(
        select(Agent).where(Agent.agent_id == UUID(agent_id))
    ).first()
    if not db_agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(db_agent, k, v)

    session.add(db_agent)
    session.commit()
    session.refresh(db_agent)

    return AgentRead(
        id=db_agent.id,
        uuid=db_agent.uuid,
        agent_id=db_agent.agent_id,
        name=db_agent.name,
        description=db_agent.description,
        system_prompt_id=db_agent.system_prompt_id,
        provider_type=db_agent.provider_type,
        provider_config=db_agent.provider_config,
        tags=db_agent.tags,
        status=db_agent.status,
        organization_id=db_agent.organization_id,
        created_by=db_agent.created_by,
        created_at=str(db_agent.created_at),
        updated_at=str(db_agent.updated_at) if db_agent.updated_at else None,
    )


@router.delete("/{agent_id}")
async def delete_agent(agent_id: str, session: Session = Depends(get_db_session)):
    from uuid import UUID

    db_agent = session.exec(
        select(Agent).where(Agent.agent_id == UUID(agent_id))
    ).first()
    if not db_agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    session.delete(db_agent)
    session.commit()
    return {"deleted": True}


# ---------- Prompts CRUD ----------
@router.post("/prompts", response_model=PromptRead)
async def create_prompt(
    prompt: PromptCreate, session: Session = Depends(get_db_session)
):
    # uniqueness by unique_label within org
    if prompt.organization_id:
        existing = session.exec(
            select(Prompt).where(
                Prompt.unique_label == prompt.unique_label,
                Prompt.organization_id == prompt.organization_id,
            )
        ).first()
    else:
        existing = session.exec(
            select(Prompt).where(Prompt.unique_label == prompt.unique_label)
        ).first()

    if existing:
        raise HTTPException(
            status_code=409, detail="Prompt with this unique_label already exists"
        )

    db_prompt = Prompt(**prompt.model_dump())
    session.add(db_prompt)
    session.commit()
    session.refresh(db_prompt)

    return PromptRead(
        **prompt.model_dump(),
        id=db_prompt.id,
        uuid=db_prompt.uuid,
        pid=db_prompt.pid,
        created_time=str(db_prompt.created_time),
        updated_time=str(db_prompt.updated_time) if db_prompt.updated_time else None,
    )


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

    return [
        PromptRead(
            id=p.id,
            uuid=p.uuid,
            pid=p.pid,
            prompt_label=p.prompt_label,
            prompt=p.prompt,
            unique_label=p.unique_label,
            app_name=p.app_name,
            ai_model_provider=p.ai_model_provider,
            ai_model_name=p.ai_model_name,
            tags=p.tags,
            hyper_parameters=p.hyper_parameters,
            variables=p.variables,
            organization_id=p.organization_id,
            created_by=p.created_by,
            created_time=str(p.created_time),
            updated_time=str(p.updated_time) if p.updated_time else None,
        )
        for p in prompts
    ]


@router.get("/prompts/{prompt_id}", response_model=PromptRead)
async def get_prompt(prompt_id: str, session: Session = Depends(get_db_session)):
    from uuid import UUID

    prompt = session.exec(select(Prompt).where(Prompt.pid == UUID(prompt_id))).first()
    if not prompt:
        raise HTTPException(status_code=404, detail="Prompt not found")

    return PromptRead(
        id=prompt.id,
        uuid=prompt.uuid,
        pid=prompt.pid,
        prompt_label=prompt.prompt_label,
        prompt=prompt.prompt,
        unique_label=prompt.unique_label,
        app_name=prompt.app_name,
        ai_model_provider=prompt.ai_model_provider,
        ai_model_name=prompt.ai_model_name,
        tags=prompt.tags,
        hyper_parameters=prompt.hyper_parameters,
        variables=prompt.variables,
        organization_id=prompt.organization_id,
        created_by=prompt.created_by,
        created_time=str(prompt.created_time),
        updated_time=str(prompt.updated_time) if prompt.updated_time else None,
    )


@router.patch("/prompts/{prompt_id}", response_model=PromptRead)
async def update_prompt(
    prompt_id: str, payload: PromptUpdate, session: Session = Depends(get_db_session)
):
    from uuid import UUID

    db_prompt = session.exec(
        select(Prompt).where(Prompt.pid == UUID(prompt_id))
    ).first()
    if not db_prompt:
        raise HTTPException(status_code=404, detail="Prompt not found")

    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(db_prompt, k, v)

    session.add(db_prompt)
    session.commit()
    session.refresh(db_prompt)

    return PromptRead(
        id=db_prompt.id,
        uuid=db_prompt.uuid,
        pid=db_prompt.pid,
        prompt_label=db_prompt.prompt_label,
        prompt=db_prompt.prompt,
        unique_label=db_prompt.unique_label,
        app_name=db_prompt.app_name,
        ai_model_provider=db_prompt.ai_model_provider,
        ai_model_name=db_prompt.ai_model_name,
        tags=db_prompt.tags,
        hyper_parameters=db_prompt.hyper_parameters,
        variables=db_prompt.variables,
        organization_id=db_prompt.organization_id,
        created_by=db_prompt.created_by,
        created_time=str(db_prompt.created_time),
        updated_time=str(db_prompt.updated_time) if db_prompt.updated_time else None,
    )


@router.delete("/prompts/{prompt_id}")
async def delete_prompt(prompt_id: str, session: Session = Depends(get_db_session)):
    from uuid import UUID

    db_prompt = session.exec(
        select(Prompt).where(Prompt.pid == UUID(prompt_id))
    ).first()
    if not db_prompt:
        raise HTTPException(status_code=404, detail="Prompt not found")

    session.delete(db_prompt)
    session.commit()
    return {"deleted": True}


# ---------- Agent Tool Bindings ----------
@router.get("/{agent_id}/tools", response_model=List[Dict[str, Any]])
async def list_agent_tools(agent_id: str, session: Session = Depends(get_db_session)):
    from uuid import UUID

    bindings = session.exec(
        select(AgentToolBinding).where(AgentToolBinding.agent_id == UUID(agent_id))
    ).all()

    return [
        {
            "id": b.id,
            "uuid": str(b.uuid),
            "agent_id": str(b.agent_id),
            "tool_id": str(b.tool_id),
            "override_parameters": b.override_parameters,
            "is_active": b.is_active,
            "organization_id": b.organization_id,
            "created_by": b.created_by,
            "created_at": str(b.created_at),
            "updated_at": str(b.updated_at) if b.updated_at else None,
        }
        for b in bindings
    ]


@router.post("/{agent_id}/tools", response_model=Dict[str, Any])
async def attach_tool_to_agent(
    agent_id: str,
    body: Dict[str, Any],
    session: Session = Depends(get_db_session),
):
    from uuid import UUID

    # Validate agent exists
    db_agent = session.exec(
        select(Agent).where(Agent.agent_id == UUID(agent_id))
    ).first()
    if not db_agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    tool_id = body.get("tool_id")
    if not tool_id:
        raise HTTPException(status_code=400, detail="tool_id is required")

    binding = AgentToolBinding(
        agent_id=db_agent.agent_id,
        tool_id=UUID(tool_id),
        override_parameters=body.get("override_parameters", {}),
        is_active=bool(body.get("is_active", True)),
        organization_id=db_agent.organization_id,
        created_by=db_agent.created_by,
    )

    session.add(binding)
    session.commit()
    session.refresh(binding)

    return {
        "id": binding.id,
        "uuid": str(binding.uuid),
        "agent_id": str(binding.agent_id),
        "tool_id": str(binding.tool_id),
        "override_parameters": binding.override_parameters,
        "is_active": binding.is_active,
        "organization_id": binding.organization_id,
        "created_by": binding.created_by,
        "created_at": str(binding.created_at),
        "updated_at": str(binding.updated_at) if binding.updated_at else None,
    }


@router.patch("/{agent_id}/tools/{binding_id}", response_model=Dict[str, Any])
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

    return {
        "id": binding.id,
        "uuid": str(binding.uuid),
        "agent_id": str(binding.agent_id),
        "tool_id": str(binding.tool_id),
        "override_parameters": binding.override_parameters,
        "is_active": binding.is_active,
        "organization_id": binding.organization_id,
        "created_by": binding.created_by,
        "created_at": str(binding.created_at),
        "updated_at": str(binding.updated_at) if binding.updated_at else None,
    }


@router.delete("/{agent_id}/tools/{binding_id}")
async def detach_tool_from_agent(
    agent_id: str, binding_id: int, session: Session = Depends(get_db_session)
):
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

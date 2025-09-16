from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from uuid import UUID

from sqlmodel import Session, select

from ..db.models import Agent, AgentUpdate, AgentToolBinding
from ..tools.registry import tool_registry


@dataclass
class AgentsListQuery:
    organization_id: Optional[str] = None
    status: Optional[str] = None
    q: Optional[str] = None
    limit: int = 100
    offset: int = 0


class AgentsService:
    # ----- Agents CRUD -----
    @staticmethod
    def create_agent(session: Session, agent_data: Dict[str, Any]) -> Agent:
        # Basic uniqueness within org by name
        if agent_data.get("organization_id"):
            existing = session.exec(
                select(Agent).where(
                    Agent.name == agent_data.get("name"),
                    Agent.organization_id == agent_data.get("organization_id"),
                )
            ).first()
        else:
            existing = session.exec(select(Agent).where(Agent.name == agent_data.get("name"))).first()
        if existing:
            raise ValueError("Agent with this name already exists")

        db_agent = Agent(**agent_data)
        session.add(db_agent)
        session.commit()
        session.refresh(db_agent)
        return db_agent

    @staticmethod
    def list_agents(session: Session, params: AgentsListQuery) -> List[Agent]:
        query = select(Agent)
        if params.organization_id:
            query = query.where(Agent.organization_id == params.organization_id)
        if params.status:
            query = query.where(Agent.status == params.status)

        agents = session.exec(query.offset(params.offset).limit(params.limit)).all()

        # Apply Python-level filters for portability across DBs
        if params.q:
            q_lower = params.q.lower()
            agents = [a for a in agents if q_lower in (a.name or "").lower()]

        return agents

    @staticmethod
    def get_agent(session: Session, agent_id: str) -> Optional[Agent]:
        return session.exec(select(Agent).where(Agent.id == UUID(agent_id))).first()

    @staticmethod
    def update_agent(session: Session, agent_id: str, payload: AgentUpdate) -> Agent:
        db_agent = session.exec(select(Agent).where(Agent.id == UUID(agent_id))).first()
        if not db_agent:
            raise ValueError("Agent not found")

        for k, v in payload.model_dump(exclude_unset=True).items():
            setattr(db_agent, k, v)

        session.add(db_agent)
        session.commit()
        session.refresh(db_agent)
        return db_agent

    @staticmethod
    def delete_agent(session: Session, agent_id: str) -> bool:
        db_agent = session.exec(select(Agent).where(Agent.id == UUID(agent_id))).first()
        if not db_agent:
            return False
        session.delete(db_agent)
        session.commit()
        return True

    # ----- Agent Tool Bindings -----
    @staticmethod
    def list_agent_tools(session: Session, agent_id: str) -> List[AgentToolBinding]:
        return session.exec(select(AgentToolBinding).where(AgentToolBinding.agent_id == UUID(agent_id))).all()

    @staticmethod
    def attach_tool_to_agent(
        session: Session,
        agent_id: str,
        *,
        tool_id: Optional[str] = None,
        local_tool_name: Optional[str] = None,
        override_parameters: Optional[Dict[str, Any]] = None,
        is_active: bool = True,
    ) -> AgentToolBinding:
        db_agent = session.exec(select(Agent).where(Agent.id == UUID(agent_id))).first()
        if not db_agent:
            raise ValueError("Agent not found")

        resolved_tool_id: Optional[str] = tool_id
        if not resolved_tool_id and local_tool_name:
            synced_id = tool_registry.sync_local_tool_by_name(session, str(local_tool_name))
            if not synced_id:
                raise ValueError("Local tool not found in registry")
            resolved_tool_id = str(synced_id)

        if not resolved_tool_id:
            raise ValueError("Provide tool_id or local_tool_name")

        binding = AgentToolBinding(
            agent_id=db_agent.id,
            tool_id=UUID(resolved_tool_id),
            override_parameters=override_parameters or {},
            is_active=bool(is_active),
            organization_id=db_agent.organization_id,
            created_by=db_agent.created_by,
        )

        session.add(binding)
        session.commit()
        session.refresh(binding)
        return binding

    @staticmethod
    def update_agent_tool_binding(
        session: Session,
        agent_id: str,
        binding_id: int,
        updates: Dict[str, Any],
    ) -> AgentToolBinding:
        binding = session.get(AgentToolBinding, binding_id)
        if not binding:
            raise ValueError("Binding not found")

        # Optional: validate binding.agent_id matches URL
        if str(binding.agent_id) != str(UUID(agent_id)):
            raise ValueError("Agent/binding mismatch")

        for k in ["override_parameters", "is_active"]:
            if k in updates:
                setattr(binding, k, updates[k])

        session.add(binding)
        session.commit()
        session.refresh(binding)
        return binding

    @staticmethod
    def detach_tool_from_agent(session: Session, agent_id: str, binding_id: int) -> bool:
        binding = session.get(AgentToolBinding, binding_id)
        if not binding:
            return False
        if str(binding.agent_id) != str(UUID(agent_id)):
            raise ValueError("Agent/binding mismatch")
        session.delete(binding)
        session.commit()
        return True

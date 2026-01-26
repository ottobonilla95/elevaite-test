"""
A2A Agents Service for managing external A2A agent registrations.

Provides CRUD operations for A2A agents, Agent Card fetching, and health check management.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlmodel import Session, select

from ..db.models import A2AAgent, A2AAgentCreate, A2AAgentStatus, A2AAgentUpdate
from ..utils import decrypt_if_encrypted, encrypt_if_configured


logger = logging.getLogger(__name__)


@dataclass
class A2AAgentsListQuery:
    """Query parameters for listing A2A agents."""

    organization_id: Optional[str] = None
    status: Optional[str] = None
    q: Optional[str] = None
    tags: Optional[List[str]] = None
    limit: int = 100
    offset: int = 0


class A2AAgentsService:
    """Service for managing A2A agent registrations.

    This service handles CRUD operations for A2A agents stored in the database.
    Agent Card fetching and A2A protocol communication is handled by llm-gateway.
    """

    # ----- A2A Agents CRUD -----
    @staticmethod
    def create_agent(
        session: Session,
        payload: A2AAgentCreate,
        created_by: Optional[str] = None,
    ) -> A2AAgent:
        """Register a new A2A agent.

        Args:
            session: Database session.
            payload: Agent creation data.
            created_by: ID of user creating the agent.

        Returns:
            The created A2AAgent.

        Raises:
            ValueError: If an agent with the same base_url already exists in the org.
        """
        # Check for existing agent with same base_url in organization
        query = select(A2AAgent).where(A2AAgent.base_url == payload.base_url)
        if payload.organization_id:
            query = query.where(A2AAgent.organization_id == payload.organization_id)

        existing = session.exec(query).first()
        if existing:
            raise ValueError(
                f"A2A agent with base_url '{payload.base_url}' already exists"
            )

        # Encrypt auth_config if encryption is configured
        agent_data = payload.model_dump()
        if agent_data.get("auth_config"):
            encrypted = encrypt_if_configured(agent_data["auth_config"])
            agent_data["auth_config"] = encrypted

        db_agent = A2AAgent(
            **agent_data,
            created_by=created_by,
        )
        session.add(db_agent)
        session.commit()
        session.refresh(db_agent)
        return db_agent

    @staticmethod
    def list_agents(session: Session, params: A2AAgentsListQuery) -> List[A2AAgent]:
        """List A2A agents with optional filtering.

        Args:
            session: Database session.
            params: Query parameters for filtering and pagination.

        Returns:
            List of matching A2AAgent records.
        """
        query = select(A2AAgent)

        if params.organization_id:
            query = query.where(A2AAgent.organization_id == params.organization_id)
        if params.status:
            query = query.where(A2AAgent.status == params.status)

        agents = list(
            session.exec(query.offset(params.offset).limit(params.limit)).all()
        )

        # Apply Python-level filters for portability
        if params.q:
            q_lower = params.q.lower()
            agents = [
                a
                for a in agents
                if q_lower in (a.name or "").lower()
                or q_lower in (a.description or "").lower()
            ]

        if params.tags:
            agents = [
                a
                for a in agents
                if a.tags and any(tag in a.tags for tag in params.tags)
            ]

        return agents

    @staticmethod
    def get_agent(session: Session, agent_id: str) -> Optional[A2AAgent]:
        """Get a single A2A agent by ID.

        Args:
            session: Database session.
            agent_id: The agent's UUID.

        Returns:
            The A2AAgent if found, else None.
        """
        return session.exec(
            select(A2AAgent).where(A2AAgent.id == UUID(agent_id))
        ).first()

    @staticmethod
    def get_decrypted_auth_config(agent: A2AAgent) -> Optional[Dict[str, Any]]:
        """Get decrypted auth_config for an agent.

        This method handles both encrypted and plaintext auth_config.

        Args:
            agent: The A2AAgent to get credentials for.

        Returns:
            Decrypted auth_config dict, or None if not configured.
        """
        if not agent.auth_config:
            return None
        return decrypt_if_encrypted(agent.auth_config)

    @staticmethod
    def get_agent_by_base_url(
        session: Session,
        base_url: str,
        organization_id: Optional[str] = None,
    ) -> Optional[A2AAgent]:
        """Get an A2A agent by its base URL.

        Args:
            session: Database session.
            base_url: The agent's base URL.
            organization_id: Optional organization filter.

        Returns:
            The A2AAgent if found, else None.
        """
        query = select(A2AAgent).where(A2AAgent.base_url == base_url)
        if organization_id:
            query = query.where(A2AAgent.organization_id == organization_id)
        return session.exec(query).first()

    @staticmethod
    def update_agent(
        session: Session,
        agent_id: str,
        payload: A2AAgentUpdate,
    ) -> A2AAgent:
        """Update an A2A agent's configuration.

        Args:
            session: Database session.
            agent_id: The agent's UUID.
            payload: Fields to update.

        Returns:
            The updated A2AAgent.

        Raises:
            ValueError: If agent not found.
        """
        db_agent = session.exec(
            select(A2AAgent).where(A2AAgent.id == UUID(agent_id))
        ).first()
        if not db_agent:
            raise ValueError("A2A agent not found")

        update_data = payload.model_dump(exclude_unset=True)

        # Encrypt auth_config if being updated and encryption is configured
        if "auth_config" in update_data and update_data["auth_config"]:
            encrypted = encrypt_if_configured(update_data["auth_config"])
            update_data["auth_config"] = encrypted

        for key, value in update_data.items():
            setattr(db_agent, key, value)

        session.add(db_agent)
        session.commit()
        session.refresh(db_agent)
        return db_agent

    @staticmethod
    def delete_agent(session: Session, agent_id: str) -> bool:
        """Delete an A2A agent registration.

        Args:
            session: Database session.
            agent_id: The agent's UUID.

        Returns:
            True if deleted, False if not found.
        """
        db_agent = session.exec(
            select(A2AAgent).where(A2AAgent.id == UUID(agent_id))
        ).first()
        if not db_agent:
            return False
        session.delete(db_agent)
        session.commit()
        return True

    # ----- Agent Card Management -----
    @staticmethod
    def update_agent_card(
        session: Session,
        agent_id: str,
        agent_card: Dict[str, Any],
    ) -> A2AAgent:
        """Update cached Agent Card data for an agent.

        This should be called after fetching an Agent Card from the remote agent
        to persist the data locally.

        Args:
            session: Database session.
            agent_id: The agent's UUID.
            agent_card: The full Agent Card JSON.

        Returns:
            The updated A2AAgent.

        Raises:
            ValueError: If agent not found.
        """
        db_agent = session.exec(
            select(A2AAgent).where(A2AAgent.id == UUID(agent_id))
        ).first()
        if not db_agent:
            raise ValueError("A2A agent not found")

        # Store full agent card
        db_agent.agent_card = agent_card

        # Extract key fields
        db_agent.protocol_version = agent_card.get("protocolVersion")
        db_agent.skills = agent_card.get("skills")

        # Extract supported modes from capabilities
        capabilities = agent_card.get("capabilities", {})
        db_agent.supported_input_modes = capabilities.get("inputModes")
        db_agent.supported_output_modes = capabilities.get("outputModes")

        # Update last seen
        db_agent.last_seen = datetime.now(timezone.utc)

        session.add(db_agent)
        session.commit()
        session.refresh(db_agent)
        return db_agent

    # ----- Health Check Management -----
    @staticmethod
    def update_health_status(
        session: Session,
        agent_id: str,
        is_healthy: bool,
        error_message: Optional[str] = None,
    ) -> A2AAgent:
        """Update an agent's health status after a health check.

        Args:
            session: Database session.
            agent_id: The agent's UUID.
            is_healthy: Whether the agent responded successfully.
            error_message: Optional error message if unhealthy.

        Returns:
            The updated A2AAgent.

        Raises:
            ValueError: If agent not found.
        """
        db_agent = session.exec(
            select(A2AAgent).where(A2AAgent.id == UUID(agent_id))
        ).first()
        if not db_agent:
            raise ValueError("A2A agent not found")

        now = datetime.now(timezone.utc)
        db_agent.last_health_check = now

        if is_healthy:
            db_agent.status = A2AAgentStatus.ACTIVE
            db_agent.consecutive_failures = 0
            db_agent.last_seen = now
        else:
            db_agent.consecutive_failures += 1
            # Mark as unreachable after 3 consecutive failures
            if db_agent.consecutive_failures >= 3:
                db_agent.status = A2AAgentStatus.UNREACHABLE
            elif db_agent.consecutive_failures >= 1:
                db_agent.status = A2AAgentStatus.ERROR

        session.add(db_agent)
        session.commit()
        session.refresh(db_agent)
        return db_agent

    @staticmethod
    def get_agents_needing_health_check(
        session: Session,
        organization_id: Optional[str] = None,
    ) -> List[A2AAgent]:
        """Get agents that are due for a health check.

        Returns agents where:
        - status is 'active' or 'error' (not 'inactive')
        - last_health_check is None OR older than health_check_interval

        Args:
            session: Database session.
            organization_id: Optional organization filter.

        Returns:
            List of A2AAgent records needing health checks.
        """
        now = datetime.now(timezone.utc)
        query = select(A2AAgent).where(
            A2AAgent.status.in_([A2AAgentStatus.ACTIVE, A2AAgentStatus.ERROR])
        )

        if organization_id:
            query = query.where(A2AAgent.organization_id == organization_id)

        agents = list(session.exec(query).all())

        # Filter by health check interval
        agents_needing_check = []
        for agent in agents:
            if agent.last_health_check is None:
                agents_needing_check.append(agent)
            else:
                seconds_since_check = (now - agent.last_health_check).total_seconds()
                if seconds_since_check >= agent.health_check_interval:
                    agents_needing_check.append(agent)

        return agents_needing_check

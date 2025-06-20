
import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship, remote, foreign

from .base import Base

class Agent(Base):
    __tablename__ = "agents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    agent_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), unique=True, nullable=False, default=uuid.uuid4)

    name: Mapped[str] = mapped_column(String, nullable=False)
    agent_type: Mapped[Optional[str]] = mapped_column(
        String, nullable=True
    )  # router, web_search, data, troubleshooting, api, etc.
    description: Mapped[Optional[str]] = mapped_column(String, nullable=True)  # Description of what the agent does
    parent_agent_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agents.agent_id"), nullable=True
    )
    system_prompt_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("prompts.pid"), nullable=False)
    persona: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    functions: Mapped[List[dict]] = mapped_column(JSONB, nullable=False)
    routing_options: Mapped[dict] = mapped_column(JSONB, nullable=False)
    short_term_memory: Mapped[bool] = mapped_column(Boolean, default=False)
    long_term_memory: Mapped[bool] = mapped_column(Boolean, default=False)
    reasoning: Mapped[bool] = mapped_column(Boolean, default=False)

    input_type: Mapped[List[str]] = mapped_column(JSONB, default=["text", "voice"])
    output_type: Mapped[List[str]] = mapped_column(JSONB, default=["text", "voice"])
    response_type: Mapped[str] = mapped_column(String, default="json")

    max_retries: Mapped[int] = mapped_column(Integer, default=3)
    timeout: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    deployed: Mapped[bool] = mapped_column(Boolean, default=False)
    status: Mapped[str] = mapped_column(String, default="active")
    priority: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    available_for_deployment: Mapped[bool] = mapped_column(Boolean, default=True)
    deployment_code: Mapped[Optional[str]] = mapped_column(String, nullable=True)  # Short code for deployment (e.g., "w", "h")

    failure_strategies: Mapped[Optional[List[str]]] = mapped_column(JSONB, nullable=True)

    session_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    last_active: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    collaboration_mode: Mapped[str] = mapped_column(String, default="single")

    system_prompt = relationship("Prompt", back_populates="agents")

    child_agents = relationship(
        "Agent",
        backref="parent",
        primaryjoin=remote(parent_agent_id) == foreign(agent_id),
    )

    __table_args__ = (UniqueConstraint("name", "system_prompt_id", name="uix_agent_name_prompt"),)

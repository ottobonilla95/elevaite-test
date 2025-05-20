import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.orm import relationship, remote, foreign

from .database import Base


class Prompt(Base):
    __tablename__ = "prompts"

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    pid = Column(UUID(as_uuid=True), unique=True, nullable=False, default=uuid.uuid4)

    # Basic prompt information
    prompt_label = Column(String, nullable=False)
    prompt = Column(String, nullable=False)
    sha_hash = Column(String, nullable=False)
    unique_label = Column(String, nullable=False, unique=True)
    app_name = Column(String, nullable=False)
    version = Column(String, nullable=False)

    # Model information
    model_provider = Column(String, nullable=False)
    model_name = Column(String, nullable=False)

    # Status and timestamps
    is_deployed = Column(Boolean, default=False)
    created_time = Column(DateTime, default=datetime.now)
    deployed_time = Column(DateTime, nullable=True)
    last_deployed = Column(DateTime, nullable=True)

    # Additional metadata
    tags = Column(ARRAY(String), nullable=True)
    hyper_parameters = Column(JSONB, nullable=True)
    variables = Column(JSONB, nullable=True)

    # Relationships
    agents = relationship("Agent", back_populates="system_prompt")

    # Constraints
    __table_args__ = (
        UniqueConstraint(
            "app_name", "prompt_label", "version", name="uix_prompt_app_label_version"
        ),
    )


class Agent(Base):
    __tablename__ = "agents"

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    agent_id = Column(
        UUID(as_uuid=True), unique=True, nullable=False, default=uuid.uuid4
    )

    # Basic agent information
    name = Column(String, nullable=False)
    parent_agent_id = Column(
        UUID(as_uuid=True), ForeignKey("agents.agent_id"), nullable=True
    )
    system_prompt_id = Column(
        UUID(as_uuid=True), ForeignKey("prompts.pid"), nullable=False
    )
    persona = Column(String, nullable=True)

    # Agent capabilities
    functions = Column(JSONB, nullable=False)
    routing_options = Column(JSONB, nullable=False)
    short_term_memory = Column(Boolean, default=False)
    long_term_memory = Column(Boolean, default=False)
    reasoning = Column(Boolean, default=False)

    # Input/Output configuration
    input_type = Column(JSONB, default=["text", "voice"])
    output_type = Column(JSONB, default=["text", "voice"])
    response_type = Column(String, default="json")

    # Execution parameters
    max_retries = Column(Integer, default=3)
    timeout = Column(Integer, nullable=True)
    deployed = Column(Boolean, default=False)
    status = Column(String, default="active")
    priority = Column(Integer, nullable=True)

    # Failure handling
    failure_strategies = Column(JSONB, nullable=True)

    # Monitoring
    session_id = Column(String, nullable=True)
    last_active = Column(DateTime, nullable=True)
    collaboration_mode = Column(String, default="single")

    # Relationships
    system_prompt = relationship("Prompt", back_populates="agents")

    # Self-referential relationship
    child_agents = relationship(
        "Agent",
        backref="parent",
        primaryjoin=remote(parent_agent_id) == foreign(agent_id),
    )

    # Constraints
    __table_args__ = (
        UniqueConstraint("name", "system_prompt_id", name="uix_agent_name_prompt"),
    )


class PromptVersion(Base):
    __tablename__ = "prompt_versions"

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Version information
    prompt_id = Column(UUID(as_uuid=True), ForeignKey("prompts.pid"), nullable=False)
    version_number = Column(String, nullable=False)
    prompt_content = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.now)
    created_by = Column(String, nullable=True)

    # Additional metadata
    commit_message = Column(String, nullable=True)
    hyper_parameters = Column(JSONB, nullable=True)

    # Relationships
    prompt = relationship("Prompt")

    # Constraints
    __table_args__ = (
        UniqueConstraint("prompt_id", "version_number", name="uix_prompt_version"),
    )


class PromptDeployment(Base):
    __tablename__ = "prompt_deployments"

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Deployment information
    prompt_id = Column(UUID(as_uuid=True), ForeignKey("prompts.pid"), nullable=False)
    environment = Column(String, nullable=False)
    deployed_at = Column(DateTime, default=datetime.now)
    deployed_by = Column(String, nullable=True)
    version_number = Column(String, nullable=False)

    # Status
    is_active = Column(Boolean, default=True)

    # Relationships
    prompt = relationship("Prompt")

    # Constraints
    __table_args__ = (
        UniqueConstraint("prompt_id", "environment", name="uix_prompt_environment"),
    )

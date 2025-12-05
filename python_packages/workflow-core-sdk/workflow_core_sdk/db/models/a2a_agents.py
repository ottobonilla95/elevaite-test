"""
A2A (Agent-to-Agent) Agent SQLModel definitions for external agent registration.

A2A is Google's open protocol that enables AI agents to communicate with each other.
This model stores connection information for external agents exposed via A2A protocol.
"""

from typing import Optional, List, Dict, Any, Literal
import uuid as uuid_module
from datetime import datetime
from sqlmodel import SQLModel, Field
from sqlalchemy import Column, JSON, DateTime, func

from .base import get_utc_datetime


# A2A Agent status options
A2AAgentStatus = Literal["active", "inactive", "error", "unreachable"]

# A2A Authentication types
A2AAuthType = Literal["none", "bearer", "api_key", "oauth2"]


# ---------- A2A Agent Skill (from Agent Card) ----------
class A2AAgentSkill(SQLModel):
    """Represents a skill/capability advertised by an A2A agent in its Agent Card."""
    id: str
    name: str
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    examples: Optional[List[str]] = None
    input_modes: Optional[List[str]] = None  # ["text", "file", "data"]
    output_modes: Optional[List[str]] = None  # ["text", "file", "data"]


# ---------- A2A Agent Base Schema ----------
class A2AAgentBase(SQLModel):
    """Base schema for A2A agent data."""
    name: str
    description: Optional[str] = None
    
    # Connection info
    base_url: str  # e.g., "https://agent.example.com"
    agent_card_url: Optional[str] = None  # Defaults to {base_url}/.well-known/agent.json
    
    # Authentication
    auth_type: A2AAuthType = "none"
    auth_config: Optional[Dict[str, Any]] = None  # Credentials config
    
    # Health check settings
    health_check_interval: int = 300  # seconds
    
    # Organization/multi-tenancy
    organization_id: Optional[str] = None
    tags: Optional[List[str]] = None


class A2AAgentCreate(A2AAgentBase):
    """Schema for creating a new A2A agent registration."""
    pass


class A2AAgentUpdate(SQLModel):
    """Schema for updating an A2A agent registration."""
    name: Optional[str] = None
    description: Optional[str] = None
    base_url: Optional[str] = None
    agent_card_url: Optional[str] = None
    auth_type: Optional[A2AAuthType] = None
    auth_config: Optional[Dict[str, Any]] = None
    health_check_interval: Optional[int] = None
    status: Optional[A2AAgentStatus] = None
    tags: Optional[List[str]] = None


class A2AAgentRead(A2AAgentBase):
    """Schema for reading A2A agent data."""
    id: uuid_module.UUID
    
    # Agent Card data (cached from remote)
    agent_card: Optional[Dict[str, Any]] = None
    skills: Optional[List[Dict[str, Any]]] = None
    supported_input_modes: Optional[List[str]] = None
    supported_output_modes: Optional[List[str]] = None
    
    # Protocol version
    protocol_version: Optional[str] = None
    
    # Status & Health
    status: A2AAgentStatus = "active"
    last_health_check: Optional[datetime] = None
    consecutive_failures: int = 0
    
    # Metadata
    created_by: Optional[str] = None
    registered_at: datetime
    last_seen: Optional[datetime] = None
    updated_at: datetime


# ---------- A2A Agent Database Model ----------
class A2AAgent(SQLModel, table=True):
    """
    Database model for storing A2A (Agent-to-Agent) agent connections.
    
    Stores connection information, cached Agent Card data, authentication,
    and health status for external agents exposed via the A2A protocol.
    """
    __tablename__ = "a2a_agents"
    
    id: uuid_module.UUID = Field(default_factory=uuid_module.uuid4, primary_key=True)
    name: str
    description: Optional[str] = None
    
    # Connection info
    base_url: str  # e.g., "https://agent.example.com"
    agent_card_url: Optional[str] = None  # Defaults to {base_url}/.well-known/agent.json
    
    # Agent Card data (cached from remote)
    agent_card: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON))
    skills: Optional[List[Dict[str, Any]]] = Field(default=None, sa_column=Column(JSON))
    supported_input_modes: Optional[List[str]] = Field(default=None, sa_column=Column(JSON))
    supported_output_modes: Optional[List[str]] = Field(default=None, sa_column=Column(JSON))
    
    # Protocol version from Agent Card
    protocol_version: Optional[str] = None
    
    # Authentication
    auth_type: str = "none"  # none, bearer, api_key, oauth2
    auth_config: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON))
    
    # Health check settings
    health_check_interval: int = 300  # seconds
    
    # Status & Health
    status: str = Field(default="active")  # active, inactive, error, unreachable
    last_health_check: Optional[datetime] = Field(default=None, sa_column=Column(DateTime(timezone=True)))
    consecutive_failures: int = 0
    
    # Organization/multi-tenancy
    organization_id: Optional[str] = None
    created_by: Optional[str] = None
    tags: Optional[List[str]] = Field(default=None, sa_column=Column(JSON))
    
    # Timestamps
    registered_at: datetime = Field(
        default_factory=get_utc_datetime,
        sa_column=Column(DateTime(timezone=True), server_default=func.now()),
    )
    last_seen: Optional[datetime] = Field(default=None, sa_column=Column(DateTime(timezone=True)))
    updated_at: datetime = Field(
        default_factory=get_utc_datetime,
        sa_column=Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now()),
    )


"""
Agent and AgentToolBinding SQLModel definitions

This module defines Agent and AgentToolBinding database models and API schemas.
"""

import uuid as uuid_module
from typing import Optional, List, Dict, Any, Literal, Union
from sqlmodel import SQLModel, Field
from sqlalchemy import Column, JSON, DateTime, func

from datetime import datetime
from .base import get_utc_datetime


class ProviderType(str):
    OPENAI = "openai_textgen"
    GEMINI = "gemini_textgen"
    BEDROCK = "bedrock_textgen"
    ON_PREM = "on-prem_textgen"


# Provider-specific config models (Pydantic via SQLModel)
class OpenAIConfig(SQLModel):
    provider_type: Literal[ProviderType.OPENAI]
    model_name: Optional[str] = None
    temperature: Optional[float] = 0.5
    max_tokens: Optional[int] = 100


class GeminiConfig(SQLModel):
    provider_type: Literal[ProviderType.GEMINI]
    model_name: Optional[str] = None
    temperature: Optional[float] = 0.5
    max_tokens: Optional[int] = 100


class BedrockConfig(SQLModel):
    provider_type: Literal[ProviderType.BEDROCK]
    model_name: Optional[str] = None
    temperature: Optional[float] = 0.5
    max_tokens: Optional[int] = 100


class OnPremConfig(SQLModel):
    provider_type: Literal[ProviderType.ON_PREM]
    model_name: Optional[str] = None
    temperature: Optional[float] = 0.5
    max_tokens: Optional[int] = 100


ProviderConfig = Union[OpenAIConfig, GeminiConfig, BedrockConfig, OnPremConfig]


# API Schemas
class AgentBase(SQLModel):
    name: str
    description: Optional[str] = None
    system_prompt_id: uuid_module.UUID
    provider_type: str
    provider_config: Dict[str, Any] = {}
    tags: List[str] = []
    status: Literal["active", "inactive", "draft"] = "active"
    organization_id: Optional[str] = None
    created_by: Optional[str] = None


class AgentCreate(AgentBase):
    pass


class AgentUpdate(SQLModel):
    name: Optional[str] = None
    description: Optional[str] = None
    system_prompt_id: Optional[uuid_module.UUID] = None
    provider_type: Optional[str] = None
    provider_config: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None
    status: Optional[Literal["active", "inactive", "draft"]] = None


class AgentRead(AgentBase):
    id: uuid_module.UUID
    created_at: datetime
    updated_at: Optional[datetime] = None


# Database models
class Agent(SQLModel, table=True):
    __tablename__: str = "agents"  # type: ignore

    id: uuid_module.UUID = Field(
        default_factory=uuid_module.uuid4,
        primary_key=True,
    )

    name: str
    description: Optional[str] = None

    system_prompt_id: uuid_module.UUID

    provider_type: str
    provider_config: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))

    tags: List[str] = Field(default_factory=list, sa_column=Column(JSON))
    status: str = Field(default="active")

    organization_id: Optional[str] = None
    created_by: Optional[str] = None

    created_at: datetime = Field(
        default_factory=get_utc_datetime,
        sa_column=Column(DateTime(timezone=True), server_default=func.now()),
    )
    updated_at: Optional[datetime] = Field(default=None, sa_column=Column(DateTime(timezone=True), onupdate=func.now()))


class AgentToolBinding(SQLModel, table=True):
    __tablename__: str = "agent_tool_bindings"  # type: ignore

    id: uuid_module.UUID = Field(
        default_factory=uuid_module.uuid4,
        primary_key=True,
    )
    agent_id: uuid_module.UUID
    tool_id: uuid_module.UUID
    override_parameters: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    is_active: bool = True

    organization_id: Optional[str] = None
    created_by: Optional[str] = None

    created_at: datetime = Field(
        default_factory=get_utc_datetime,
        sa_column=Column(DateTime(timezone=True), server_default=func.now()),
    )
    updated_at: Optional[datetime] = Field(default=None, sa_column=Column(DateTime(timezone=True), onupdate=func.now()))

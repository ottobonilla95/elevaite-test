"""
Prompt SQLModel definitions
"""

import uuid as uuid_module
from typing import Optional, List, Dict, Any
from sqlmodel import SQLModel, Field
from sqlalchemy import Column, JSON, DateTime, func
from sqlalchemy.dialects.postgresql import UUID

from .base import get_utc_datetime


class PromptBase(SQLModel):
    prompt_label: str
    prompt: str
    unique_label: str
    app_name: str
    ai_model_provider: str
    ai_model_name: str
    tags: List[str] = []
    hyper_parameters: Dict[str, Any] = {}
    variables: Dict[str, Any] = {}
    organization_id: Optional[str] = None
    created_by: Optional[str] = None


class PromptCreate(PromptBase):
    pass


class PromptUpdate(SQLModel):
    prompt_label: Optional[str] = None
    prompt: Optional[str] = None
    unique_label: Optional[str] = None
    app_name: Optional[str] = None
    ai_model_provider: Optional[str] = None
    ai_model_name: Optional[str] = None
    tags: Optional[List[str]] = None
    hyper_parameters: Optional[Dict[str, Any]] = None
    variables: Optional[Dict[str, Any]] = None


class PromptRead(PromptBase):
    id: int
    uuid: uuid_module.UUID
    pid: uuid_module.UUID
    created_time: str
    updated_time: Optional[str] = None


class Prompt(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    uuid: uuid_module.UUID = Field(
        default_factory=uuid_module.uuid4,
        sa_column=Column(UUID(as_uuid=True), unique=True, nullable=False),
    )
    pid: uuid_module.UUID = Field(
        default_factory=uuid_module.uuid4,
        sa_column=Column(UUID(as_uuid=True), unique=True, nullable=False),
        description="External prompt identifier",
    )

    prompt_label: str
    prompt: str
    unique_label: str
    app_name: str
    ai_model_provider: str
    ai_model_name: str

    tags: List[str] = Field(default_factory=list, sa_column=Column(JSON))
    hyper_parameters: Dict[str, Any] = Field(
        default_factory=dict, sa_column=Column(JSON)
    )
    variables: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))

    organization_id: Optional[str] = None
    created_by: Optional[str] = None

    created_time: Any = Field(
        default_factory=get_utc_datetime,
        sa_column=Column(DateTime(timezone=True), server_default=func.now()),
    )
    updated_time: Optional[Any] = Field(
        default=None, sa_column=Column(DateTime(timezone=True), onupdate=func.now())
    )

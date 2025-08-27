"""
Prompt SQLModel definitions
"""

import uuid as uuid_module
from typing import Optional, List, Dict, Any
from datetime import datetime
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
    id: uuid_module.UUID
    created_time: datetime
    updated_time: Optional[datetime] = None


class Prompt(SQLModel, table=True):
    id: uuid_module.UUID = Field(
        default_factory=uuid_module.uuid4,
        primary_key=True,
    )

    prompt_label: str
    prompt: str
    unique_label: str
    app_name: str
    ai_model_provider: str
    ai_model_name: str

    tags: List[str] = Field(default_factory=list, sa_column=Column(JSON))
    hyper_parameters: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    variables: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))

    organization_id: Optional[str] = None
    created_by: Optional[str] = None

    created_time: datetime = Field(
        default_factory=get_utc_datetime,
        sa_column=Column(DateTime(timezone=True), server_default=func.now()),
    )
    updated_time: Optional[datetime] = Field(default=None, sa_column=Column(DateTime(timezone=True), onupdate=func.now()))

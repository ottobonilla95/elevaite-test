"""
Approval request SQLModel definitions
"""

from __future__ import annotations

import uuid as uuid_module
from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum
from sqlmodel import SQLModel, Field, Column, JSON

from .base import get_utc_datetime


class ApprovalStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    DENIED = "denied"


class ApprovalRequestBase(SQLModel):
    workflow_id: uuid_module.UUID = Field(description="Related workflow id")
    execution_id: uuid_module.UUID = Field(description="Related execution id")
    step_id: str = Field(max_length=255, description="Step awaiting approval")

    status: ApprovalStatus = Field(default=ApprovalStatus.PENDING)
    prompt: Optional[str] = Field(default=None, description="Prompt/instructions shown to approver")
    approval_metadata: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    response_payload: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON))

    requested_at: datetime = Field(default_factory=get_utc_datetime)
    decided_at: Optional[datetime] = Field(default=None)
    decided_by: Optional[str] = Field(default=None, max_length=255)


class ApprovalRequest(ApprovalRequestBase, table=True):
    id: uuid_module.UUID = Field(default_factory=uuid_module.uuid4, primary_key=True)


class ApprovalRequestRead(ApprovalRequestBase):
    id: uuid_module.UUID
    requested_at: datetime = Field(default_factory=get_utc_datetime)
    decided_at: Optional[datetime] = None

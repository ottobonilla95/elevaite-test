"""
Agent message models for interactive per-agent chat
"""

import uuid as uuid_module
from typing import Optional, Dict, Any
from datetime import datetime
from sqlmodel import SQLModel, Field
from sqlalchemy import Column, JSON, Text, DateTime, func


from .base import get_utc_datetime


class AgentMessage(SQLModel, table=True):
    """Stores chat messages for interactive per-agent steps within an execution"""

    id: uuid_module.UUID = Field(default_factory=uuid_module.uuid4, primary_key=True)

    # Associations
    execution_id: uuid_module.UUID = Field(description="Execution ID")
    step_id: str = Field(max_length=255, description="Step ID within the workflow")

    # Message content
    role: str = Field(max_length=50, description="Message role: user/assistant/system")
    content: str = Field(sa_column=Column(Text), description="Message content")
    message_metadata: Optional[Dict[str, Any]] = Field(
        default=None, sa_column=Column(JSON)
    )

    # User/session context
    user_id: Optional[str] = Field(default=None, max_length=255)
    session_id: Optional[str] = Field(default=None, max_length=255)

    # Timestamps
    created_at: datetime = Field(
        default_factory=get_utc_datetime,
        sa_column=Column(DateTime(timezone=True), server_default=func.now()),
    )

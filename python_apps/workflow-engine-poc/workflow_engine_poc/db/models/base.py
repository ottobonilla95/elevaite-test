"""
Base SQLModel classes and mixins

This module provides common functionality and mixins for all database models.
"""

import uuid as uuid_module
from datetime import datetime, timezone
from typing import Optional
from sqlmodel import SQLModel, Field
from sqlalchemy import Column, DateTime, func
from sqlalchemy.dialects.postgresql import UUID


def get_utc_datetime() -> datetime:
    """Get current UTC datetime"""
    return datetime.now(timezone.utc)


class BaseModel(SQLModel):
    """Base model with single UUID primary key and timestamps"""

    id: uuid_module.UUID = Field(
        default_factory=uuid_module.uuid4,
        primary_key=True,
        description="Primary identifier",
    )

    created_at: datetime = Field(
        default_factory=get_utc_datetime,
        sa_column=Column(DateTime(timezone=True), server_default=func.now()),
        description="When the record was created",
    )
    updated_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), onupdate=func.now()),
        description="When the record was last updated",
    )

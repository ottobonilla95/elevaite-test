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


class UUIDMixin(SQLModel):
    """Mixin for models that need a UUID primary key"""

    id: Optional[int] = Field(default=None, primary_key=True)
    uuid: uuid_module.UUID = Field(
        default_factory=uuid_module.uuid4,
        sa_column=Column(UUID(as_uuid=True), unique=True, nullable=False),
        description="Unique identifier",
    )


class TimestampMixin(SQLModel):
    """Mixin for models that need created_at and updated_at timestamps"""

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


class BaseModel(SQLModel):
    """Base model with UUID and timestamp functionality"""

    id: Optional[int] = Field(default=None, primary_key=True)
    uuid: uuid_module.UUID = Field(
        default_factory=uuid_module.uuid4,
        sa_column=Column(UUID(as_uuid=True), unique=True, nullable=False),
        description="Unique identifier",
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

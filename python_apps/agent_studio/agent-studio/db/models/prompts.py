
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
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, get_utc_datetime

class Prompt(Base):
    __tablename__ = "prompts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    pid: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), unique=True, nullable=False, default=uuid.uuid4)

    prompt_label: Mapped[str] = mapped_column(String, nullable=False)
    prompt: Mapped[str] = mapped_column(String, nullable=False)
    sha_hash: Mapped[str] = mapped_column(String, nullable=False)
    unique_label: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    app_name: Mapped[str] = mapped_column(String, nullable=False)
    version: Mapped[str] = mapped_column(String, nullable=False)

    ai_model_provider: Mapped[str] = mapped_column(String, nullable=False)
    ai_model_name: Mapped[str] = mapped_column(String, nullable=False)

    is_deployed: Mapped[bool] = mapped_column(Boolean, default=False)
    created_time: Mapped[datetime] = mapped_column(DateTime, default=get_utc_datetime)
    deployed_time: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    last_deployed: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    tags: Mapped[Optional[List[str]]] = mapped_column(ARRAY(String), nullable=True)
    hyper_parameters: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    variables: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    agents = relationship("Agent", back_populates="system_prompt")

    __table_args__ = (UniqueConstraint("app_name", "prompt_label", "version", name="uix_prompt_app_label_version"),)

class PromptVersion(Base):
    __tablename__ = "prompt_versions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    prompt_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("prompts.pid"), nullable=False)
    version_number: Mapped[str] = mapped_column(String, nullable=False)
    prompt_content: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=get_utc_datetime)
    created_by: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    commit_message: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    hyper_parameters: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    prompt = relationship("Prompt")

    __table_args__ = (UniqueConstraint("prompt_id", "version_number", name="uix_prompt_version"),)

class PromptDeployment(Base):
    __tablename__ = "prompt_deployments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    prompt_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("prompts.pid"), nullable=False)
    environment: Mapped[str] = mapped_column(String, nullable=False)
    deployed_at: Mapped[datetime] = mapped_column(DateTime, default=get_utc_datetime)
    deployed_by: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    version_number: Mapped[str] = mapped_column(String, nullable=False)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    prompt = relationship("Prompt")

    __table_args__ = (UniqueConstraint("prompt_id", "environment", name="uix_prompt_environment"),)

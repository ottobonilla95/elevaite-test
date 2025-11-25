"""
Data models for the ingestion service.
"""

from __future__ import annotations

import uuid as uuid_module
from datetime import datetime, timezone
from enum import Enum
from typing import Optional, Dict, Any

from sqlmodel import SQLModel, Field, Column, JSON, Text
from sqlalchemy import DateTime


class JobStatus(str, Enum):
    """Status of an ingestion job"""

    PENDING = "PENDING"
    RUNNING = "RUNNING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"


class IngestionJob(SQLModel, table=True):
    """
    Ingestion job entity.

    Stores information about ingestion jobs including their configuration,
    status, and callback information for DBOS event notification.
    """

    __tablename__ = "ingestion_jobs"

    id: uuid_module.UUID = Field(
        default_factory=uuid_module.uuid4,
        primary_key=True,
        nullable=False,
        description="Unique job identifier",
    )

    config: Dict[str, Any] = Field(
        sa_column=Column(JSON),
        description="Ingestion configuration (validated by elevaite_ingestion config model)",
    )

    status: JobStatus = Field(
        default=JobStatus.PENDING,
        description="Current job status",
    )

    error_message: Optional[str] = Field(
        default=None,
        sa_column=Column(Text),
        description="Error message if job failed",
    )

    callback_topic: Optional[str] = Field(
        default=None,
        max_length=500,
        description="DBOS topic to notify when job completes",
    )

    tenant_id: Optional[str] = Field(
        default=None,
        max_length=255,
        description="Tenant/organization identifier",
    )

    execution_id: Optional[str] = Field(
        default=None,
        max_length=255,
        description="Workflow execution ID that triggered this job",
    )

    step_id: Optional[str] = Field(
        default=None,
        max_length=255,
        description="Workflow step ID that triggered this job",
    )

    dbos_workflow_id: Optional[str] = Field(
        default=None,
        max_length=255,
        description="DBOS workflow ID for sending completion events (destination_id)",
    )

    job_type: Optional[str] = Field(
        default="BULK_DATASET",
        max_length=100,
        description="Type of ingestion job (e.g., BULK_DATASET, ADHOC_FILE)",
    )

    result_summary: Optional[Dict[str, Any]] = Field(
        default=None,
        sa_column=Column(JSON),
        description="Summary of job results (e.g., files processed, index IDs)",
    )

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True)),
        description="Job creation timestamp",
    )

    updated_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), onupdate=lambda: datetime.now(timezone.utc)),
        description="Job last update timestamp",
    )

    completed_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True)),
        description="Job completion timestamp",
    )


class CreateJobRequest(SQLModel):
    """Request model for creating an ingestion job"""

    config: Dict[str, Any] = Field(description="Ingestion configuration matching elevaite_ingestion schema")

    metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional metadata (tenant_id, execution_id, step_id, callback_topic)",
    )


class JobResponse(SQLModel):
    """Response model for job status"""

    job_id: uuid_module.UUID
    status: JobStatus
    error_message: Optional[str] = None
    result_summary: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

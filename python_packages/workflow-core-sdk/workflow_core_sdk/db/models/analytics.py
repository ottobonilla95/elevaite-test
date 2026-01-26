"""
Analytics models (tokens-only parity)
"""
import uuid as uuid_module
from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field
from sqlalchemy import Column, DateTime, Text


class AgentExecutionMetrics(SQLModel, table=True):
    id: uuid_module.UUID = Field(default_factory=uuid_module.uuid4, primary_key=True)

    # Relations/identifiers
    execution_id: uuid_module.UUID = Field(description="WorkflowExecution.id")
    step_execution_id: Optional[uuid_module.UUID] = Field(default=None, description="StepExecution.id if available")

    # Agent identity
    agent_id: Optional[str] = Field(default=None, description="Agent instance id")
    agent_name: str

    # Timing
    start_time: datetime = Field(default_factory=datetime.utcnow)
    end_time: Optional[datetime] = Field(default=None, sa_column=Column(DateTime))
    duration_ms: Optional[int] = Field(default=None)

    # Status
    status: str = Field(default="completed")
    error_message: Optional[str] = Field(default=None, sa_column=Column(Text))

    # Query/response (optional, truncated upstream if needed)
    query: Optional[str] = Field(default=None, sa_column=Column(Text))
    response: Optional[str] = Field(default=None, sa_column=Column(Text))

    # Tokens-only usage
    tokens_in: Optional[int] = Field(default=None)
    tokens_out: Optional[int] = Field(default=None)
    total_tokens: Optional[int] = Field(default=None)
    llm_calls: Optional[int] = Field(default=None)

    # Model info (for later pricing calc)
    model_provider: Optional[str] = Field(default=None)
    model_name: Optional[str] = Field(default=None)


class WorkflowMetrics(SQLModel, table=True):
    id: uuid_module.UUID = Field(default_factory=uuid_module.uuid4, primary_key=True)

    execution_id: uuid_module.UUID = Field(description="WorkflowExecution.id")
    workflow_id: uuid_module.UUID = Field(description="Workflow.id")
    workflow_name: Optional[str] = Field(default=None)

    # Timing
    start_time: Optional[datetime] = Field(default=None, sa_column=Column(DateTime))
    end_time: Optional[datetime] = Field(default=None, sa_column=Column(DateTime))
    duration_ms: Optional[int] = Field(default=None)

    status: str = Field(default="completed")

    # Step counts
    total_steps: Optional[int] = Field(default=None)
    completed_steps: Optional[int] = Field(default=None)
    failed_steps: Optional[int] = Field(default=None)

    # Tokens-only rollup
    total_tokens_in: Optional[int] = Field(default=None)
    total_tokens_out: Optional[int] = Field(default=None)
    total_tokens: Optional[int] = Field(default=None)
    total_llm_calls: Optional[int] = Field(default=None)


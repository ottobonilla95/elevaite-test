"""
SQLModel database models for the Workflow Engine

This package contains all database model definitions using SQLModel,
which provides both SQLAlchemy ORM functionality and Pydantic validation.
"""

from .base import TimestampMixin, UUIDMixin
from .workflows import (
    Workflow,
    WorkflowBase,
    WorkflowCreate,
    WorkflowRead,
    WorkflowUpdate,
)
from .executions import (
    ExecutionStatus,
    StepStatus,
    WorkflowExecution,
    WorkflowExecutionBase,
    WorkflowExecutionRead,
    WorkflowExecutionUpdate,
    StepExecution,
    StepExecutionBase,
    StepExecutionRead,
    StepExecutionUpdate,
)
from .step_registry import (
    StepType,
    StepTypeBase,
    StepTypeCreate,
    StepTypeRead,
    StepTypeUpdate,
)
from .agents import (
    Agent,
    AgentBase,
    AgentCreate,
    AgentRead,
    AgentUpdate,
    AgentToolBinding,
)
from .prompts import (
    Prompt,
    PromptCreate,
    PromptRead,
    PromptUpdate,
)

__all__ = [
    # Base mixins
    "TimestampMixin",
    "UUIDMixin",
    # Workflow models
    "Workflow",
    "WorkflowBase",
    "WorkflowCreate",
    "WorkflowRead",
    "WorkflowUpdate",
    # Execution models
    "ExecutionStatus",
    "StepStatus",
    "WorkflowExecution",
    "WorkflowExecutionBase",
    "WorkflowExecutionRead",
    "WorkflowExecutionUpdate",
    "StepExecution",
    "StepExecutionBase",
    "StepExecutionRead",
    "StepExecutionUpdate",
    # Step registry models
    "StepType",
    "StepTypeBase",
    "StepTypeCreate",
    "StepTypeRead",
    "StepTypeUpdate",
    # Agent models
    "Agent",
    "AgentBase",
    "AgentCreate",
    "AgentRead",
    "AgentUpdate",
    "AgentToolBinding",
    # Prompt models
    "Prompt",
    "PromptCreate",
    "PromptRead",
    "PromptUpdate",
]

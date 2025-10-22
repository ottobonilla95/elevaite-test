"""
SQLModel database models for the Workflow Engine

This package contains all database model definitions using SQLModel,
which provides both SQLAlchemy ORM functionality and Pydantic validation.
"""

from .base import BaseModel
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
from .messages import AgentMessage
from .prompts import (
    Prompt,
    PromptCreate,
    PromptRead,
    PromptUpdate,
)
from .analytics import (
    AgentExecutionMetrics,
    WorkflowMetrics,
)
from .tools import (
    Tool,
    ToolBase,
    ToolCreate,
    ToolRead,
    ToolUpdate,
    ToolCategory,
    ToolCategoryBase,
    ToolCategoryCreate,
    ToolCategoryRead,
    ToolCategoryUpdate,
    MCPServer,
    MCPServerBase,
    MCPServerCreate,
    MCPServerUpdate,
    MCPServerRead,
)
from .approvals import (
    ApprovalRequest,
    ApprovalRequestBase,
    ApprovalRequestRead,
    ApprovalStatus,
)

__all__ = [
    # Base model
    "BaseModel",
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
    # Messages
    "AgentMessage",
    # Prompt models
    "Prompt",
    "PromptCreate",
    "PromptRead",
    "PromptUpdate",
    # Approvals
    "ApprovalRequest",
    "ApprovalRequestBase",
    "ApprovalRequestRead",
    "ApprovalStatus",
]

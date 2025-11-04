"""workflow-core-sdk: Shared execution core for Elevaite workflows."""

__version__ = "0.1.0"

# Core execution components
from .workflow_engine import WorkflowEngine
from workflow_core_sdk.execution.context_impl import ExecutionContext
from workflow_core_sdk.execution.registry_impl import StepRegistry

# Database
from .db.database import engine, get_db_session, create_db_and_tables

# Database models
from .db.models import (
    Workflow,
    WorkflowExecution,
    StepExecution,
    Agent,
    Tool,
    ToolCategory,
    MCPServer,
)

# Services - Business logic layer
from .services.workflows_service import WorkflowsService
from .services.executions_service import ExecutionsService
from .services.execution_service import ExecutionService
from .services.tools_service import ToolsService
from .services.agents_service import AgentsService
from .services.prompts_service import PromptsService
from .services.approvals_service import ApprovalsService
from .services.analytics_service import analytics_service

# Tools
from .tools import get_all_tools, get_all_schemas, function_schema, tool_handler
from .tools.registry import tool_registry

# NOTE: Routers are NOT exported from SDK
# They should live in the API applications (agent_studio, workflow-engine-poc)
# The SDK provides services that routers can use

__all__ = [
    "__version__",
    # Execution
    "WorkflowEngine",
    "ExecutionContext",
    "StepRegistry",
    # Database
    "engine",
    "get_db_session",
    "create_db_and_tables",
    # Models
    "Workflow",
    "WorkflowExecution",
    "StepExecution",
    "Agent",
    "Tool",
    "ToolCategory",
    "MCPServer",
    # Services
    "WorkflowsService",
    "ExecutionsService",
    "ExecutionService",
    "ToolsService",
    "AgentsService",
    "PromptsService",
    "ApprovalsService",
    "analytics_service",
    # Tools
    "get_all_tools",
    "get_all_schemas",
    "function_schema",
    "tool_handler",
    "tool_registry",
]

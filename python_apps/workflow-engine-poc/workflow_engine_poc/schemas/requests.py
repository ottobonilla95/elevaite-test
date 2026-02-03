"""
Request schemas for workflow-engine-poc API endpoints

These models define the structure of request bodies for endpoints that don't
have corresponding models in the SDK.
"""

from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field, model_validator
import uuid as uuid_module

from workflow_core_sdk.schemas.inline_tools import (
    InlineToolDefinition,
    UserFunctionDefinition,
    WebSearchToolConfig,
    CodeExecutionToolConfig,
)


# ============================================================================
# Agent Tool Binding Requests
# ============================================================================


class AgentToolBindingCreate(BaseModel):
    """Request model for attaching a tool to an agent.

    There are three ways to attach a tool:
    1. By tool_id: Reference an existing tool in the database
    2. By local_tool_name: Reference a tool from the local registry
    3. By inline_definition: Provide a full tool definition inline

    For inline definitions, the definition is stored in override_parameters
    and a placeholder tool_id is used for the database FK.
    """

    tool_id: Optional[str] = Field(
        default=None,
        description="ID of the tool to attach (UUID as string)",
    )
    local_tool_name: Optional[str] = Field(
        default=None,
        description="Name of a local tool to attach (alternative to tool_id)",
    )
    inline_definition: Optional[
        Union[UserFunctionDefinition, WebSearchToolConfig, CodeExecutionToolConfig]
    ] = Field(
        default=None,
        description="Full inline tool definition (alternative to tool_id/local_tool_name)",
    )
    override_parameters: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Tool-specific parameter overrides for this agent",
    )
    is_active: bool = Field(
        default=True,
        description="Whether this tool binding is enabled",
    )

    @model_validator(mode="after")
    def validate_tool_source(self) -> "AgentToolBindingCreate":
        """Ensure exactly one tool source is provided."""
        sources = [
            self.tool_id is not None,
            self.local_tool_name is not None,
            self.inline_definition is not None,
        ]
        if sum(sources) == 0:
            raise ValueError(
                "Must provide one of: tool_id, local_tool_name, or inline_definition"
            )
        if sum(sources) > 1:
            raise ValueError(
                "Provide only one of: tool_id, local_tool_name, or inline_definition"
            )
        return self


class AgentToolBindingUpdate(BaseModel):
    """Request model for updating an agent-tool binding"""

    override_parameters: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Updated tool-specific parameter overrides",
    )
    is_active: Optional[bool] = Field(
        default=None,
        description="Whether this tool binding is enabled",
    )


# ============================================================================
# Step Registration Requests
# ============================================================================


class StepConfigCreate(BaseModel):
    """Request model for registering a new step type"""

    step_type: str = Field(
        description="Unique identifier for this step type",
        min_length=1,
        max_length=100,
    )
    name: str = Field(
        description="Human-readable name for this step type",
        min_length=1,
        max_length=255,
    )
    description: Optional[str] = Field(
        default=None,
        description="Description of what this step does",
    )
    category: Optional[str] = Field(
        default=None,
        description="Category for organizing steps (e.g., 'data', 'ai', 'integration')",
    )
    parameters_schema: Dict[str, Any] = Field(
        default_factory=dict,
        description="JSON Schema defining the parameters this step accepts",
    )
    return_schema: Optional[Dict[str, Any]] = Field(
        default=None,
        description="JSON Schema defining the return value structure",
    )
    execution_config: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Configuration for step execution (timeout, retry, etc.)",
    )
    handler_url: Optional[str] = Field(
        default=None,
        description="URL endpoint for remote step execution",
    )
    handler_method: Optional[str] = Field(
        default="POST",
        description="HTTP method for remote step execution",
    )
    tags: Optional[List[str]] = Field(
        default=None,
        description="Tags for categorizing and searching steps",
    )
    version: str = Field(
        default="1.0.0",
        description="Version of this step type",
    )
    is_async: bool = Field(
        default=True,
        description="Whether this step executes asynchronously",
    )


# ============================================================================
# Approval Decision Requests
# ============================================================================


class ApprovalDecisionRequest(BaseModel):
    """Request model for approval/denial decisions"""

    payload: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional data to pass with the decision",
    )
    decided_by: Optional[str] = Field(
        default=None,
        description="User ID or identifier of who made the decision",
    )
    comment: Optional[str] = Field(
        default=None,
        description="Optional comment explaining the decision",
    )


# ============================================================================
# File Upload Requests
# ============================================================================


class FileUploadMetadata(BaseModel):
    """Metadata for file uploads (used with multipart forms)"""

    workflow_id: Optional[str] = Field(
        default=None,
        description="Workflow ID to trigger after upload",
    )
    auto_process: bool = Field(
        default=False,
        description="Whether to automatically trigger workflow processing",
    )
    tags: Optional[List[str]] = Field(
        default=None,
        description="Tags to associate with the uploaded file",
    )
    metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional metadata to store with the file",
    )


# ============================================================================
# Workflow Execution Requests
# ============================================================================


class WorkflowExecutionRequest(BaseModel):
    """Request model for workflow execution (alternative to multipart form)"""

    body_data: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Input data for the workflow",
    )
    message: Optional[str] = Field(
        default=None,
        description="User message to pass to the workflow",
    )
    chat_history: Optional[List[Dict[str, str]]] = Field(
        default=None,
        description="Chat history for conversational workflows",
    )
    execution_id: Optional[str] = Field(
        default=None,
        description="Optional execution ID to resume or track",
    )
    backend: Optional[str] = Field(
        default="local",
        description="Execution backend to use (local, dbos)",
    )
    metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional metadata for the execution",
    )


# ============================================================================
# Tool Update Requests (for stub endpoints)
# ============================================================================


class ToolStubUpdate(BaseModel):
    """Request model for updating tool stub metadata"""

    display_name: Optional[str] = Field(
        default=None,
        description="Updated display name",
    )
    description: Optional[str] = Field(
        default=None,
        description="Updated description",
    )
    tags: Optional[List[str]] = Field(
        default=None,
        description="Updated tags",
    )
    is_active: Optional[bool] = Field(
        default=None,
        description="Whether the tool is active",
    )
    documentation: Optional[str] = Field(
        default=None,
        description="Updated documentation",
    )
    examples: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="Updated usage examples",
    )


# ============================================================================
# Query Parameter Models
# ============================================================================


class PaginationParams(BaseModel):
    """Common pagination parameters"""

    limit: int = Field(
        default=100, ge=1, le=1000, description="Maximum number of results"
    )
    offset: int = Field(default=0, ge=0, description="Number of results to skip")


class WorkflowFilterParams(PaginationParams):
    """Query parameters for filtering workflows"""

    status: Optional[str] = Field(default=None, description="Filter by workflow status")
    tags: Optional[List[str]] = Field(default=None, description="Filter by tags")
    search: Optional[str] = Field(
        default=None, description="Search in name and description"
    )


class ExecutionFilterParams(PaginationParams):
    """Query parameters for filtering executions"""

    workflow_id: Optional[str] = Field(
        default=None, description="Filter by workflow ID"
    )
    status: Optional[str] = Field(
        default=None, description="Filter by execution status"
    )
    start_date: Optional[str] = Field(
        default=None, description="Filter by start date (ISO format)"
    )
    end_date: Optional[str] = Field(
        default=None, description="Filter by end date (ISO format)"
    )


class ToolFilterParams(PaginationParams):
    """Query parameters for filtering tools"""

    category_id: Optional[uuid_module.UUID] = Field(
        default=None, description="Filter by category"
    )
    tool_type: Optional[str] = Field(default=None, description="Filter by tool type")
    search: Optional[str] = Field(
        default=None, description="Search in name and description"
    )
    is_active: Optional[bool] = Field(
        default=None, description="Filter by active status"
    )

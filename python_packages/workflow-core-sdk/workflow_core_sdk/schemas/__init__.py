"""
Schemas module for workflow-core-sdk

Provides Pydantic schemas for workflows, inline tools, and other configurations.
"""

from .workflows import (
    WorkflowConfig,
    StepConfig,
    StepBase,
    TriggerStepConfig,
    InputStepConfig,
    MergeStepConfig,
    PromptStepConfig,
    ExecutionRequest,
    ChatMessage,
    Attachment,
    ChatTriggerPayload,
    FileTriggerPayload,
    WebhookTriggerPayload,
    TriggerPayload,
)

from .inline_tools import (
    InlineToolDefinition,
    UserFunctionDefinition,
    WebSearchToolConfig,
    WebSearchUserLocation,
    CodeExecutionToolConfig,
    PLACEHOLDER_TOOL_IDS,
)

__all__ = [
    # Workflow schemas
    "WorkflowConfig",
    "StepConfig",
    "StepBase",
    "TriggerStepConfig",
    "InputStepConfig",
    "MergeStepConfig",
    "PromptStepConfig",
    "ExecutionRequest",
    "ChatMessage",
    "Attachment",
    "ChatTriggerPayload",
    "FileTriggerPayload",
    "WebhookTriggerPayload",
    "TriggerPayload",
    # Inline tool schemas
    "InlineToolDefinition",
    "UserFunctionDefinition",
    "WebSearchToolConfig",
    "WebSearchUserLocation",
    "CodeExecutionToolConfig",
    "PLACEHOLDER_TOOL_IDS",
]

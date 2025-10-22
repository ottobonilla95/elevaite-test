"""
Compatibility module for workflow execution context.

This module provides backwards compatibility for Agent Studio-specific
workflow execution concepts that are not part of the core SDK.

Most workflow execution is now handled by workflow-core-sdk.
This module only contains Agent Studio-specific extensions.
"""

from enum import Enum
from typing import Optional, Dict, Any

# Re-export ExecutionPattern from SDK
from workflow_core_sdk.db.models.workflows import ExecutionPattern


class DeterministicStepType(str, Enum):
    """
    Agent Studio-specific step type enumeration.

    This is used for Agent Studio's custom step implementations
    and is not part of the core SDK.
    """

    # Generic step types
    DATA_INPUT = "data_input"
    DATA_OUTPUT = "data_output"
    DATA_PROCESSING = "data_processing"
    TRANSFORMATION = "transformation"
    VALIDATION = "validation"
    BATCH_PROCESSING = "batch_processing"

    # Specific step types
    FILE_READER = "file_reader"
    TEXT_CHUNKING = "text_chunking"
    EMBEDDING_GENERATION = "embedding_generation"
    VECTOR_STORAGE = "vector_storage"
    AGENT_EXECUTION = "agent_execution"
    TOOL_EXECUTION = "tool_execution"
    CUSTOM = "custom"


# Placeholder for workflow_execution_context singleton
# This is deprecated and should not be used in new code
class WorkflowExecutionContext:
    """
    DEPRECATED: Use SDK ExecutionContext instead.

    This class is kept for backwards compatibility only.
    """

    def __init__(self):
        self._executions: Dict[str, Any] = {}

    def track_execution(self, execution_id: str, **kwargs):
        """DEPRECATED: Use SDK ExecutionsService instead."""
        self._executions[execution_id] = kwargs
        return execution_id

    def get_execution(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """DEPRECATED: Use SDK ExecutionsService instead."""
        return self._executions.get(execution_id)

    def update_execution(self, execution_id: str, **kwargs):
        """DEPRECATED: Use SDK ExecutionsService instead."""
        if execution_id in self._executions:
            self._executions[execution_id].update(kwargs)


# Global singleton instance (deprecated)
workflow_execution_context = WorkflowExecutionContext()


__all__ = [
    "DeterministicStepType",
    "ExecutionPattern",
    "WorkflowExecutionContext",
    "workflow_execution_context",
]

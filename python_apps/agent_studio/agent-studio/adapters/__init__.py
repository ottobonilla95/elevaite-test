"""
Adapter layer for backwards compatibility between Agent Studio and SDK

This module provides adapters to convert between Agent Studio's API format
and the workflow-core-sdk's format, enabling drop-in compatibility while
using the SDK backend.

When the UI is reworked, these adapters can be removed and the SDK format
can be used directly.
"""

from .workflow_adapter import WorkflowAdapter
from .execution_adapter import ExecutionAdapter
from .request_adapter import RequestAdapter
from .response_adapter import ResponseAdapter

__all__ = [
    "WorkflowAdapter",
    "ExecutionAdapter",
    "RequestAdapter",
    "ResponseAdapter",
]


"""
Streaming utilities for Server-Sent Events (SSE) in workflow execution.

This module re-exports all streaming utilities from workflow_core_sdk.streaming
to ensure a single shared stream_manager instance is used across the entire application.
"""

# Re-export everything from the SDK's streaming module
# This ensures the same stream_manager singleton is used everywhere
from workflow_core_sdk.streaming import (
    StreamEventType,
    StreamEvent,
    StreamManager,
    stream_manager,
    create_sse_stream,
    get_sse_headers,
    create_status_event,
    create_step_event,
    create_error_event,
)

__all__ = [
    "StreamEventType",
    "StreamEvent",
    "StreamManager",
    "stream_manager",
    "create_sse_stream",
    "get_sse_headers",
    "create_status_event",
    "create_step_event",
    "create_error_event",
]

"""
Streaming utilities for Server-Sent Events (SSE) in workflow execution.

Provides standardized SSE format, connection management, and streaming utilities
for real-time workflow and execution updates.
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timezone
from typing import Dict, Any, Optional, Set, AsyncGenerator
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class StreamEventType(str, Enum):
    """Types of streaming events"""

    STATUS = "status"
    STEP = "step"
    ERROR = "error"
    HEARTBEAT = "heartbeat"
    COMPLETE = "complete"


@dataclass
class StreamEvent:
    """Standardized streaming event structure"""

    type: StreamEventType
    execution_id: str
    workflow_id: Optional[str] = None
    timestamp: Optional[str] = None
    data: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now(timezone.utc).isoformat()

    def to_sse(self) -> str:
        """Convert to Server-Sent Events format"""
        event_data = {
            "type": self.type,
            "execution_id": self.execution_id,
            "timestamp": self.timestamp,
            "data": self.data,
        }
        if self.workflow_id:
            event_data["workflow_id"] = self.workflow_id

        return f"data: {json.dumps(event_data)}\n\n"


class StreamManager:
    """Manages active streaming connections and event distribution"""

    def __init__(self):
        # Track active connections per execution
        self.execution_streams: Dict[str, Set[asyncio.Queue]] = {}
        # Track active connections per workflow
        self.workflow_streams: Dict[str, Set[asyncio.Queue]] = {}
        self._cleanup_task: Optional[asyncio.Task] = None

    def add_execution_stream(self, execution_id: str, queue: asyncio.Queue) -> None:
        """Add a streaming connection for a specific execution"""
        if execution_id not in self.execution_streams:
            self.execution_streams[execution_id] = set()
        self.execution_streams[execution_id].add(queue)
        logger.debug(
            f"Added execution stream for {execution_id}, total: {len(self.execution_streams[execution_id])}"
        )

    def add_workflow_stream(self, workflow_id: str, queue: asyncio.Queue) -> None:
        """Add a streaming connection for a workflow"""
        if workflow_id not in self.workflow_streams:
            self.workflow_streams[workflow_id] = set()
        self.workflow_streams[workflow_id].add(queue)
        logger.debug(
            f"Added workflow stream for {workflow_id}, total: {len(self.workflow_streams[workflow_id])}"
        )

    def remove_execution_stream(self, execution_id: str, queue: asyncio.Queue) -> None:
        """Remove a streaming connection for an execution"""
        if execution_id in self.execution_streams:
            self.execution_streams[execution_id].discard(queue)
            if not self.execution_streams[execution_id]:
                del self.execution_streams[execution_id]
                logger.debug(f"Execution stream registry deleted for {execution_id}")
        logger.debug(f"Removed execution stream for {execution_id}")

    def remove_workflow_stream(self, workflow_id: str, queue: asyncio.Queue) -> None:
        """Remove a streaming connection for a workflow"""
        if workflow_id in self.workflow_streams:
            self.workflow_streams[workflow_id].discard(queue)
            if not self.workflow_streams[workflow_id]:
                del self.workflow_streams[workflow_id]
        logger.debug(f"Removed workflow stream for {workflow_id}")

    async def emit_execution_event(self, event: StreamEvent) -> None:
        """Emit an event to all streams listening to this execution"""
        execution_id = event.execution_id
        logger.debug(f"Emit event: type={event.type}, execution_id={execution_id}")
        if execution_id not in self.execution_streams:
            logger.debug(f"No streams registered for execution {execution_id}")
            return

        sse_data = event.to_sse()
        dead_queues = set()
        queue_count = len(self.execution_streams[execution_id])
        logger.debug(f"Adding event to {queue_count} queue(s)")

        for queue in self.execution_streams[execution_id]:
            try:
                queue.put_nowait(sse_data)
                logger.debug(f"Event added to queue (qsize={queue.qsize()})")
            except asyncio.QueueFull:
                logger.warning(f"Stream queue full for execution {execution_id}")
                dead_queues.add(queue)
            except Exception as e:
                logger.error(f"Error sending to execution stream {execution_id}: {e}")
                dead_queues.add(queue)

        # Clean up dead queues
        for queue in dead_queues:
            self.remove_execution_stream(execution_id, queue)

    async def emit_workflow_event(self, event: StreamEvent) -> None:
        """Emit an event to all streams listening to this workflow"""
        if not event.workflow_id:
            return

        workflow_id = event.workflow_id
        if workflow_id not in self.workflow_streams:
            return

        sse_data = event.to_sse()
        dead_queues = set()

        for queue in self.workflow_streams[workflow_id]:
            try:
                queue.put_nowait(sse_data)
            except asyncio.QueueFull:
                logger.warning(f"Stream queue full for workflow {workflow_id}")
                dead_queues.add(queue)
            except Exception as e:
                logger.error(f"Error sending to workflow stream {workflow_id}: {e}")
                dead_queues.add(queue)

        # Clean up dead queues
        for queue in dead_queues:
            self.remove_workflow_stream(workflow_id, queue)

    def get_stats(self) -> Dict[str, Any]:
        """Get streaming statistics"""
        return {
            "active_execution_streams": len(self.execution_streams),
            "active_workflow_streams": len(self.workflow_streams),
            "total_execution_connections": sum(
                len(queues) for queues in self.execution_streams.values()
            ),
            "total_workflow_connections": sum(
                len(queues) for queues in self.workflow_streams.values()
            ),
        }


# Global stream manager instance
stream_manager = StreamManager()


async def create_sse_stream(
    queue: asyncio.Queue, heartbeat_interval: int = 30, max_events: int = 1000
) -> AsyncGenerator[str, None]:
    """
    Create a Server-Sent Events stream from a queue.

    Args:
        queue: Queue to read events from
        heartbeat_interval: Seconds between heartbeat events
        max_events: Maximum events before auto-closing stream
    """
    event_count = 0
    last_heartbeat = time.time()
    cancelled = False

    try:
        while event_count < max_events:
            try:
                # Check if we need to send a heartbeat
                now = time.time()
                if now - last_heartbeat >= heartbeat_interval:
                    heartbeat_event = StreamEvent(
                        type=StreamEventType.HEARTBEAT,
                        execution_id="system",
                        data={"timestamp": now},
                    )
                    yield heartbeat_event.to_sse()
                    last_heartbeat = now

                # Try to get an event from the queue (with short timeout)
                try:
                    event_data = await asyncio.wait_for(queue.get(), timeout=0.5)
                except asyncio.TimeoutError:
                    # No events available within timeout, loop again
                    continue
                except Exception:
                    # Re-raise non-timeout exceptions
                    raise
                else:
                    yield event_data
                    event_count += 1
                    queue.task_done()

                    # Check if this is a completion event and close the stream
                    try:
                        # Parse the SSE data to check for completion
                        # Format: "data: {...}\n\n"
                        if event_data.startswith("data: "):
                            json_str = event_data[6:].strip()
                            parsed = json.loads(json_str)
                            status = parsed.get("data", {}).get("status")
                            if status in ("completed", "failed", "error"):
                                logger.debug(
                                    f"Stream closing: received '{status}' status"
                                )
                                break
                    except (json.JSONDecodeError, KeyError, TypeError):
                        # If we can't parse, just continue
                        pass

            except asyncio.CancelledError:
                logger.debug("SSE stream cancelled")
                cancelled = True
                break
            except Exception as e:
                logger.error(f"Error in SSE stream: {e}")
                # Send error event and close
                error_event = StreamEvent(
                    type=StreamEventType.ERROR,
                    execution_id="system",
                    data={"error": str(e)},
                )
                yield error_event.to_sse()
                break

    except GeneratorExit:
        # Generator is being closed, don't try to yield
        logger.debug("SSE stream generator exit")
        cancelled = True
        raise
    finally:
        # Only send completion event if not cancelled/closed
        if not cancelled:
            try:
                complete_event = StreamEvent(
                    type=StreamEventType.COMPLETE,
                    execution_id="system",
                    data={"events_sent": event_count},
                )
                yield complete_event.to_sse()
            except GeneratorExit:
                # Ignore if generator is already closed
                pass


def get_sse_headers() -> Dict[str, str]:
    """Get standard SSE headers"""
    return {
        "Content-Type": "text/event-stream",
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "X-Accel-Buffering": "no",  # Disable nginx buffering
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET, OPTIONS",
        "Access-Control-Allow-Headers": "Cache-Control, Accept, Accept-Encoding, Accept-Language",
    }


def create_status_event(
    execution_id: str, status: str, workflow_id: Optional[str] = None, **extra_data
) -> StreamEvent:
    """Create a status change event"""
    return StreamEvent(
        type=StreamEventType.STATUS,
        execution_id=execution_id,
        workflow_id=workflow_id,
        data={"status": status, **extra_data},
    )


def create_step_event(
    execution_id: str,
    step_id: str,
    step_status: str,
    workflow_id: Optional[str] = None,
    **extra_data,
) -> StreamEvent:
    """Create a step execution event"""
    return StreamEvent(
        type=StreamEventType.STEP,
        execution_id=execution_id,
        workflow_id=workflow_id,
        data={"step_id": step_id, "step_status": step_status, **extra_data},
    )


def create_error_event(
    execution_id: str,
    error_message: str,
    workflow_id: Optional[str] = None,
    **extra_data,
) -> StreamEvent:
    """Create an error event"""
    return StreamEvent(
        type=StreamEventType.ERROR,
        execution_id=execution_id,
        workflow_id=workflow_id,
        data={"error": error_message, **extra_data},
    )

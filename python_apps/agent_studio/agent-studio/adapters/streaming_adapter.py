"""
Streaming adapter to convert SDK streaming events to Agent Studio format.

This adapter maintains backwards compatibility with the old AgentStreamChunk format
while using the new SDK streaming infrastructure.
"""

import json
import logging
from typing import AsyncGenerator, Dict, Any

logger = logging.getLogger(__name__)


class StreamingAdapter:
    """
    Converts SDK StreamEvent format to Agent Studio AgentStreamChunk format.

    SDK Format:
    {
        "type": "step",
        "execution_id": "...",
        "timestamp": "...",
        "data": {
            "step_id": "...",
            "step_status": "running",
            "delta": "Hello",
            ...
        }
    }

    Agent Studio Format:
    {
        "type": "content",  # or "info", "tool_response", "error"
        "message": "Hello"
    }
    """

    @staticmethod
    async def adapt_stream(
        sdk_stream: AsyncGenerator[str, None], execution_id: str = None, workflow_id: str = None
    ) -> AsyncGenerator[str, None]:
        """
        Convert SDK SSE stream to Agent Studio format.

        Args:
            sdk_stream: AsyncGenerator yielding SDK StreamEvent SSE strings
            execution_id: Execution ID for status chunks
            workflow_id: Workflow ID for status chunks

        Yields:
            SSE strings in Agent Studio AgentStreamChunk format
        """
        event_count = 0
        started_emitted = False

        async for sse_line in sdk_stream:
            event_count += 1

            # Parse SDK event
            if not sse_line.startswith("data: "):
                continue

            try:
                sdk_event = json.loads(sse_line[6:])  # Remove "data: " prefix
                event_type = sdk_event.get("type")

                # Emit 'started' status chunk on first real event (not heartbeat)
                if not started_emitted and event_type in ["status", "step"]:
                    from datetime import datetime

                    started_chunk = {
                        "status": "started",
                        "workflow_id": workflow_id or sdk_event.get("workflow_id", "unknown"),
                        "execution_id": execution_id or sdk_event.get("execution_id", "unknown"),
                        "timestamp": datetime.now().isoformat(),
                    }
                    yield f"data: {json.dumps(started_chunk)}\n\n"
                    started_emitted = True

                # Convert to Agent Studio format
                agent_chunks = StreamingAdapter._convert_event(sdk_event)

                # Yield converted chunks
                for chunk in agent_chunks:
                    yield f"data: {json.dumps(chunk)}\n\n"

                # Emit 'completed' status chunk on complete event and end stream
                if event_type == "complete":
                    from datetime import datetime

                    completed_chunk = {
                        "status": "completed",
                        "workflow_id": workflow_id or sdk_event.get("workflow_id", "unknown"),
                        "execution_id": execution_id or sdk_event.get("execution_id", "unknown"),
                        "timestamp": datetime.now().isoformat(),
                    }
                    yield f"data: {json.dumps(completed_chunk)}\n\n"
                    return

                # Also check for status="completed" events from workflow execution
                if event_type == "status" and sdk_event.get("data", {}).get("status") == "completed":
                    from datetime import datetime

                    completed_chunk = {
                        "status": "completed",
                        "workflow_id": workflow_id or sdk_event.get("workflow_id", "unknown"),
                        "execution_id": execution_id or sdk_event.get("execution_id", "unknown"),
                        "timestamp": datetime.now().isoformat(),
                    }
                    yield f"data: {json.dumps(completed_chunk)}\n\n"
                    return

            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse SDK event: {e}, line: {sse_line[:100]}")
                continue
            except Exception as e:
                logger.error(f"Error converting SDK event: {e}, line: {sse_line[:100]}", exc_info=True)
                continue

        logger.info(f"StreamingAdapter: Stream ended after {event_count} events")

    @staticmethod
    def _convert_event(sdk_event: Dict[str, Any]) -> list[Dict[str, Any]]:
        """
        Convert a single SDK event to one or more Agent Studio chunks.

        Returns:
            List of Agent Studio chunks (may be empty, one, or multiple)
        """
        event_type = sdk_event.get("type")
        data = sdk_event.get("data", {})

        # Handle different SDK event types
        if event_type == "heartbeat":
            # Skip heartbeats in Agent Studio format
            return []

        elif event_type == "status":
            # Convert status events to info chunks
            status = data.get("status")
            if status == "started":
                return [{"type": "info", "message": "Workflow execution started\n"}]
            elif status == "completed":
                return [{"type": "info", "message": "Workflow execution completed\n"}]
            elif status == "failed":
                error_msg = data.get("error_message", "Unknown error")
                return [{"type": "error", "message": f"Workflow failed: {error_msg}\n"}]
            return []

        elif event_type == "step":
            # Convert step events based on step status and data
            step_status = data.get("step_status")
            step_id = data.get("step_id", "")
            output_data = data.get("output_data", {})

            if step_status == "running":
                # Check for special event types in output_data
                event_subtype = output_data.get("event_type")

                if event_subtype == "agent_call":
                    # Agent-to-agent call event - convert to info type for frontend
                    agent_name = output_data.get("agent_name", "Unknown Agent")
                    query = output_data.get("query", "")
                    return [{"type": "info", "message": f"Agent Called: {agent_name}: {query}\n"}]

                elif event_subtype == "tool_call":
                    # Regular tool call event - show tool being executed
                    tool_name = output_data.get("tool_name", "Unknown Tool")
                    return [{"type": "info", "message": f"Tool Called: {tool_name}\n"}]

                elif event_subtype == "tool_response":
                    # Tool response event (both agent and regular tools)
                    # Check if this is an agent tool or regular tool
                    if "agent_name" in output_data:
                        # Agent tool response
                        agent_name = output_data.get("agent_name", "Unknown Agent")
                        response = output_data.get("response", "")
                        duration_ms = output_data.get("duration_ms", 0)
                        return [{"type": "tool_response", "message": f"{agent_name} responded ({duration_ms}ms): {response}\n"}]
                    else:
                        # Regular tool response
                        tool_name = output_data.get("tool_name", "Unknown Tool")
                        duration_ms = output_data.get("duration_ms", 0)
                        return [{"type": "info", "message": f"Tool Completed: {tool_name} ({duration_ms}ms)\n"}]

                # Check if this is a tool execution start event
                if "tool_name" in output_data and "message" in output_data:
                    tool_name = output_data.get("tool_name")
                    params = output_data.get("params", {})
                    return [
                        {"type": "info", "message": f"Executing tool: {tool_name} with params {params}\n", "source": step_id}
                    ]

                # Check if this is a streaming delta (agent content)
                # Delta can be in data.delta or data.output_data.delta
                delta = data.get("delta") or output_data.get("delta")
                if delta:  # Only emit non-empty deltas
                    # Check if this content should be visible to the user
                    visible_to_user = output_data.get("visible_to_user", True)  # Default to visible
                    chunk_type = "content" if visible_to_user else "hidden"
                    return [{"type": chunk_type, "message": delta, "source": step_id}]

                # Check if this is a tool call (legacy format)
                if "tool_name" in data:
                    tool_name = data.get("tool_name")
                    return [{"type": "info", "message": f"Agent Called: {tool_name}\n"}]

                return []

            elif step_status == "completed":
                # Check if this is a tool execution result
                output_data = data.get("output_data", {})

                # Tool execution step
                if "tool" in output_data:
                    tool_result = output_data.get("result", "")
                    # Standalone tool step: emit as primary content instead of tool_response
                    try:
                        if isinstance(tool_result, str):
                            json.loads(tool_result)  # Validate JSON
                            return [
                                {"type": "content", "message": "\n\n", "source": step_id},
                                {"type": "content", "message": tool_result + "\n", "source": step_id},
                            ]
                        else:
                            return [
                                {"type": "content", "message": "\n\n", "source": step_id},
                                {"type": "content", "message": json.dumps(tool_result) + "\n", "source": step_id},
                            ]
                    except (json.JSONDecodeError, TypeError):
                        return [
                            {"type": "content", "message": "\n\n", "source": step_id},
                            {"type": "content", "message": str(tool_result) + "\n", "source": step_id},
                        ]

                # Agent execution step
                if "response" in output_data:
                    # Agent completed - send completion marker
                    return [
                        {"type": "info", "message": "Agent Responded\n", "source": step_id},
                        {"type": "info", "message": "[STREAM_COMPLETE]\n\n", "source": step_id},
                    ]

                return []

            elif step_status == "failed":
                error_msg = output_data.get("error", "Step failed")
                return [{"type": "error", "message": f"Step {step_id} failed: {error_msg}\n"}]

            return []

        elif event_type == "error":
            # Convert error events
            error_msg = data.get("error_message", "Unknown error")
            return [{"type": "error", "message": f"Error: {error_msg}\n"}]

        elif event_type == "complete":
            # Workflow completion
            return [{"type": "info", "message": "Workflow execution complete\n"}]

        # Unknown event type - skip
        return []

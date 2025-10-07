# Streaming Tool Response Fix

## Problem

After changing tool results from `type="content"` to `type="info"` in commit `79252ad`, tool responses (which can be full JSON strings from agent-to-agent calls) started appearing in the chat UI's loading/status area.

### Root Cause

1. In `agent_base.py` (lines 707-715), tool results were yielded as `AgentStreamChunk(type="info", message=result + "\n")`
2. The frontend (`AgentTestingPanel.tsx`) was setting ALL `type="info"` messages as the `agentStatus`
3. The `agentStatus` is displayed in the loading message area
4. This caused long JSON tool responses to appear in the UI where they shouldn't

## Solution

Created a new message type `tool_response` specifically for tool execution results.

### Changes Made

#### 1. Backend: `python_apps/agent_studio/agent-studio/agents/agent_base.py`

**Updated `AgentStreamChunk` type definition:**

```python
class AgentStreamChunk(BaseModel):
    type: Literal["content"] | Literal["info"] | Literal["error"] | Literal["agent_response"] | Literal["tool_response"]
    message: str
```

**Changed tool result streaming (lines 707-715):**

```python
# Yield tool result as tool_response type so frontend can handle it separately
try:
    if isinstance(result, str):
        json.loads(result)  # Validate JSON format
        yield AgentStreamChunk(type="tool_response", message=result + "\n")
    else:
        yield AgentStreamChunk(type="tool_response", message=str(result) + "\n")
except json.JSONDecodeError:
    yield AgentStreamChunk(type="tool_response", message=str(result) + "\n")
```

#### 2. Frontend: `apps/command_agent_version1/app/components/AgentTestingPanel.tsx`

**Added handler for new `tool_response` type:**

```typescript
} else if (evt.type === "tool_response") {
  // Tool responses are now sent as a separate type
  // Frontend can choose to display these differently in the future
  // For now, we ignore them (don't show in status or chat)
}
```

## Message Type Semantics

After this fix, the streaming message types have clear semantics:

- **`content`**: Final agent response content that should be displayed in the chat
- **`info`**: Status/informational messages (e.g., "Agent Called: FunctionName", "Agent Responded", "[STREAM_COMPLETE]")
- **`tool_response`**: Tool execution results (JSON responses from agent-to-agent calls or tool outputs)
  - These are raw outputs from tools/agents that were called during execution
  - Not displayed in chat by default, but available for debugging/logging
- **`error`**: Error messages that should be displayed to the user
- **`agent_response`**: Structured agent status responses (reserved for future use)
  - Intended for structured metadata about agent execution (e.g., `{"message": "Processing...", "success": true}`)
  - Frontend can extract fields and display as status updates
  - Currently defined but not actively used in backend

## Benefits

1. **Clear Separation**: Tool responses are now clearly distinguished from status messages
2. **Future Flexibility**: Frontend developers can choose to display tool responses differently (e.g., in a debug panel, collapsible section, etc.)
3. **Default Filtering**: Tool responses are filtered out by default since there's no handler, preventing UI clutter
4. **Better Debugging**: Developers can easily identify and track tool responses in the stream

## Testing

Existing tests in `test_workflow_agent_streaming.py` continue to work correctly as they only track "Agent Called:" messages from "info" type chunks.

## Migration Notes

If other frontends are consuming the streaming API, they should add a handler for the new `tool_response` type. The default behavior (ignoring unknown types) will prevent any breaking changes.

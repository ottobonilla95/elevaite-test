# Workflow Execution Guide

Create, execute, and monitor workflows with real-time streaming.

## Overview

Workflows are directed graphs of steps that process data, invoke agents, and integrate with external systems. Each workflow consists of:

- **Trigger:** Entry point (chat, API, schedule)
- **Steps:** Processing nodes (agent, condition, loop, etc.)
- **Connections:** Edges between steps

---

## Workflow Lifecycle

```
Create → Validate → Execute → Stream → Complete
```

1. **Create:** Define workflow structure via API
2. **Validate:** System validates step connections and parameters
3. **Execute:** Trigger workflow with input data
4. **Stream:** Receive real-time updates via SSE
5. **Complete:** Get final results

---

## Creating a Workflow

### API Endpoint

```http
POST /api/workflows
Content-Type: application/json
X-elevAIte-UserId: user-123
X-elevAIte-OrganizationId: org-xyz
X-elevAIte-ProjectId: proj-abc
```

### Request Body

```json
{
  "name": "Customer Support Agent",
  "description": "Handle customer inquiries",
  "steps": [
    {
      "step_id": "trigger",
      "step_type": "trigger",
      "parameters": {
        "kind": "chat"
      },
      "next_steps": ["agent"]
    },
    {
      "step_id": "agent",
      "step_type": "agent_execution",
      "parameters": {
        "agent_id": "agent-uuid-here"
      },
      "next_steps": []
    }
  ]
}
```

### Response

```json
{
  "id": "workflow-uuid",
  "name": "Customer Support Agent",
  "status": "active",
  "created_at": "2024-01-15T10:00:00Z"
}
```

---

## Step Types

| Step Type | Description |
|-----------|-------------|
| `trigger` | Entry point (chat, api, schedule, webhook) |
| `agent_execution` | Execute an AI agent |
| `condition` | Branch based on conditions |
| `loop` | Iterate over data |
| `parallel` | Execute steps concurrently |
| `human_approval` | Wait for human approval |
| `tool_call` | Direct tool invocation |
| `data_transform` | Transform data between steps |
| `api_call` | Call external API |
| `delay` | Wait for specified duration |

### Trigger Step

```json
{
  "step_id": "trigger",
  "step_type": "trigger",
  "parameters": {
    "kind": "chat"
  }
}
```

**Trigger kinds:**
- `chat` - Chat message input
- `api` - API call trigger
- `schedule` - Cron-based schedule
- `webhook` - External webhook

### Agent Execution Step

```json
{
  "step_id": "agent",
  "step_type": "agent_execution",
  "parameters": {
    "agent_id": "agent-uuid",
    "max_iterations": 10,
    "timeout_seconds": 300
  }
}
```

### Condition Step

```json
{
  "step_id": "check_priority",
  "step_type": "condition",
  "parameters": {
    "condition": "{{input.priority}} == 'high'"
  },
  "next_steps": ["escalate"],
  "else_steps": ["standard_response"]
}
```

### Human Approval Step

```json
{
  "step_id": "approval",
  "step_type": "human_approval",
  "parameters": {
    "approvers": ["manager@example.com"],
    "timeout_hours": 24,
    "message": "Please approve this action"
  }
}
```

---

## Executing a Workflow

### API Endpoint

```http
POST /api/workflows/{workflow_id}/execute
Content-Type: application/json
```

### Request Body

```json
{
  "trigger": {
    "kind": "chat",
    "current_message": "I need help with my order",
    "history": [
      {"role": "user", "content": "Hello"},
      {"role": "assistant", "content": "Hi! How can I help?"}
    ]
  },
  "user_id": "user-123",
  "session_id": "session-456",
  "context": {
    "customer_id": "cust-789"
  }
}
```

### Response

```json
{
  "execution_id": "exec-uuid",
  "workflow_id": "workflow-uuid",
  "status": "running",
  "started_at": "2024-01-15T10:05:00Z"
}
```

---

## Real-time Streaming

### SSE Endpoint

```http
GET /api/executions/{execution_id}/stream
Accept: text/event-stream
Authorization: Bearer <token>
```

### Event Types

| Event | Description |
|-------|-------------|
| `connected` | Connection established |
| `status` | Execution status change |
| `step_start` | Step execution started |
| `step_complete` | Step execution completed |
| `delta` | Streaming content chunk |
| `tool_call` | Tool invocation |
| `tool_result` | Tool result received |
| `error` | Error occurred |
| `complete` | Execution finished |
| `heartbeat` | Keep-alive (every 30s) |

### Event Format

```
event: status
data: {"execution_id": "exec-uuid", "status": "running", "step": "agent"}

event: delta
data: {"content": "I can help you with your order. ", "step": "agent"}

event: tool_call
data: {"tool": "get_order", "arguments": {"order_id": "12345"}}

event: tool_result
data: {"tool": "get_order", "result": {"status": "shipped"}}

event: complete
data: {"execution_id": "exec-uuid", "status": "completed", "result": {...}}
```

### JavaScript Client Example

```javascript
const eventSource = new EventSource(
  `/api/executions/${executionId}/stream`,
  { headers: { Authorization: `Bearer ${token}` } }
);

eventSource.addEventListener('delta', (event) => {
  const data = JSON.parse(event.data);
  console.log('Content:', data.content);
});

eventSource.addEventListener('complete', (event) => {
  const data = JSON.parse(event.data);
  console.log('Completed:', data.result);
  eventSource.close();
});

eventSource.addEventListener('error', (event) => {
  console.error('Stream error:', event);
  eventSource.close();
});
```

---

## Monitoring Executions

### Get Execution Status

```http
GET /api/executions/{execution_id}
```

**Response:**
```json
{
  "id": "exec-uuid",
  "workflow_id": "workflow-uuid",
  "status": "completed",
  "started_at": "2024-01-15T10:05:00Z",
  "completed_at": "2024-01-15T10:05:30Z",
  "steps": [
    {
      "step_id": "trigger",
      "status": "completed",
      "started_at": "...",
      "completed_at": "..."
    },
    {
      "step_id": "agent",
      "status": "completed",
      "started_at": "...",
      "completed_at": "...",
      "result": {...}
    }
  ],
  "result": {
    "response": "Your order #12345 has been shipped..."
  }
}
```

### Execution Statuses

| Status | Description |
|--------|-------------|
| `pending` | Queued for execution |
| `running` | Currently executing |
| `waiting` | Waiting for approval/input |
| `completed` | Successfully finished |
| `failed` | Execution failed |
| `cancelled` | Manually cancelled |
| `timeout` | Exceeded time limit |

### List Executions

```http
GET /api/executions?workflow_id={workflow_id}&status=running&limit=10
```

---

## Human-in-the-Loop Approvals

When a workflow reaches a `human_approval` step:

### Get Pending Approvals

```http
GET /api/approvals?status=pending
```

### Approve/Reject

```http
POST /api/approvals/{approval_id}
Content-Type: application/json

{
  "decision": "approved",
  "comment": "Looks good, proceed"
}
```

**Decision values:** `approved`, `rejected`

---

## Error Handling

### Retry Configuration

```json
{
  "step_id": "api_call",
  "step_type": "api_call",
  "parameters": {
    "url": "https://api.example.com/action"
  },
  "retry": {
    "max_attempts": 3,
    "backoff_seconds": 5
  }
}
```

### Error Events

```
event: error
data: {"step": "agent", "error": "Tool execution failed", "code": "TOOL_ERROR"}
```

### Common Error Codes

| Code | Description |
|------|-------------|
| `VALIDATION_ERROR` | Invalid workflow or input |
| `AGENT_ERROR` | Agent execution failed |
| `TOOL_ERROR` | Tool invocation failed |
| `TIMEOUT` | Step or workflow timeout |
| `APPROVAL_REJECTED` | Human rejected approval |
| `RATE_LIMIT` | Rate limit exceeded |

---

## Best Practices

1. **Use streaming** for real-time user feedback
2. **Set timeouts** on agent and API steps
3. **Add retry logic** for external API calls
4. **Use conditions** to handle edge cases
5. **Log context** for debugging
6. **Test workflows** with mock data first


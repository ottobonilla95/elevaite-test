# Agent Configuration Guide

Create and configure AI agents with tools, prompts, and execution settings.

## Overview

Agents are AI-powered entities that:
- Process user inputs using LLMs
- Execute tools to perform actions
- Follow system prompts for behavior
- Maintain conversation context

---

## Creating an Agent

### API Endpoint

```http
POST /api/agents
Content-Type: application/json
X-elevAIte-UserId: user-123
X-elevAIte-OrganizationId: org-xyz
X-elevAIte-ProjectId: proj-abc
```

### Request Body

```json
{
  "name": "Customer Support Agent",
  "description": "Handles customer inquiries and support tickets",
  "model": "gpt-4o",
  "system_prompt": "You are a helpful customer support agent...",
  "tools": ["web_search", "ServiceNow_ITSM", "get_order"],
  "settings": {
    "temperature": 0.7,
    "max_tokens": 2048,
    "max_iterations": 10
  }
}
```

### Response

```json
{
  "id": "agent-uuid",
  "name": "Customer Support Agent",
  "model": "gpt-4o",
  "is_active": true,
  "created_at": "2024-01-15T10:00:00Z"
}
```

---

## Agent Configuration Options

### Core Settings

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Agent display name |
| `description` | string | Agent description |
| `model` | string | LLM model identifier |
| `system_prompt` | string | System prompt text |
| `prompt_id` | string | Reference to stored prompt |
| `tools` | array | List of tool names |
| `is_active` | boolean | Enable/disable agent |

### Model Settings

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `temperature` | float | 0.7 | Response randomness (0-2) |
| `max_tokens` | integer | 2048 | Max response tokens |
| `top_p` | float | 1.0 | Nucleus sampling |
| `frequency_penalty` | float | 0 | Reduce repetition |
| `presence_penalty` | float | 0 | Encourage new topics |

### Execution Settings

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `max_iterations` | integer | 10 | Max tool call loops |
| `timeout_seconds` | integer | 300 | Execution timeout |
| `parallel_tool_calls` | boolean | true | Allow parallel tools |
| `require_approval` | boolean | false | Human approval for tools |

---

## Tool Binding

### Bind Tools to Agent

```http
PUT /api/agents/{agent_id}/tools
Content-Type: application/json

{
  "tools": ["web_search", "postgres_query", "ServiceNow_ITSM"]
}
```

### Tool Configuration per Agent

```json
{
  "tools": [
    {
      "name": "postgres_query",
      "config": {
        "database": "customer_db",
        "read_only": true
      }
    },
    {
      "name": "ServiceNow_ITSM",
      "config": {
        "instance": "company.service-now.com",
        "default_category": "inquiry"
      }
    }
  ]
}
```

### Get Agent Tools

```http
GET /api/agents/{agent_id}/tools
```

**Response:**
```json
{
  "tools": [
    {
      "name": "web_search",
      "description": "Search the web...",
      "parameters_schema": {...}
    }
  ]
}
```

---

## Prompt Management

### Create a Prompt Template

```http
POST /api/prompts
Content-Type: application/json

{
  "name": "customer_support_v1",
  "content": "You are a customer support agent for {{company_name}}.\n\nGuidelines:\n- Be helpful and professional\n- Use available tools to look up information\n- Escalate complex issues to human agents",
  "variables": ["company_name"],
  "tags": ["support", "production"]
}
```

### Use Prompt in Agent

```json
{
  "name": "Support Agent",
  "prompt_id": "prompt-uuid",
  "prompt_variables": {
    "company_name": "Acme Corp"
  }
}
```

### Prompt Versioning

```http
GET /api/prompts/{prompt_id}/versions
```

```http
POST /api/prompts/{prompt_id}/versions
Content-Type: application/json

{
  "content": "Updated prompt content...",
  "change_notes": "Added escalation guidelines"
}
```

---

## Agent Execution

### Direct Execution

```http
POST /api/agents/{agent_id}/execute
Content-Type: application/json

{
  "message": "I need help with my order #12345",
  "history": [],
  "context": {
    "customer_id": "cust-789"
  }
}
```

### Streaming Execution

```http
POST /api/agents/{agent_id}/stream
Content-Type: application/json
Accept: text/event-stream

{
  "message": "What's the status of my order?",
  "history": [...]
}
```

---

## Context and Memory

### Session Context

Agents maintain context within a session:

```json
{
  "message": "What about order #67890?",
  "session_id": "session-456",
  "history": [
    {"role": "user", "content": "Check order #12345"},
    {"role": "assistant", "content": "Order #12345 is shipped..."}
  ]
}
```

### Injecting Context

Provide additional context for the agent:

```json
{
  "message": "Help me with my account",
  "context": {
    "customer_id": "cust-789",
    "customer_name": "John Doe",
    "account_tier": "premium",
    "recent_orders": ["12345", "67890"]
  }
}
```

Context is available to the agent's system prompt via `{{context.customer_name}}`.

---

## Supported Models

| Model | Provider | Description |
|-------|----------|-------------|
| `gpt-4o` | OpenAI | GPT-4o (recommended) |
| `gpt-4o-mini` | OpenAI | Faster, cheaper GPT-4o |
| `gpt-4-turbo` | OpenAI | GPT-4 Turbo |
| `gpt-3.5-turbo` | OpenAI | GPT-3.5 Turbo |
| `claude-3-opus` | Anthropic | Claude 3 Opus |
| `claude-3-sonnet` | Anthropic | Claude 3 Sonnet |
| `claude-3-haiku` | Anthropic | Claude 3 Haiku |
| `gemini-pro` | Google | Gemini Pro |

---

## Testing Agents

### Test Endpoint

```http
POST /api/agents/{agent_id}/test
Content-Type: application/json

{
  "message": "Test message",
  "mock_tools": true
}
```

**Response:**
```json
{
  "response": "Agent response...",
  "tool_calls": [
    {"tool": "web_search", "arguments": {...}, "mocked": true}
  ],
  "tokens_used": 150,
  "latency_ms": 1200
}
```

### Dry Run

Execute without side effects:

```http
POST /api/agents/{agent_id}/execute?dry_run=true
```

---

## Agent Management

### List Agents

```http
GET /api/agents?project_id={project_id}&is_active=true
```

### Update Agent

```http
PUT /api/agents/{agent_id}
Content-Type: application/json

{
  "name": "Updated Agent Name",
  "settings": {
    "temperature": 0.5
  }
}
```

### Delete Agent

```http
DELETE /api/agents/{agent_id}
```

### Clone Agent

```http
POST /api/agents/{agent_id}/clone
Content-Type: application/json

{
  "name": "Agent Copy",
  "project_id": "new-project-id"
}
```

---

## Best Practices

1. **Write clear system prompts** - Be specific about agent behavior
2. **Limit tool access** - Only bind necessary tools
3. **Set appropriate timeouts** - Prevent runaway executions
4. **Use prompt templates** - Version and reuse prompts
5. **Test with mock tools** - Validate logic before production
6. **Monitor token usage** - Track costs and optimize
7. **Use temperature wisely** - Lower for factual, higher for creative
8. **Provide context** - Help agents understand user situation


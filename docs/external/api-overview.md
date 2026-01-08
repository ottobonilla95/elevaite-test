# API Overview

The elevAIte platform exposes multiple API services for authentication, workflow execution, agent management, and data processing.

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                           API Gateway                                │
├──────────────┬──────────────┬──────────────┬───────────────────────┤
│   Auth API   │ Workflow API │ Agent Studio │      ETL API          │
│  (auth_api)  │  (workflow-  │   (agent-    │      (etl)            │
│              │  engine-poc) │   studio)    │                       │
└──────────────┴──────────────┴──────────────┴───────────────────────┘
```

---

## API Services

### 1. Auth API

**Base Path:** `/api/auth`, `/api/user`, `/api/rbac`, `/api/authz`

Authentication, authorization, user management, and RBAC services.

| Endpoint Group | Description |
|----------------|-------------|
| `/api/auth` | Login, logout, token refresh, password management |
| `/api/auth/register` | User registration |
| `/api/auth/me` | Current user info |
| `/api/user` | User profile management |
| `/api/rbac` | Role-based access control management |
| `/api/authz` | Authorization decisions (check-access) |
| `/api/sms-mfa` | SMS-based MFA |
| `/api/email-mfa` | Email-based MFA |
| `/api/admin` | Admin user operations |

### 2. Workflow Engine API

**Base Path:** `/api`

Workflow creation, execution, and management.

| Endpoint Group | Description |
|----------------|-------------|
| `/api/workflows` | CRUD for workflow definitions |
| `/api/workflows/{id}/execute` | Execute a workflow |
| `/api/workflows/{id}/stream` | SSE streaming for execution updates |
| `/api/executions` | Execution status and results |
| `/api/executions/{id}/stream` | Real-time execution streaming |
| `/api/agents` | Agent CRUD and tool bindings |
| `/api/tools` | Tool registry and management |
| `/api/steps` | Step type definitions |
| `/api/prompts` | Prompt templates |
| `/api/files` | File uploads and management |
| `/api/messages` | Chat messages for agent sessions |
| `/api/approvals` | Human-in-the-loop approvals |
| `/api/monitoring` | Workflow monitoring |

### 3. Agent Studio API

**Base Path:** `/api`

Agent configuration, tools, and execution.

| Endpoint Group | Description |
|----------------|-------------|
| `/api/prompts` | Prompt management |
| `/api/agents` | Agent definitions |
| `/api/analytics` | Usage analytics |
| `/api/tools` | Tool schemas and execution |
| `/api/files` | File operations |
| `/api/pipelines` | Data pipelines |
| `/api/steps` | Workflow step schemas |

### 4. ETL API

**Base Path:** `/api`

Data ingestion and pipeline management.

| Endpoint Group | Description |
|----------------|-------------|
| `/_pipeline/providers` | List pipeline providers |
| `/_pipeline/create` | Create data pipelines |
| `/_pipeline/monitor` | Monitor pipeline status |
| `/_pipeline/rerun` | Re-run failed pipelines |

---

## Authentication

All APIs use Bearer token authentication via JWT.

### Headers

| Header | Description | Required |
|--------|-------------|----------|
| `Authorization` | `Bearer <access_token>` | Yes |
| `X-elevAIte-UserId` | User ID for RBAC | For RBAC-protected endpoints |
| `X-elevAIte-OrganizationId` | Organization context | For RBAC-protected endpoints |
| `X-elevAIte-AccountId` | Account context | For account/project resources |
| `X-elevAIte-ProjectId` | Project context | For project resources |
| `X-elevAIte-apikey` | API key (service-to-service) | Alternative to Bearer token |

### Login Flow

```http
POST /api/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "password123"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer"
}
```

---

## Common Response Patterns

### Success Responses

| Status | Meaning |
|--------|---------|
| `200 OK` | Request succeeded |
| `201 Created` | Resource created |
| `204 No Content` | Delete succeeded |

### Error Responses

| Status | Meaning |
|--------|---------|
| `400 Bad Request` | Invalid request body or parameters |
| `401 Unauthorized` | Missing or invalid authentication |
| `403 Forbidden` | RBAC denied access |
| `404 Not Found` | Resource not found |
| `409 Conflict` | Resource already exists |
| `429 Too Many Requests` | Rate limit exceeded |
| `500 Internal Server Error` | Server error |

---

## Core Endpoint Examples

### Create and Execute a Workflow

```http
POST /api/workflows
Content-Type: application/json
X-elevAIte-UserId: user-123
X-elevAIte-OrganizationId: org-xyz
X-elevAIte-ProjectId: proj-abc

{
  "name": "Chat Workflow",
  "description": "Simple chat agent workflow",
  "steps": [
    {
      "step_id": "trigger",
      "step_type": "trigger",
      "parameters": { "kind": "chat" }
    },
    {
      "step_id": "agent",
      "step_type": "agent_execution",
      "parameters": { "agent_id": "agent-uuid" }
    }
  ]
}
```

### Execute Workflow

```http
POST /api/workflows/{workflow_id}/execute
Content-Type: application/json

{
  "trigger": {
    "kind": "chat",
    "current_message": "Hello, how can you help?",
    "history": []
  },
  "user_id": "user-123",
  "session_id": "session-456"
}
```

### Stream Execution Updates (SSE)

```http
GET /api/executions/{execution_id}/stream
Accept: text/event-stream
```

**Event format:**
```
event: status
data: {"execution_id": "...", "status": "running", "step": "agent"}

event: delta
data: {"content": "Hello! I can help you with..."}

event: complete
data: {"execution_id": "...", "status": "completed"}
```

---

## Real-time Streaming

The API supports Server-Sent Events (SSE) for real-time updates:

| Endpoint | Description |
|----------|-------------|
| `/api/workflows/{id}/stream` | Stream all executions for a workflow |
| `/api/executions/{id}/stream` | Stream updates for a specific execution |

### Event Types

| Event | Description |
|-------|-------------|
| `connected` | SSE connection established |
| `status` | Execution status change |
| `step_start` | Step execution started |
| `step_complete` | Step execution completed |
| `delta` | Streaming content chunk (LLM responses) |
| `error` | Error occurred |
| `complete` | Execution finished |
| `heartbeat` | Keep-alive ping |

---

## Rate Limiting

The Auth API implements rate limiting on sensitive endpoints:

| Endpoint | Limit |
|----------|-------|
| `/api/auth/login` | 5/minute per IP |
| `/api/auth/register` | 10/minute per IP |
| `/api/auth/forgot-password` | 3/minute per IP |
| General endpoints | 60/minute per IP |

Rate limit headers:
- `X-RateLimit-Limit`: Maximum requests allowed
- `X-RateLimit-Remaining`: Requests remaining
- `X-RateLimit-Reset`: Unix timestamp for limit reset

---

## MFA Support

The Auth API supports multiple MFA methods:

| Method | Description |
|--------|-------------|
| TOTP | Time-based OTP via authenticator app |
| SMS | Code sent via SMS to verified phone |
| Email | Code sent via email |

When MFA is required, login returns `400` with headers indicating the method:
- `X-MFA-Type`: `TOTP`, `SMS`, `EMAIL`, or `MULTIPLE`
- `X-MFA-Methods`: Comma-separated list if multiple methods available

---

## API Key Authentication

For service-to-service communication:

```http
POST /api/workflows/{id}/execute
X-elevAIte-apikey: eyJhbGciOiJIUzI1NiIs...
```

API keys are JWTs with:
- `type`: `"api_key"`
- `sub`: Service account user ID
- `tenant_id`: (optional) Tenant scope

Validate API keys:
```http
POST /api/auth/validate-apikey
X-elevAIte-apikey: <api_key>
```

---

## CORS

All APIs support CORS with configurable origins. Development mode allows `*`.


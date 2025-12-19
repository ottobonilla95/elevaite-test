# A2A (Agent-to-Agent) Integration

This document tracks the progress of integrating Google's A2A protocol for external agent communication.

## Completed

### 1. Database Model (`workflow_core_sdk/db/models/a2a_agents.py`)

- [x] `A2AAgent` SQLModel with all connection and health fields
- [x] `A2AAgentStatus` enum: `ACTIVE`, `INACTIVE`, `ERROR`, `UNREACHABLE`
- [x] `A2AAuthType` enum: `NONE`, `BEARER`, `API_KEY`, `OAUTH2`
- [x] Pydantic schemas: `A2AAgentBase`, `A2AAgentCreate`, `A2AAgentRead`, `A2AAgentUpdate`
- [x] `A2AAgentSkill` model for agent capabilities

### 2. A2A Client Service (`llm_gateway/a2a/`)

- [x] `A2AClientService` using official `a2a-sdk>=0.3.22`
- [x] Support for streaming and non-streaming message sending
- [x] Agent Card fetching from `/.well-known/agent.json`
- [x] Health check support
- [x] Authentication: none, bearer, api_key, oauth2
- [x] Type definitions: `A2AAgentInfo`, `A2AAuthConfig`, `A2AMessageRequest`, `A2AMessageResponse`

### 3. A2A Agents CRUD Service (`workflow_core_sdk/services/a2a_agents_service.py`)

- [x] `A2AAgentsService` with full CRUD operations
- [x] Agent Card refresh from remote
- [x] Health status tracking with consecutive failure counting
- [x] Query filtering by organization, status, tags, search

### 4. A2A Agents REST API (`workflow_engine_poc/routers/a2a_agents.py`)

- [x] CRUD endpoints: GET, POST, PUT, DELETE
- [x] `POST /{agent_id}/refresh-card` - Refresh Agent Card from remote
- [x] `GET /{agent_id}/health` - Health check endpoint

### 5. Agent Execution Integration (`workflow_core_sdk/steps/ai_steps.py`)

- [x] A2A agents work in existing `agent_execution_step`
- [x] Dispatch via `a2a_agent_id` in step config
- [x] Uses `A2AClientService` for remote communication
- [x] Consistent response format with built-in agents

### 6. Streaming Support

- [x] SSE streaming in `_execute_a2a_agent()` via `stream_manager`
- [x] Delta events emitted during A2A streaming responses
- [x] Enabled via `config.stream: true` in step config

### 7. Tests

- [x] 16 tests for A2A client (`llm_gateway/tests/test_a2a_client.py`)
- [x] 22 tests for A2A agents service (`workflow_core_sdk/tests/services/test_a2a_agents_service.py`)
- [x] 6 tests for A2A agent execution (`workflow_core_sdk/tests/steps/test_a2a_agent_execution.py`)

## TODO

### Database

- [x] Alembic migration for `a2a_agents` table (`alembic/versions/a2a_agents_001_add_a2a_agents_table.py`)
- [ ] Review other models for enum opportunities (scan for string literals like status fields)

### Streaming

- [x] ~~Add SSE streaming support in `_execute_a2a_agent()` when needed~~ (completed)

### Frontend

- [ ] UI for registering/managing A2A agents
- [ ] Agent picker showing both built-in and A2A agents
- [ ] Display A2A agent status/health in UI

### Health Checks

- [ ] Background task/scheduler for periodic health checks
- [ ] Configurable health check intervals per agent

### Security

- [ ] Secure storage for auth credentials (consider encryption)
- [ ] OAuth2 token refresh flow

### Documentation

- [ ] API documentation for A2A endpoints
- [ ] User guide for registering external agents

# Agent Studio Test Plan

**Goal**: Create comprehensive integration tests for all Agent Studio API endpoints

## API Endpoints to Test

Based on `main.py`, Agent Studio exposes these routers:

1. **Prompts API** (`/api/prompts`) - prompt_router
2. **Agents API** (`/api/agents`) - agent_router  
3. **Analytics API** (`/api/analytics`) - analytics_router
4. **Tools API** (`/api/tools`) - tools_router
5. **Files API** (`/api/files`) - file_router
6. **Workflows API** (`/api/workflows`) - workflow_router
7. **Executions API** (`/api/executions`) - execution_router
8. **Pipelines API** (`/api/pipelines`) - pipeline_router
9. **Steps API** (`/api/steps`) - step_router

## Current Test Status

### Existing Tests
- ✅ E2E: `test_workflow_agent_streaming.py` (1 test - PASSING)
- ⚠️ Integration: `test_prompts_api.py` (14 tests - BLOCKED by session compatibility)
- ⚠️ Integration: `test_executions_api.py` (20 tests - BLOCKED by session compatibility)
- ✅ Workflows: `test_workflow_api.py` (existing workflow tests)
- ✅ Functional: `test_tool_endpoints.py` (existing tool tests)
- ✅ Functional: `test_analytics_endpoints.py` (existing analytics tests)

### Blocking Issue
**SDK/Database Session Compatibility**: The SDK services use `session.exec()` (SQLModel) but Agent Studio provides regular SQLAlchemy sessions.

**Solutions**:
1. Migrate Agent Studio to use SQLModel sessions (recommended)
2. Update SDK services to use `session.execute().scalars()` instead of `session.exec()`
3. Create adapter layer to convert between session types

## Test Coverage Plan

### 1. Prompts API (`/api/prompts`)
**Status**: 14 tests created, blocked by session compatibility

**Endpoints**:
- `POST /api/prompts/` - Create prompt
- `GET /api/prompts/` - List prompts
- `GET /api/prompts/{id}` - Get prompt by ID
- `PUT /api/prompts/{id}` - Update prompt
- `DELETE /api/prompts/{id}` - Delete prompt

**Test Cases**:
- ✅ Create prompt with all fields
- ✅ Create prompt with minimal fields
- ✅ Create prompt with invalid data
- ✅ List all prompts
- ✅ List prompts with filters (by app_name, tags, provider)
- ✅ List prompts with pagination
- ✅ Get prompt by ID
- ✅ Get non-existent prompt (404)
- ✅ Update prompt
- ✅ Update non-existent prompt (404)
- ✅ Delete prompt
- ✅ Delete non-existent prompt (404)
- ✅ Duplicate unique_label validation
- ✅ Search prompts by label

### 2. Agents API (`/api/agents`)
**Status**: Needs to be created

**Endpoints**:
- `POST /api/agents/` - Create agent
- `GET /api/agents/` - List agents
- `GET /api/agents/{id}` - Get agent by ID
- `PUT /api/agents/{id}` - Update agent
- `DELETE /api/agents/{id}` - Delete agent
- `POST /api/agents/{id}/tools` - Attach tool to agent
- `GET /api/agents/{id}/tools` - List agent tools
- `DELETE /api/agents/{id}/tools/{tool_id}` - Detach tool from agent

**Test Cases** (21 tests):
- Create agent with different providers (OpenAI, Anthropic, etc.)
- Create agent with invalid provider
- Create agent with missing required fields
- List agents with filters (by provider, status, tags)
- List agents with pagination
- Get agent by ID
- Get non-existent agent (404)
- Update agent configuration
- Update agent provider settings
- Delete agent
- Delete non-existent agent (404)
- Attach local tool to agent
- Attach MCP tool to agent
- Attach tool with override parameters
- Attach non-existent tool (404)
- List agent tools
- Detach tool from agent
- Detach non-existent tool (404)
- Agent with multiple tools
- Agent execution (if endpoint exists)
- Agent streaming (if endpoint exists)

### 3. Workflows API (`/api/workflows`)
**Status**: Partial coverage exists

**Endpoints**:
- `POST /api/workflows/` - Create workflow
- `GET /api/workflows/` - List workflows
- `GET /api/workflows/{id}` - Get workflow by ID
- `PUT /api/workflows/{id}` - Update workflow
- `DELETE /api/workflows/{id}` - Delete workflow
- `POST /api/workflows/{id}/execute` - Execute workflow
- `POST /api/workflows/{id}/stream` - Stream workflow execution

**Test Cases** (25 tests):
- Create workflow with all step types
- Create workflow with minimal configuration
- Create workflow with invalid step type
- Create workflow with circular dependencies
- Create workflow with missing dependencies
- List workflows with filters (by tags, editable)
- List workflows with pagination
- Get workflow by ID
- Get non-existent workflow (404)
- Update workflow configuration
- Update workflow steps
- Update non-existent workflow (404)
- Delete workflow
- Delete non-existent workflow (404)
- Execute workflow with webhook trigger
- Execute workflow with manual trigger
- Execute workflow with invalid trigger
- Execute workflow not found (404)
- Stream workflow execution
- Workflow with agent step
- Workflow with tool step
- Workflow with data processing step
- Workflow with conditional logic
- Workflow with parallel execution
- Workflow with subflow

### 4. Executions API (`/api/executions`)
**Status**: 20 tests created, blocked by session compatibility

**Endpoints**:
- `GET /api/executions/` - List executions
- `GET /api/executions/{id}` - Get execution by ID
- `GET /api/executions/{id}/status` - Get execution status
- `POST /api/executions/{id}/cancel` - Cancel execution
- `GET /api/executions/{id}/logs` - Get execution logs

**Test Cases**:
- ✅ List all executions
- ✅ List executions with filters (by workflow_id, status)
- ✅ List executions with pagination
- ✅ Get execution by ID
- ✅ Get non-existent execution (404)
- ✅ Get execution status
- ✅ Get execution logs
- ✅ Cancel running execution
- ✅ Cancel completed execution (should fail)
- ✅ Cancel non-existent execution (404)
- ✅ Execution with success status
- ✅ Execution with failure status
- ✅ Execution with pending status
- ✅ Execution with streaming
- ✅ Execution with multiple steps
- ✅ Execution error handling
- ✅ Execution retry logic
- ✅ Execution timeout handling
- ✅ Execution with agent step
- ✅ Execution with tool step

### 5. Tools API (`/api/tools`)
**Status**: Partial coverage exists in functional tests

**Endpoints**:
- `GET /api/tools/` - List all tools
- `GET /api/tools/{id}` - Get tool by ID
- `POST /api/tools/` - Create custom tool
- `PUT /api/tools/{id}` - Update tool
- `DELETE /api/tools/{id}` - Delete tool
- `GET /api/tools/categories` - List tool categories
- `POST /api/tools/categories` - Create category
- `GET /api/tools/mcp-servers` - List MCP servers
- `POST /api/tools/mcp-servers` - Register MCP server

**Test Cases** (20 tests):
- List all tools (local + DB + MCP)
- List tools with pagination
- List tools by source (local/db/mcp)
- List tools by category
- Get tool by ID
- Get tool by name
- Get non-existent tool (404)
- Create custom tool
- Create tool with invalid schema
- Update tool
- Update non-existent tool (404)
- Delete tool
- Delete non-existent tool (404)
- List tool categories
- Create tool category
- Update tool category
- Delete tool category
- List MCP servers
- Register MCP server
- MCP server health check

### 6. Files API (`/api/files`)
**Status**: Needs to be created

**Endpoints**:
- `POST /api/files/upload` - Upload file
- `GET /api/files/` - List files
- `GET /api/files/{id}` - Get file metadata
- `GET /api/files/{id}/download` - Download file
- `DELETE /api/files/{id}` - Delete file

**Test Cases** (10 tests):
- Upload text file
- Upload PDF file
- Upload image file
- Upload file with invalid type
- Upload file too large
- List uploaded files
- Get file metadata
- Download file
- Delete file
- Delete non-existent file (404)

### 7. Analytics API (`/api/analytics`)
**Status**: Partial coverage exists in functional tests

**Endpoints**:
- `GET /api/analytics/workflows` - Workflow analytics
- `GET /api/analytics/agents` - Agent analytics
- `GET /api/analytics/executions` - Execution analytics

**Test Cases** (8 tests):
- Get workflow execution stats
- Get agent usage stats
- Get execution success/failure rates
- Get execution duration metrics
- Get tool usage stats
- Get analytics with date range filter
- Get analytics with workflow filter
- Get analytics with agent filter

### 8. Pipelines API (`/api/pipelines`)
**Status**: Needs investigation (may be deprecated)

**Test Cases**: TBD based on endpoint discovery

### 9. Steps API (`/api/steps`)
**Status**: Needs investigation

**Test Cases**: TBD based on endpoint discovery

## Test Infrastructure

### Fixtures Needed
- ✅ `test_client` - FastAPI TestClient
- ✅ `db_session` - Database session with cleanup
- ✅ `sample_prompt_data` - Prompt test data
- ✅ `sample_agent_data` - Agent test data
- ✅ `sample_workflow_data` - Workflow test data
- ✅ `sample_tool_data` - Tool test data
- ⚠️ `sample_execution_data` - Execution test data
- ⚠️ `sample_file_data` - File upload test data

### Test Organization
```
tests/
├── integration/          # API integration tests
│   ├── test_prompts_api.py      ✅ (blocked)
│   ├── test_agents_api.py       ⚠️ (to create)
│   ├── test_workflows_api.py    ⚠️ (to create)
│   ├── test_executions_api.py   ✅ (blocked)
│   ├── test_tools_api.py        ⚠️ (to create)
│   ├── test_files_api.py        ⚠️ (to create)
│   └── test_analytics_api.py    ⚠️ (to create)
├── e2e/                  # End-to-end tests
│   └── test_workflow_agent_streaming.py ✅
└── conftest.py          # Shared fixtures
```

## Priority Order

### Phase 1: Fix Blocking Issue (HIGH PRIORITY)
1. Fix SDK/database session compatibility
2. Verify existing prompts and executions tests pass

### Phase 2: Core API Tests (HIGH PRIORITY)
1. Agents API (21 tests)
2. Workflows API (25 tests)
3. Tools API (20 tests)

### Phase 3: Supporting API Tests (MEDIUM PRIORITY)
1. Files API (10 tests)
2. Analytics API (8 tests)

### Phase 4: Additional Coverage (LOW PRIORITY)
1. Pipelines API (TBD)
2. Steps API (TBD)
3. E2E scenarios

## Success Criteria

- [ ] All API endpoints have integration tests
- [ ] Test coverage > 80% for API layer
- [ ] All tests pass consistently
- [ ] Tests run in < 2 minutes
- [ ] Clear test documentation
- [ ] CI/CD integration ready

## Estimated Test Count

- Prompts API: 14 tests ✅
- Agents API: 21 tests ⚠️
- Workflows API: 25 tests ⚠️
- Executions API: 20 tests ✅
- Tools API: 20 tests ⚠️
- Files API: 10 tests ⚠️
- Analytics API: 8 tests ⚠️
- **Total: ~118 integration tests**


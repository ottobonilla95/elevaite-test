# API Test Coverage Analysis

## Current Test Status

### Existing Tests (13 test files)

#### Unit/Integration Tests
1. **test_api.py** - Basic API endpoint testing with TestClient
2. **test_conditional_execution.py** - Conditional workflow logic
3. **test_error_handling.py** - Error handling scenarios
4. **test_monitoring.py** - Monitoring and metrics
5. **test_ingest_e2e.py** - File ingestion workflows
6. **test_rag_e2e.py** - RAG workflows

#### E2E Tests
7. **test_smoke_live_api.py** - End-to-end smoke test (requires running server)
8. **test_approvals_e2e.py** - Human approval workflows
9. **test_dbos_api.py** - DBOS backend testing
10. **test_streaming.py** - SSE streaming tests
11. **test_interactive_api_e2e.py** - Interactive multi-agent workflows
12. **test_interactive_e2e.py** - Interactive flow testing
13. **test_megaflow.py** - Complex workflow scenarios

### API Endpoints Coverage

#### ✅ Currently Tested
- Health endpoints (`/`, `/health`)
- Basic workflow CRUD
- Workflow execution (local backend)
- File upload workflows
- Agent execution in workflows
- Streaming execution
- Human approvals
- DBOS backend execution

#### ❌ Missing Coverage

**Workflows Router** (`/workflows`)
- [ ] POST `/workflows/` - Create workflow (partial coverage)
- [ ] GET `/workflows/` - List workflows with filters
- [ ] GET `/workflows/{workflow_id}` - Get workflow by ID
- [ ] PUT `/workflows/{workflow_id}` - Update workflow
- [ ] DELETE `/workflows/{workflow_id}` - Delete workflow
- [ ] POST `/workflows/{workflow_id}/execute/{backend}` - Execute with specific backend
- [ ] POST `/workflows/{workflow_id}/stream` - Stream execution

**Agents Router** (`/agents`)
- [ ] POST `/agents/` - Create agent
- [ ] GET `/agents/` - List agents with filters (organization, status, tags)
- [ ] GET `/agents/{agent_id}` - Get agent by ID
- [ ] PUT `/agents/{agent_id}` - Update agent
- [ ] DELETE `/agents/{agent_id}` - Delete agent
- [ ] POST `/agents/{agent_id}/tools` - Attach tool to agent
- [ ] GET `/agents/{agent_id}/tools` - List agent tools
- [ ] PATCH `/agents/{agent_id}/tools/{binding_id}` - Update tool binding
- [ ] DELETE `/agents/{agent_id}/tools/{binding_id}` - Detach tool
- [ ] POST `/agents/{agent_id}/execute` - Execute agent directly

**Tools Router** (`/tools`)
- [ ] GET `/tools/` - List all tools (unified registry)
- [ ] GET `/tools/{tool_id}` - Get tool by ID
- [ ] POST `/tools/` - Create custom tool
- [ ] PUT `/tools/{tool_id}` - Update tool
- [ ] DELETE `/tools/{tool_id}` - Delete tool
- [ ] GET `/tools/categories` - List tool categories
- [ ] POST `/tools/categories` - Create category
- [ ] GET `/tools/mcp-servers` - List MCP servers
- [ ] POST `/tools/mcp-servers` - Register MCP server

**Prompts Router** (`/prompts`)
- [ ] POST `/prompts/` - Create prompt
- [ ] GET `/prompts/` - List prompts
- [ ] GET `/prompts/{prompt_id}` - Get prompt by ID
- [ ] PUT `/prompts/{prompt_id}` - Update prompt
- [ ] DELETE `/prompts/{prompt_id}` - Delete prompt

**Executions Router** (`/executions`)
- [ ] GET `/executions/{execution_id}` - Get execution status (partial)
- [ ] GET `/executions/{execution_id}/results` - Get execution results (partial)
- [ ] GET `/executions/` - List executions with filters
- [ ] GET `/executions/{execution_id}/stream` - Stream execution updates

**Messages Router** (`/messages`)
- [ ] GET `/executions/{execution_id}/steps/{step_id}/messages` - Get step messages
- [ ] POST `/executions/{execution_id}/steps/{step_id}/messages` - Send message to step

**Files Router** (`/files`)
- [ ] POST `/files/upload` - Upload file
- [ ] GET `/files/{file_id}` - Get file metadata
- [ ] GET `/files/{file_id}/download` - Download file

**Steps Router** (`/steps`)
- [ ] GET `/steps/` - List registered steps
- [ ] GET `/steps/{step_type}` - Get step info

**Monitoring Router** (`/monitoring`)
- [ ] GET `/metrics` - Prometheus metrics

**Approvals Router** (`/approvals`)
- [ ] GET `/approvals/{approval_id}` - Get approval status (partial)
- [ ] POST `/approvals/{approval_id}/respond` - Respond to approval (partial)

## Test Suite Structure Recommendation

```
tests/
├── conftest.py                          # Shared fixtures
├── unit/                                # Fast unit tests
│   ├── test_models.py                   # Database model validation
│   ├── test_services.py                 # Service layer logic
│   └── test_utils.py                    # Utility functions
├── integration/                         # API integration tests
│   ├── test_workflows_api.py            # Workflow CRUD + execution
│   ├── test_agents_api.py               # Agent CRUD + tool binding
│   ├── test_tools_api.py                # Tool registry operations
│   ├── test_prompts_api.py              # Prompt management
│   ├── test_executions_api.py           # Execution tracking
│   ├── test_messages_api.py             # Interactive messaging
│   ├── test_files_api.py                # File upload/download
│   ├── test_approvals_api.py            # Human approvals
│   └── test_monitoring_api.py           # Metrics and health
├── e2e/                                 # End-to-end scenarios
│   ├── test_complete_workflow.py        # Full workflow lifecycle
│   ├── test_agent_tool_workflow.py      # Agent + tool execution
│   ├── test_streaming_workflow.py       # SSE streaming
│   ├── test_interactive_workflow.py     # Multi-turn conversations
│   └── test_dbos_backend.py             # DBOS execution
└── performance/                         # Load and performance tests
    ├── test_concurrent_executions.py
    └── test_large_workflows.py
```

## Priority Test Coverage

### Phase 1: Core API Coverage (High Priority)
1. **Workflows API** - Complete CRUD + execution
2. **Agents API** - Complete CRUD + tool binding
3. **Tools API** - Registry operations
4. **Prompts API** - CRUD operations
5. **Executions API** - Status tracking and results

### Phase 2: Advanced Features (Medium Priority)
6. **Messages API** - Interactive workflows
7. **Files API** - Upload/download
8. **Approvals API** - Human-in-the-loop
9. **Streaming** - SSE execution updates

### Phase 3: Operations (Lower Priority)
10. **Monitoring** - Metrics and health checks
11. **Performance** - Load testing
12. **Error scenarios** - Edge cases and failures

## Test Data Strategy

### Fixtures
- **Prompts**: Reusable system prompts for agents
- **Agents**: Pre-configured agents with different providers
- **Tools**: Sample tools for testing
- **Workflows**: Template workflows for different scenarios
- **Files**: Sample documents for file-based workflows

### Cleanup Strategy
- Use pytest fixtures with `yield` for automatic cleanup
- Delete test resources after each test
- Use unique identifiers (timestamps/UUIDs) to avoid conflicts
- Implement cleanup hooks for failed tests

## CI/CD Integration

### GitHub Actions Workflow
```yaml
name: API Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -e python_packages/workflow-core-sdk[test]
      
      - name: Run unit tests
        run: pytest tests/unit -v --cov
      
      - name: Run integration tests
        run: pytest tests/integration -v --cov --cov-append
        env:
          DATABASE_URL: postgresql://postgres:postgres@localhost/test_db
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

## Next Steps

1. Create `conftest.py` with shared fixtures
2. Implement Phase 1 tests (Core API Coverage)
3. Set up CI/CD pipeline
4. Add coverage reporting
5. Implement Phase 2 and 3 tests iteratively


# Agent Studio Test Implementation Plan

**Goal**: Create comprehensive integration tests for all Agent Studio API endpoints  
**Status**: Session compatibility fixed ✅ | 4 prompts tests passing | Ready to scale up

## Current State

### ✅ Completed
- Session compatibility issue resolved (SQLModel Session in tests)
- Test infrastructure in place (conftest.py with fixtures)
- 4 prompts API tests passing
- E2E test for workflow agent streaming passing

### ⚠️ In Progress
- Prompts API: 4 passing, 10 failing (validation errors - schema mismatches)

### ❌ Not Started
- Agents API (9 endpoints)
- Workflows API (13 endpoints)
- Tools API (13 endpoints)
- Executions API (11 endpoints)
- Files API (6 endpoints)
- Analytics API (8 endpoints)

## API Endpoint Inventory

### 1. Prompts API (`/api/prompts`) - 5 endpoints
**Status**: Partially tested (4/14 tests passing)

| Method | Endpoint | Purpose | Test Status |
|--------|----------|---------|-------------|
| POST | `/` | Create prompt | ✅ Passing |
| GET | `/` | List prompts | ✅ Passing |
| GET | `/{prompt_id}` | Get prompt | ❌ Failing (validation) |
| PUT | `/{prompt_id}` | Update prompt | ❌ Failing (validation) |
| DELETE | `/{prompt_id}` | Delete prompt | ❌ Failing (validation) |

**Priority**: HIGH - Fix validation errors first

### 2. Agents API (`/api/agents`) - 9 endpoints
**Status**: Not tested

| Method | Endpoint | Purpose | Test Priority |
|--------|----------|---------|---------------|
| POST | `/` | Create agent | HIGH |
| GET | `/` | List agents | HIGH |
| GET | `/{agent_id}` | Get agent | HIGH |
| PUT | `/{agent_id}` | Update agent | HIGH |
| DELETE | `/{agent_id}` | Delete agent | HIGH |
| PUT | `/{agent_id}/functions` | Update agent tools | MEDIUM |
| POST | `/{agent_id}/execute` | Execute agent | LOW (via workflows) |
| POST | `/{agent_id}/stream` | Stream agent | LOW (via workflows) |
| POST | `/{agent_id}/chat` | Chat with agent | LOW (via workflows) |

**Priority**: HIGH - Core CRUD operations needed

### 3. Workflows API (`/api/workflows`) - 13 endpoints
**Status**: Partial coverage in existing tests

| Method | Endpoint | Purpose | Test Priority |
|--------|----------|---------|---------------|
| POST | `/` | Create workflow | HIGH |
| GET | `/` | List workflows | HIGH |
| GET | `/{workflow_id}` | Get workflow | HIGH |
| PUT | `/{workflow_id}` | Update workflow | HIGH |
| DELETE | `/{workflow_id}` | Delete workflow | HIGH |
| POST | `/{workflow_id}/execute` | Execute workflow | HIGH |
| POST | `/{workflow_id}/execute/async` | Async execute | MEDIUM |
| POST | `/{workflow_id}/stream` | Stream execution | HIGH |
| POST | `/{workflow_id}/agents` | Add agent to workflow | LOW (deprecated?) |
| POST | `/{workflow_id}/connections` | Add connections | LOW (deprecated?) |
| POST | `/{workflow_id}/deploy` | Deploy workflow | LOW (deprecated?) |
| GET | `/deployments/active` | List deployments | LOW (deprecated?) |
| POST | `/deployments/{name}/stop` | Stop deployment | LOW (deprecated?) |

**Priority**: HIGH - Core workflow functionality

### 4. Tools API (`/api/tools`) - 13 endpoints
**Status**: Partial coverage in functional tests

| Method | Endpoint | Purpose | Test Priority |
|--------|----------|---------|---------------|
| GET | `/` | List all tools | HIGH |
| GET | `/available` | List available tools | MEDIUM |
| GET | `/by-name/{tool_name}` | Get tool by name | HIGH |
| POST | `/sync-local` | Sync local tools | MEDIUM |
| POST | `/` | Create custom tool | HIGH |
| GET | `/categories` | List categories | MEDIUM |
| GET | `/{tool_id}` | Get tool by ID | HIGH |
| PUT | `/{tool_id}` | Update tool | HIGH |
| DELETE | `/{tool_id}` | Delete tool | HIGH |
| POST | `/{tool_id}/execute` | Execute tool | MEDIUM |
| POST | `/categories/` | Create category | MEDIUM |
| GET | `/mcp-servers/` | List MCP servers | MEDIUM |
| POST | `/mcp-servers/` | Register MCP server | MEDIUM |

**Priority**: HIGH - Tool management is core functionality

### 5. Executions API (`/api/executions`) - 11 endpoints
**Status**: Not tested (20 tests created but not run)

| Method | Endpoint | Purpose | Test Priority |
|--------|----------|---------|---------------|
| GET | `/{execution_id}/status` | Get status | HIGH |
| GET | `/` | List executions | HIGH |
| POST | `/{execution_id}/cancel` | Cancel execution | HIGH |
| GET | `/{execution_id}/result` | Get result | HIGH |
| GET | `/{execution_id}/trace` | Get trace | MEDIUM |
| GET | `/{execution_id}/steps` | Get steps | MEDIUM |
| GET | `/{execution_id}/progress` | Get progress | MEDIUM |
| GET | `/stats` | Get statistics | LOW |
| GET | `/analytics` | Get analytics | LOW |
| POST | `/cleanup` | Cleanup old executions | LOW |
| GET | `/{execution_id}/input-output` | Get I/O | MEDIUM |

**Priority**: HIGH - Execution monitoring is critical

### 6. Files API (`/api/files`) - 6 endpoints
**Status**: Not tested

| Method | Endpoint | Purpose | Test Priority |
|--------|----------|---------|---------------|
| POST | `/upload` | Upload file | HIGH |
| GET | `/` | List files | HIGH |
| DELETE | `/{file_id}` | Delete file | HIGH |
| GET | `/config` | Get config | LOW |
| POST | `/upload-to-s3` | Upload to S3 | MEDIUM |
| POST | `/upload-direct-to-s3` | Direct S3 upload | MEDIUM |

**Priority**: MEDIUM - File handling is important but not critical

### 7. Analytics API (`/api/analytics`) - 8 endpoints
**Status**: Partial coverage in functional tests

| Method | Endpoint | Purpose | Test Priority |
|--------|----------|---------|---------------|
| GET | `/health` | Health check | LOW |
| GET | `/agents/usage` | Agent usage stats | MEDIUM |
| GET | `/tools/usage` | Tool usage stats | MEDIUM |
| GET | `/workflows/performance` | Workflow performance | MEDIUM |
| GET | `/errors/summary` | Error summary | MEDIUM |
| GET | `/sessions/activity` | Session activity | LOW |
| GET | `/summary` | Overall summary | MEDIUM |
| GET | `/executions/{id}` | Execution analytics | MEDIUM |
| GET | `/sessions/{id}` | Session analytics | LOW |

**Priority**: LOW - Analytics are nice-to-have

## Implementation Strategy

### Phase 1: Fix Existing Tests (Week 1, Day 1-2)
**Goal**: Get all prompts API tests passing

1. **Investigate validation errors** (422 responses)
   - Check schema mismatches between test data and API expectations
   - Fix test data to match actual API schemas
   - Verify all 14 prompts tests pass

2. **Run executions API tests**
   - Tests already created, just need to run them
   - Fix any validation errors
   - Target: 20 executions tests passing

**Deliverable**: 34 tests passing (14 prompts + 20 executions)

### Phase 2: Core CRUD Tests (Week 1, Day 3-5)
**Goal**: Test all core CRUD operations

1. **Agents API** (Priority: HIGH)
   - Create test file: `test_agents_api.py`
   - Test all 5 CRUD endpoints
   - Test tool binding (PUT `/functions`)
   - Target: 15 tests

2. **Workflows API** (Priority: HIGH)
   - Create test file: `test_workflows_api.py`
   - Test all 5 CRUD endpoints
   - Test execution endpoints (execute, stream)
   - Target: 20 tests

3. **Tools API** (Priority: HIGH)
   - Create test file: `test_tools_api.py`
   - Test all CRUD endpoints
   - Test categories and MCP servers
   - Target: 15 tests

**Deliverable**: 84 tests passing (34 + 50 new)

### Phase 3: Execution & Files (Week 2, Day 1-2)
**Goal**: Test execution monitoring and file handling

1. **Executions API** (already have tests, just verify)
   - Verify all 20 tests pass
   - Add any missing edge cases

2. **Files API**
   - Create test file: `test_files_api.py`
   - Test upload, list, delete
   - Test S3 integration (if configured)
   - Target: 10 tests

**Deliverable**: 94 tests passing (84 + 10 new)

### Phase 4: Analytics & Edge Cases (Week 2, Day 3-5)
**Goal**: Complete coverage and edge cases

1. **Analytics API**
   - Create test file: `test_analytics_api.py`
   - Test all analytics endpoints
   - Target: 10 tests

2. **Edge Cases & Integration**
   - Cross-API workflows (create agent → create workflow → execute)
   - Error handling scenarios
   - Performance tests
   - Target: 15 tests

**Deliverable**: 119 tests passing (94 + 25 new)

## Test Organization

### Directory Structure
```
tests/
├── integration/
│   ├── test_prompts_api.py      ✅ (4/14 passing)
│   ├── test_executions_api.py   ✅ (created, not run)
│   ├── test_agents_api.py       ⚠️ (to create)
│   ├── test_workflows_api.py    ⚠️ (to create)
│   ├── test_tools_api.py        ⚠️ (to create)
│   ├── test_files_api.py        ⚠️ (to create)
│   └── test_analytics_api.py    ⚠️ (to create)
├── e2e/
│   └── test_workflow_agent_streaming.py ✅
└── conftest.py                  ✅ (fixed)
```

### Test Naming Convention
- `test_<action>_<entity>_<scenario>`
- Examples:
  - `test_create_agent_success`
  - `test_list_workflows_with_pagination`
  - `test_execute_workflow_not_found`

### Fixture Strategy
- Use existing fixtures in `conftest.py`
- Add new fixtures as needed for each API
- Keep fixtures DRY (Don't Repeat Yourself)

## Success Metrics

### Coverage Targets
- **API Endpoint Coverage**: 100% of active endpoints
- **Code Coverage**: >80% for API layer
- **Test Execution Time**: <3 minutes for full suite
- **Test Reliability**: >95% pass rate on CI/CD

### Quality Gates
- [ ] All CRUD operations tested for each entity
- [ ] All error cases tested (404, 422, 500)
- [ ] All pagination tested where applicable
- [ ] All filtering tested where applicable
- [ ] All validation tested
- [ ] All authentication/authorization tested (if applicable)

## Risk Mitigation

### Known Risks
1. **Schema Mismatches**: Test data may not match API expectations
   - **Mitigation**: Validate schemas before writing tests
   
2. **Database State**: Tests may interfere with each other
   - **Mitigation**: Use function-scoped fixtures with cleanup
   
3. **External Dependencies**: MCP servers, S3, Redis may not be available
   - **Mitigation**: Mock external services or skip tests gracefully
   
4. **Deprecated Endpoints**: Some endpoints may be legacy
   - **Mitigation**: Mark as low priority, test only if time permits

## Timeline

| Phase | Duration | Deliverable | Tests |
|-------|----------|-------------|-------|
| Phase 1 | 2 days | Fix existing tests | 34 |
| Phase 2 | 3 days | Core CRUD tests | 84 |
| Phase 3 | 2 days | Execution & Files | 94 |
| Phase 4 | 3 days | Analytics & Edge cases | 119 |
| **Total** | **10 days** | **Full test suite** | **119** |

## Next Immediate Steps

1. **Fix prompts API validation errors** (2-3 hours)
   - Investigate 422 responses
   - Fix test data schemas
   - Verify all 14 tests pass

2. **Run executions API tests** (1 hour)
   - Execute existing test file
   - Fix any failures
   - Verify 20 tests pass

3. **Create agents API tests** (4-6 hours)
   - Write 15 tests for agents CRUD
   - Test tool binding
   - Verify all pass

**Total for Day 1**: ~8 hours → 49 tests passing (14 + 20 + 15)


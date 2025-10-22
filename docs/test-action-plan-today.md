# Agent Studio Test Suite - Action Plan for Today

**Date**: Current Session  
**Goal**: Get 49+ integration tests passing by end of session

## Session Overview

### Current Status
- ✅ Session compatibility fixed
- ✅ 4 prompts API tests passing
- ✅ Test infrastructure ready
- ⚠️ 10 prompts tests failing (validation errors)
- ⚠️ 20 executions tests created but not run

### Target for Today
- **49 tests passing** (14 prompts + 20 executions + 15 agents)
- **3 API endpoints fully tested** (Prompts, Executions, Agents)

## Task Breakdown

### Task 1: Fix Prompts API Validation Errors (1-2 hours)
**Current**: 4/14 tests passing  
**Target**: 14/14 tests passing

**Steps**:
1. Run one failing test with verbose output to see exact error
2. Compare test data schema with API schema expectations
3. Check SDK PromptCreate/PromptUpdate schemas
4. Fix test data in `test_prompts_api.py`
5. Run all prompts tests and verify 14/14 pass

**Commands**:
```bash
cd python_apps/agent_studio/agent-studio
pytest tests/integration/test_prompts_api.py::TestPromptsAPI::test_create_prompt_minimal_fields -vv
pytest tests/integration/test_prompts_api.py -v
```

**Expected Issues**:
- Missing required fields in test data
- Wrong field names (SDK vs Agent Studio schemas)
- Wrong data types (string vs dict, etc.)

### Task 2: Run Executions API Tests (30 min - 1 hour)
**Current**: Tests created, not run  
**Target**: 20/20 tests passing (or identify issues)

**Steps**:
1. Run executions API tests
2. Fix any validation errors (similar to prompts)
3. Verify all tests pass

**Commands**:
```bash
pytest tests/integration/test_executions_api.py -v
```

**Expected Issues**:
- Similar validation errors as prompts
- May need to create actual executions first (via workflows)

### Task 3: Create Agents API Tests (3-4 hours)
**Current**: No tests  
**Target**: 15 tests passing

**Steps**:
1. Review agent_endpoints.py to understand API
2. Review SDK AgentCreate/AgentUpdate schemas
3. Create test file structure
4. Write tests for CRUD operations (5 tests)
5. Write tests for tool binding (3 tests)
6. Write tests for error cases (4 tests)
7. Write tests for filtering/pagination (3 tests)
8. Run and verify all pass

**Test Cases**:
```python
class TestAgentsAPI:
    # CRUD Operations
    def test_create_agent_success(self, test_client):
        """Create agent with all fields"""
        
    def test_create_agent_minimal(self, test_client):
        """Create agent with minimal required fields"""
        
    def test_list_agents(self, test_client):
        """List all agents"""
        
    def test_get_agent_by_id(self, test_client):
        """Get specific agent"""
        
    def test_update_agent(self, test_client):
        """Update agent configuration"""
        
    def test_delete_agent(self, test_client):
        """Delete agent"""
    
    # Tool Binding
    def test_attach_tool_to_agent(self, test_client):
        """Attach tool to agent via PUT /functions"""
        
    def test_attach_multiple_tools(self, test_client):
        """Attach multiple tools to agent"""
        
    def test_remove_tool_from_agent(self, test_client):
        """Remove tool from agent"""
    
    # Error Cases
    def test_get_agent_not_found(self, test_client):
        """Get non-existent agent returns 404"""
        
    def test_update_agent_not_found(self, test_client):
        """Update non-existent agent returns 404"""
        
    def test_delete_agent_not_found(self, test_client):
        """Delete non-existent agent returns 404"""
        
    def test_create_agent_invalid_data(self, test_client):
        """Create agent with invalid data returns 422"""
    
    # Filtering & Pagination
    def test_list_agents_with_pagination(self, test_client):
        """List agents with limit/offset"""
        
    def test_list_agents_with_filters(self, test_client):
        """List agents filtered by status, tags, etc."""
```

**Commands**:
```bash
pytest tests/integration/test_agents_api.py -v
```

## Detailed Workflow

### Step-by-Step Execution

#### Step 1: Investigate Prompts Validation Error
```bash
# Run one failing test with full output
pytest tests/integration/test_prompts_api.py::TestPromptsAPI::test_create_prompt_minimal_fields -vv --tb=short

# Check what the API expects
# Look at: python_packages/workflow-core-sdk/workflow_core_sdk/db/models/prompts.py
# Look at: python_apps/agent_studio/agent-studio/api/prompt_endpoints.py
```

#### Step 2: Fix Test Data
```python
# Example fix in test_prompts_api.py
prompt_data = {
    "prompt_label": "Test Prompt",
    "prompt": "You are a test assistant",
    "unique_label": f"test_{uuid.uuid4().hex[:8]}",
    "app_name": "test_app",
    # Add any missing required fields
    # Fix any field name mismatches
    # Fix any type mismatches
}
```

#### Step 3: Verify Prompts Tests
```bash
pytest tests/integration/test_prompts_api.py -v
# Should see: 14 passed
```

#### Step 4: Run Executions Tests
```bash
pytest tests/integration/test_executions_api.py -v
# Fix any errors, aim for 20 passed
```

#### Step 5: Create Agents Tests
```bash
# Create new file
touch tests/integration/test_agents_api.py

# Write tests (use prompts tests as template)
# Run tests
pytest tests/integration/test_agents_api.py -v
# Should see: 15 passed
```

## Success Criteria

### Minimum Success (End of Session)
- [ ] 14 prompts API tests passing
- [ ] 20 executions API tests passing
- [ ] 15 agents API tests passing
- [ ] **Total: 49 tests passing**

### Stretch Goals
- [ ] 10 additional agents tests (edge cases)
- [ ] Start workflows API tests
- [ ] **Total: 60+ tests passing**

## Checkpoints

### Checkpoint 1 (After 1 hour)
- [ ] Identified root cause of prompts validation errors
- [ ] Fixed at least 5 prompts tests
- **Decision Point**: Continue fixing prompts or move to executions?

### Checkpoint 2 (After 2 hours)
- [ ] All 14 prompts tests passing
- [ ] Executions tests run (pass/fail status known)
- **Decision Point**: Fix executions or start agents?

### Checkpoint 3 (After 4 hours)
- [ ] Prompts: 14/14 passing
- [ ] Executions: 20/20 passing (or issues documented)
- [ ] Agents: Test file created, first 5 tests written
- **Decision Point**: Continue agents or address blockers?

### Checkpoint 4 (End of Session)
- [ ] Prompts: 14/14 passing
- [ ] Executions: 20/20 passing
- [ ] Agents: 15/15 passing
- [ ] Documentation updated
- [ ] Commit made with summary

## Commit Strategy

### Commit 1: Fix Prompts Validation
```bash
git add tests/integration/test_prompts_api.py
git commit -m "fix: resolve prompts API validation errors

- Fixed test data schemas to match SDK PromptCreate/PromptUpdate
- All 14 prompts API tests now passing
- Identified schema mismatches: [list specific issues]"
```

### Commit 2: Verify Executions Tests
```bash
git add tests/integration/test_executions_api.py
git commit -m "test: verify executions API integration tests

- Ran 20 executions API tests
- [X/20] tests passing
- [Issues if any]"
```

### Commit 3: Add Agents Tests
```bash
git add tests/integration/test_agents_api.py
git commit -m "test: add comprehensive agents API integration tests

- Created 15 integration tests for agents API
- Tests cover CRUD operations, tool binding, error cases
- All tests passing"
```

## Resources Needed

### Files to Reference
- `python_packages/workflow-core-sdk/workflow_core_sdk/db/models/prompts.py` - Prompt schema
- `python_packages/workflow-core-sdk/workflow_core_sdk/db/models/agents.py` - Agent schema
- `python_packages/workflow-core-sdk/workflow_core_sdk/db/models/executions.py` - Execution schema
- `python_apps/agent_studio/agent-studio/api/prompt_endpoints.py` - Prompts API
- `python_apps/agent_studio/agent-studio/api/agent_endpoints.py` - Agents API
- `python_apps/agent_studio/agent-studio/api/execution_endpoints.py` - Executions API

### Commands Reference
```bash
# Run specific test
pytest tests/integration/test_prompts_api.py::TestPromptsAPI::test_create_prompt_success -vv

# Run test file
pytest tests/integration/test_prompts_api.py -v

# Run with coverage
pytest tests/integration/test_prompts_api.py --cov=api --cov-report=term-missing

# Run all integration tests
pytest tests/integration/ -v

# Run with specific markers
pytest -m integration -v
```

## Notes & Observations

### Key Learnings
- Session compatibility was the main blocker (now fixed)
- Validation errors are likely schema mismatches
- SDK schemas may differ from Agent Studio schemas
- Adapter layer may need attention

### Potential Blockers
- External dependencies (Redis, S3, MCP servers)
- Database state between tests
- Async execution timing issues
- Missing test data fixtures

### Mitigation Strategies
- Mock external services where needed
- Use function-scoped fixtures with cleanup
- Add appropriate waits/retries for async operations
- Create comprehensive fixtures in conftest.py

## End of Session Deliverable

### Summary Document
Create `docs/test-progress-summary.md` with:
- Tests passing count
- Issues encountered and resolved
- Remaining work
- Next steps

### Metrics
- **Tests Created**: X
- **Tests Passing**: X/X
- **Code Coverage**: X%
- **Time Spent**: X hours
- **Velocity**: X tests/hour

---

**Ready to start? Let's begin with Task 1: Fix Prompts API Validation Errors!**


# Quick Wins - Testing Improvements

This document outlines the quickest, highest-impact testing improvements we can make right now.

## Current State

- **Coverage**: 33% (baseline established)
- **Passing Tests**: 12/17 (71%)
- **Failing Tests**: 3 (all fixable)
- **Skipped Tests**: 2 (require API keys)

## Quick Wins (Today)

### 1. Fix 3 Failing Tests ⚡

#### Test 1: `test_api_endpoints` - UUID Validation
**Time**: 5 minutes  
**Impact**: +1 passing test

**Problem**: Test uses `workflow_id="test-api-workflow"` but API expects UUID

**Solution**: Update test to use UUID format
```python
# Change from:
workflow_id = "test-api-workflow"

# To:
import uuid
workflow_id = str(uuid.uuid4())
```

#### Test 2: `test_workflow_error_integration` - Missing Method
**Time**: 10 minutes  
**Impact**: +1 passing test

**Problem**: `ExecutionContext` missing `fail_execution` method

**Solution**: Check if method exists in workflow-core-sdk or update test to use correct method

#### Test 3: `test_monitoring_api_endpoints` - Import Error
**Time**: 2 minutes  
**Impact**: +1 passing test

**Problem**: Wrong import path `workflow_engine_poc.database`

**Solution**: Update import
```python
# Change from:
from workflow_engine_poc.database import get_database

# To:
from workflow_engine_poc.db.database import get_database
```

**Total Time**: ~20 minutes  
**Result**: 15/17 tests passing (88%)

### 2. Add Basic Router Tests ⚡

**Time**: 2-3 hours  
**Impact**: +15-20% coverage

Add simple CRUD tests for the most critical routers:

#### Workflows Router (Priority 1)
```python
def test_create_workflow(test_client):
    response = test_client.post("/workflows/", json={...})
    assert response.status_code == 200

def test_list_workflows(test_client):
    response = test_client.get("/workflows/")
    assert response.status_code == 200

def test_get_workflow(test_client, sample_workflow):
    response = test_client.get(f"/workflows/{sample_workflow.id}")
    assert response.status_code == 200

def test_delete_workflow(test_client, sample_workflow):
    response = test_client.delete(f"/workflows/{sample_workflow.id}")
    assert response.status_code == 200
```

#### Agents Router (Priority 2)
```python
def test_create_agent(test_client):
    # Similar CRUD tests
    pass

def test_list_agents(test_client):
    pass
```

#### Tools Router (Priority 3)
```python
def test_list_tools(test_client):
    # Similar CRUD tests
    pass
```

**Files to Create**:
- `tests/test_workflows_router.py` (~100 lines)
- `tests/test_agents_router.py` (~100 lines)
- `tests/test_tools_router.py` (~80 lines)

**Total Time**: 2-3 hours  
**Result**: ~48% coverage

### 3. Add Basic Step Tests ⚡

**Time**: 1-2 hours  
**Impact**: +5-10% coverage

Add tests for the most-used steps:

```python
# tests/test_data_input_step.py
@pytest.mark.unit
def test_data_input_step():
    step = DataInputStep()
    result = await step.execute({
        "config": {"input_type": "static", "data": {"key": "value"}}
    })
    assert result["key"] == "value"

# tests/test_data_processing_step.py
@pytest.mark.unit
def test_data_processing_step():
    step = DataProcessingStep()
    result = await step.execute({
        "config": {"operation": "transform", "transformation": "upper"},
        "input": {"message": "hello"}
    })
    assert result["message"] == "HELLO"
```

**Files to Create**:
- `tests/test_data_input_step.py` (~50 lines)
- `tests/test_data_processing_step.py` (~80 lines)
- `tests/test_agent_execution_step.py` (~100 lines, with mocks)

**Total Time**: 1-2 hours  
**Result**: ~55% coverage

## Medium Wins (This Week)

### 4. Add Service Layer Tests

**Time**: 3-4 hours  
**Impact**: +10-15% coverage

Test the database service layer:

```python
# tests/test_workflows_service.py
@pytest.mark.integration
def test_create_workflow_service(session):
    from workflow_core_sdk.services.workflows_service import WorkflowsService
    
    service = WorkflowsService(session)
    workflow = service.create_workflow({...})
    
    assert workflow.id is not None
    assert workflow.name == "Test Workflow"
```

**Files to Create**:
- `tests/test_workflows_service.py`
- `tests/test_executions_service.py`
- `tests/test_agents_service.py`

**Total Time**: 3-4 hours  
**Result**: ~65% coverage

### 5. Add Error Handling Tests

**Time**: 2-3 hours  
**Impact**: +5% coverage

Test error cases for routers:

```python
@pytest.mark.integration
def test_create_workflow_invalid_data(test_client):
    response = test_client.post("/workflows/", json={"name": ""})
    assert response.status_code == 422

@pytest.mark.integration
def test_get_workflow_not_found(test_client):
    response = test_client.get(f"/workflows/{uuid.uuid4()}")
    assert response.status_code == 404
```

**Total Time**: 2-3 hours  
**Result**: ~70% coverage

## Summary

| Task | Time | Coverage Gain | Total Coverage |
|------|------|---------------|----------------|
| **Baseline** | - | - | 33% |
| Fix 3 failing tests | 20 min | +0% | 33% |
| Add router tests | 2-3 hrs | +15% | 48% |
| Add step tests | 1-2 hrs | +7% | 55% |
| Add service tests | 3-4 hrs | +10% | 65% |
| Add error tests | 2-3 hrs | +5% | 70% |
| **Total** | **~10 hrs** | **+37%** | **70%** |

## Recommended Order

### Day 1 (Today)
1. ✅ Fix 3 failing tests (20 min)
2. ✅ Add workflows router tests (1 hr)
3. ✅ Add agents router tests (1 hr)
4. ✅ Add tools router tests (1 hr)

**End of Day 1**: ~48% coverage, 15/17 tests passing

### Day 2 (Tomorrow)
5. ✅ Add data input step tests (30 min)
6. ✅ Add data processing step tests (1 hr)
7. ✅ Add agent execution step tests (1.5 hrs)

**End of Day 2**: ~55% coverage

### Day 3 (Day After)
8. ✅ Add workflows service tests (1.5 hrs)
9. ✅ Add executions service tests (1.5 hrs)
10. ✅ Add agents service tests (1 hr)

**End of Day 3**: ~65% coverage

### Day 4 (Final Day)
11. ✅ Add error handling tests for routers (2 hrs)
12. ✅ Add error handling tests for services (1 hr)

**End of Day 4**: ~70% coverage ✅

## Tools Needed

- ✅ pytest-cov (installed)
- ✅ Test fixtures (created in conftest.py)
- ✅ Test template (test_template.py.example)
- ✅ Documentation (TESTING.md)

## Success Criteria

- [ ] All tests passing (17/17 or more)
- [ ] Coverage >70%
- [ ] All critical routers tested
- [ ] All common steps tested
- [ ] Service layer tested
- [ ] Error cases tested
- [ ] CI passing

## Notes

- Focus on **breadth over depth** initially
- Test **happy paths first**, then error cases
- Use **fixtures** to avoid duplication
- **Mock external services** (OpenAI, Anthropic)
- Keep tests **fast** (<10s total for unit tests)
- **Document** any skipped tests with reasons

## After 70% Coverage

Once we hit 70%, focus on:

1. **Quality over quantity** - Better assertions, edge cases
2. **RBAC tests** - Security is critical
3. **Performance tests** - Load testing
4. **E2E tests** - Full workflow execution
5. **Mutation testing** - Ensure tests catch bugs

But first, let's get to 70%! 🚀


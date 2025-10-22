# Coverage Baseline Report

**Date**: 2025-10-15  
**Overall Coverage**: **33%** (3450 of 5159 statements uncovered)

## Test Results

- ✅ **12 passing tests**
- ❌ **3 failing tests** (fixable)
- ⏭️ **2 skipped tests** (require OpenAI API key)
- **Total**: 17 tests

## Coverage by Module

### High Coverage (>70%) ✅
- `workflow_engine_poc/error_handling.py` - **91%** (16/184 uncovered)
- `workflow_engine_poc/db/database.py` - **75%** (8/32 uncovered)
- `workflow_engine_poc/tools/decorators.py` - **74%** (14/53 uncovered)
- `workflow_engine_poc/dbos_impl/messaging.py` - **67%** (2/6 uncovered)
- `workflow_engine_poc/execution_context.py` - **63%** (90/243 uncovered)
- `workflow_engine_poc/main.py` - **61%** (36/92 uncovered)
- `workflow_engine_poc/routers/health.py` - **61%** (12/31 uncovered)

### Medium Coverage (40-70%) ⚠️
- `workflow_engine_poc/routers/steps.py` - **57%** (16/37 uncovered)
- `workflow_engine_poc/condition_evaluator.py` - **55%** (88/197 uncovered)
- `workflow_engine_poc/monitoring.py` - **55%** (111/245 uncovered)
- `workflow_engine_poc/dbos_impl/steps.py` - **53%** (15/32 uncovered)
- `workflow_engine_poc/step_registry.py` - **49%** (80/158 uncovered)
- `workflow_engine_poc/routers/prompts.py` - **49%** (18/35 uncovered)
- `workflow_engine_poc/routers/approvals.py` - **45%** (31/56 uncovered)
- `workflow_engine_poc/workflow_engine.py` - **43%** (213/374 uncovered)
- `workflow_engine_poc/streaming.py` - **40%** (81/135 uncovered)

### Low Coverage (<40%) ❌
- `workflow_engine_poc/dbos_impl/runtime.py` - **36%** (16/25 uncovered)
- `workflow_engine_poc/routers/agents.py` - **35%** (110/169 uncovered)
- `workflow_engine_poc/routers/tools.py` - **36%** (88/138 uncovered)
- `workflow_engine_poc/tools/registry.py` - **33%** (72/107 uncovered)
- `workflow_engine_poc/routers/monitoring.py` - **31%** (38/55 uncovered)
- `workflow_engine_poc/routers/messages.py` - **30%** (76/108 uncovered)
- `workflow_engine_poc/tools/basic_tools.py` - **28%** (83/116 uncovered)
- `workflow_engine_poc/steps/data_steps.py` - **28%** (94/131 uncovered)
- `workflow_engine_poc/routers/files.py` - **28%** (26/36 uncovered)
- `workflow_engine_poc/routers/workflows.py` - **20%** (193/241 uncovered)
- `workflow_engine_poc/routers/executions.py` - **20%** (94/117 uncovered)
- `workflow_engine_poc/db/service.py` - **18%** (152/186 uncovered)
- `workflow_engine_poc/steps/trigger_steps.py` - **18%** (27/33 uncovered)
- `workflow_engine_poc/steps/tool_steps.py` - **17%** (48/58 uncovered)
- `workflow_engine_poc/steps/file_steps.py` - **13%** (153/176 uncovered)
- `workflow_engine_poc/dbos_impl/workflows.py` - **10%** (235/262 uncovered)
- `workflow_engine_poc/steps/human_steps.py` - **10%** (52/58 uncovered)
- `workflow_engine_poc/steps/flow_steps.py` - **9%** (61/67 uncovered)
- `workflow_engine_poc/steps/ai_steps.py` - **6%** (537/569 uncovered)

### Zero Coverage (0%) 🚨
- `workflow_engine_poc/dbos_impl/adapter.py` - **0%** (157/157 uncovered)
- `workflow_engine_poc/decorators.py` - **0%** (23/23 uncovered)
- `workflow_engine_poc/examples/__init__.py` - **0%** (2/2 uncovered)
- `workflow_engine_poc/examples/workflows.py` - **0%** (6/6 uncovered)
- `workflow_engine_poc/main_sdk.py` - **0%** (100/100 uncovered)
- `workflow_engine_poc/scheduler.py` - **0%** (176/176 uncovered)

## Failing Tests (Need Fixing)

### 1. `test_api_endpoints` - UUID Validation Issue
**Error**: `badly formed hexadecimal UUID string`  
**Location**: `tests/test_api.py:118`  
**Issue**: Test uses `workflow_id="test-api-workflow"` but API expects UUID format  
**Fix**: Either update test to use UUID or update API to accept string IDs

### 2. `test_workflow_error_integration` - Missing Method
**Error**: `AttributeError: 'ExecutionContext' object has no attribute 'fail_execution'`  
**Location**: `tests/test_error_handling.py:291`  
**Issue**: ExecutionContext missing `fail_execution` method  
**Fix**: Add `fail_execution` method to ExecutionContext or update test

### 3. `test_monitoring_api_endpoints` - Import Error
**Error**: `ModuleNotFoundError: No module named 'workflow_engine_poc.database'`  
**Location**: `tests/test_monitoring.py:211`  
**Issue**: Incorrect import path (should be `workflow_engine_poc.db.database`)  
**Fix**: Update import in test

## Critical Coverage Gaps

### 1. Routers (API Endpoints) - 20-36% Coverage
**Impact**: HIGH - These are the public API  
**Priority**: CRITICAL

- `routers/workflows.py` - 20% (main workflow API)
- `routers/executions.py` - 20% (execution API)
- `routers/files.py` - 28% (file upload API)
- `routers/messages.py` - 30% (agent messages API)
- `routers/monitoring.py` - 31% (monitoring API)
- `routers/tools.py` - 36% (tool registry API)
- `routers/agents.py` - 35% (agent management API)

**Recommendation**: Add integration tests for all router endpoints

### 2. Steps (Business Logic) - 6-28% Coverage
**Impact**: HIGH - Core workflow functionality  
**Priority**: CRITICAL

- `steps/ai_steps.py` - 6% (569 statements, only 32 covered!)
- `steps/flow_steps.py` - 9% (subflow execution)
- `steps/human_steps.py` - 10% (approval steps)
- `steps/file_steps.py` - 13% (file processing)
- `steps/tool_steps.py` - 17% (tool execution)
- `steps/trigger_steps.py` - 18% (workflow triggers)
- `steps/data_steps.py` - 28% (data processing)

**Recommendation**: Add unit tests for each step type

### 3. DBOS Implementation - 0-36% Coverage
**Impact**: MEDIUM - Alternative execution engine  
**Priority**: HIGH

- `dbos_impl/adapter.py` - 0% (157 statements uncovered)
- `dbos_impl/workflows.py` - 10% (235 statements uncovered)
- `dbos_impl/runtime.py` - 36% (16 statements uncovered)

**Recommendation**: Add DBOS integration tests or mark as experimental

### 4. Scheduler - 0% Coverage
**Impact**: MEDIUM - Scheduled workflow execution  
**Priority**: HIGH

- `scheduler.py` - 0% (176 statements uncovered)

**Recommendation**: Add scheduler tests or remove if unused

### 5. Services - 18% Coverage
**Impact**: HIGH - Database operations  
**Priority**: CRITICAL

- `db/service.py` - 18% (152/186 uncovered)

**Recommendation**: Add service layer tests

## Recommendations

### Immediate (This Week)

1. **Fix 3 failing tests** - Should be quick wins
2. **Add router tests** - Focus on workflows, executions, agents, tools
3. **Add step tests** - Start with most-used steps (data_input, agent_execution)

### Short Term (Next 2 Weeks)

4. **Add service tests** - Test database operations
5. **Add DBOS tests** - Or mark as experimental/remove
6. **Add scheduler tests** - Or remove if unused
7. **Target 50% coverage** - Double current coverage

### Medium Term (Next Month)

8. **Add AI step tests** - Mock LLM calls
9. **Add file step tests** - Test file processing
10. **Add monitoring tests** - Test tracing and metrics
11. **Target 70% coverage** - Production-ready

## Coverage Goals

| Timeframe | Target | Current | Gap |
|-----------|--------|---------|-----|
| Baseline | - | 33% | - |
| 1 Week | 40% | 33% | +7% |
| 2 Weeks | 50% | 33% | +17% |
| 1 Month | 70% | 33% | +37% |
| 3 Months | 80% | 33% | +47% |

## Files to Prioritize

Based on importance and current coverage:

### Priority 1 (Critical + Low Coverage)
1. `routers/workflows.py` (20%) - Main API
2. `routers/executions.py` (20%) - Execution API
3. `steps/ai_steps.py` (6%) - AI functionality
4. `db/service.py` (18%) - Database operations

### Priority 2 (Important + Low Coverage)
5. `routers/agents.py` (35%) - Agent management
6. `routers/tools.py` (36%) - Tool registry
7. `steps/data_steps.py` (28%) - Data processing
8. `workflow_engine.py` (43%) - Core engine

### Priority 3 (Nice to Have)
9. `scheduler.py` (0%) - Scheduled execution
10. `dbos_impl/` (0-36%) - Alternative engine
11. `monitoring.py` (55%) - Observability
12. `streaming.py` (40%) - SSE streaming

## Next Steps

1. ✅ **Baseline established** - 33% coverage
2. ⏭️ **Fix 3 failing tests** - Get to 100% passing
3. ⏭️ **Add router tests** - Boost coverage to 40%+
4. ⏭️ **Add step tests** - Boost coverage to 50%+
5. ⏭️ **Add service tests** - Boost coverage to 60%+
6. ⏭️ **Add DBOS/scheduler tests** - Boost coverage to 70%+

## How to View Coverage Report

```bash
# Generate coverage report
cd python_apps/workflow-engine-poc
pytest tests/ -m "not e2e" --ignore=tests/e2e/ --cov=workflow_engine_poc --cov-report=html

# Open in browser
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

## Notes

- Coverage report generated with pytest-cov 7.0.0
- Tests run on Python 3.11.11
- In-memory SQLite database used for tests
- External services (OpenAI, Anthropic) mocked
- E2E tests excluded from coverage (require running server)


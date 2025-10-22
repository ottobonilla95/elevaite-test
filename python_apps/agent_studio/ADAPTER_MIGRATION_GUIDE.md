# Agent Studio SDK Migration Guide - Adapter Approach

## Overview

This guide walks through migrating Agent Studio to use workflow-core-SDK while maintaining 100% backwards compatibility using an adapter layer.

## Strategy

**Phase 1: Add Adapters (Current)**
- ✅ Create adapter layer
- ✅ Create SDK-based endpoints with adapters
- ✅ Test thoroughly
- ⏳ Gradually replace old endpoints

**Phase 2: Run Both Systems (Transition)**
- Run old and new endpoints side-by-side
- Feature flag to switch between them
- Validate adapter correctness
- Monitor performance

**Phase 3: Remove Old Code (Cleanup)**
- Remove old execution handlers
- Remove old workflow services
- Keep only SDK-based endpoints with adapters

**Phase 4: Remove Adapters (Future - UI Rework)**
- Update frontend to use SDK format
- Remove adapter layer
- Use SDK format end-to-end

## Step-by-Step Migration

### Step 1: Install SDK (5 minutes)

```bash
cd python_apps/agent_studio/agent-studio

# Add SDK dependency
uv add workflow-core-sdk

# Verify installation
python -c "from workflow_core_sdk import WorkflowEngine; print('SDK installed!')"
```

### Step 2: Test Adapters (15 minutes)

```bash
# Run adapter tests
pytest tests/test_adapters.py -v

# Expected output:
# test_adapters.py::TestRequestAdapter::test_adapt_workflow_execute_request_basic PASSED
# test_adapters.py::TestRequestAdapter::test_adapt_workflow_execute_request_with_attachments PASSED
# ... (all tests should pass)
```

### Step 3: Update One Endpoint (30 minutes)

Let's start with the execution status endpoint as a proof of concept.

**Before (old code):**
```python
# api/execution_endpoints.py

@router.get("/{execution_id}/status", response_model=ExecutionStatus)
def get_execution_status(execution_id: str, db: Session = Depends(get_db)):
    execution = analytics_service.get_execution(execution_id)
    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")
    return execution
```

**After (with SDK + adapters):**
```python
# api/execution_endpoints.py

from workflow_core_sdk.services import ExecutionsService
from adapters import ExecutionAdapter

@router.get("/{execution_id}/status")
async def get_execution_status(execution_id: str, db: Session = Depends(get_db)):
    # Convert to UUID
    exec_uuid = UUID(execution_id)
    
    # Get from SDK
    sdk_execution = await ExecutionsService.get_execution(db, exec_uuid)
    if not sdk_execution:
        raise HTTPException(status_code=404, detail="Execution not found")
    
    # Adapt to Agent Studio format
    as_response = ExecutionAdapter.adapt_status_response(sdk_execution)
    return as_response
```

**Test it:**
```bash
# Start agent_studio
python main.py

# In another terminal, test the endpoint
curl http://localhost:8000/api/executions/{some_execution_id}/status

# Should return Agent Studio format:
# {
#   "execution_id": "...",
#   "status": "queued",  # Not "pending"
#   "workflow_id": "..."
# }
```

### Step 4: Update Workflow Execution Endpoint (1 hour)

This is the most important endpoint - where workflows are executed.

**Before:**
```python
# api/workflow_endpoints.py

@router.post("/{workflow_id}/execute")
async def execute_workflow(workflow_id: UUID, request: Dict):
    # Custom execution logic
    context = WorkflowExecutionContext(...)
    result = await execute_hybrid_workflow(context)
    analytics_service.track_execution(...)
    return result
```

**After:**
```python
# api/workflow_endpoints.py

from workflow_core_sdk.services import ExecutionsService
from adapters import ExecutionAdapter

@router.post("/{workflow_id}/execute")
async def execute_workflow(
    workflow_id: UUID,
    request: Dict[str, Any],
    db: Session = Depends(get_db),
):
    # 1. Adapt request to SDK format
    sdk_request = ExecutionAdapter.adapt_execute_request(request)
    
    # 2. Execute via SDK
    sdk_execution = await ExecutionsService.execute_workflow(
        db=db,
        workflow_id=workflow_id,
        input_data=sdk_request["input"],
        user_context=sdk_request["user_context"],
    )
    
    # 3. Adapt response to Agent Studio format
    as_response = ExecutionAdapter.adapt_execute_response(sdk_execution)
    
    return as_response
```

**Test it:**
```bash
# Execute a workflow
curl -X POST http://localhost:8000/api/workflows/{workflow_id}/execute \
  -H "Content-Type: application/json" \
  -d '{
    "user_message": "Test message",
    "session_id": "test_session"
  }'

# Should return Agent Studio format:
# {
#   "execution_id": "...",
#   "status": "queued",
#   "workflow_id": "..."
# }
```

### Step 5: Update Workflow CRUD Endpoints (1 hour)

**Create Workflow:**
```python
from workflow_core_sdk.services import WorkflowsService
from adapters import WorkflowAdapter

@router.post("/")
async def create_workflow(
    request: Dict[str, Any],
    db: Session = Depends(get_db),
):
    # Adapt request
    sdk_request = WorkflowAdapter.adapt_create_request(request)
    
    # Create via SDK
    sdk_workflow = await WorkflowsService.create_workflow(db, sdk_request)
    
    # Adapt response
    as_response = WorkflowAdapter.adapt_workflow_response(sdk_workflow)
    
    return as_response
```

**Get Workflow:**
```python
@router.get("/{workflow_id}")
async def get_workflow(
    workflow_id: UUID,
    db: Session = Depends(get_db),
):
    # Get from SDK
    sdk_workflow = await WorkflowsService.get_workflow(db, workflow_id)
    
    if not sdk_workflow:
        raise HTTPException(404, "Workflow not found")
    
    # Adapt response
    as_response = WorkflowAdapter.adapt_workflow_response(sdk_workflow)
    
    return as_response
```

**List Workflows:**
```python
@router.get("/")
async def list_workflows(
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db),
):
    # List from SDK
    sdk_workflows = await WorkflowsService.list_workflows(
        db, limit=limit, offset=offset
    )
    
    # Adapt response
    as_response = WorkflowAdapter.adapt_list_response(sdk_workflows)
    
    return as_response
```

### Step 6: Update Remaining Endpoints (2 hours)

Apply the same pattern to:
- ✅ Execution list endpoint
- ✅ Execution cancel endpoint
- ✅ Execution result endpoint
- ✅ Execution trace endpoint
- ✅ Workflow update endpoint
- ✅ Workflow delete endpoint

See `api/execution_endpoints_sdk.py` for complete examples.

### Step 7: Integration Testing (1 hour)

Create integration tests that verify backwards compatibility:

```python
# tests/test_sdk_integration.py

import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_workflow_execution_backwards_compatible():
    """Test that workflow execution maintains Agent Studio format"""
    
    # Create workflow (Agent Studio format)
    create_response = client.post("/api/workflows/", json={
        "name": "Test Workflow",
        "configuration": {
            "agents": [{
                "agent_id": "agent_1",
                "name": "Test Agent",
                "config": {}
            }],
            "connections": []
        }
    })
    
    assert create_response.status_code == 200
    workflow = create_response.json()
    
    # Verify Agent Studio format
    assert "workflow_id" in workflow  # Not "id"
    assert "is_active" in workflow    # Not "status"
    assert "configuration" in workflow
    assert "agents" in workflow["configuration"]
    
    # Execute workflow (Agent Studio format)
    exec_response = client.post(
        f"/api/workflows/{workflow['workflow_id']}/execute",
        json={
            "user_message": "Test",
            "session_id": "test_session"
        }
    )
    
    assert exec_response.status_code == 200
    execution = exec_response.json()
    
    # Verify Agent Studio format
    assert "execution_id" in execution  # Not "id"
    assert "status" in execution
    assert execution["status"] in ["queued", "running", "completed", "failed"]
    
    # Get execution status (Agent Studio format)
    status_response = client.get(
        f"/api/executions/{execution['execution_id']}/status"
    )
    
    assert status_response.status_code == 200
    status = status_response.json()
    
    # Verify Agent Studio format
    assert "execution_id" in status
    assert "current_step" in status  # Not "current_step_id"
```

Run tests:
```bash
pytest tests/test_sdk_integration.py -v
```

### Step 8: Performance Testing (30 minutes)

Verify that adapter overhead is negligible:

```python
# tests/test_adapter_performance.py

import time
from adapters import ExecutionAdapter

def test_adapter_performance():
    """Verify adapter overhead is <1ms"""
    
    sdk_execution = {
        "id": "exec_123",
        "workflow_id": "wf_456",
        "status": "pending",
        "started_at": datetime.now(),
    }
    
    # Measure adapter time
    iterations = 1000
    start = time.time()
    
    for _ in range(iterations):
        as_response = ExecutionAdapter.adapt_status_response(sdk_execution)
    
    end = time.time()
    avg_time_ms = ((end - start) / iterations) * 1000
    
    print(f"Average adapter time: {avg_time_ms:.3f}ms")
    assert avg_time_ms < 1.0  # Should be <1ms
```

### Step 9: Deploy to Staging (1 hour)

1. Deploy to staging environment
2. Run smoke tests
3. Monitor for errors
4. Compare responses with production

### Step 10: Gradual Rollout (1 week)

Use feature flags to gradually enable SDK endpoints:

```python
# config.py

USE_SDK_ENDPOINTS = os.getenv("USE_SDK_ENDPOINTS", "false").lower() == "true"

# main.py

if USE_SDK_ENDPOINTS:
    from api.execution_endpoints_sdk import router as executions_router
else:
    from api.execution_endpoints import router as executions_router

app.include_router(executions_router)
```

**Rollout plan:**
- Day 1: 10% of traffic
- Day 2: 25% of traffic
- Day 3: 50% of traffic
- Day 5: 100% of traffic

Monitor:
- Error rates
- Response times
- Response format correctness

## Verification Checklist

### API Compatibility
- [ ] All endpoint paths unchanged
- [ ] All request formats accepted
- [ ] All response formats match Agent Studio format
- [ ] Error messages unchanged
- [ ] Status codes unchanged

### Functionality
- [ ] Workflow creation works
- [ ] Workflow execution works
- [ ] Execution status polling works
- [ ] Execution cancellation works
- [ ] Execution results retrieval works
- [ ] Workflow listing works
- [ ] Execution listing works

### Performance
- [ ] Response times similar or better
- [ ] Adapter overhead <1ms
- [ ] No memory leaks
- [ ] Database queries optimized

### Testing
- [ ] All unit tests pass
- [ ] All integration tests pass
- [ ] All e2e tests pass
- [ ] Performance tests pass

## Rollback Plan

If issues are found:

1. **Immediate rollback:**
   ```bash
   # Set feature flag
   export USE_SDK_ENDPOINTS=false
   
   # Restart service
   systemctl restart agent-studio
   ```

2. **Code rollback:**
   ```bash
   git revert <commit-hash>
   git push
   ```

3. **Database rollback:**
   - SDK uses separate tables, so no rollback needed
   - Old tables remain intact

## Future: Removing Adapters

When UI is reworked:

1. Update frontend to use SDK format
2. Remove adapter imports from endpoints
3. Use SDK format directly
4. Delete `adapters/` directory
5. Update API documentation

**Estimated time to remove adapters: 2 hours**

## Support

If you encounter issues:

1. Check adapter tests: `pytest tests/test_adapters.py -v`
2. Use debug endpoint: `GET /api/executions/{id}/debug`
3. Check logs for adapter errors
4. Compare SDK vs Agent Studio formats

## Summary

**Total Migration Time: ~8 hours**
- Setup: 30 min
- Update endpoints: 4 hours
- Testing: 2 hours
- Deployment: 1.5 hours

**Benefits:**
- ✅ Drop-in backwards compatibility
- ✅ Use SDK backend immediately
- ✅ No frontend changes needed
- ✅ Can remove adapters later

**Next Steps:**
1. Install SDK
2. Run adapter tests
3. Update one endpoint
4. Test thoroughly
5. Repeat for all endpoints


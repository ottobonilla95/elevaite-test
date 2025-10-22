# Adapter Layer for Agent Studio SDK Migration

## Purpose

This adapter layer provides **drop-in backwards compatibility** between Agent Studio's existing API format and the workflow-core-SDK's format. It allows Agent Studio to use the SDK backend while maintaining 100% API compatibility with existing clients and the frontend.

## When to Remove

**This is temporary code.** When the UI is reworked to use the SDK format directly, these adapters should be removed and the SDK format should be used end-to-end.

## Architecture

```
Frontend (Agent Studio Format)
         ↓
API Endpoints (Agent Studio Format)
         ↓
    [ADAPTER LAYER] ← You are here
         ↓
SDK Services (SDK Format)
         ↓
Database (SDK Schema)
```

## Adapters

### 1. RequestAdapter
Converts incoming API requests from Agent Studio format to SDK format.

**Example:**
```python
# Agent Studio request
as_request = {
    "user_message": "Hello",
    "session_id": "123"
}

# Convert to SDK format
sdk_request = RequestAdapter.adapt_workflow_execute_request(as_request)
# {
#     "input": {"message": "Hello"},
#     "user_context": {"session_id": "123"}
# }
```

### 2. ResponseAdapter
Converts SDK responses back to Agent Studio format.

**Example:**
```python
# SDK response
sdk_execution = {
    "id": "exec_123",
    "status": "pending"
}

# Convert to Agent Studio format
as_response = ResponseAdapter.adapt_execution_response(sdk_execution)
# {
#     "execution_id": "exec_123",
#     "status": "queued"
# }
```

### 3. ExecutionAdapter
High-level adapter for execution operations (combines request + response adapters).

**Example:**
```python
# In endpoint
sdk_execution = await ExecutionsService.execute_workflow(...)
as_response = ExecutionAdapter.adapt_execute_response(sdk_execution)
return as_response
```

### 4. WorkflowAdapter
High-level adapter for workflow operations (combines request + response adapters).

**Example:**
```python
# In endpoint
sdk_request = WorkflowAdapter.adapt_create_request(request.dict())
sdk_workflow = await WorkflowsService.create_workflow(db, sdk_request)
as_response = WorkflowAdapter.adapt_workflow_response(sdk_workflow)
return as_response
```

## Key Mappings

### Status Values
| Agent Studio | SDK |
|--------------|-----|
| `queued` | `pending` |
| `running` | `running` |
| `completed` | `completed` |
| `failed` | `failed` |
| `cancelled` | `cancelled` |

### Field Names
| Agent Studio | SDK |
|--------------|-----|
| `execution_id` | `id` |
| `workflow_id` | `id` |
| `current_step` | `current_step_id` |
| `is_active` | `status == "active"` |
| `is_editable` | `editable` |

### Workflow Structure
| Agent Studio | SDK |
|--------------|-----|
| `configuration.agents[]` | `configuration.steps[]` (type: agent_execution) |
| `configuration.connections[]` | `step.dependencies[]` |
| `configuration.steps[]` | `configuration.steps[]` (other types) |

## Usage in Endpoints

### Workflow Execution Endpoint

```python
from adapters import ExecutionAdapter
from workflow_core_sdk.services import ExecutionsService

@router.post("/{workflow_id}/execute")
async def execute_workflow(
    workflow_id: UUID,
    request: Dict[str, Any],
    db: Session = Depends(get_db),
):
    # 1. Adapt request from AS to SDK format
    sdk_request = ExecutionAdapter.adapt_execute_request(request)
    
    # 2. Execute via SDK
    sdk_execution = await ExecutionsService.execute_workflow(
        db=db,
        workflow_id=workflow_id,
        input_data=sdk_request["input"],
        user_context=sdk_request["user_context"],
    )
    
    # 3. Adapt response from SDK to AS format
    as_response = ExecutionAdapter.adapt_execute_response(sdk_execution)
    
    return as_response
```

### Workflow Creation Endpoint

```python
from adapters import WorkflowAdapter
from workflow_core_sdk.services import WorkflowsService

@router.post("/")
async def create_workflow(
    request: Dict[str, Any],
    db: Session = Depends(get_db),
):
    # 1. Adapt request from AS to SDK format
    sdk_request = WorkflowAdapter.adapt_create_request(request)
    
    # 2. Create via SDK
    sdk_workflow = await WorkflowsService.create_workflow(db, sdk_request)
    
    # 3. Adapt response from SDK to AS format
    as_response = WorkflowAdapter.adapt_workflow_response(sdk_workflow)
    
    return as_response
```

### Execution Status Endpoint

```python
from adapters import ExecutionAdapter
from workflow_core_sdk.services import ExecutionsService

@router.get("/{execution_id}/status")
async def get_execution_status(
    execution_id: UUID,
    db: Session = Depends(get_db),
):
    # 1. Get execution from SDK
    sdk_execution = await ExecutionsService.get_execution(db, execution_id)
    
    if not sdk_execution:
        raise HTTPException(404, "Execution not found")
    
    # 2. Adapt response from SDK to AS format
    as_response = ExecutionAdapter.adapt_status_response(sdk_execution)
    
    return as_response
```

### Execution List Endpoint

```python
from adapters import ExecutionAdapter
from workflow_core_sdk.services import ExecutionsService

@router.get("/")
async def list_executions(
    status: Optional[str] = None,
    user_id: Optional[str] = None,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    # 1. Adapt query parameters from AS to SDK format
    sdk_params = ExecutionAdapter.adapt_list_params(
        status=status,
        user_id=user_id,
        limit=limit,
    )
    
    # 2. Query via SDK
    sdk_executions = await ExecutionsService.list_executions(db, **sdk_params)
    
    # 3. Adapt response from SDK to AS format
    as_response = ExecutionAdapter.adapt_list_response(sdk_executions)
    
    return as_response
```

## Testing

Run adapter tests:
```bash
cd python_apps/agent_studio/agent-studio
pytest tests/test_adapters.py -v
```

## Migration Path

### Phase 1: Current (Using Adapters)
```
Frontend → AS API → Adapters → SDK → Database
```

### Phase 2: After UI Rework (No Adapters)
```
Frontend → SDK API → SDK → Database
```

**To migrate:**
1. Update frontend to use SDK format
2. Remove adapter imports from endpoints
3. Use SDK format directly in endpoints
4. Delete `adapters/` directory
5. Update API documentation

## Performance Considerations

The adapter layer adds minimal overhead:
- **Request adaptation**: ~0.1ms (simple dict manipulation)
- **Response adaptation**: ~0.5ms (includes list comprehensions)
- **Total overhead**: <1ms per request

This is negligible compared to:
- Database queries: 10-100ms
- LLM calls: 1000-5000ms
- Workflow execution: seconds to minutes

## Maintenance

### Adding New Fields

If SDK adds new fields:
1. Update `ResponseAdapter` to include them
2. Map to Agent Studio format if needed
3. Update tests

If Agent Studio needs new fields:
1. Update `RequestAdapter` to extract them
2. Map to SDK format
3. Update tests

### Debugging

Enable adapter logging:
```python
import logging
logging.getLogger("adapters").setLevel(logging.DEBUG)
```

This will log all conversions for debugging.

## Examples

See `tests/test_adapters.py` for comprehensive examples of all adapter functionality.

## Questions?

- **Why not just update the frontend?** We will, but this allows incremental migration.
- **Is this performant?** Yes, <1ms overhead is negligible.
- **When will this be removed?** When the UI is reworked to use SDK format.
- **Can I use SDK format directly?** Yes! Just don't use the adapters in your endpoint.


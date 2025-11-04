# ExecutionService - Programmatic Workflow Execution

## Overview

The `ExecutionService` provides a service-level API for executing workflows programmatically without requiring HTTP request handling. This is essential for internal components like schedulers, background tasks, and other automated systems that need to trigger workflow executions.

## Problem Statement

Previously, the workflow scheduler was calling `execute_workflow_by_id`, which was a router-level function that:
- Required HTTP request objects
- Handled multipart form data and file uploads
- Performed RBAC validation
- Parsed request headers and bodies

This created an architectural problem where the SDK (which should be a pure library) was depending on router-level code that belonged in the API applications.

## Solution

We extracted the core workflow execution logic into a new `ExecutionService` class that:
- Lives in the SDK at `workflow_core_sdk/services/execution_service.py`
- Provides a clean, programmatic API for workflow execution
- Handles both local and DBOS execution backends
- Supports synchronous and asynchronous execution modes
- Can be used by schedulers, background tasks, and other internal components

## API

### `ExecutionService.execute_workflow()`

```python
async def execute_workflow(
    *,
    workflow_id: str,
    session: Session,
    workflow_engine: Any,  # WorkflowEngine instance
    backend: str = "dbos",
    trigger_payload: Optional[Dict[str, Any]] = None,
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
    organization_id: Optional[str] = None,
    input_data: Optional[Dict[str, Any]] = None,
    metadata: Optional[Dict[str, Any]] = None,
    wait: bool = False,
) -> str:
    """
    Execute a workflow programmatically without HTTP request handling.

    Args:
        workflow_id: ID of the workflow to execute
        session: Database session
        workflow_engine: WorkflowEngine instance
        backend: Execution backend ("dbos" or "local")
        trigger_payload: Trigger data (defaults to webhook trigger with metadata)
        user_id: User ID for execution context
        session_id: Session ID for execution context
        organization_id: Organization ID for execution context
        input_data: Additional input data for the workflow
        metadata: Execution metadata
        wait: Whether to wait for execution to complete

    Returns:
        execution_id: ID of the created execution

    Raises:
        ValueError: If workflow not found or invalid backend
        RuntimeError: If execution fails
    """
```

## Usage Examples

### Scheduler Usage

```python
from workflow_core_sdk.services.execution_service import ExecutionService

# In scheduler tick
await ExecutionService.execute_workflow(
    workflow_id=workflow_id,
    session=db_session,
    workflow_engine=app.state.workflow_engine,
    backend="dbos",
    metadata={"source": "scheduler"},
    wait=False,  # Don't wait for completion
)
```

### Background Task Usage

```python
from workflow_core_sdk import ExecutionService

# Trigger workflow from background task
execution_id = await ExecutionService.execute_workflow(
    workflow_id="my-workflow-id",
    session=session,
    workflow_engine=engine,
    backend="local",
    trigger_payload={
        "kind": "webhook",
        "data": {"event": "user_signup"},
    },
    user_id="user-123",
    metadata={"source": "background_task"},
    wait=True,  # Wait for completion
)
```

### Custom Trigger Payload

```python
# Execute with chat trigger
execution_id = await ExecutionService.execute_workflow(
    workflow_id="chat-workflow",
    session=session,
    workflow_engine=engine,
    backend="local",
    trigger_payload={
        "kind": "chat",
        "current_message": "Hello, world!",
        "history": [],
        "messages": [{"role": "user", "content": "Hello, world!"}],
    },
    wait=False,
)
```

## Architecture

### Before

```
Scheduler → execute_workflow_by_id (router function)
                ↓
            HTTP request parsing
                ↓
            RBAC validation
                ↓
            File upload handling
                ↓
            Core execution logic
```

### After

```
Scheduler → ExecutionService.execute_workflow (service function)
                ↓
            Core execution logic
                ↓
            WorkflowEngine.execute_workflow
```

The router function `execute_workflow_by_id` still exists for HTTP API endpoints, but now internal components use the cleaner `ExecutionService` API.

## Files Changed

### New Files
- `python_packages/workflow-core-sdk/workflow_core_sdk/services/execution_service.py` - New service class
- `python_packages/workflow-core-sdk/workflow_core_sdk/services/__init__.py` - Service exports
- `python_packages/workflow-core-sdk/tests/test_execution_service.py` - Unit tests

### Modified Files
- `python_packages/workflow-core-sdk/workflow_core_sdk/scheduler.py` - Updated to use ExecutionService
- `python_apps/workflow-engine-poc/workflow_engine_poc/scheduler.py` - Updated to use ExecutionService
- `python_packages/workflow-core-sdk/workflow_core_sdk/__init__.py` - Export ExecutionService

### Removed Files
- `python_packages/workflow-core-sdk/workflow_core_sdk/utils/scheduler.py` - Old duplicate with broken imports

## Testing

Run the tests with:

```bash
cd python_packages/workflow-core-sdk
pytest tests/test_execution_service.py -v
```

All 5 tests should pass:
- ✅ test_execute_workflow_not_found
- ✅ test_execute_workflow_invalid_backend
- ✅ test_execute_workflow_local_backend
- ✅ test_execute_workflow_with_trigger_payload
- ✅ test_execute_workflow_default_trigger

## Benefits

1. **Clean Architecture**: SDK no longer depends on router-level code
2. **Reusability**: Can be used by any internal component (schedulers, background tasks, webhooks, etc.)
3. **Testability**: Easy to unit test without mocking HTTP requests
4. **Maintainability**: Single source of truth for programmatic workflow execution
5. **Flexibility**: Supports multiple backends and execution modes

## Migration Guide

If you have code that was calling `execute_workflow_by_id` from non-router contexts:

### Before
```python
from .routers.workflows import execute_workflow_by_id

# Create dummy request object
class DummyRequest:
    def __init__(self, app):
        self.app = app
        self.headers = {"content-type": "application/json"}
    
    async def json(self):
        return {"metadata": {"source": "scheduler"}}

req = DummyRequest(app)
await execute_workflow_by_id(
    workflow_id=workflow_id,
    request=cast(Request, req),
    backend=backend,
    session=session,
    payload=None,
    files=None,
)
```

### After
```python
from workflow_core_sdk.services.execution_service import ExecutionService

await ExecutionService.execute_workflow(
    workflow_id=workflow_id,
    session=session,
    workflow_engine=app.state.workflow_engine,
    backend=backend,
    metadata={"source": "scheduler"},
    wait=False,
)
```

## Future Enhancements

Potential future improvements:
- Add support for workflow execution with approval gates
- Add support for workflow execution with custom step overrides
- Add support for workflow execution with custom timeout configurations
- Add execution result streaming support
- Add execution cancellation support


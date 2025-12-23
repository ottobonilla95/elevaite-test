"""
Workflow management endpoints
"""

import logging
import os
import uuid
import asyncio
from pathlib import Path
from fastapi import (
    APIRouter,
    BackgroundTasks,
    Request,
    HTTPException,
    UploadFile,
    File,
    Form,
    Depends,
    Security,
    Header,
)

from fastapi.responses import StreamingResponse
from typing import Dict, Any, Optional, List

from fastapi.security.api_key import APIKeyHeader
from rbac_sdk import (
    HDR_API_KEY,
    HDR_USER_ID,
    HDR_ORG_ID,
    HDR_ACCOUNT_ID,
    HDR_PROJECT_ID,
)

from sqlmodel import Session
from ..db.database import get_db_session
from ..db.models import WorkflowRead, WorkflowBase
from ..services.workflows_service import WorkflowsService
from ..workflow_engine import WorkflowEngine
from workflow_core_sdk.dbos_impl.workflows import execute_and_persist_dbos_result
from ..db.models import WorkflowExecutionRead, ExecutionStatus
from workflow_core_sdk.db.service import DatabaseService
from ..streaming import (
    stream_manager,
    create_sse_stream,
    get_sse_headers,
    create_status_event,
)

from ..execution_context import ExecutionContext, UserContext
from ..schemas.workflows import WorkflowConfig, ExecutionRequest
from ..util import api_key_or_user_guard

# NOTE: Pydantic BaseModel not strictly required for these new routes


logger = logging.getLogger(__name__)

# Trigger defaults
MAX_FILES_DEFAULT = 10
PER_FILE_MB_DEFAULT = 20
TOTAL_MB_DEFAULT = 60
# Swagger/OpenAPI: expose API key header for testing in docs
api_key_header = APIKeyHeader(name=HDR_API_KEY, auto_error=False)

ALLOWED_MIME_DEFAULT = {
    "doc": [
        "application/pdf",
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "text/plain",
        "text/markdown",
    ],
    "image": ["image/png", "image/jpeg", "image/webp"],
    "audio": ["audio/mpeg", "audio/wav", "audio/mp4"],
}


router = APIRouter(prefix="/workflows", tags=["workflows"])


@router.post(
    "/{workflow_id}/execute",
    response_model=WorkflowExecutionRead,
    dependencies=[Depends(api_key_or_user_guard("execute_workflow"))],
)
@router.post(
    "/{workflow_id}/execute/{backend}",
    response_model=WorkflowExecutionRead,
    dependencies=[Depends(api_key_or_user_guard("execute_workflow"))],
)
async def execute_workflow_by_id(
    workflow_id: str,
    request: Request,
    background_tasks: BackgroundTasks,
    session: Session = Depends(get_db_session),
    payload: Optional[str] = Form(None),
    files: Optional[list[UploadFile]] = File(None),
    backend: Optional[str] = None,
    # RBAC headers for Swagger UI testing
    api_key: Optional[str] = Security(api_key_header),
    user_id: Optional[str] = Header(default=None, alias=HDR_USER_ID),
    org_id: Optional[str] = Header(default=None, alias=HDR_ORG_ID),
    project_id: Optional[str] = Header(default=None, alias=HDR_ACCOUNT_ID),
    account_id: Optional[str] = Header(default=None, alias=HDR_ACCOUNT_ID),
) -> WorkflowExecutionRead:
    """Create a WorkflowExecution and kick off execution by workflow id.

    Supports both JSON and multipart/form-data payloads. For multipart, send:
    - payload: JSON string for non-file fields (trigger, user/session/org ids)
    - files[]: attachments for chat/file triggers

    JSON body schema when not using multipart: ExecutionRequest
    """
    try:
        workflow_engine: WorkflowEngine = request.app.state.workflow_engine
        # Ensure workflow exists
        workflow = WorkflowsService.get_workflow_config(session, workflow_id)
        if not workflow:
            raise HTTPException(status_code=404, detail="Workflow not found")

        # Ensure workflow_id is in the config (needed for SSE streaming)
        if "workflow_id" not in workflow:
            workflow["workflow_id"] = workflow_id

        # Parse incoming body
        content_type = request.headers.get("content-type", "").lower()
        body_data: Dict[str, Any] = {}
        if payload is not None or files is not None or "multipart/form-data" in content_type:
            # Multipart path
            import json

            if payload is None:
                raise HTTPException(status_code=400, detail="Missing 'payload' form field")
            try:
                body_data = json.loads(payload)
            except Exception:
                raise HTTPException(status_code=400, detail="Invalid JSON in 'payload' form field")
        else:
            # JSON path
            parsed = await request.json()
            try:
                # Validate into our documented schema; continue using dict for existing engine usage
                _req_model = ExecutionRequest.model_validate(parsed)
                body_data = _req_model.model_dump()
            except Exception:
                # Fall back to raw dict for backward-compat
                body_data = parsed

        user_id = body_data.get("user_id")
        session_id_val = body_data.get("session_id")
        organization_id = body_data.get("organization_id")
        input_data = body_data.get("input_data", {})
        metadata = body_data.get("metadata", {})
        wait = bool(body_data.get("wait", False))

        # Extract trigger config from workflow (enforce presence)
        steps = workflow.get("steps", [])
        trigger_cfg = next((s for s in steps if s.get("step_type") == "trigger"), None)
        if not trigger_cfg:
            raise HTTPException(status_code=400, detail="Workflow is missing required 'trigger' step")
        trigger_params = trigger_cfg.get("parameters", {})
        kind = (
            body_data.get("trigger", {}).get("kind") or body_data.get("kind") or trigger_params.get("kind") or "webhook"
        ).lower()

        # Limits and MIME rules
        max_files = int(trigger_params.get("max_files", MAX_FILES_DEFAULT))
        per_file_mb = int(trigger_params.get("per_file_size_mb", PER_FILE_MB_DEFAULT))
        total_mb = int(trigger_params.get("total_size_mb", TOTAL_MB_DEFAULT))
        per_file_limit = per_file_mb * 1024 * 1024
        total_limit = total_mb * 1024 * 1024
        allowed_modalities = trigger_params.get("allowed_modalities") or (
            ["text", "image", "audio"] if kind == "chat" else ["doc"]
        )
        allowed_mime_types = set(trigger_params.get("allowed_mime_types") or [])
        if "doc" in allowed_modalities:
            allowed_mime_types.update(ALLOWED_MIME_DEFAULT["doc"])
        if "image" in allowed_modalities:
            allowed_mime_types.update(ALLOWED_MIME_DEFAULT["image"])
        if "audio" in allowed_modalities:
            allowed_mime_types.update(ALLOWED_MIME_DEFAULT["audio"])

        # Handle attachments if multipart
        attachments = []
        total_size = 0
        if files:
            if len(files) > max_files:
                raise HTTPException(status_code=400, detail=f"Too many files (max {max_files})")
            upload_root = Path("uploads")
            upload_root.mkdir(exist_ok=True)
            import uuid as uuid_module

            run_dir = upload_root / str(uuid_module.uuid4())
            run_dir.mkdir(exist_ok=True)
            for up in files:
                mime = up.content_type or "application/octet-stream"
                if allowed_mime_types and mime not in allowed_mime_types:
                    raise HTTPException(status_code=400, detail=f"Disallowed MIME type: {mime}")
                content = await up.read()
                size = len(content)
                if size > per_file_limit:
                    raise HTTPException(status_code=400, detail=f"File too large (> {per_file_mb} MB): {up.filename}")
                total_size += size
                if total_size > total_limit:
                    raise HTTPException(status_code=400, detail=f"Total attachment size exceeds {total_mb} MB")
                dest = run_dir / (up.filename or "upload.bin")
                with open(dest, "wb") as f:
                    f.write(content)
                attachments.append(
                    {
                        "name": up.filename,
                        "mime": mime,
                        "size_bytes": size,
                        "path": str(dest),
                    }
                )

        # Build trigger payload for engine
        trigger_payload = body_data.get("trigger", {})
        if kind == "chat":
            # Allow aliasing 'query' -> current_message for convenience
            trigger_payload = {
                "kind": "chat",
                "current_message": (
                    (trigger_payload.get("current_message") if isinstance(trigger_payload, dict) else None)
                    or body_data.get("current_message")
                    or body_data.get("query")
                ),
                "history": (
                    (trigger_payload.get("history") if isinstance(trigger_payload, dict) else None)
                    or body_data.get("history", [])
                ),
                # Accept an optional pre-assembled messages array of {role, content}
                "messages": (
                    (trigger_payload.get("messages") if isinstance(trigger_payload, dict) else None)
                    or body_data.get("messages")
                ),
                "attachments": attachments
                or (trigger_payload.get("attachments", []) if isinstance(trigger_payload, dict) else []),
                "need_history": bool(trigger_params.get("need_history", True)),
            }
            # If messages missing but current_message provided, synthesize a single user message
            if not trigger_payload.get("messages") and trigger_payload.get("current_message"):
                trigger_payload["messages"] = [{"role": "user", "content": trigger_payload["current_message"]}]
        elif kind == "file":
            trigger_payload = {
                "kind": "file",
                "attachments": attachments,
            }
        else:
            # webhook or other kinds: pass-through
            trigger_payload = {
                "kind": kind,
                "data": body_data.get("data", body_data),
            }

        # Persist execution first
        execution_id = WorkflowsService.create_execution(
            session,
            {
                "workflow_id": workflow_id,
                "user_id": user_id,
                "session_id": session_id_val,
                "organization_id": organization_id,
                "input_data": input_data,
                "metadata": metadata,
            },
        )

        # Hydrate execution context from stored workflow config
        user_context = UserContext(
            user_id=user_id,
            session_id=session_id_val,
            organization_id=organization_id,
        )
        execution_context = ExecutionContext(
            workflow_config=workflow,
            user_context=user_context,
            workflow_engine=workflow_engine,
            execution_id=execution_id,
        )

        # Seed raw trigger payload + input_data
        execution_context.step_io_data["trigger_raw"] = trigger_payload

        # Persist initial chat messages to the DB under the first agent step so they are queryable
        try:
            if isinstance(trigger_payload, dict) and trigger_payload.get("kind") == "chat":
                initial_msgs = trigger_payload.get("messages") or []
                if initial_msgs:
                    # Choose first agent_execution step to scope these messages
                    first_agent_step_id = None
                    for _s in execution_context.steps_config:
                        if _s.get("step_type") == "agent_execution":
                            first_agent_step_id = _s.get("step_id")
                            break
                    if first_agent_step_id:
                        for m in initial_msgs:
                            if isinstance(m, dict) and m.get("role") and m.get("content"):
                                WorkflowsService.create_agent_message(
                                    session,
                                    execution_id=execution_id,
                                    step_id=first_agent_step_id,
                                    role=str(m["role"]),
                                    content=str(m["content"]),
                                    metadata=None,
                                    user_id=user_id,
                                    session_id=session_id_val,
                                )
        except Exception as _seed_e:
            logger.warning(f"Failed to persist initial trigger messages: {_seed_e}")

        if input_data:
            execution_context.step_io_data.update(input_data)

        # Decide backend: DBOS vs local engine
        # Default to local in test mode, dbos otherwise
        default_backend = "local" if os.getenv("TESTING") else "dbos"
        chosen_backend = (backend or body_data.get("backend") or body_data.get("execution_backend") or default_backend).lower()
        if chosen_backend not in ("dbos", "local"):
            raise HTTPException(status_code=400, detail=f"Invalid execution backend: {chosen_backend}")

        if chosen_backend == "dbos":
            # Execute via DBOS adapter and persist normalized results using helper
            try:
                execution_id = await execute_and_persist_dbos_result(
                    session,
                    DatabaseService(),
                    workflow=workflow,
                    trigger_payload=trigger_payload,
                    user_context={
                        "user_id": user_id,
                        "session_id": session_id_val,
                        "organization_id": organization_id,
                    },
                    execution_id=execution_id,
                    wait=wait,
                    metadata=metadata,
                    chosen_backend=chosen_backend,
                )
            except RuntimeError as e:
                raise HTTPException(status_code=502, detail=str(e))
        else:
            # Local backend: async or sync based on 'wait'
            if wait:
                await workflow_engine.execute_workflow(execution_context)
            else:
                # Use background_tasks for async execution
                background_tasks.add_task(workflow_engine.execute_workflow, execution_context)

        # Commit and refresh session to see updates from workflow engine (which uses its own session)
        # The workflow engine commits in a separate session, so we need to end our transaction
        # to see those changes in SQLite (which has different isolation than PostgreSQL)
        session.commit()

        # Return the execution as response
        created = WorkflowsService.get_execution(session, execution_id)
        assert created is not None
        return WorkflowExecutionRead(
            id=uuid.UUID(created["execution_id"]),
            workflow_id=uuid.UUID(created["workflow_id"]),
            user_id=created.get("user_id"),
            session_id=created.get("session_id"),
            organization_id=created.get("organization_id"),
            status=ExecutionStatus(created["status"]),
            input_data=created.get("input_data", {}),
            output_data=created.get("output_data", {}),
            step_io_data=created.get("step_io_data", {}),
            execution_metadata=created.get("metadata", {}),
            error_message=created.get("error_message"),
            started_at=created.get("started_at"),
            completed_at=created.get("completed_at"),
            execution_time_seconds=created.get("execution_time_seconds"),
            created_at=created["created_at"],
            updated_at=created.get("updated_at"),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to execute workflow {workflow_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{workflow_id}/stream", dependencies=[Depends(api_key_or_user_guard("view_workflow"))])
async def stream_workflow_execution(
    workflow_id: str,
    request: Request,
    session: Session = Depends(get_db_session),
    execution_id: Optional[str] = None,
    # RBAC headers for Swagger UI testing
    api_key: Optional[str] = Security(api_key_header),
    user_id: Optional[str] = Header(default=None, alias=HDR_USER_ID),
    org_id: Optional[str] = Header(default=None, alias=HDR_ORG_ID),
    project_id: Optional[str] = Header(default=None, alias=HDR_PROJECT_ID),
    account_id: Optional[str] = Header(default=None, alias=HDR_ACCOUNT_ID),
) -> StreamingResponse:
    """
    Stream real-time updates for workflow executions using Server-Sent Events (SSE).

    If execution_id is provided, streams updates for that specific execution.
    Otherwise, streams updates for all executions of the workflow.
    """
    try:
        workflow_engine: WorkflowEngine = request.app.state.workflow_engine
        # Verify workflow exists
        workflow = WorkflowsService.get_workflow_config(session, workflow_id)
        if not workflow:
            raise HTTPException(status_code=404, detail="Workflow not found")

        # Create a queue for this streaming connection
        queue = asyncio.Queue(maxsize=1000)

        async def event_generator():
            try:
                # Add this connection to the stream manager
                stream_manager.add_workflow_stream(workflow_id, queue)

                # Emit an immediate 'connected' event so clients receive a first chunk promptly
                connected_event = create_status_event(
                    execution_id="system",
                    status="connected",
                    workflow_id=workflow_id,
                )
                yield connected_event.to_sse()

                # If specific execution_id provided, also listen to that execution
                if execution_id:
                    stream_manager.add_execution_stream(execution_id, queue)

                    # Send initial status for the specific execution
                    execution_context = await workflow_engine.get_execution_context(execution_id)
                    if execution_context:
                        initial_event = create_status_event(
                            execution_id=execution_id,
                            status=execution_context.status.value,
                            workflow_id=workflow_id,
                            step_count=len(execution_context.steps_config),
                            completed_steps=len(execution_context.completed_steps),
                            failed_steps=len(execution_context.failed_steps),
                        )
                        yield initial_event.to_sse()
                else:
                    # Send status for latest execution of the workflow
                    executions = WorkflowsService.list_executions(session, workflow_id=workflow_id, limit=1, offset=0)
                    if executions:
                        latest_execution = executions[0]
                        initial_event = create_status_event(
                            execution_id=str(latest_execution.get("execution_id", "")),
                            status=latest_execution.get("status", "unknown"),
                            workflow_id=workflow_id,
                            from_db=True,
                        )
                        yield initial_event.to_sse()

                # Stream events from the queue
                # Use a shorter heartbeat for workflow streams to ensure a second chunk arrives promptly
                async for event_data in create_sse_stream(queue, heartbeat_interval=2, max_events=1000):
                    yield event_data

            except asyncio.CancelledError:
                logger.debug(f"Streaming cancelled for workflow {workflow_id}")
            except Exception as e:
                logger.error(f"Error in workflow stream {workflow_id}: {e}")
                # Send error event
                error_event = create_status_event(execution_id="system", status="error", workflow_id=workflow_id, error=str(e))
                yield error_event.to_sse()
            finally:
                # Clean up the connections
                stream_manager.remove_workflow_stream(workflow_id, queue)
                if execution_id:
                    stream_manager.remove_execution_stream(execution_id, queue)

        return StreamingResponse(event_generator(), media_type="text/event-stream", headers=get_sse_headers())

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start workflow stream {workflow_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/validate", dependencies=[Depends(api_key_or_user_guard("view_workflow"))])
async def validate_workflow(
    workflow_config: WorkflowBase,
    request: Request,
    # RBAC headers for Swagger UI testing
    api_key: Optional[str] = Security(api_key_header),
    user_id: Optional[str] = Header(default=None, alias=HDR_USER_ID),
    org_id: Optional[str] = Header(default=None, alias=HDR_ORG_ID),
    project_id: Optional[str] = Header(default=None, alias=HDR_PROJECT_ID),
    account_id: Optional[str] = Header(default=None, alias=HDR_ACCOUNT_ID),
):
    """Validate a workflow configuration"""
    try:
        workflow_engine: WorkflowEngine = request.app.state.workflow_engine
        validation_result = await workflow_engine.validate_workflow(workflow_config.model_dump())

        return validation_result
    except Exception as e:
        logger.error(f"Failed to validate workflow: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=List[WorkflowRead], dependencies=[Depends(api_key_or_user_guard("view_workflow"))])
async def list_workflows(
    session: Session = Depends(get_db_session),
    limit: int = 100,
    offset: int = 0,
    # Swagger inputs for testing headers
    api_key: Optional[str] = Security(api_key_header),
    user_id: Optional[str] = Header(default=None, alias=HDR_USER_ID),
    org_id: Optional[str] = Header(default=None, alias=HDR_ORG_ID),
    project_id: Optional[str] = Header(default=None, alias=HDR_PROJECT_ID),
    account_id: Optional[str] = Header(default=None, alias=HDR_ACCOUNT_ID),
) -> List[WorkflowRead]:
    """List all saved workflows returning ORM entities"""
    try:
        workflows = WorkflowsService.list_workflows_entities(session, limit=limit, offset=offset)
        # Convert Workflow entities to WorkflowRead schemas
        return [WorkflowRead.model_validate(workflow) for workflow in workflows]
    except Exception as e:
        logger.error(f"Failed to list workflows: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{workflow_id}", dependencies=[Depends(api_key_or_user_guard("delete_workflow"))])
async def delete_workflow(
    workflow_id: str,
    session: Session = Depends(get_db_session),
    # RBAC headers for Swagger UI testing
    api_key: Optional[str] = Security(api_key_header),
    user_id: Optional[str] = Header(default=None, alias=HDR_USER_ID),
    org_id: Optional[str] = Header(default=None, alias=HDR_ORG_ID),
    project_id: Optional[str] = Header(default=None, alias=HDR_PROJECT_ID),
    account_id: Optional[str] = Header(default=None, alias=HDR_ACCOUNT_ID),
):
    """Delete a workflow configuration"""
    try:
        deleted = WorkflowsService.delete_workflow(session, workflow_id)

        if not deleted:
            raise HTTPException(status_code=404, detail="Workflow not found")

        return {"message": f"Workflow {workflow_id} deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete workflow: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# New SQLModel-based endpoints


@router.post("/", response_model=WorkflowRead, dependencies=[Depends(api_key_or_user_guard("create_workflow"))])
async def create_workflow(
    workflow_data: WorkflowConfig,
    session: Session = Depends(get_db_session),
    # RBAC headers for Swagger UI testing
    api_key: Optional[str] = Security(api_key_header),
    user_id: Optional[str] = Header(default=None, alias=HDR_USER_ID),
    org_id: Optional[str] = Header(default=None, alias=HDR_ORG_ID),
    project_id: Optional[str] = Header(default=None, alias=HDR_PROJECT_ID),
    account_id: Optional[str] = Header(default=None, alias=HDR_ACCOUNT_ID),
) -> WorkflowRead:
    """Create a new workflow using SQLModel and return the SQLModel entity.

    Request body schema: WorkflowConfig
    """
    try:
        workflow_obj = WorkflowsService.create_workflow(session, workflow_data.model_dump())
        return workflow_obj  # type: ignore[return-value]

    except Exception as e:
        logger.error(f"Failed to create workflow: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{workflow_id}", response_model=WorkflowRead, dependencies=[Depends(api_key_or_user_guard("view_workflow"))])
async def get_workflow_by_id(
    workflow_id: str,
    session: Session = Depends(get_db_session),
    # RBAC headers for Swagger UI testing
    api_key: Optional[str] = Security(api_key_header),
    user_id: Optional[str] = Header(default=None, alias=HDR_USER_ID),
    org_id: Optional[str] = Header(default=None, alias=HDR_ORG_ID),
    project_id: Optional[str] = Header(default=None, alias=HDR_PROJECT_ID),
    account_id: Optional[str] = Header(default=None, alias=HDR_ACCOUNT_ID),
) -> WorkflowRead:
    """Get a workflow by ID using SQLModel and return the SQLModel entity."""
    try:
        workflow_obj = WorkflowsService.get_workflow_entity(session, workflow_id)
        if not workflow_obj:
            raise HTTPException(status_code=404, detail="Workflow not found")
        # Return ORM entity; FastAPI will serialize it to WorkflowRead
        return workflow_obj  # type: ignore[return-value]

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get workflow {workflow_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

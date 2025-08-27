"""
Workflow management endpoints
"""

import logging
import uuid
import asyncio
from pathlib import Path
from fastapi import (
    APIRouter,
    Request,
    HTTPException,
    UploadFile,
    File,
    Form,
    Depends,
    BackgroundTasks,
)
from fastapi.responses import StreamingResponse
from typing import Dict, Any, Optional, List
from datetime import datetime

from sqlmodel import Session, select
from ..db.database import get_db_session
from ..db.models import Workflow, WorkflowRead, WorkflowBase
from ..db.service import DatabaseService
from ..workflow_engine import WorkflowEngine
from ..db.models import WorkflowExecutionRead, ExecutionStatus

from ..execution_context import ExecutionContext, UserContext


# NOTE: Pydantic BaseModel not strictly required for these new routes


logger = logging.getLogger(__name__)

# Trigger defaults
MAX_FILES_DEFAULT = 10
PER_FILE_MB_DEFAULT = 20
TOTAL_MB_DEFAULT = 60
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


@router.post("/{workflow_id}/execute", response_model=WorkflowExecutionRead)
async def execute_workflow_by_id(
    workflow_id: str,
    request: Request,
    session: Session = Depends(get_db_session),
    payload: Optional[str] = Form(None),
    files: Optional[list[UploadFile]] = File(None),
) -> WorkflowExecutionRead:
    """Create a WorkflowExecution and kick off execution by workflow id.

    Supports both JSON and multipart/form-data payloads. For multipart, send:
    - payload: JSON string for non-file fields (trigger, user/session/org ids)
    - files[]: attachments for chat/file triggers
    """
    try:
        workflow_engine: WorkflowEngine = request.app.state.workflow_engine
        db_service = DatabaseService()

        # Ensure workflow exists
        workflow = db_service.get_workflow(session, workflow_id)
        if not workflow:
            raise HTTPException(status_code=404, detail="Workflow not found")

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
            body_data = await request.json()

        user_id = body_data.get("user_id")
        session_id_val = body_data.get("session_id")
        organization_id = body_data.get("organization_id")
        input_data = body_data.get("input_data", {})
        metadata = body_data.get("metadata", {})

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
        allowed_modalities = trigger_params.get("allowed_modalities", ["text", "image", "audio"]) if kind == "chat" else ["doc"]
        allowed_mime_types = set(trigger_params.get("allowed_mime_types", []))
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
            trigger_payload = {
                "kind": "chat",
                "current_message": trigger_payload.get("current_message") or body_data.get("current_message"),
                "history": trigger_payload.get("history") or body_data.get("history", []),
                "attachments": attachments or trigger_payload.get("attachments", []),
                "need_history": bool(trigger_params.get("need_history", True)),
            }
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
        execution_id = db_service.create_execution(
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
        if input_data:
            execution_context.step_io_data.update(input_data)

        # Kick off in background
        asyncio.create_task(workflow_engine.execute_workflow(execution_context))

        # Return the created execution as response
        created = db_service.get_execution(session, execution_id)
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


@router.get("/{workflow_id}/stream")
async def stream_workflow_execution(workflow_id: str, session: Session = Depends(get_db_session)):
    """Simple streaming endpoint that polls DB for the latest execution of the workflow and streams status updates."""
    db_service = DatabaseService()

    async def event_generator():
        last_status = None
        while True:
            # Fetch the most recent execution for the workflow
            executions = db_service.list_executions(session, workflow_id=workflow_id, limit=1, offset=0)
            if executions:
                exe = executions[0]
                status = exe.get("status")
                if status != last_status:
                    last_status = status
                    yield f"data: {exe}\n\n"
                if status in {"completed", "failed", "cancelled", "timeout"}:
                    break
            await asyncio.sleep(1)

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.post("/validate")
async def validate_workflow(workflow_config: WorkflowBase, request: Request):
    """Validate a workflow configuration"""
    try:
        workflow_engine: WorkflowEngine = request.app.state.workflow_engine
        validation_result = await workflow_engine.validate_workflow(workflow_config.model_dump())

        return validation_result
    except Exception as e:
        logger.error(f"Failed to validate workflow: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/config")
async def save_workflow(
    workflow_config: WorkflowBase,
    session: Session = Depends(get_db_session),
):
    """Save a workflow configuration to the database"""
    try:
        db_service = DatabaseService()
        workflow_id = f"workflow-{workflow_config.name.lower().replace(' ', '-')}"
        workflow_id = db_service.save_workflow(session, workflow_id, workflow_config.model_dump())

        return {"workflow_id": workflow_id, "message": "Workflow saved successfully"}

    except Exception as e:
        logger.error(f"Failed to save workflow: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/config/{workflow_id}")
async def get_workflow(workflow_id: str, session: Session = Depends(get_db_session)):
    """Get a workflow configuration by ID"""
    try:
        db_service = DatabaseService()
        workflow = db_service.get_workflow(session, workflow_id)

        if not workflow:
            raise HTTPException(status_code=404, detail="Workflow not found")

        return {"workflow_id": workflow_id, "workflow_config": workflow}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get workflow: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=List[WorkflowRead])
async def list_workflows(session: Session = Depends(get_db_session), limit: int = 100, offset: int = 0) -> List[WorkflowRead]:
    """List all saved workflows returning ORM entities"""
    try:
        db_service = DatabaseService()
        workflows = db_service.list_workflow_entities(session, limit=limit, offset=offset)
        # Convert Workflow entities to WorkflowRead schemas
        return [WorkflowRead.model_validate(workflow) for workflow in workflows]
    except Exception as e:
        logger.error(f"Failed to list workflows: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{workflow_id}")
async def delete_workflow(workflow_id: str, session: Session = Depends(get_db_session)):
    """Delete a workflow configuration"""
    try:
        db_service = DatabaseService()
        deleted = db_service.delete_workflow(session, workflow_id)

        if not deleted:
            raise HTTPException(status_code=404, detail="Workflow not found")

        return {"message": f"Workflow {workflow_id} deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete workflow: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/execute-with-file")
async def execute_workflow_with_file(
    request: Request,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    workflow_config: str = Form(...),
    user_id: Optional[str] = Form("file_user"),
):
    """Execute a workflow with an uploaded file"""
    try:
        import json
        from pathlib import Path

        # Parse workflow config
        workflow_data = json.loads(workflow_config)
        workflow_config_obj = WorkflowBase.model_validate(workflow_data)

        # Save uploaded file
        upload_dir = Path("uploads")
        upload_dir.mkdir(exist_ok=True)
        file_path = f"{upload_dir}/{file.filename}"

        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)

        # Build user and execution context directly
        workflow_engine: WorkflowEngine = request.app.state.workflow_engine
        session_id_val = f"file-session-{datetime.now().isoformat()}"
        user_context = UserContext(
            user_id=user_id,
            session_id=session_id_val,
            organization_id="file-org",
        )

        execution_context = ExecutionContext(
            workflow_config=workflow_config_obj.model_dump(),
            user_context=user_context,
            workflow_engine=workflow_engine,
        )
        execution_context.step_io_data["file_upload"] = {
            "file_path": str(file_path),
            "filename": file.filename,
        }

        # Start execution in background
        background_tasks.add_task(workflow_engine.execute_workflow, execution_context)

        return {
            "execution_id": execution_context.execution_id,
            "status": "started",
            "message": f"Workflow execution started with file: {file.filename}",
            "started_at": datetime.now().isoformat(),
        }

    except Exception as e:
        logger.error(f"Failed to execute workflow with file: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# New SQLModel-based endpoints


@router.post("/", response_model=WorkflowRead)
async def create_workflow(workflow_data: Dict[str, Any], session: Session = Depends(get_db_session)) -> WorkflowRead:
    """Create a new workflow using SQLModel and return the SQLModel entity."""
    try:
        db_service = DatabaseService()

        import uuid as uuid_module

        workflow_id = str(uuid_module.uuid4())

        # Persist via service (upsert by id), then fetch ORM entity
        db_service.save_workflow(session, workflow_id, workflow_data)
        from uuid import UUID

        workflow_obj = session.exec(select(Workflow).where(Workflow.id == UUID(workflow_id))).first()
        if not workflow_obj:
            raise HTTPException(status_code=500, detail="Failed to retrieve saved workflow entity")

        return workflow_obj  # type: ignore[return-value]

    except Exception as e:
        logger.error(f"Failed to create workflow: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{workflow_id}", response_model=WorkflowRead)
async def get_workflow_by_id(workflow_id: str, session: Session = Depends(get_db_session)) -> WorkflowRead:
    """Get a workflow by ID using SQLModel and return the SQLModel entity."""
    try:
        from uuid import UUID

        workflow_obj = session.exec(select(Workflow).where(Workflow.id == UUID(workflow_id))).first()
        if not workflow_obj:
            raise HTTPException(status_code=404, detail="Workflow not found")

        # Return ORM entity; FastAPI will serialize it to WorkflowRead
        return workflow_obj  # type: ignore[return-value]

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get workflow {workflow_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

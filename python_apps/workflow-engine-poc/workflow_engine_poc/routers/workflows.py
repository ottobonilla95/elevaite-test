"""
Workflow management endpoints
"""

import logging
import uuid
from fastapi import (
    APIRouter,
    Request,
    HTTPException,
    BackgroundTasks,
    UploadFile,
    File,
    Form,
)
from typing import Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel

from fastapi import Depends
from sqlmodel import Session
from ..db.database import get_db_session
from ..db.models import WorkflowRead, WorkflowBase
from ..db.service import DatabaseService
from ..workflow_engine import WorkflowEngine
from ..execution_context import ExecutionContext, UserContext


class ExecutionRequest(BaseModel):
    workflow_config: WorkflowBase
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    organization_id: Optional[str] = None
    input_data: Dict[str, Any] = {}


class ExecutionResponse(BaseModel):
    execution_id: str
    status: str
    message: str
    started_at: str


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/workflows", tags=["workflows"])


@router.post("/execute", response_model=ExecutionResponse)
async def execute_workflow(
    request: ExecutionRequest,
    background_tasks: BackgroundTasks,
    app_request: Request,
):
    """
    Execute a workflow configuration.

    This is the main endpoint that accepts a workflow configuration
    and executes it using the unified execution engine.
    """
    try:
        workflow_engine: WorkflowEngine = app_request.app.state.workflow_engine

        # Create user context
        user_context = UserContext(
            user_id=request.user_id,
            session_id=request.session_id,
            organization_id=request.organization_id,
        )

        # Create execution context
        execution_context = ExecutionContext(
            workflow_config=request.workflow_config.model_dump(),
            user_context=user_context,
            workflow_engine=workflow_engine,
        )
        # Include any input_data at top-level
        if request.input_data:
            execution_context.step_io_data.update(request.input_data)

        # Start execution in background
        background_tasks.add_task(workflow_engine.execute_workflow, execution_context)

        return ExecutionResponse(
            execution_id=execution_context.execution_id,
            status="started",
            message="Workflow execution started",
            started_at=datetime.now().isoformat(),
        )

    except Exception as e:
        logger.error(f"Failed to start workflow execution: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/validate")
async def validate_workflow(workflow_config: WorkflowBase, request: Request):
    """Validate a workflow configuration"""
    try:
        workflow_engine: WorkflowEngine = request.app.state.workflow_engine
        validation_result = await workflow_engine.validate_workflow(
            workflow_config.model_dump()
        )

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
        workflow_id = f"workflow-{workflow_config.name.lower().replace(' ', '-') }"
        workflow_id = db_service.save_workflow(
            session, workflow_id, workflow_config.model_dump()
        )

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


@router.get("/")
async def list_workflows(
    session: Session = Depends(get_db_session), limit: int = 100, offset: int = 0
):
    """List all saved workflows"""
    try:
        db_service = DatabaseService()
        workflows = db_service.list_workflows(session, limit=limit, offset=offset)

        return {
            "workflows": workflows,
            "total": len(workflows),
            "limit": limit,
            "offset": offset,
        }
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

        # Create execution request
        exec_request = ExecutionRequest(
            workflow_config=workflow_config_obj,
            user_id=user_id,
            session_id=f"file-session-{datetime.now().isoformat()}",
            organization_id="file-org",
            input_data={"file_path": str(file_path), "filename": file.filename},
        )

        # Execute workflow
        workflow_engine: WorkflowEngine = request.app.state.workflow_engine
        user_context = UserContext(
            user_id=exec_request.user_id,
            session_id=exec_request.session_id,
            organization_id=exec_request.organization_id,
        )

        execution_context = ExecutionContext(
            workflow_config=exec_request.workflow_config.model_dump(),
            user_context=user_context,
            workflow_engine=workflow_engine,
        )
        execution_context.step_io_data["file_upload"] = {
            "file_path": str(file_path),
            "filename": file.filename,
        }

        # Start execution in background
        background_tasks.add_task(workflow_engine.execute_workflow, execution_context)

        return ExecutionResponse(
            execution_id=execution_context.execution_id,
            status="started",
            message=f"Workflow execution started with file: {file.filename}",
            started_at=datetime.now().isoformat(),
        )

    except Exception as e:
        logger.error(f"Failed to execute workflow with file: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# New SQLModel-based endpoints
from fastapi import Depends
from sqlmodel import Session
from ..db.service import DatabaseService


@router.post("/", response_model=WorkflowRead)
async def create_workflow(
    workflow_data: Dict[str, Any], session: Session = Depends(get_db_session)
) -> WorkflowRead:
    """Create a new workflow using SQLModel"""
    try:
        db_service = DatabaseService()

        # Generate a new workflow ID
        import uuid

        workflow_id = str(uuid.uuid4())

        # Save the workflow
        saved_id = db_service.save_workflow(session, workflow_id, workflow_data)

        # Get the saved workflow
        saved_workflow = db_service.get_workflow(session, saved_id)
        if not saved_workflow:
            raise HTTPException(
                status_code=500, detail="Failed to retrieve saved workflow"
            )

        # Convert to response model
        return WorkflowRead(
            id=1,  # This would come from the database
            uuid=uuid.UUID(workflow_id),
            workflow_id=uuid.UUID(workflow_id),
            name=saved_workflow.get("name", ""),
            description=saved_workflow.get("description"),
            version=saved_workflow.get("version", "1.0.0"),
            execution_pattern=saved_workflow.get("execution_pattern", "sequential"),
            configuration=saved_workflow.get("configuration", {}),
            global_config=saved_workflow.get("global_config", {}),
            tags=saved_workflow.get("tags", []),
            timeout_seconds=saved_workflow.get("timeout_seconds"),
            status=saved_workflow.get("status", "draft"),
            created_by=saved_workflow.get("created_by"),
            created_at=datetime.now().isoformat(),
            updated_at=None,
        )

    except Exception as e:
        logger.error(f"Failed to create workflow: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{workflow_id}", response_model=WorkflowRead)
async def get_workflow_by_id(
    workflow_id: str, session: Session = Depends(get_db_session)
) -> WorkflowRead:
    """Get a workflow by ID using SQLModel"""
    try:
        db_service = DatabaseService()
        workflow = db_service.get_workflow(session, workflow_id)

        if not workflow:
            raise HTTPException(status_code=404, detail="Workflow not found")

        # Convert to response model (simplified for now)
        return WorkflowRead(
            id=1,
            uuid=uuid.UUID(workflow_id),
            workflow_id=uuid.UUID(workflow_id),
            name=workflow.get("name", ""),
            description=workflow.get("description"),
            version=workflow.get("version", "1.0.0"),
            execution_pattern=workflow.get("execution_pattern", "sequential"),
            configuration=workflow.get("configuration", {}),
            global_config=workflow.get("global_config", {}),
            tags=workflow.get("tags", []),
            timeout_seconds=workflow.get("timeout_seconds"),
            status=workflow.get("status", "draft"),
            created_by=workflow.get("created_by"),
            created_at=datetime.now().isoformat(),
            updated_at=None,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get workflow {workflow_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

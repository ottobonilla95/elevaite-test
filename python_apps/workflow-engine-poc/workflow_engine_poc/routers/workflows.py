"""
Workflow management endpoints
"""
import logging
from fastapi import APIRouter, Request, HTTPException, BackgroundTasks, UploadFile, File, Form
from typing import Dict, Any, Optional
from datetime import datetime

from ..models import WorkflowConfig, ExecutionRequest, ExecutionResponse
from ..workflow_engine import WorkflowEngine
from ..execution_context import ExecutionContext, UserContext
from ..database import get_database

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/workflows", tags=["workflows"])


@router.post("/execute", response_model=ExecutionResponse)
async def execute_workflow(
    request: ExecutionRequest, background_tasks: BackgroundTasks, app_request: Request
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
        )

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
async def validate_workflow(workflow_config: WorkflowConfig, request: Request):
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


@router.post("/")
async def save_workflow(workflow_config: WorkflowConfig, request: Request):
    """Save a workflow configuration to the database"""
    try:
        database = request.app.state.database
        workflow_id = (
            workflow_config.workflow_id
            or f"workflow-{workflow_config.name.lower().replace(' ', '-')}"
        )
        workflow_id = await database.save_workflow(
            workflow_id, workflow_config.model_dump()
        )

        return {"workflow_id": workflow_id, "message": "Workflow saved successfully"}

    except Exception as e:
        logger.error(f"Failed to save workflow: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{workflow_id}")
async def get_workflow(workflow_id: str, request: Request):
    """Get a workflow configuration by ID"""
    try:
        database = request.app.state.database
        workflow = await database.get_workflow(workflow_id)

        if not workflow:
            raise HTTPException(status_code=404, detail="Workflow not found")

        return {"workflow_id": workflow_id, "workflow_config": workflow}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get workflow: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/")
async def list_workflows(limit: int = 100, offset: int = 0, request: Request = None):
    """List all saved workflows"""
    try:
        database = request.app.state.database
        workflows = await database.list_workflows(limit=limit, offset=offset)

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
async def delete_workflow(workflow_id: str, request: Request):
    """Delete a workflow configuration"""
    try:
        database = request.app.state.database
        deleted = await database.delete_workflow(workflow_id)

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
    file: UploadFile = File(...),
    workflow_config: str = Form(...),
    user_id: Optional[str] = Form("file_user"),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    request: Request = None,
):
    """Execute a workflow with an uploaded file"""
    try:
        import json
        from pathlib import Path

        # Parse workflow config
        workflow_data = json.loads(workflow_config)
        workflow_config_obj = WorkflowConfig(**workflow_data)

        # Save uploaded file
        upload_dir = Path("uploads")
        upload_dir.mkdir(exist_ok=True)
        file_path = upload_dir / file.filename

        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)

        # Create execution request
        execution_request = ExecutionRequest(
            workflow_config=workflow_config_obj,
            user_id=user_id,
            session_id=f"file-session-{datetime.now().isoformat()}",
            organization_id="file-org",
            input_data={"file_path": str(file_path), "filename": file.filename},
        )

        # Execute workflow
        workflow_engine: WorkflowEngine = request.app.state.workflow_engine
        user_context = UserContext(
            user_id=execution_request.user_id,
            session_id=execution_request.session_id,
            organization_id=execution_request.organization_id,
        )

        execution_context = ExecutionContext(
            workflow_config=execution_request.workflow_config.model_dump(),
            user_context=user_context,
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

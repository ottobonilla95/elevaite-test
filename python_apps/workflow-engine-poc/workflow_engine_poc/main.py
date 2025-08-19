"""
Unified Workflow Execution Engine - FastAPI PoC

A clean, agnostic workflow execution engine that supports:
- Conditional, sequential, and parallel execution
- RPC-like step registration
- Simplified agent execution
- Database-backed configuration
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks, UploadFile, File, Form
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn
import logging
import tempfile
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional

from workflow_engine_poc.execution_context import ExecutionContext, UserContext
from workflow_engine_poc.step_registry import StepRegistry
from workflow_engine_poc.workflow_engine import WorkflowEngine
from workflow_engine_poc.models import (
    WorkflowConfig,
    ExecutionRequest,
    ExecutionResponse,
)
from workflow_engine_poc.database import get_database
from workflow_engine_poc.monitoring import monitoring


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    logger.info("🚀 Starting Workflow Execution Engine PoC")

    # Initialize database
    database = await get_database()
    logger.info("✅ Database initialized")
    app.state.database = database

    # Initialize step registry with built-in steps
    step_registry = StepRegistry()
    await step_registry.register_builtin_steps()
    logger.info("✅ Built-in steps registered")

    # Store registry in app state
    app.state.step_registry = step_registry
    app.state.workflow_engine = WorkflowEngine(step_registry)

    yield

    logger.info("🛑 Shutting down Workflow Execution Engine")


# Create FastAPI app
app = FastAPI(
    title="Unified Workflow Execution Engine",
    description="A clean, agnostic workflow execution engine PoC",
    version="1.0.0-poc",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "message": "Unified Workflow Execution Engine PoC",
        "version": "1.0.0-poc",
        "status": "running",
    }


@app.get("/health")
async def health_check():
    """Detailed health check"""
    step_registry: StepRegistry = app.state.step_registry
    registered_steps = await step_registry.get_registered_steps()

    return {
        "status": "healthy",
        "registered_steps": len(registered_steps),
        "step_types": list(set(step["step_type"] for step in registered_steps)),
    }


@app.post("/workflows/execute", response_model=ExecutionResponse)
async def execute_workflow(
    request: ExecutionRequest, background_tasks: BackgroundTasks
):
    """
    Execute a workflow configuration.

    This is the main endpoint that accepts a workflow configuration
    and executes it using the unified execution engine.
    """
    try:
        workflow_engine: WorkflowEngine = app.state.workflow_engine

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


@app.get("/executions/{execution_id}")
async def get_execution_status(execution_id: str):
    """Get the status of a workflow execution"""
    try:
        workflow_engine: WorkflowEngine = app.state.workflow_engine
        execution_context = await workflow_engine.get_execution_context(execution_id)

        if not execution_context:
            raise HTTPException(status_code=404, detail="Execution not found")

        return execution_context.get_execution_summary()

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get execution status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/executions/{execution_id}/results")
async def get_execution_results(execution_id: str):
    """Get the detailed results of a workflow execution"""
    try:
        workflow_engine: WorkflowEngine = app.state.workflow_engine
        execution_context = await workflow_engine.get_execution_context(execution_id)

        if not execution_context:
            raise HTTPException(status_code=404, detail="Execution not found")

        return {
            "execution_id": execution_id,
            "status": execution_context.status.value,
            "step_results": {
                step_id: {
                    "status": result.status.value,
                    "output_data": result.output_data,
                    "error_message": result.error_message,
                    "execution_time_ms": result.execution_time_ms,
                    "retry_count": result.retry_count,
                }
                for step_id, result in execution_context.step_results.items()
            },
            "step_io_data": execution_context.step_io_data,
            "metadata": execution_context.metadata,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get execution results: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/steps/register")
async def register_step(step_config: Dict[str, Any]):
    """
    Register a new step function.

    This enables RPC-like step registration where clients can
    register new step types without redeploying the engine.
    """
    try:
        step_registry: StepRegistry = app.state.step_registry
        step_id = await step_registry.register_step(step_config)

        return {"step_id": step_id, "message": "Step registered successfully"}

    except Exception as e:
        logger.error(f"Failed to register step: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/steps")
async def list_registered_steps():
    """List all registered step functions"""
    try:
        step_registry: StepRegistry = app.state.step_registry
        steps = await step_registry.get_registered_steps()

        return {"steps": steps, "total": len(steps)}

    except Exception as e:
        logger.error(f"Failed to list steps: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/steps/{step_type}")
async def get_step_info(step_type: str):
    """Get information about a specific step type"""
    try:
        step_registry: StepRegistry = app.state.step_registry
        step_info = await step_registry.get_step_info(step_type)

        if not step_info:
            raise HTTPException(status_code=404, detail="Step type not found")

        return step_info

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get step info: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/workflows/validate")
async def validate_workflow(workflow_config: WorkflowConfig):
    """Validate a workflow configuration"""
    try:
        workflow_engine: WorkflowEngine = app.state.workflow_engine
        validation_result = await workflow_engine.validate_workflow(
            workflow_config.model_dump()
        )

        return validation_result

    except Exception as e:
        logger.error(f"Failed to validate workflow: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/analytics/executions")
async def get_execution_analytics(
    limit: int = 100, offset: int = 0, status: Optional[str] = None
):
    """Get execution analytics and history"""
    try:
        workflow_engine: WorkflowEngine = app.state.workflow_engine
        analytics = await workflow_engine.get_execution_analytics(
            limit=limit, offset=offset, status=status
        )

        return analytics

    except Exception as e:
        logger.error(f"Failed to get execution analytics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Workflow Management Endpoints


@app.post("/workflows")
async def save_workflow(workflow_config: WorkflowConfig):
    """Save a workflow configuration to the database"""
    try:
        database = app.state.database
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


@app.get("/workflows/{workflow_id}")
async def get_workflow(workflow_id: str):
    """Get a workflow configuration by ID"""
    try:
        database = app.state.database
        workflow = await database.get_workflow(workflow_id)

        if not workflow:
            raise HTTPException(status_code=404, detail="Workflow not found")

        return workflow

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get workflow: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/workflows")
async def list_workflows(limit: int = 100, offset: int = 0):
    """List all saved workflows"""
    try:
        database = app.state.database
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


@app.delete("/workflows/{workflow_id}")
async def delete_workflow(workflow_id: str):
    """Delete a workflow configuration"""
    try:
        database = app.state.database
        deleted = await database.delete_workflow(workflow_id)

        if not deleted:
            raise HTTPException(status_code=404, detail="Workflow not found")

        return {"message": "Workflow deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete workflow: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# File Upload and Processing Endpoints


@app.post("/files/upload")
async def upload_file(
    file: UploadFile = File(...),
    workflow_id: Optional[str] = Form(None),
    auto_process: bool = Form(False),
):
    """
    Upload a file for processing.

    Optionally trigger automatic processing with a specified workflow.
    """
    try:
        # Create temporary file
        temp_dir = Path(tempfile.gettempdir()) / "workflow_engine_uploads"
        temp_dir.mkdir(exist_ok=True)

        file_path = temp_dir / f"{file.filename}"

        # Save uploaded file
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)

        result = {
            "filename": file.filename,
            "file_path": str(file_path),
            "file_size": len(content),
            "content_type": file.content_type,
            "message": "File uploaded successfully",
        }

        # Auto-process if requested
        if auto_process and workflow_id:
            database = app.state.database
            workflow_config = await database.get_workflow(workflow_id)

            if workflow_config:
                # Execute workflow with file path
                workflow_engine: WorkflowEngine = app.state.workflow_engine
                user_context = UserContext(user_id="file_upload_user")
                execution_context = ExecutionContext(
                    workflow_config=workflow_config, user_context=user_context
                )
                execution_context.step_io_data["file_upload"] = {
                    "file_path": str(file_path)
                }

                # Start execution in background
                import asyncio

                asyncio.create_task(workflow_engine.execute_workflow(execution_context))

                result["auto_processing"] = {
                    "execution_id": execution_context.execution_id,
                    "workflow_id": workflow_id,
                    "status": "started",
                }

        return result

    except Exception as e:
        logger.error(f"Failed to upload file: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/workflows/execute-with-file")
async def execute_workflow_with_file(
    file: UploadFile = File(...),
    workflow_config: str = Form(...),
    user_id: Optional[str] = Form("file_user"),
    background_tasks: BackgroundTasks = BackgroundTasks(),
):
    """
    Execute a workflow with an uploaded file.

    This endpoint combines file upload and workflow execution in one call.
    """
    try:
        import json

        # Parse workflow config
        workflow_data = json.loads(workflow_config)

        # Create temporary file
        temp_dir = Path(tempfile.gettempdir()) / "workflow_engine_uploads"
        temp_dir.mkdir(exist_ok=True)

        file_path = temp_dir / f"{file.filename}"

        # Save uploaded file
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)

        # Create execution context
        workflow_engine: WorkflowEngine = app.state.workflow_engine
        user_context = UserContext(user_id=user_id)
        execution_context = ExecutionContext(
            workflow_config=workflow_data, user_context=user_context
        )

        # Add file path to execution context
        execution_context.step_io_data["file_upload"] = {
            "file_path": str(file_path),
            "filename": file.filename,
            "file_size": len(content),
            "content_type": file.content_type,
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


@app.get("/analytics/errors")
async def get_error_analytics(component: Optional[str] = None):
    """Get error analytics and statistics"""
    try:
        from .error_handling import error_handler

        stats = error_handler.get_error_statistics(component=component)

        return {
            "error_statistics": stats,
            "component_filter": component,
            "timestamp": datetime.now().isoformat(),
        }

    except Exception as e:
        logger.error(f"Failed to get error analytics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health/detailed")
async def detailed_health_check():
    """Detailed health check with error statistics"""
    try:
        from .error_handling import error_handler

        step_registry: StepRegistry = app.state.step_registry
        workflow_engine: WorkflowEngine = app.state.workflow_engine

        registered_steps = await step_registry.get_registered_steps()
        error_stats = error_handler.get_error_statistics()

        # Get active executions count
        active_executions = len(workflow_engine.active_executions)

        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "components": {
                "step_registry": {
                    "status": "healthy",
                    "registered_steps": len(registered_steps),
                    "step_types": list(
                        set(step["step_type"] for step in registered_steps)
                    ),
                },
                "workflow_engine": {
                    "status": "healthy",
                    "active_executions": active_executions,
                },
                "error_handler": {
                    "status": "healthy",
                    "total_errors": error_stats.get("total_errors", 0),
                    "recent_errors": error_stats.get("recent_errors", 0),
                    "circuit_breakers": len(error_stats.get("circuit_breakers", {})),
                },
            },
            "error_statistics": error_stats,
        }

    except Exception as e:
        logger.error(f"Failed to get detailed health check: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Monitoring and Observability Endpoints


@app.get("/metrics")
async def get_metrics():
    """Get Prometheus metrics"""
    try:
        metrics_data = monitoring.get_metrics()
        return Response(content=metrics_data, media_type="text/plain")

    except Exception as e:
        logger.error(f"Failed to get metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/monitoring/traces")
async def get_traces(limit: int = 100):
    """Get trace data for debugging"""
    try:
        traces = monitoring.get_traces()

        # Limit results
        if limit > 0:
            traces = traces[-limit:]

        return {"traces": traces, "total": len(monitoring.traces), "limit": limit}

    except Exception as e:
        logger.error(f"Failed to get traces: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/monitoring/summary")
async def get_monitoring_summary():
    """Get monitoring system summary"""
    try:
        summary = monitoring.get_monitoring_summary()

        # Add workflow engine stats
        workflow_engine: WorkflowEngine = app.state.workflow_engine
        summary.update(
            {
                "active_executions": len(workflow_engine.active_executions),
                "execution_history": len(workflow_engine.execution_history),
                "registered_steps": len(app.state.step_registry.registered_steps),
            }
        )

        return summary

    except Exception as e:
        logger.error(f"Failed to get monitoring summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health/monitoring")
async def monitoring_health_check():
    """Health check specifically for monitoring components"""
    try:
        summary = monitoring.get_monitoring_summary()

        # Check if monitoring is working
        is_healthy = summary["monitoring_enabled"]

        return {
            "status": "healthy" if is_healthy else "degraded",
            "monitoring": summary,
            "timestamp": datetime.now().isoformat(),
        }

    except Exception as e:
        logger.error(f"Monitoring health check failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run(
        "workflow_engine_poc.main:app",
        host="0.0.0.0",
        port=8006,  # Different port from agent-studio
        reload=True,
        log_level="info",
    )

import asyncio
import json
import logging
import uuid
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse, StreamingResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from db.database import get_db
from services.pipeline_executor import pipeline_executor


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/pipeline", tags=["pipeline"])


# Request/Response Models
class PipelineStepConfig(BaseModel):
    """Configuration for a single pipeline step"""

    step_type: str = Field(..., description="Type of step (load, parse, chunk, embed, store)")
    config: Dict[str, Any] = Field(default_factory=dict, description="Step-specific configuration")


class PipelineExecutionRequest(BaseModel):
    """Request model for pipeline execution"""

    steps: List[PipelineStepConfig] = Field(..., description="List of pipeline steps in order")
    file_id: Optional[str] = Field(None, description="ID of uploaded file to process")
    file_ids: Optional[List[str]] = Field(None, description="List of file IDs for multi-file support")
    pipeline_name: Optional[str] = Field("default", description="Name for this pipeline execution")
    pipeline_id: Optional[str] = Field(None, description="Optional pipeline ID from frontend")


class PipelineExecutionResponse(BaseModel):
    """Response model for pipeline execution"""

    pipeline_id: str
    status: str
    message: str
    steps_completed: int
    total_steps: int
    results: Optional[Dict[str, Any]] = None


# Progress tracking for SSE
class PipelineProgressTracker:
    """Tracks pipeline progress for Server-Sent Events"""

    def __init__(self):
        self.progress_data: Dict[str, Dict[str, Any]] = {}
        self.subscribers: Dict[str, List[asyncio.Queue]] = {}

    def start_pipeline(self, pipeline_id: str, total_steps: int):
        """Start tracking a new pipeline"""
        self.progress_data[pipeline_id] = {
            "pipeline_id": pipeline_id,
            "status": "running",
            "current_step": 0,
            "total_steps": total_steps,
            "completed_steps": [],
            "current_stage": None,
            "message": "Pipeline started",
        }
        self.subscribers[pipeline_id] = []

    def update_progress(self, pipeline_id: str, stage_name: str, stage_status: str):
        """Update progress for a pipeline stage"""
        if pipeline_id not in self.progress_data:
            return

        progress = self.progress_data[pipeline_id]

        if stage_status == "started":
            progress["current_stage"] = stage_name
            progress["message"] = f"Executing {stage_name} stage"
        elif stage_status == "completed":
            if stage_name not in progress["completed_steps"]:
                progress["completed_steps"].append(stage_name)
                progress["current_step"] = len(progress["completed_steps"])
            progress["message"] = f"Completed {stage_name} stage"
        elif stage_status == "failed":
            progress["status"] = "failed"
            progress["message"] = f"Failed at {stage_name} stage"

        # Notify subscribers
        self._notify_subscribers(pipeline_id, progress.copy())

    def complete_pipeline(self, pipeline_id: str, status: str, message: str):
        """Mark pipeline as completed or failed"""
        if pipeline_id not in self.progress_data:
            return

        progress = self.progress_data[pipeline_id]
        progress["status"] = status
        progress["message"] = message

        if status == "completed":
            progress["current_step"] = progress["total_steps"]

        # Notify subscribers
        self._notify_subscribers(pipeline_id, progress.copy())

    def add_subscriber(self, pipeline_id: str, queue: asyncio.Queue):
        """Add a subscriber for pipeline updates"""
        if pipeline_id not in self.subscribers:
            self.subscribers[pipeline_id] = []
        self.subscribers[pipeline_id].append(queue)

    def remove_subscriber(self, pipeline_id: str, queue: asyncio.Queue):
        """Remove a subscriber"""
        if pipeline_id in self.subscribers:
            try:
                self.subscribers[pipeline_id].remove(queue)
            except ValueError:
                pass

    def _notify_subscribers(self, pipeline_id: str, progress_data: Dict[str, Any]):
        """Notify all subscribers of progress update"""
        if pipeline_id in self.subscribers:
            for queue in self.subscribers[pipeline_id]:
                try:
                    queue.put_nowait(progress_data)
                except asyncio.QueueFull:
                    logger.warning(f"Queue full for pipeline {pipeline_id}")

    def pipeline_exists(self, pipeline_id: str) -> bool:
        """Check if a pipeline is registered"""
        return pipeline_id in self.progress_data


# Global progress tracker
progress_tracker = PipelineProgressTracker()


@router.post("/execute", response_model=PipelineExecutionResponse)
async def execute_pipeline(
    request: PipelineExecutionRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """
    Execute a document processing pipeline using the steps-based architecture.

    This endpoint starts the pipeline execution asynchronously and returns immediately
    with a pipeline_id. Clients can use the pipeline_id to monitor progress via SSE.

    Args:
        request: Pipeline configuration and file information
        background_tasks: FastAPI background tasks
        db: Database session

    Returns:
        Pipeline ID and initial status
    """
    logger.info(f"🚀 Pipeline execution request received: {request.pipeline_name}")
    logger.info(f"📋 Steps: {[step.step_type for step in request.steps]}")
    logger.info(f"📁 File IDs: {request.file_ids or [request.file_id] if request.file_id else []}")

    try:
        # Use provided pipeline_id or generate a new one
        pipeline_id = request.pipeline_id or str(uuid.uuid4())

        # Validate request
        if not request.steps:
            raise HTTPException(status_code=400, detail="No pipeline steps provided")

        # Get file IDs
        file_ids = []
        if request.file_ids:
            file_ids = request.file_ids
        elif request.file_id:
            file_ids = [request.file_id]

        if not file_ids:
            raise HTTPException(status_code=400, detail="No files provided for processing")

        # Start progress tracking
        progress_tracker.start_pipeline(pipeline_id, len(request.steps))

        # Start the pipeline in the background
        background_tasks.add_task(
            run_pipeline_background,
            pipeline_id,
            [step.dict() for step in request.steps],
            file_ids,
        )

        return PipelineExecutionResponse(
            pipeline_id=pipeline_id,
            status="running",
            message="Pipeline started successfully. Use the pipeline_id to monitor progress.",
            steps_completed=0,
            total_steps=len(request.steps),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start pipeline: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to start pipeline: {str(e)}")


async def run_pipeline_background(pipeline_id: str, steps_config: List[Dict[str, Any]], file_ids: List[str]):
    """
    Run pipeline execution in the background.

    Args:
        pipeline_id: Unique pipeline identifier
        steps_config: List of step configurations
        file_ids: List of file IDs to process
    """
    try:
        # Add a delay to ensure any monitoring connections are established
        await asyncio.sleep(2)

        # Create progress callback
        def progress_callback(pid: str, stage: str, status: str):
            progress_tracker.update_progress(pid, stage, status)

        # Execute the pipeline
        result = await pipeline_executor.execute_pipeline(
            pipeline_id=pipeline_id,
            steps_config=steps_config,
            file_ids=file_ids,
            progress_callback=progress_callback,
        )

        # Mark pipeline as completed
        progress_tracker.complete_pipeline(pipeline_id, result.status, result.message)

        logger.info(f"Pipeline {pipeline_id} completed with status: {result.status}")

    except Exception as e:
        logger.error(f"Background pipeline execution failed: {str(e)}", exc_info=True)
        progress_tracker.complete_pipeline(pipeline_id, "failed", f"Pipeline execution failed: {str(e)}")


@router.get("/progress/{pipeline_id}")
async def stream_pipeline_progress(pipeline_id: str):
    """
    Stream pipeline progress updates via Server-Sent Events.

    Args:
        pipeline_id: Unique pipeline identifier

    Returns:
        SSE stream of progress updates

    Raises:
        HTTPException: If pipeline_id does not exist
    """
    # Validate that the pipeline exists
    if not progress_tracker.pipeline_exists(pipeline_id):
        raise HTTPException(status_code=404, detail=f"Pipeline {pipeline_id} not found")

    async def event_stream():
        queue = asyncio.Queue(maxsize=100)
        progress_tracker.add_subscriber(pipeline_id, queue)

        try:
            # Send initial progress if pipeline exists
            if pipeline_id in progress_tracker.progress_data:
                initial_data = progress_tracker.progress_data[pipeline_id]
                yield f"data: {json.dumps(initial_data)}\n\n"

            # Stream updates
            while True:
                try:
                    # Wait for progress update with timeout
                    progress_data = await asyncio.wait_for(queue.get(), timeout=30.0)
                    yield f"data: {json.dumps(progress_data)}\n\n"

                    # If pipeline is completed or failed, send final message and break
                    if progress_data.get("status") in ["completed", "failed"]:
                        break

                except asyncio.TimeoutError:
                    # Send heartbeat to keep connection alive
                    yield f"data: {json.dumps({'type': 'heartbeat', 'timestamp': str(uuid.uuid4())})}\n\n"

        except Exception as e:
            logger.error(f"Error in SSE stream for pipeline {pipeline_id}: {e}")
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
        finally:
            progress_tracker.remove_subscriber(pipeline_id, queue)

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/event-stream",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, OPTIONS",
            "Access-Control-Allow-Headers": "Cache-Control, Accept, Accept-Encoding, Accept-Language",
            "Access-Control-Allow-Credentials": "false",
        },
    )


@router.get("/{pipeline_id}/status")
async def get_pipeline_status(pipeline_id: str, db: Session = Depends(get_db)):
    """
    Get the status of a running or completed pipeline.

    Args:
        pipeline_id: Unique pipeline identifier
        db: Database session

    Returns:
        Pipeline status information
    """
    # Check if pipeline exists in progress tracker
    if pipeline_id in progress_tracker.progress_data:
        progress_data = progress_tracker.progress_data[pipeline_id].copy()
        return JSONResponse(content=progress_data)
    else:
        return JSONResponse(
            content={
                "pipeline_id": pipeline_id,
                "status": "not_found",
                "message": "Pipeline not found",
                "current_step": 0,
                "total_steps": 0,
                "completed_steps": [],
                "current_stage": None,
            }
        )


@router.get("/config/template")
async def get_pipeline_config_template():
    """
    Get a template configuration for pipeline execution.

    Returns:
        Template configuration with all available options
    """
    template = {
        "steps": [
            {
                "step_type": "load",
                "config": {
                    "provider": "local",
                    "file_path": "/path/to/file",
                    "file_pattern": "*.pdf",
                },
            },
            {
                "step_type": "parse",
                "config": {"provider": "unstructured", "strategy": "auto"},
            },
            {
                "step_type": "chunk",
                "config": {
                    "strategy": "recursive",
                    "chunk_size": 1000,
                    "chunk_overlap": 200,
                },
            },
            {
                "step_type": "embed",
                "config": {
                    "provider": "openai",
                    "model": "text-embedding-3-small",
                    "batch_size": 100,
                },
            },
            {
                "step_type": "store",
                "config": {
                    "provider": "qdrant",
                    "collection_name": "documents",
                    "index_name": "pipeline-index",
                },
            },
        ],
        "file_id": "your-uploaded-file-id",
        "pipeline_name": "my-document-pipeline",
    }

    return JSONResponse(content=template)

import os
import sys
import json
import uuid
import tempfile
import shutil
import logging
import subprocess
import asyncio
from typing import Dict, Any, Optional, List
from pathlib import Path
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    UploadFile,
    File,
    Form,
    BackgroundTasks,
)
from fastapi.responses import JSONResponse, StreamingResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from db.database import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/vectorization", tags=["vectorization"])


# Global progress tracking
class PipelineProgressTracker:
    def __init__(self):
        self.progress_data = {}
        self.subscribers = {}

    def start_pipeline(self, pipeline_id: str, total_steps: int):
        """Start tracking a new pipeline."""
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

    def update_progress(
        self, pipeline_id: str, stage: str, status: str, message: str = ""
    ):
        """Update progress for a pipeline."""
        if pipeline_id not in self.progress_data:
            return

        progress = self.progress_data[pipeline_id]

        if status == "started":
            progress["current_stage"] = stage
            progress["message"] = f"Starting {stage}..."
        elif status == "completed":
            progress["completed_steps"].append(stage)
            progress["current_step"] = len(progress["completed_steps"])
            progress["message"] = f"Completed {stage}"

            if progress["current_step"] >= progress["total_steps"]:
                progress["status"] = "completed"
                progress["current_stage"] = None
                progress["message"] = "Pipeline completed successfully"

        # Notify all subscribers
        self._notify_subscribers(pipeline_id, progress.copy())

    def complete_pipeline(
        self, pipeline_id: str, status: str = "completed", message: str = ""
    ):
        """Mark pipeline as completed."""
        if pipeline_id not in self.progress_data:
            return

        self.progress_data[pipeline_id]["status"] = status
        self.progress_data[pipeline_id]["message"] = message or f"Pipeline {status}"
        self._notify_subscribers(pipeline_id, self.progress_data[pipeline_id].copy())

    def add_subscriber(self, pipeline_id: str, queue: asyncio.Queue):
        """Add a subscriber for pipeline updates."""
        if pipeline_id not in self.subscribers:
            self.subscribers[pipeline_id] = []
        self.subscribers[pipeline_id].append(queue)

    def remove_subscriber(self, pipeline_id: str, queue: asyncio.Queue):
        """Remove a subscriber."""
        if pipeline_id in self.subscribers and queue in self.subscribers[pipeline_id]:
            self.subscribers[pipeline_id].remove(queue)

    def _notify_subscribers(self, pipeline_id: str, progress_data: dict):
        """Notify all subscribers of progress update."""
        if pipeline_id not in self.subscribers:
            return

        try:
            for queue in self.subscribers[pipeline_id]:
                try:
                    queue.put_nowait(progress_data)
                except asyncio.QueueFull:
                    logger.warning(
                        f"Queue full for pipeline {pipeline_id}, skipping update"
                    )
                except Exception as e:
                    logger.error(f"Error notifying subscriber for {pipeline_id}: {e}")
        except Exception as e:
            logger.error(f"Error in _notify_subscribers for {pipeline_id}: {e}")


# Global progress tracker instance
progress_tracker = PipelineProgressTracker()


# Pydantic models for request/response
class VectorizationStepConfig(BaseModel):
    """Configuration for a single vectorization step."""

    step_type: str = Field(
        ..., description="Type of step: load, parse, chunk, embed, store, query"
    )
    config: Dict[str, Any] = Field(
        default_factory=dict, description="Step-specific configuration"
    )


class VectorizationPipelineRequest(BaseModel):
    """Request model for vectorization pipeline execution."""

    steps: List[VectorizationStepConfig] = Field(
        ..., description="List of pipeline steps in order"
    )
    file_id: Optional[str] = Field(None, description="ID of uploaded file to process")
    file_ids: Optional[List[str]] = Field(
        None, description="List of file IDs for multi-file support"
    )
    pipeline_name: Optional[str] = Field(
        "default", description="Name for this pipeline execution"
    )
    pipeline_id: Optional[str] = Field(
        None, description="Optional pipeline ID from frontend"
    )


class VectorizationPipelineResponse(BaseModel):
    """Response model for vectorization pipeline execution."""

    pipeline_id: str = Field(..., description="Unique ID for this pipeline execution")
    status: str = Field(..., description="Pipeline status: running, completed, failed")
    message: str = Field(..., description="Status message")
    steps_completed: int = Field(default=0, description="Number of steps completed")
    total_steps: int = Field(..., description="Total number of steps")
    results: Optional[Dict[str, Any]] = Field(
        None, description="Pipeline execution results"
    )


async def execute_ingestion_pipeline(
    config_file: Path, working_dir: Path, pipeline_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Execute the elevaite-ingestion pipeline with the provided configuration.

    Args:
        config_file: Path to the configuration JSON file
        working_dir: Working directory for the pipeline
        pipeline_id: Optional pipeline ID for progress tracking

    Returns:
        Pipeline execution results
    """
    try:
        # Get the path to the elevaite_ingestion package
        ingestion_package_path = (
            Path(__file__).parent.parent.parent.parent.parent
            / "python_packages"
            / "elevaite_ingestion"
        )

        if not ingestion_package_path.exists():
            raise FileNotFoundError(
                f"elevaite_ingestion package not found at {ingestion_package_path}"
            )

        # Change to the ingestion package directory
        original_cwd = os.getcwd()
        os.chdir(ingestion_package_path)

        # Add the ingestion package to Python path
        sys.path.insert(0, str(ingestion_package_path))

        try:
            # Execute the real ingestion pipeline
            logger.info("Starting ingestion pipeline execution...")

            # Set up environment for the ingestion pipeline
            os.environ["CONFIG_FILE"] = str(config_file)

            # Import and execute the pipeline stages sequentially
            result = await execute_pipeline_stages(
                config_file, working_dir, pipeline_id
            )

            logger.info("Ingestion pipeline completed successfully")
            return {
                "status": "completed",
                "message": "Pipeline executed successfully",
                "result": result,
            }

        except Exception as e:
            logger.error(f"Pipeline execution failed: {str(e)}")
            return {
                "status": "failed",
                "message": f"Pipeline execution failed: {str(e)}",
                "error": str(e),
            }
        finally:
            # Restore original working directory
            os.chdir(original_cwd)
            # Remove from Python path
            if str(ingestion_package_path) in sys.path:
                sys.path.remove(str(ingestion_package_path))

    except Exception as e:
        logger.error(f"Failed to execute ingestion pipeline: {str(e)}")
        return {
            "status": "failed",
            "message": f"Failed to execute ingestion pipeline: {str(e)}",
            "error": str(e),
        }


async def execute_pipeline_stages(
    config_file: Path, working_dir: Path, pipeline_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Execute the ingestion pipeline stages sequentially.

    Args:
        config_file: Path to the configuration file
        working_dir: Working directory for the pipeline
        pipeline_id: Optional pipeline ID for progress tracking

    Returns:
        Pipeline execution results
    """
    stages_completed = []
    stage_results = {}

    try:
        # Define the pipeline stages in order
        stages = [
            ("load", "stage/load_stage/load_main.py"),
            ("parse", "stage/parse_stage/parse_main.py"),
            ("chunk", "stage/chunk_stage/chunk_main.py"),
            ("embed", "stage/embed_stage/embed_main.py"),
            ("store", "stage/vectorstore_stage/vectordb_main.py"),
        ]

        # Get the ingestion package path
        ingestion_package_path = (
            Path(__file__).parent.parent.parent.parent.parent
            / "python_packages"
            / "elevaite_ingestion"
        )

        for stage_name, stage_script in stages:
            logger.info(f"Executing stage: {stage_name}")

            # Emit progress update - stage started
            if pipeline_id:
                try:
                    progress_tracker.update_progress(pipeline_id, stage_name, "started")
                except Exception as e:
                    logger.error(f"Error updating progress for {stage_name} start: {e}")

            stage_path = ingestion_package_path / stage_script
            if not stage_path.exists():
                logger.error(f"Stage script not found: {stage_path}")
                stage_results[stage_name] = {
                    "status": "failed",
                    "error": f"Stage script not found: {stage_path}",
                    "return_code": -1,
                }
                # Emit progress update - stage failed
                if pipeline_id:
                    try:
                        progress_tracker.update_progress(
                            pipeline_id,
                            stage_name,
                            "failed",
                            f"Stage script not found: {stage_path}",
                        )
                    except Exception as e:
                        logger.error(
                            f"Error updating progress for {stage_name} failure: {e}"
                        )
                raise Exception(
                    f"Critical pipeline stage missing: {stage_name} at {stage_path}"
                )

            # Execute stage using subprocess to avoid import issues
            logger.info(f"Starting subprocess execution for {stage_name}")
            result = await execute_stage_subprocess(stage_path, working_dir)
            logger.info(
                f"Subprocess execution completed for {stage_name} with result: {result.get('status', 'unknown')}"
            )

            stage_results[stage_name] = result

            # Check if stage execution was successful
            if result.get("status") != "completed" or result.get("return_code", 0) != 0:
                logger.error(f"Stage {stage_name} failed: {result}")
                # Emit progress update - stage failed
                if pipeline_id:
                    try:
                        progress_tracker.update_progress(
                            pipeline_id,
                            stage_name,
                            "failed",
                            f"Stage failed: {result.get('error', 'Unknown error')}",
                        )
                    except Exception as e:
                        logger.error(
                            f"Error updating progress for {stage_name} failure: {e}"
                        )
                raise Exception(
                    f"Stage {stage_name} failed with return code {result.get('return_code', -1)}"
                )

            stages_completed.append(stage_name)
            logger.info(f"Stage {stage_name} completed successfully")

            # Emit progress update - stage completed
            if pipeline_id:
                try:
                    progress_tracker.update_progress(
                        pipeline_id, stage_name, "completed"
                    )
                    logger.info(f"Progress updated for {stage_name} completion")
                except Exception as e:
                    logger.error(
                        f"Error updating progress for {stage_name} completion: {e}"
                    )

        return {
            "stages_completed": stages_completed,
            "stage_results": stage_results,
            "total_stages": len(stages),
            "config_file": str(config_file),
            "working_directory": str(working_dir),
            "execution_summary": {
                "files_processed": stage_results.get("load", {}).get("files_count", 0),
                "chunks_created": stage_results.get("chunk", {}).get("chunks_count", 0),
                "embeddings_generated": stage_results.get("embed", {}).get(
                    "embeddings_count", 0
                ),
                "vectors_stored": stage_results.get("store", {}).get(
                    "vectors_count", 0
                ),
            },
        }

    except Exception as e:
        logger.error(f"Pipeline stage execution failed: {str(e)}")
        return {
            "stages_completed": stages_completed,
            "stage_results": stage_results,
            "error": str(e),
            "failed_at_stage": len(stages_completed),
        }


async def execute_stage_subprocess(
    stage_path: Path, working_dir: Path
) -> Dict[str, Any]:
    """
    Execute a single stage using subprocess to avoid import conflicts.

    Args:
        stage_path: Path to the stage script
        working_dir: Working directory

    Returns:
        Stage execution result
    """
    try:
        # Change to the ingestion package directory
        ingestion_dir = stage_path.parent.parent.parent

        # Execute the stage script
        logger.info(
            f"Creating subprocess for {stage_path} in directory {ingestion_dir}"
        )
        process = await asyncio.create_subprocess_exec(
            sys.executable,
            str(stage_path),
            cwd=str(ingestion_dir),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env={**os.environ, "PYTHONPATH": str(ingestion_dir)},
        )
        logger.info(
            f"Subprocess created with PID {process.pid}, waiting for completion..."
        )

        # Add timeout to prevent hanging (10 minutes for heavy stages like chunking)
        # Also add periodic logging to track progress
        async def monitor_process():
            for i in range(60):  # Check every 10 seconds for 10 minutes
                await asyncio.sleep(10)
                if process.returncode is not None:
                    break
                logger.info(f"Subprocess still running after {(i+1)*10} seconds...")

        monitor_task = asyncio.create_task(monitor_process())

        try:
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=600)
            logger.info(f"Subprocess completed with return code {process.returncode}")
        except asyncio.TimeoutError:
            logger.error(f"Stage execution timed out after 10 minutes: {stage_path}")
            process.kill()
            await process.wait()
            return {
                "status": "failed",
                "error": "Stage execution timed out after 10 minutes",
                "return_code": -1,
            }
        finally:
            monitor_task.cancel()
            try:
                await monitor_task
            except asyncio.CancelledError:
                pass

        if process.returncode == 0:
            return {
                "status": "completed",
                "stdout": stdout.decode() if stdout else "",
                "stderr": stderr.decode() if stderr else "",
                "return_code": process.returncode,
            }
        else:
            return {
                "status": "failed",
                "stdout": stdout.decode() if stdout else "",
                "stderr": stderr.decode() if stderr else "",
                "return_code": process.returncode,
                "error": f"Stage failed with return code {process.returncode}",
            }

    except Exception as e:
        return {"status": "failed", "error": str(e), "return_code": -1}


def create_ingestion_config(
    steps: List[VectorizationStepConfig], file_path: Optional[str]
) -> Dict[str, Any]:
    """
    Convert frontend vectorization steps to elevaite-ingestion config format.

    Args:
        steps: List of vectorization step configurations
        file_path: Path to the file to process (None for S3 mode)

    Returns:
        Configuration dictionary compatible with elevaite-ingestion
    """
    # Check if we're dealing with S3 or local files
    s3_load_steps = [
        step
        for step in steps
        if step.step_type == "load" and step.config.get("provider") == "s3"
    ]

    if file_path is None and s3_load_steps:
        # S3 mode - use S3 configuration
        s3_config = s3_load_steps[0].config  # Use first S3 load step config
        bucket_name = s3_config.get("bucket_name", "")
        s3_prefix = s3_config.get("s3_prefix", "")

        config = {
            "loading": {
                "default_source": "s3",
                "sources": {
                    "s3": {
                        "bucket_name": bucket_name,
                        "prefix": s3_prefix,
                        "aws_access_key_id": os.getenv("AWS_ACCESS_KEY_ID", ""),
                        "aws_secret_access_key": os.getenv("AWS_SECRET_ACCESS_KEY", ""),
                        "region_name": os.getenv("AWS_DEFAULT_REGION", "us-east-2"),
                    }
                },
            },
        }
    else:
        # Local mode - use local file configuration
        if file_path is None:
            raise ValueError("file_path is required for local mode")

        # Create directories for the pipeline
        input_dir = Path(file_path).parent / "input_data"
        output_dir = Path(file_path).parent / "output_data"
        parsed_dir = Path(file_path).parent / "data" / "processed"

        input_dir.mkdir(exist_ok=True)
        output_dir.mkdir(exist_ok=True)
        parsed_dir.mkdir(parents=True, exist_ok=True)

        # Copy the file to the input directory with a standard name
        input_file = input_dir / Path(file_path).name
        if not input_file.exists():
            shutil.copy2(file_path, input_file)

        config = {
            "loading": {
                "default_source": "local",
                "sources": {
                    "local": {
                        "input_directory": str(input_dir),
                        "output_directory": str(output_dir),
                    }
                },
            },
        }

    # Add common configuration sections
    config.update(
        {
            "parsing": {
                "default_mode": "auto_parser",
                "custom_parser_selection": {"parser": "pdf", "tool": None},
                "parsers": {"pdf": {"default_tool": None, "available_tools": []}},
            },
            "chunking": {
                "default_strategy": "recursive_chunking",
                "strategies": {
                    "recursive_chunking": {"chunk_size": 1000, "chunk_overlap": 200}
                },
            },
            "embedding": {
                "default_provider": "openai",
                "default_model": "text-embedding-3-small",
                "providers": {
                    "openai": {
                        "api_key": os.getenv("OPENAI_API_KEY", ""),
                        "models": {
                            "text-embedding-ada-002": {"dimension": 1536},
                            "text-embedding-3-small": {"dimension": 1536},
                            "text-embedding-3-large": {"dimension": 3072},
                        },
                    },
                    "cohere": {
                        "models": {
                            "embed-english-light-v3.0": {"dimension": 1024},
                            "embed-english-v3.0": {"dimension": 1024},
                            "embed-multilingual-v3.0": {"dimension": 1024},
                        }
                    },
                    "local": {
                        "models": {
                            "all-MiniLM-L6-v2": {"dimension": 384},
                            "all-mpnet-base-v2": {"dimension": 768},
                        }
                    },
                    "amazon_bedrock": {
                        "models": {
                            "amazon.titan-embed-text-v1": {"dimension": 1536},
                            "amazon.titan-embed-text-v2:0": {"dimension": 1024},
                        }
                    },
                },
            },
            "vector_db": {
                "default_db": "qdrant",
                "databases": {
                    "qdrant": {
                        "host": os.getenv("QDRANT_HOST", "localhost"),
                        "port": int(os.getenv("QDRANT_PORT", "6333")),
                        "collection_name": f"vectorization_{uuid.uuid4().hex[:8]}",
                    }
                },
            },
        }
    )

    # Add local-specific parsing configuration if in local mode
    if file_path is not None:
        input_dir = Path(file_path).parent / "input_data"
        parsed_dir = Path(file_path).parent / "data" / "processed"
        parsed_dir.mkdir(parents=True, exist_ok=True)
        config["parsing"]["local"] = {
            "input_directory": str(input_dir),
            "output_parsed_directory": str(parsed_dir),
        }

    # Apply step-specific configurations
    for step in steps:
        if step.step_type == "chunk":
            chunk_config = step.config
            if "chunk_size" in chunk_config:
                config["chunking"]["strategies"]["recursive_chunking"]["chunk_size"] = (
                    chunk_config["chunk_size"]
                )
            if "chunk_overlap" in chunk_config:
                config["chunking"]["strategies"]["recursive_chunking"][
                    "chunk_overlap"
                ] = chunk_config["chunk_overlap"]
            if "strategy" in chunk_config:
                config["chunking"]["default_strategy"] = chunk_config["strategy"]

        elif step.step_type == "embed":
            embed_config = step.config
            if "provider" in embed_config:
                config["embedding"]["default_provider"] = embed_config["provider"]
            if "model" in embed_config:
                config["embedding"]["default_model"] = embed_config["model"]
            if "api_key" in embed_config and embed_config["api_key"]:
                provider = embed_config.get("provider", "openai")
                if provider in ["openai", "cohere"]:  # Providers that need API keys
                    if provider not in config["embedding"]["providers"]:
                        config["embedding"]["providers"][provider] = {}
                    config["embedding"]["providers"][provider]["api_key"] = (
                        embed_config["api_key"]
                    )

        elif step.step_type == "load":
            load_config = step.config
            if "provider" in load_config:
                provider = load_config["provider"]
                if provider == "s3":
                    # Update S3 configuration with step-specific settings
                    if "s3" in config["loading"]["sources"]:
                        if "bucket_name" in load_config:
                            config["loading"]["sources"]["s3"]["bucket_name"] = (
                                load_config["bucket_name"]
                            )
                        if "s3_prefix" in load_config:
                            config["loading"]["sources"]["s3"]["prefix"] = load_config[
                                "s3_prefix"
                            ]

        elif step.step_type == "store":
            store_config = step.config
            if "provider" in store_config:
                config["vector_db"]["default_db"] = store_config["provider"]
            if "collection_name" in store_config:
                config["vector_db"]["databases"]["qdrant"]["collection_name"] = (
                    store_config["collection_name"]
                )
            if "index_name" in store_config:
                config["vector_db"]["databases"]["qdrant"]["collection_name"] = (
                    store_config["index_name"]
                )

    return config


@router.get("/pipeline/progress/{pipeline_id}")
async def stream_pipeline_progress(pipeline_id: str):
    """
    Stream pipeline progress updates using Server-Sent Events (SSE).

    Args:
        pipeline_id: ID of the pipeline to monitor

    Returns:
        StreamingResponse with SSE data
    """
    logger.info(f"🔗 SSE connection request for pipeline: {pipeline_id}")

    async def event_stream():
        queue = asyncio.Queue(maxsize=100)
        logger.info(f"📡 Adding subscriber for pipeline: {pipeline_id}")
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


async def run_pipeline_background(
    pipeline_id: str, request: VectorizationPipelineRequest
):
    """
    Background task to run the pipeline asynchronously.

    Args:
        pipeline_id: Unique pipeline identifier
        request: Pipeline configuration and file information
    """
    try:
        # Add a delay to ensure any monitoring connections are established
        await asyncio.sleep(3)

        # Validate steps
        if not request.steps:
            progress_tracker.complete_pipeline(
                pipeline_id, "failed", "No pipeline steps provided"
            )
            return

        # Start progress tracking - count actual pipeline stages
        # The pipeline always runs: load, parse, chunk, embed, store (5 stages)
        total_steps = 5
        progress_tracker.start_pipeline(pipeline_id, total_steps)

        # Check if we have file IDs (either single file_id or multiple file_ids)
        file_ids = []
        if request.file_ids:
            file_ids = request.file_ids
        elif request.file_id:
            file_ids = [request.file_id]

        if not file_ids:
            raise HTTPException(
                status_code=400,
                detail="file_id or file_ids are required for pipeline execution",
            )

        # Check if any load step uses S3
        s3_load_steps = [
            step
            for step in request.steps
            if step.step_type == "load" and step.config.get("provider") == "s3"
        ]

        # Create temporary working directory for this pipeline
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            if s3_load_steps:
                # S3 pipeline - files are already in S3, no need to look for local files
                logger.info(f"Processing S3 pipeline with {len(file_ids)} file(s)")

                # For S3 pipelines, we don't need to copy files locally
                # The ingestion config will point to S3 directly
                ingestion_config = create_ingestion_config(request.steps, None)
                file_processed = "S3 files"
            else:
                # Local file pipeline - look for files in upload directory
                upload_dir = Path(os.getenv("UPLOAD_DIR", "uploads"))
                file_path = None

                # Find file by ID in upload directory (use first file_id for backward compatibility)
                primary_file_id = file_ids[0]
                for file in upload_dir.iterdir():
                    if file.is_file() and file.stem == primary_file_id:
                        file_path = file
                        break

                if not file_path or not file_path.exists():
                    raise HTTPException(
                        status_code=404,
                        detail=f"File with ID {primary_file_id} not found",
                    )

                logger.info(f"Processing local file: {file_path}")

                # Copy file to temp directory
                temp_file = temp_path / file_path.name
                shutil.copy2(file_path, temp_file)

                # Create ingestion config
                ingestion_config = create_ingestion_config(
                    request.steps, str(temp_file)
                )
                file_processed = str(file_path)

            # Save config to temp directory (common for both S3 and local)
            config_file = temp_path / "config.json"
            with open(config_file, "w") as f:
                json.dump(ingestion_config, f, indent=2)

            logger.info(f"Created ingestion config: {config_file}")

            # Execute the actual ingestion pipeline
            pipeline_result = await execute_ingestion_pipeline(
                config_file, temp_path, pipeline_id
            )

            # Prepare results
            results = {
                "config_used": ingestion_config,
                "file_processed": file_processed,
                "temp_directory": temp_dir,
                "steps_executed": [step.step_type for step in request.steps],
                "pipeline_result": pipeline_result,
                "status": pipeline_result.get("status", "unknown"),
                "message": pipeline_result.get(
                    "message", "Pipeline execution completed"
                ),
            }

            # Determine final status based on pipeline result
            final_status = (
                "completed"
                if pipeline_result.get("status") == "completed"
                else "failed"
            )
            final_message = pipeline_result.get(
                "message", "Pipeline execution completed"
            )

            # Calculate steps completed based on stages completed
            stages_completed = pipeline_result.get("result", {}).get(
                "stages_completed", []
            )
            steps_completed = (
                len(stages_completed) if final_status == "completed" else 0
            )

            # Add execution summary to results
            execution_summary = pipeline_result.get("result", {}).get(
                "execution_summary", {}
            )
            if execution_summary:
                results["execution_summary"] = execution_summary

            # Add stage details for debugging
            stage_results = pipeline_result.get("result", {}).get("stage_results", {})
            if stage_results:
                results["stage_details"] = stage_results

            # Mark pipeline as completed
            progress_tracker.complete_pipeline(pipeline_id, final_status, final_message)

            return VectorizationPipelineResponse(
                pipeline_id=pipeline_id,
                status=final_status,
                message=final_message,
                steps_completed=steps_completed,
                total_steps=len(request.steps),
                results=results,
            )

    except Exception as e:
        logger.error(f"Background pipeline execution failed: {str(e)}")
        logger.error(f"Exception type: {type(e).__name__}")
        logger.error(f"Exception details: {e}", exc_info=True)
        # Mark pipeline as failed
        progress_tracker.complete_pipeline(
            pipeline_id, "failed", f"Pipeline execution failed: {str(e)}"
        )


@router.options("/pipeline/progress/{pipeline_id}")
async def options_pipeline_progress(pipeline_id: str):
    """Handle CORS preflight for SSE endpoint."""
    logger.info(f"🔧 CORS preflight request for pipeline: {pipeline_id}")
    return JSONResponse(
        content={},
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, HEAD, OPTIONS",
            "Access-Control-Allow-Headers": "Cache-Control, Accept, Accept-Encoding, Accept-Language",
            "Access-Control-Allow-Credentials": "false",
        },
    )


@router.head("/pipeline/progress/{pipeline_id}")
async def head_pipeline_progress(pipeline_id: str):
    """Handle HEAD request for SSE endpoint."""
    logger.info(f"🧪 HEAD request for pipeline: {pipeline_id}")
    return JSONResponse(
        content={},
        headers={
            "Access-Control-Allow-Origin": "*",
            "Content-Type": "text/event-stream",
        },
    )


@router.post("/pipeline/execute", response_model=VectorizationPipelineResponse)
async def execute_vectorization_pipeline(
    request: VectorizationPipelineRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """
    Start a vectorization pipeline execution in the background.

    This endpoint starts the pipeline execution asynchronously and returns immediately
    with a pipeline_id. Clients can use the pipeline_id to monitor progress via SSE.

    Args:
        request: Pipeline configuration and file information
        background_tasks: FastAPI background tasks
        db: Database session

    Returns:
        Pipeline ID and initial status
    """
    # Use provided pipeline_id or generate a new one
    pipeline_id = request.pipeline_id or str(uuid.uuid4())

    # Start the pipeline in the background
    background_tasks.add_task(run_pipeline_background, pipeline_id, request)

    return VectorizationPipelineResponse(
        pipeline_id=pipeline_id,
        status="running",
        message="Pipeline started successfully. Use the pipeline_id to monitor progress.",
        steps_completed=0,
        total_steps=len(request.steps),
        results=None,
    )


@router.get("/pipeline/{pipeline_id}/status")
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
async def get_config_template():
    """
    Get a template configuration for vectorization pipeline.

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
                    "index_name": "vectorizer-index",
                },
            },
        ],
        "file_id": "your-uploaded-file-id",
        "pipeline_name": "my-vectorization-pipeline",
    }

    return JSONResponse(content=template)

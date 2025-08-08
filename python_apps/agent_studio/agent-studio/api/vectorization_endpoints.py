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
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from db.database import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/vectorization", tags=["vectorization"])


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
    config_file: Path, working_dir: Path
) -> Dict[str, Any]:
    """
    Execute the elevaite-ingestion pipeline with the provided configuration.

    Args:
        config_file: Path to the configuration JSON file
        working_dir: Working directory for the pipeline

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
            result = await execute_pipeline_stages(config_file, working_dir)

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
    config_file: Path, working_dir: Path
) -> Dict[str, Any]:
    """
    Execute the ingestion pipeline stages sequentially.

    Args:
        config_file: Path to the configuration file
        working_dir: Working directory for the pipeline

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

            stage_path = ingestion_package_path / stage_script
            if not stage_path.exists():
                logger.error(f"Stage script not found: {stage_path}")
                stage_results[stage_name] = {
                    "status": "failed",
                    "error": f"Stage script not found: {stage_path}",
                    "return_code": -1,
                }
                raise Exception(
                    f"Critical pipeline stage missing: {stage_name} at {stage_path}"
                )

            # Execute stage using subprocess to avoid import issues
            result = await execute_stage_subprocess(stage_path, working_dir)

            stage_results[stage_name] = result

            # Check if stage execution was successful
            if result.get("status") != "completed" or result.get("return_code", 0) != 0:
                logger.error(f"Stage {stage_name} failed: {result}")
                raise Exception(
                    f"Stage {stage_name} failed with return code {result.get('return_code', -1)}"
                )

            stages_completed.append(stage_name)
            logger.info(f"Stage {stage_name} completed successfully")

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
        process = await asyncio.create_subprocess_exec(
            sys.executable,
            str(stage_path),
            cwd=str(ingestion_dir),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env={**os.environ, "PYTHONPATH": str(ingestion_dir)},
        )

        stdout, stderr = await process.communicate()

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


@router.post("/pipeline/execute", response_model=VectorizationPipelineResponse)
async def execute_vectorization_pipeline(
    request: VectorizationPipelineRequest, db: Session = Depends(get_db)
):
    """
    Execute a vectorization pipeline with the provided configuration.

    This endpoint processes uploaded files through the complete ingestion pipeline:
    load → parse → chunk → embed → store

    Args:
        request: Pipeline configuration and file information
        db: Database session

    Returns:
        Pipeline execution status and results
    """
    pipeline_id = str(uuid.uuid4())

    try:
        # Validate steps
        if not request.steps:
            raise HTTPException(status_code=400, detail="No pipeline steps provided")

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
            pipeline_result = await execute_ingestion_pipeline(config_file, temp_path)

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

            return VectorizationPipelineResponse(
                pipeline_id=pipeline_id,
                status=final_status,
                message=final_message,
                steps_completed=steps_completed,
                total_steps=len(request.steps),
                results=results,
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Pipeline execution failed: {str(e)}")
        return VectorizationPipelineResponse(
            pipeline_id=pipeline_id,
            status="failed",
            message=f"Pipeline execution failed: {str(e)}",
            steps_completed=0,
            total_steps=len(request.steps) if request.steps else 0,
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
    # TODO: Implement pipeline status tracking
    # For now, return a mock response
    return JSONResponse(
        content={
            "pipeline_id": pipeline_id,
            "status": "completed",
            "message": "Status tracking not yet implemented",
            "steps_completed": 0,
            "total_steps": 0,
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

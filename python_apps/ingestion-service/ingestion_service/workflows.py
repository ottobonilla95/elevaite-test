"""
DBOS workflows for ingestion jobs.
"""

from __future__ import annotations

import logging
import uuid as uuid_module
from datetime import datetime, timezone
from typing import Dict, Any, Optional

from dbos import DBOS
from sqlmodel import Session

from .models import IngestionJob, JobStatus
from .database import engine

logger = logging.getLogger(__name__)


async def _run_ingestion_job_impl(job_id: str, db_engine=None) -> Dict[str, Any]:
    """
    Core implementation of the ingestion job workflow.

    This function contains the actual business logic and can be tested directly
    without DBOS initialization. The DBOS-decorated wrapper calls this function.

    Args:
        job_id: UUID of the ingestion job
        db_engine: Optional database engine override (for testing)

    Returns:
        Dict with job_id, status, and optional error_message or result_summary
    """
    # Use provided engine or default
    _engine = db_engine or engine

    logger.info(f"Starting ingestion workflow for job {job_id}")

    # Load job from database
    with Session(_engine) as session:
        job = session.get(IngestionJob, uuid_module.UUID(job_id))
        if not job:
            error_msg = f"Job {job_id} not found"
            logger.error(error_msg)
            return {"job_id": job_id, "status": "FAILED", "error_message": error_msg}

        # Update status to RUNNING
        job.status = JobStatus.RUNNING
        job.updated_at = datetime.now(timezone.utc)
        session.add(job)
        session.commit()
        session.refresh(job)

        config = job.config
        callback_topic = job.callback_topic
        dbos_workflow_id = job.dbos_workflow_id

    logger.info(f"Job {job_id} status updated to RUNNING")

    # Execute the ingestion pipeline
    try:
        result_summary = await execute_ingestion_pipeline(config)

        # Update job status to SUCCEEDED
        with Session(_engine) as session:
            job = session.get(IngestionJob, uuid_module.UUID(job_id))
            if job:
                job.status = JobStatus.SUCCEEDED
                job.result_summary = result_summary
                job.updated_at = datetime.now(timezone.utc)
                job.completed_at = datetime.now(timezone.utc)
                session.add(job)
                session.commit()

        logger.info(f"Job {job_id} completed successfully")

        # Send completion event if callback_topic is configured
        # Event send failures should not affect the job result
        if callback_topic:
            event_payload = {
                "job_id": job_id,
                "status": "SUCCEEDED",
                "result_summary": result_summary,
            }
            try:
                await send_completion_event(callback_topic, dbos_workflow_id, event_payload)
            except Exception as event_error:
                logger.error(f"Failed to send completion event for job {job_id}: {event_error}")

        return {
            "job_id": job_id,
            "status": "SUCCEEDED",
            "result_summary": result_summary,
        }

    except Exception as e:
        error_message = str(e)
        logger.error(f"Job {job_id} failed: {error_message}", exc_info=True)

        # Update job status to FAILED
        with Session(_engine) as session:
            job = session.get(IngestionJob, uuid_module.UUID(job_id))
            if job:
                job.status = JobStatus.FAILED
                job.error_message = error_message
                job.updated_at = datetime.now(timezone.utc)
                job.completed_at = datetime.now(timezone.utc)
                session.add(job)
                session.commit()

        # Send failure event if callback_topic is configured
        # Event send failures should not affect the job result
        if callback_topic:
            event_payload = {
                "job_id": job_id,
                "status": "FAILED",
                "error_message": error_message,
            }
            try:
                await send_completion_event(callback_topic, dbos_workflow_id, event_payload)
            except Exception as event_error:
                logger.error(f"Failed to send failure event for job {job_id}: {event_error}")

        return {
            "job_id": job_id,
            "status": "FAILED",
            "error_message": error_message,
        }


@DBOS.workflow()
async def run_ingestion_job(job_id: str) -> Dict[str, Any]:
    """
    DBOS workflow that executes an ingestion job.

    This workflow:
    1. Loads the job from the database
    2. Updates status to RUNNING
    3. Executes the elevaite_ingestion pipeline
    4. Updates status to SUCCEEDED or FAILED
    5. Sends completion event on callback_topic if configured

    Args:
        job_id: UUID of the ingestion job

    Returns:
        Dict with job_id, status, and optional error_message or result_summary
    """
    return await _run_ingestion_job_impl(job_id)


def _build_pipeline_config(config: Dict[str, Any]):
    """
    Build a PipelineConfig object from the job configuration dictionary.

    Args:
        config: Job configuration dictionary

    Returns:
        PipelineConfig object for passing to pipeline stages
    """
    from elevaite_ingestion.config.pipeline_config import PipelineConfig

    return PipelineConfig.from_dict(config)


async def execute_ingestion_pipeline(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute the elevaite_ingestion pipeline with the given configuration.

    The pipeline runs the following stages sequentially:
    1. PARSING - Parse documents into structured format
    2. CHUNKING - Split parsed content into chunks
    3. EMBEDDING - Generate embeddings for chunks
    4. VECTOR_DB - Store embeddings in vector database

    Args:
        config: Ingestion configuration containing:
            - mode: 's3' or 'local'
            - aws: AWS config (input_bucket, intermediate_bucket)
            - embedding: provider, model configuration
            - vector_db: target vector database configuration

    Returns:
        Summary of ingestion results
    """
    import asyncio

    logger.info(f"Executing ingestion pipeline with config: {config}")

    # Build PipelineConfig from the job configuration
    pipeline_config = _build_pipeline_config(config)

    # Track results from each stage
    mode = config.get("mode", "s3")
    pipeline_results = {
        "stages": {},
        "files_processed": 0,
        "chunks_created": 0,
        "embeddings_generated": 0,
        "index_ids": [],
    }

    try:
        # Stage 1: PARSING
        logger.info("Starting STAGE_2: PARSING...")
        try:
            from elevaite_ingestion.stage.parse_stage.parse_main import execute_pipeline as execute_parsing

            # Run in thread pool since it's sync
            loop = asyncio.get_event_loop()
            parse_result = await loop.run_in_executor(None, lambda: execute_parsing(mode=mode, config=pipeline_config))

            pipeline_results["stages"]["PARSING"] = parse_result

            # Extract file count
            parsing_status = parse_result.get("STAGE_2: PARSING", {})
            pipeline_results["files_processed"] = parsing_status.get("TOTAL_FILES", 0)

            if parsing_status.get("STATUS") == "Failed":
                raise Exception(f"Parsing stage failed: {parsing_status}")

            logger.info(f"PARSING completed: {parsing_status.get('TOTAL_FILES', 0)} files processed")

        except (ImportError, ValueError) as e:
            logger.warning(f"Could not import/configure parsing module: {e}")
            pipeline_results["stages"]["PARSING"] = {"STATUS": "Skipped", "reason": str(e)}

        # Stage 2: CHUNKING
        logger.info("Starting STAGE_3: CHUNKING...")
        try:
            from elevaite_ingestion.stage.chunk_stage.chunk_main import execute_chunking_pipeline

            chunk_result = await execute_chunking_pipeline(config=pipeline_config)
            pipeline_results["stages"]["CHUNKING"] = chunk_result

            # Extract chunk count from the result
            chunking_status = chunk_result.get("STAGE_3: CHUNKING", {})
            if isinstance(chunking_status, dict):
                chunks = chunking_status.get("TOTAL_CHUNKS", 0)
                pipeline_results["chunks_created"] = chunks

            logger.info(f"CHUNKING completed: {pipeline_results['chunks_created']} chunks created")

        except (ImportError, ValueError) as e:
            logger.warning(f"Could not import/configure chunking module: {e}")
            pipeline_results["stages"]["CHUNKING"] = {"STATUS": "Skipped", "reason": str(e)}

        # Stage 3: EMBEDDING
        logger.info("Starting STAGE_4: EMBEDDING...")
        try:
            from elevaite_ingestion.stage.embed_stage.embed_main import execute_embedding_pipeline

            # Run in thread pool since it's sync
            loop = asyncio.get_event_loop()
            embed_result = await loop.run_in_executor(None, lambda: execute_embedding_pipeline(config=pipeline_config))

            pipeline_results["stages"]["EMBEDDING"] = embed_result

            # Extract embedding count
            if isinstance(embed_result, dict):
                embed_status = embed_result.get("STAGE_4: EMBEDDING", {})
                pipeline_results["embeddings_generated"] = embed_status.get("TOTAL_EMBEDDINGS", 0)

            logger.info(f"EMBEDDING completed: {pipeline_results['embeddings_generated']} embeddings generated")

        except (ImportError, ValueError) as e:
            logger.warning(f"Could not import/configure embedding module: {e}")
            pipeline_results["stages"]["EMBEDDING"] = {"STATUS": "Skipped", "reason": str(e)}

        # Stage 4: VECTOR_DB
        logger.info("Starting STAGE_5: VECTOR_DB...")
        try:
            from elevaite_ingestion.stage.vectorstore_stage.vectordb_main import execute_vector_db_pipeline

            # Run in thread pool since it's sync
            loop = asyncio.get_event_loop()
            vectordb_result = await loop.run_in_executor(
                None, lambda: execute_vector_db_pipeline(config=pipeline_config)
            )

            pipeline_results["stages"]["VECTOR_DB"] = vectordb_result

            # Extract index IDs
            if isinstance(vectordb_result, dict):
                vectordb_status = vectordb_result.get("STAGE_5: VECTORSTORE", {})
                if isinstance(vectordb_status, dict):
                    index_id = vectordb_status.get("INDEX_ID") or vectordb_status.get("COLLECTION_NAME")
                    if index_id:
                        pipeline_results["index_ids"].append(index_id)

            logger.info(f"VECTOR_DB completed: indexes={pipeline_results['index_ids']}")

        except (ImportError, ValueError) as e:
            logger.warning(f"Could not import/configure vectordb module: {e}")
            pipeline_results["stages"]["VECTOR_DB"] = {"STATUS": "Skipped", "reason": str(e)}

        logger.info(f"Pipeline completed successfully: {pipeline_results}")

        return {
            "files_processed": pipeline_results["files_processed"],
            "chunks_created": pipeline_results["chunks_created"],
            "embeddings_generated": pipeline_results["embeddings_generated"],
            "index_ids": pipeline_results["index_ids"],
            "stages": pipeline_results["stages"],
        }

    except Exception as e:
        logger.error(f"Pipeline execution failed: {e}", exc_info=True)
        raise


async def send_completion_event(
    callback_topic: str, dbos_workflow_id: Optional[str], event_payload: Dict[str, Any]
) -> None:
    """
    Send a completion event via HTTP callback to the workflow engine.

    This notifies the workflow engine that the ingestion job has completed.

    Args:
        callback_topic: DBOS topic (used to extract execution_id and step_id)
        dbos_workflow_id: DBOS workflow ID (not used for HTTP callbacks)
        event_payload: Event data (job_id, status, result_summary or error_message)
    """
    import httpx
    import os

    try:
        # Parse callback_topic to extract execution_id and step_id
        # Format: wf:{execution_id}:{step_id}:ingestion_done
        if not callback_topic or not callback_topic.startswith("wf:"):
            logger.warning(f"Invalid callback_topic format: {callback_topic}")
            return

        parts = callback_topic.split(":")
        if len(parts) < 3:
            logger.warning(f"Cannot parse callback_topic: {callback_topic}")
            return

        execution_id = parts[1]
        step_id = parts[2]

        # Get workflow engine URL from environment
        workflow_engine_url = os.getenv("WORKFLOW_ENGINE_URL", "http://localhost:8006")
        callback_url = f"{workflow_engine_url}/api/executions/{execution_id}/steps/{step_id}/callback"

        logger.info(f"Sending HTTP callback to {callback_url}: {event_payload}")

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(callback_url, json=event_payload)
            response.raise_for_status()
            logger.info(f"Completion event sent successfully to {callback_url}")
    except Exception as e:
        logger.error(f"Failed to send completion event to {callback_topic}: {e}", exc_info=True)
        # Don't raise - we don't want to fail the job if event sending fails

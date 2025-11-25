"""
DBOS workflows for ingestion jobs.
"""

from __future__ import annotations

import logging
import uuid as uuid_module
from datetime import datetime, timezone
from typing import Dict, Any, Optional

from dbos import DBOS
from sqlmodel import Session, select

from .models import IngestionJob, JobStatus
from .database import engine

logger = logging.getLogger(__name__)


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
    logger.info(f"Starting ingestion workflow for job {job_id}")

    # Load job from database
    with Session(engine) as session:
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
        with Session(engine) as session:
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
        if callback_topic:
            event_payload = {
                "job_id": job_id,
                "status": "SUCCEEDED",
                "result_summary": result_summary,
            }
            await send_completion_event(callback_topic, dbos_workflow_id, event_payload)

        return {
            "job_id": job_id,
            "status": "SUCCEEDED",
            "result_summary": result_summary,
        }

    except Exception as e:
        error_message = str(e)
        logger.error(f"Job {job_id} failed: {error_message}", exc_info=True)

        # Update job status to FAILED
        with Session(engine) as session:
            job = session.get(IngestionJob, uuid_module.UUID(job_id))
            if job:
                job.status = JobStatus.FAILED
                job.error_message = error_message
                job.updated_at = datetime.now(timezone.utc)
                job.completed_at = datetime.now(timezone.utc)
                session.add(job)
                session.commit()

        # Send failure event if callback_topic is configured
        if callback_topic:
            event_payload = {
                "job_id": job_id,
                "status": "FAILED",
                "error_message": error_message,
            }
            await send_completion_event(callback_topic, dbos_workflow_id, event_payload)

        return {
            "job_id": job_id,
            "status": "FAILED",
            "error_message": error_message,
        }


async def execute_ingestion_pipeline(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute the elevaite_ingestion pipeline with the given configuration.

    This is a placeholder that will invoke the actual ingestion pipeline.
    The implementation will depend on how elevaite_ingestion exposes its API.

    Args:
        config: Ingestion configuration

    Returns:
        Summary of ingestion results
    """
    # TODO: Implement actual ingestion pipeline invocation
    # For now, this is a placeholder that simulates the pipeline
    logger.info(f"Executing ingestion pipeline with config: {config}")

    # The actual implementation would call into elevaite_ingestion
    # For example:
    # from elevaite_ingestion.ingest_main import main as run_ingestion
    # result = await run_ingestion(config)

    # Placeholder result
    return {
        "files_processed": 0,
        "chunks_created": 0,
        "embeddings_generated": 0,
        "index_ids": [],
    }


async def send_completion_event(callback_topic: str, dbos_workflow_id: Optional[str], event_payload: Dict[str, Any]) -> None:
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

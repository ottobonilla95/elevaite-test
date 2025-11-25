"""
Ingestion Step

Allows invoking the ingestion service as a workflow step with durable execution.
Supports two-phase execution: job creation and completion.
"""

from __future__ import annotations

import logging
import os
from typing import Dict, Any, Optional
from datetime import datetime

import httpx

from ..execution_context import ExecutionContext
from ..streaming import stream_manager

logger = logging.getLogger(__name__)

# Get ingestion service URL from environment
INGESTION_SERVICE_URL = os.getenv("INGESTION_SERVICE_URL", "http://localhost:8000")


async def ingestion_step(
    step_config: Dict[str, Any],
    input_data: Dict[str, Any],
    execution_context: ExecutionContext,
) -> Dict[str, Any]:
    """
    Execute an ingestion job via the ingestion service.

    This step has two-phase behavior:
    1. First execution: Creates an ingestion job and returns status="ingesting"
    2. Second execution: Checks job completion and returns success=True

    Config options (step_config["config"]):
    - ingestion_config: Dict[str, Any]  # Configuration for elevaite_ingestion
    - tenant_id: Optional[str]          # Tenant/organization identifier

    The step is idempotent - if called multiple times, it will:
    - On first call: Create job and return status="ingesting"
    - On subsequent calls: Check if job completed and return final result

    Args:
        step_config: Step configuration
        input_data: Input data from previous steps
        execution_context: Execution context

    Returns:
        Dict with success, status, output_data, and optional error
    """
    config = step_config.get("config", {})
    step_id = step_config.get("step_id", "ingestion")

    # Check if this is a re-entry (job already created)
    # For DBOS-backed execution, step_io_data[step_id] contains the full
    # step output dict, with the actual job info nested under "output_data".
    prior_output = execution_context.step_io_data.get(step_id, {}) or {}
    job_info = prior_output
    if isinstance(prior_output, dict) and isinstance(prior_output.get("output_data"), dict):
        job_info = prior_output["output_data"]

    ingestion_job_id = job_info.get("ingestion_job_id")
    callback_topic = job_info.get("callback_topic")

    if ingestion_job_id:
        # Second execution - job already created, check completion
        logger.info(f"Ingestion step re-entry for job {ingestion_job_id}")
        return await _check_job_completion(ingestion_job_id, callback_topic)

    # First execution - create ingestion job
    logger.info(f"Creating ingestion job for step {step_id}")

    try:
        # Build callback topic for DBOS event notification
        from ..dbos_impl.messaging import make_decision_topic

        callback_topic = make_decision_topic(
            execution_context.execution_id,
            step_id,
            suffix="ingestion_done",
        )

        # Prepare job request
        ingestion_config = config.get("ingestion_config", {})
        tenant_id = config.get("tenant_id")

        # Get DBOS workflow ID from execution metadata (if running under DBOS backend)
        dbos_workflow_id = execution_context.metadata.get("dbos_workflow_id")

        job_request = {
            "config": ingestion_config,
            "metadata": {
                "tenant_id": tenant_id,
                "execution_id": execution_context.execution_id,
                "step_id": step_id,
                "callback_topic": callback_topic,
                "dbos_workflow_id": dbos_workflow_id,  # For DBOS.send() destination_id
            },
        }

        # Call ingestion service to create job
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{INGESTION_SERVICE_URL}/ingestion/jobs",
                json=job_request,
            )
            response.raise_for_status()
            job_data = response.json()

        ingestion_job_id = job_data["job_id"]
        logger.info(f"Created ingestion job {ingestion_job_id} for step {step_id}")

        # Emit step event for ingesting status
        try:
            from ..streaming import create_step_event

            step_event = create_step_event(
                execution_id=execution_context.execution_id,
                step_id=step_id,
                step_status="ingesting",
                workflow_id=execution_context.workflow_id,
                output_data={"ingestion_job_id": ingestion_job_id},
            )
            await stream_manager.emit_execution_event(step_event)
            await stream_manager.emit_workflow_event(step_event)
        except Exception as e:
            logger.warning(f"Failed to emit ingesting event: {e}")

        # Return status="ingesting" to trigger DBOS blocking
        return {
            "success": False,  # Not complete yet
            "status": "ingesting",
            "output_data": {
                "ingestion_job_id": ingestion_job_id,
                "callback_topic": callback_topic,
                "started_at": datetime.now().isoformat(),
            },
        }

    except Exception as e:
        error_msg = f"Failed to create ingestion job: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return {
            "success": False,
            "status": "failed",
            "error": error_msg,
            "output_data": {},
        }


async def _check_job_completion(job_id: str, callback_topic: Optional[str]) -> Dict[str, Any]:
    """
    Check if an ingestion job has completed.

    This is called on re-entry after the DBOS event is received.

    Args:
        job_id: Ingestion job ID
        callback_topic: DBOS callback topic (for logging)

    Returns:
        Final step result with success=True or error
    """
    logger.info(f"Checking completion for ingestion job {job_id}")

    try:
        # Query ingestion service for job status
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{INGESTION_SERVICE_URL}/ingestion/jobs/{job_id}")
            response.raise_for_status()
            job_data = response.json()

        status = job_data.get("status")
        logger.info(f"Ingestion job {job_id} status: {status}")

        if status == "SUCCEEDED":
            return {
                "success": True,
                "status": "completed",
                "output_data": {
                    "ingestion_job_id": job_id,
                    "result_summary": job_data.get("result_summary", {}),
                    "completed_at": job_data.get("completed_at"),
                },
            }
        elif status == "FAILED":
            error_msg = job_data.get("error_message", "Ingestion job failed")
            return {
                "success": False,
                "status": "failed",
                "error": error_msg,
                "output_data": {"ingestion_job_id": job_id},
            }
        else:
            # Job still running - this shouldn't happen if DBOS event was sent correctly
            logger.warning(f"Job {job_id} status is {status}, expected SUCCEEDED or FAILED")
            return {
                "success": False,
                "status": "ingesting",
                "output_data": {"ingestion_job_id": job_id, "callback_topic": callback_topic},
            }

    except Exception as e:
        error_msg = f"Failed to check job status: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return {
            "success": False,
            "status": "failed",
            "error": error_msg,
            "output_data": {"ingestion_job_id": job_id},
        }

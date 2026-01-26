"""
Ingestion Service FastAPI Application
"""

from __future__ import annotations

# Load environment variables FIRST, before any other imports
# This ensures AWS_ENDPOINT_URL is set before boto3 clients are created
from dotenv import load_dotenv

load_dotenv()

import logging
import os
import uuid as uuid_module
from contextlib import asynccontextmanager
from typing import Dict

from fastapi import FastAPI, HTTPException, Depends
from sqlmodel import Session
from dbos import DBOS, DBOSConfig

# Configure logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Early DBOS initialization (before importing workflows with decorators)
try:
    from .database import DATABASE_URL

    _dbos_db_url = os.getenv("DBOS_DATABASE_URL") or os.getenv("DATABASE_URL") or DATABASE_URL
    _app_name = os.getenv("DBOS_APPLICATION_NAME") or "ingestion-service"
    _cfg = DBOSConfig(database_url=_dbos_db_url, name=_app_name)
    DBOS(config=_cfg)
    logger.info(f"✅ DBOS pre-initialized for {_app_name}")
except Exception as e:
    logger.warning(f"DBOS pre-init failed: {e}")

# Import workflows AFTER DBOS is initialized
from .models import IngestionJob, CreateJobRequest, JobResponse, JobStatus
from .database import get_session
from .workflows import run_ingestion_job


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    logger.info("Starting Ingestion Service...")

    # Database tables should be created via migrations (Alembic)
    logger.info("Database tables expected to exist from migrations")

    # Initialize DBOS (synchronous call)
    try:
        DBOS.launch()
        logger.info("DBOS initialized")
    except Exception as e:
        logger.error(f"Failed to initialize DBOS: {e}")
        raise

    yield

    # Cleanup
    logger.info("Shutting down Ingestion Service...")


# Create FastAPI app
app = FastAPI(
    title="Elevaite Ingestion Service",
    description="Microservice for running ingestion jobs with DBOS durable execution",
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/health")
async def health_check() -> Dict[str, str]:
    """Health check endpoint"""
    return {"status": "healthy"}


@app.post("/ingestion/jobs", response_model=JobResponse)
async def create_ingestion_job(
    request: CreateJobRequest,
    session: Session = Depends(get_session),
) -> JobResponse:
    """
    Create a new ingestion job.

    This endpoint:
    1. Validates the ingestion config
    2. Creates an IngestionJob record with status=PENDING
    3. Starts a DBOS workflow to execute the ingestion
    4. Returns the job ID and status

    Args:
        request: Job creation request with config and metadata

    Returns:
        Job response with job_id and status
    """
    try:
        # Extract metadata
        metadata = request.metadata or {}
        tenant_id = metadata.get("tenant_id")
        execution_id = metadata.get("execution_id")
        step_id = metadata.get("step_id")
        callback_topic = metadata.get("callback_topic")
        dbos_workflow_id = metadata.get("dbos_workflow_id")

        # Create job record
        job = IngestionJob(
            config=request.config,
            status=JobStatus.PENDING,
            callback_topic=callback_topic,
            tenant_id=tenant_id,
            execution_id=execution_id,
            step_id=step_id,
            dbos_workflow_id=dbos_workflow_id,
        )

        session.add(job)
        session.commit()
        session.refresh(job)

        logger.info(f"Created ingestion job {job.id}")

        # Start DBOS workflow asynchronously
        job_id_str = str(job.id)
        try:
            handle = await DBOS.start_workflow_async(run_ingestion_job, job_id_str)
            logger.info(f"Started DBOS workflow for job {job_id_str}, workflow_id={handle.workflow_id}")
        except Exception as e:
            logger.error(f"Failed to start DBOS workflow for job {job_id_str}: {e}")
            # Update job status to FAILED
            job.status = JobStatus.FAILED
            job.error_message = f"Failed to start workflow: {str(e)}"
            session.add(job)
            session.commit()
            session.refresh(job)

        return JobResponse(
            job_id=job.id,
            status=job.status,
            error_message=job.error_message,
            result_summary=job.result_summary,
            created_at=job.created_at,
            updated_at=job.updated_at,
            completed_at=job.completed_at,
        )

    except Exception as e:
        logger.error(f"Error creating ingestion job: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to create job: {str(e)}")


@app.get("/ingestion/jobs/{job_id}", response_model=JobResponse)
async def get_ingestion_job(
    job_id: uuid_module.UUID,
    session: Session = Depends(get_session),
) -> JobResponse:
    """
    Get the status of an ingestion job.

    This endpoint is intended for debugging and UI display,
    not for tight polling by the workflow engine.

    Args:
        job_id: UUID of the job

    Returns:
        Job status and details
    """
    job = session.get(IngestionJob, job_id)

    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    return JobResponse(
        job_id=job.id,
        status=job.status,
        error_message=job.error_message,
        result_summary=job.result_summary,
        created_at=job.created_at,
        updated_at=job.updated_at,
        completed_at=job.completed_at,
    )

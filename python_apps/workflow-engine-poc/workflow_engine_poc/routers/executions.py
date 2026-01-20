"""
Execution status and results endpoints
"""

import asyncio
import logging
from datetime import datetime, timezone
from fastapi import APIRouter, Request, HTTPException, Depends, Security, Header, Body
from fastapi.responses import StreamingResponse
from fastapi.security.api_key import APIKeyHeader
from typing import Optional, Dict, Any
from sqlmodel import Session
from workflow_core_sdk.db.database import get_db_session
from workflow_core_sdk.services.executions_service import ExecutionsService
from workflow_core_sdk.services.workflows_service import WorkflowsService
from workflow_core_sdk.streaming import (
    stream_manager,
    create_sse_stream,
    get_sse_headers,
    create_status_event,
)

from workflow_core_sdk import WorkflowEngine
from ..util import api_key_or_user_guard

from rbac_sdk import (
    HDR_API_KEY,
    HDR_USER_ID,
    HDR_ORG_ID,
    HDR_ACCOUNT_ID,
    HDR_PROJECT_ID,
)

logger = logging.getLogger(__name__)

# Swagger/OpenAPI: expose API key header for testing in docs
api_key_header = APIKeyHeader(name=HDR_API_KEY, auto_error=False)

router = APIRouter(prefix="/executions", tags=["executions"])


@router.get("/{execution_id}", dependencies=[Depends(api_key_or_user_guard("view_execution"))])
async def get_execution_status(
    execution_id: str,
    request: Request,
    session: Session = Depends(get_db_session),
    # RBAC headers for Swagger UI testing
    api_key: Optional[str] = Security(api_key_header),
    user_id: Optional[str] = Header(default=None, alias=HDR_USER_ID),
    org_id: Optional[str] = Header(default=None, alias=HDR_ORG_ID),
    project_id: Optional[str] = Header(default=None, alias=HDR_PROJECT_ID),
    account_id: Optional[str] = Header(default=None, alias=HDR_ACCOUNT_ID),
):
    """Get the status of a workflow execution.

    - Prefer in-memory engine context if available (most up-to-date)
    - Fallback to persisted DB execution if context not found
    """
    try:
        workflow_engine: WorkflowEngine = request.app.state.workflow_engine
        execution_context = await workflow_engine.get_execution_context(execution_id)

        if execution_context:
            summary = execution_context.get_execution_summary()
            # For backwards compatibility, expose both flattened fields and nested
            # summary, and include step_io_data so clients can inspect step outputs.
            return {
                **summary,
                "execution_summary": summary,
                "step_io_data": execution_context.step_io_data,
            }

        # Fallback to DB record
        details = ExecutionsService.get_execution(session, execution_id)
        if not details:
            raise HTTPException(status_code=404, detail="Execution not found")

        status_val = details.get("status")
        if status_val is None:
            status_str = "unknown"
        else:
            status_str = getattr(status_val, "value", status_val)

        # Heuristic: if DB says waiting but we just received a recent user message, surface as running
        if status_str == "waiting":
            try:
                msgs = WorkflowsService.list_agent_messages(session, execution_id=execution_id, limit=1, offset=0)
                if msgs:
                    created_at = msgs[0].get("created_at")
                    if isinstance(created_at, str):
                        ts = datetime.fromisoformat(created_at)
                    else:
                        ts = None
                    now = datetime.now(timezone.utc)
                    if ts and (now - ts).total_seconds() <= 90:
                        status_str = "running"
            except Exception:
                pass

        # Build execution summary from DB record and any stored metadata summary (e.g., DBOS)
        metadata = details.get("metadata") or {}
        summary_meta: Dict[str, Any] = {}
        if isinstance(metadata, dict):
            raw_summary = metadata.get("summary") or {}
            if isinstance(raw_summary, dict) and raw_summary:
                summary_meta = raw_summary

        # Fallback: derive a minimal summary from persisted step_io_data if we have none
        step_io_from_db = details.get("step_io_data") or {}
        if (not summary_meta or not summary_meta.get("total_steps")) and isinstance(step_io_from_db, dict) and step_io_from_db:
            # Treat each non-internal key as a step; this is a heuristic but ensures
            # DBOS-backed executions surface a non-zero step count even if metadata
            # summary was not persisted for some reason.
            visible_keys = [k for k in step_io_from_db.keys() if not str(k).endswith("_raw")]
            total_steps_fallback = len(visible_keys) if visible_keys else len(step_io_from_db)
            completed_steps_fallback = (
                total_steps_fallback if status_str == "completed" else summary_meta.get("completed_steps", 0)
            )
            summary_meta = {
                **summary_meta,
                "total_steps": total_steps_fallback,
                "steps_executed": summary_meta.get("steps_executed", total_steps_fallback),
                "completed_steps": completed_steps_fallback,
                "failed_steps": summary_meta.get("failed_steps", 0),
            }

        # Log for debugging what we are about to return from the DB fallback path
        try:
            logger.info(
                "Execution status DB fallback for %s: status=%s total_steps=%s completed_steps=%s step_io_keys=%s",
                execution_id,
                status_str,
                summary_meta.get("total_steps"),
                summary_meta.get("completed_steps"),
                list(step_io_from_db.keys()) if isinstance(step_io_from_db, dict) else None,
            )
        except Exception:
            # Logging must never break the endpoint
            pass

        execution_summary = {
            "execution_id": details.get("execution_id"),
            "workflow_id": details.get("workflow_id"),
            "status": status_str,
            "current_step": None,
            "completed_steps": summary_meta.get("completed_steps"),
            "failed_steps": summary_meta.get("failed_steps"),
            "pending_steps": None,
            "total_steps": summary_meta.get("total_steps"),
            "started_at": details.get("started_at"),
            "completed_at": details.get("completed_at"),
            "error_message": details.get("error_message"),
            "analytics_ids": None,
            "execution_time_seconds": details.get("execution_time_seconds"),
            "user_context": {
                "user_id": details.get("user_id"),
                "session_id": details.get("session_id"),
            },
        }

        # Keep top-level summary fields for backwards compatibility and also expose
        # nested execution_summary and step_io_data from the DB record.
        return {
            **execution_summary,
            "execution_summary": execution_summary,
            "step_io_data": step_io_from_db,
            "execution_metadata": metadata,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get execution status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{execution_id}/results", dependencies=[Depends(api_key_or_user_guard("view_execution"))])
async def get_execution_results(
    execution_id: str,
    request: Request,
    session: Session = Depends(get_db_session),
    # RBAC headers for Swagger UI testing
    api_key: Optional[str] = Security(api_key_header),
    user_id: Optional[str] = Header(default=None, alias=HDR_USER_ID),
    org_id: Optional[str] = Header(default=None, alias=HDR_ORG_ID),
    project_id: Optional[str] = Header(default=None, alias=HDR_PROJECT_ID),
    account_id: Optional[str] = Header(default=None, alias=HDR_ACCOUNT_ID),
):
    """Get the detailed results of a workflow execution.

    Returns in-memory results when available; otherwise falls back to DB record.
    """
    try:
        workflow_engine: WorkflowEngine = request.app.state.workflow_engine
        execution_context = await workflow_engine.get_execution_context(execution_id)

        if execution_context:
            # Convert step results to serializable format
            step_results = {}
            for step_id, result in execution_context.step_results.items():
                step_results[step_id] = {
                    "step_id": result.step_id,
                    "status": result.status.value,
                    "output_data": result.output_data,
                    "error_message": result.error_message,
                    "execution_time_ms": result.execution_time_ms,
                }

            # Include step_io_data for clients that need in-flight outputs (e.g., retrievals)
            return {
                "execution_id": execution_id,
                "status": execution_context.status.value,
                "step_results": step_results,
                "step_io_data": execution_context.step_io_data,
                "global_variables": execution_context.global_variables,
                "execution_summary": execution_context.get_execution_summary(),
            }

        # Fallback: DB
        details = ExecutionsService.get_execution(session, execution_id)
        if not details:
            raise HTTPException(status_code=404, detail="Execution not found")
        status_val = details.get("status")
        if status_val is None:
            status_str = "unknown"
        else:
            status_str = getattr(status_val, "value", status_val)

        # Build step_results from step_io_data for parity between local and DBOS backends
        step_io_data = details.get("step_io_data") or {}
        step_results = {}
        for step_id, output_data in step_io_data.items():
            step_results[step_id] = {
                "step_id": step_id,
                "status": "completed" if isinstance(output_data, dict) and output_data.get("success") else "unknown",
                "output_data": output_data,
                "error_message": output_data.get("error") if isinstance(output_data, dict) else None,
                "execution_time_ms": None,  # Not tracked in step_io_data
            }

        return {
            "execution_id": details.get("execution_id"),
            "status": status_str,
            "step_results": step_results,
            "global_variables": {},
            "execution_summary": {
                "execution_id": details.get("execution_id"),
                "workflow_id": details.get("workflow_id"),
                "status": status_str,
                "started_at": details.get("started_at"),
                "completed_at": details.get("completed_at"),
                "error_message": details.get("error_message"),
                "execution_time_seconds": details.get("execution_time_seconds"),
            },
            "db_record": details,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get execution results: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", dependencies=[Depends(api_key_or_user_guard("view_execution"))])
async def get_execution_analytics(
    request: Request,
    limit: int = 100,
    offset: int = 0,
    status: Optional[str] = None,
    workflow_id: Optional[str] = None,
    exclude_db: bool = False,
    session: Session = Depends(get_db_session),
    # RBAC headers for Swagger UI testing
    api_key: Optional[str] = Security(api_key_header),
    user_id: Optional[str] = Header(default=None, alias=HDR_USER_ID),
    org_id: Optional[str] = Header(default=None, alias=HDR_ORG_ID),
    project_id: Optional[str] = Header(default=None, alias=HDR_PROJECT_ID),
    account_id: Optional[str] = Header(default=None, alias=HDR_ACCOUNT_ID),
):
    """Get execution analytics and history.

    - Always returns engine analytics
    - By default also includes DB executions in "db_executions"
    - If exclude_db is True, only in-memory analytics are returned
    """
    try:
        workflow_engine: WorkflowEngine = request.app.state.workflow_engine
        analytics = await workflow_engine.get_execution_analytics(limit=limit, offset=offset, status=status)

        if exclude_db:
            return analytics

        db_items = ExecutionsService.list_executions(
            session, workflow_id=workflow_id, status=status, limit=limit, offset=offset
        )
        # Merge: keep analytics as-is and attach db_executions; additive for clients
        return {**analytics, "db_executions": db_items}
    except Exception as e:
        logger.error(f"Failed to get execution analytics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{execution_id}/stream", dependencies=[Depends(api_key_or_user_guard("view_execution"))])
async def stream_execution_updates(
    execution_id: str,
    request: Request,
    session: Session = Depends(get_db_session),
    # RBAC headers for Swagger UI testing
    api_key: Optional[str] = Security(api_key_header),
    user_id: Optional[str] = Header(default=None, alias=HDR_USER_ID),
    org_id: Optional[str] = Header(default=None, alias=HDR_ORG_ID),
    project_id: Optional[str] = Header(default=None, alias=HDR_PROJECT_ID),
    account_id: Optional[str] = Header(default=None, alias=HDR_ACCOUNT_ID),
):
    """Stream real-time updates for a specific execution using Server-Sent Events (SSE)."""
    try:
        workflow_engine: WorkflowEngine = request.app.state.workflow_engine

        # Verify execution exists (either in memory or DB)
        execution_context = await workflow_engine.get_execution_context(execution_id)
        if not execution_context:
            # Check if it exists in DB
            db_execution = ExecutionsService.get_execution(session, execution_id)
            if not db_execution:
                raise HTTPException(status_code=404, detail="Execution not found")

        # Create a queue for this streaming connection (larger buffer for delta streaming)
        queue = asyncio.Queue(maxsize=1000)

        async def event_generator():
            try:
                # Add this connection to the stream manager
                stream_manager.add_execution_stream(execution_id, queue)

                # Send initial status if execution exists
                if execution_context:
                    initial_event = create_status_event(
                        execution_id=execution_id,
                        status=execution_context.status.value,
                        workflow_id=execution_context.workflow_id,
                        step_count=len(execution_context.steps_config),
                        completed_steps=len(execution_context.completed_steps),
                        failed_steps=len(execution_context.failed_steps),
                    )
                    yield initial_event.to_sse()
                elif db_execution:
                    # Send DB status for completed executions
                    initial_event = create_status_event(
                        execution_id=execution_id,
                        status=db_execution.get("status", "unknown"),
                        workflow_id=str(db_execution.get("workflow_id", "")),
                        from_db=True,
                    )
                    yield initial_event.to_sse()

                # Stream events from the queue
                async for event_data in create_sse_stream(queue, heartbeat_interval=30, max_events=5000):
                    yield event_data

            except asyncio.CancelledError:
                logger.debug(f"Streaming cancelled for execution {execution_id}")
            except Exception as e:
                logger.error(f"Error in execution stream {execution_id}: {e}")
                # Send error event
                error_event = create_status_event(execution_id=execution_id, status="error", error=str(e))
                yield error_event.to_sse()
            finally:
                # Clean up the connection
                stream_manager.remove_execution_stream(execution_id, queue)

        return StreamingResponse(event_generator(), media_type="text/event-stream", headers=get_sse_headers())

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start execution stream {execution_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# New SQLModel-based execution endpoints


@router.post("/{execution_id}/steps/{step_id}/callback")
async def step_callback(
    execution_id: str,
    step_id: str,
    callback_data: Dict[str, Any] = Body(...),
    session: Session = Depends(get_db_session),
):
    """
    Receive callback from external services (e.g., ingestion service) when a step completes.

    This endpoint is called by external services to notify the workflow engine that
    an asynchronous step has completed. For DBOS workflows, this sends a message to
    the workflow instance to resume execution.

    Args:
        execution_id: The execution ID
        step_id: The step ID that completed
        callback_data: Callback payload (job_id, status, result_summary or error_message)
    """
    try:
        logger.info(f"Received callback for execution {execution_id}, step {step_id}: {callback_data}")

        # Get execution from database to determine backend
        from ..db.service import DatabaseService

        db_service = DatabaseService()
        execution = db_service.get_execution(session, execution_id)

        if not execution:
            raise HTTPException(status_code=404, detail=f"Execution {execution_id} not found")

        # Get backend from execution metadata
        metadata = execution.get("metadata", {})
        backend = metadata.get("backend", "local")

        if backend == "dbos":
            # For DBOS workflows, send a message to the workflow instance
            try:
                from dbos import DBOS as _DBOS

                # Get DBOS workflow ID from execution metadata
                dbos_workflow_id = metadata.get("dbos_workflow_id")
                if not dbos_workflow_id:
                    raise HTTPException(
                        status_code=400, detail=f"DBOS workflow ID not found in execution metadata for {execution_id}"
                    )

                # Send message to DBOS workflow
                callback_topic = f"wf:{execution_id}:{step_id}:ingestion_done"
                logger.info(f"Sending DBOS message to workflow {dbos_workflow_id} on topic {callback_topic}")
                _DBOS.send(destination_id=dbos_workflow_id, message=callback_data, topic=callback_topic)
                logger.info(f"DBOS message sent successfully")

                return {"status": "ok", "message": "Callback received and forwarded to DBOS workflow"}
            except Exception as e:
                logger.error(f"Failed to send DBOS message: {e}", exc_info=True)
                raise HTTPException(status_code=500, detail=f"Failed to forward callback to DBOS: {str(e)}")
        else:
            # For local backend, resume execution directly
            # TODO: Implement local backend callback handling if needed
            logger.warning(
                f"Callback received for local backend execution {execution_id}, but local callback handling is not implemented yet"
            )
            return {"status": "ok", "message": "Callback received (local backend handling not implemented)"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to process callback for {execution_id}/{step_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

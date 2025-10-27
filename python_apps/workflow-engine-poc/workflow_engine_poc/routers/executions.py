"""
Execution status and results endpoints
"""

import asyncio
import logging
from datetime import datetime, timezone
from fastapi import APIRouter, Request, HTTPException, Depends, Security, Header
from fastapi.responses import StreamingResponse
from fastapi.security.api_key import APIKeyHeader
from typing import Optional
from sqlmodel import Session
from ..db.database import get_db_session
from ..services.executions_service import ExecutionsService
from ..services.workflows_service import WorkflowsService
from ..streaming import (
    stream_manager,
    create_sse_stream,
    get_sse_headers,
    create_status_event,
)

from ..workflow_engine import WorkflowEngine

from rbac_sdk import (
    require_permission_async,
    resource_builders,
    principal_resolvers,
    HDR_API_KEY,
    HDR_USER_ID,
    HDR_ORG_ID,
    HDR_ACCOUNT_ID,
    HDR_PROJECT_ID,
)

logger = logging.getLogger(__name__)

# Swagger/OpenAPI: expose API key header for testing in docs
api_key_header = APIKeyHeader(name=HDR_API_KEY, auto_error=False)

# RBAC guard: view_project required for viewing executions
_guard_view_project = require_permission_async(
    action="view_project",
    resource_builder=resource_builders.project_from_headers(
        project_header=HDR_PROJECT_ID,
        account_header=HDR_ACCOUNT_ID,
        org_header=HDR_ORG_ID,
    ),
    principal_resolver=principal_resolvers.api_key_or_user(),
)

router = APIRouter(prefix="/executions", tags=["executions"])


@router.get("/{execution_id}", dependencies=[Depends(_guard_view_project)])
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
            return execution_context.get_execution_summary()

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

        return {
            "execution_id": details.get("execution_id"),
            "workflow_id": details.get("workflow_id"),
            "status": status_str,
            "current_step": None,
            "completed_steps": None,
            "failed_steps": None,
            "pending_steps": None,
            "total_steps": None,
            "started_at": details.get("started_at"),
            "completed_at": details.get("completed_at"),
            "analytics_ids": None,
            "user_context": {"user_id": details.get("user_id"), "session_id": details.get("session_id")},
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get execution status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{execution_id}/results", dependencies=[Depends(_guard_view_project)])
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
        return {
            "execution_id": details.get("execution_id"),
            "status": status_str,
            "step_results": {},  # No per-step timing in DB record; consumers should treat as unavailable
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


@router.get("/", dependencies=[Depends(_guard_view_project)])
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


@router.get("/{execution_id}/stream", dependencies=[Depends(_guard_view_project)])
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

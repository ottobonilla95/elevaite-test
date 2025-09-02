"""
Execution status and results endpoints
"""

import logging
from fastapi import APIRouter, Request, HTTPException
from typing import Optional
from fastapi import Depends
from sqlmodel import Session
from ..db.models import WorkflowExecutionRead, WorkflowExecutionUpdate, ExecutionStatus
from ..db.database import get_db_session
from ..db.service import DatabaseService

from ..workflow_engine import WorkflowEngine

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/executions", tags=["executions"])


@router.get("/{execution_id}")
async def get_execution_status(execution_id: str, request: Request, session: Session = Depends(get_db_session)):
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
        db_service = DatabaseService()
        details = db_service.get_execution(session, execution_id)
        if not details:
            raise HTTPException(status_code=404, detail="Execution not found")

        status_val = details.get("status")
        if status_val is None:
            status_str = "unknown"
        else:
            status_str = getattr(status_val, "value", status_val)
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


@router.get("/{execution_id}/results")
async def get_execution_results(execution_id: str, request: Request, session: Session = Depends(get_db_session)):
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

            return {
                "execution_id": execution_id,
                "status": execution_context.status.value,
                "step_results": step_results,
                "global_variables": execution_context.global_variables,
                "execution_summary": execution_context.get_execution_summary(),
            }

        # Fallback: DB
        db_service = DatabaseService()
        details = db_service.get_execution(session, execution_id)
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


@router.get("/")
async def get_execution_analytics(
    request: Request,
    limit: int = 100,
    offset: int = 0,
    status: Optional[str] = None,
    workflow_id: Optional[str] = None,
    exclude_db: bool = False,
    session: Session = Depends(get_db_session),
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

        db_service = DatabaseService()
        db_items = db_service.list_executions(session, workflow_id=workflow_id, status=status, limit=limit, offset=offset)
        # Merge: keep analytics as-is and attach db_executions; additive for clients
        return {**analytics, "db_executions": db_items}
    except Exception as e:
        logger.error(f"Failed to get execution analytics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# New SQLModel-based execution endpoints

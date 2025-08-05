from typing import List, Optional
from datetime import datetime, timedelta
import uuid
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from db.database import get_db
from db import crud, schemas

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


@router.get("/health")
def analytics_health():
    """
    Health check endpoint for analytics service.
    """
    return {
        "status": "healthy",
        "service": "analytics",
        "timestamp": datetime.now().isoformat(),
        "available_endpoints": [
            "/api/analytics/agents/usage",
            "/api/analytics/tools/usage",
            "/api/analytics/workflows/performance",
            "/api/analytics/errors/summary",
            "/api/analytics/sessions/activity",
            "/api/analytics/summary",
            "/api/analytics/executions/{execution_id}",
            "/api/analytics/sessions/{session_id}",
        ],
    }


@router.get("/agents/usage")
def get_agent_usage_statistics(
    days: Optional[int] = Query(None, description="Number of days to look back"),
    start_date: Optional[datetime] = Query(
        None, description="Start date for filtering"
    ),
    end_date: Optional[datetime] = Query(None, description="End date for filtering"),
    db: Session = Depends(get_db),
):
    """
    Get agent usage statistics including execution counts, success rates, and performance metrics.
    """
    try:
        # Set date range if days parameter is provided
        if days and not start_date and not end_date:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)

        # Use the analytics summary function which provides agent stats
        summary = crud.get_analytics_summary(
            db=db, start_date=start_date, end_date=end_date
        )
        return summary.get("agent_stats", [])
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error retrieving agent usage statistics: {str(e)}"
        )


@router.get("/tools/usage")
def get_tool_usage_statistics(
    days: Optional[int] = Query(None, description="Number of days to look back"),
    start_date: Optional[datetime] = Query(
        None, description="Start date for filtering"
    ),
    end_date: Optional[datetime] = Query(None, description="End date for filtering"),
    db: Session = Depends(get_db),
):
    """
    Get tool usage statistics including call counts, success rates, and performance metrics.
    """
    try:
        # Set date range if days parameter is provided
        if days and not start_date and not end_date:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)

        # Use the analytics summary function which provides tool stats
        summary = crud.get_analytics_summary(
            db=db, start_date=start_date, end_date=end_date
        )
        return summary.get("tool_stats", [])
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error retrieving tool usage statistics: {str(e)}"
        )


@router.get("/workflows/performance")
def get_workflow_performance_statistics(
    days: Optional[int] = Query(None, description="Number of days to look back"),
    start_date: Optional[datetime] = Query(
        None, description="Start date for filtering"
    ),
    end_date: Optional[datetime] = Query(None, description="End date for filtering"),
    db: Session = Depends(get_db),
):
    """
    Get workflow performance statistics including execution times and success rates.
    """
    try:
        # Set date range if days parameter is provided
        if days and not start_date and not end_date:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)

        # For now, return empty list as workflow stats are not implemented in analytics summary
        # TODO: Implement workflow performance stats in crud.get_analytics_summary
        return []
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving workflow performance statistics: {str(e)}",
        )


@router.get("/errors/summary")
def get_error_summary(
    days: Optional[int] = Query(None, description="Number of days to look back"),
    start_date: Optional[datetime] = Query(
        None, description="Start date for filtering"
    ),
    end_date: Optional[datetime] = Query(None, description="End date for filtering"),
    db: Session = Depends(get_db),
):
    """
    Get error summary statistics including error types, counts, and affected agents.
    """
    try:
        # Set date range if days parameter is provided
        if days and not start_date and not end_date:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)

        # For now, return empty list as error summary is not implemented
        # TODO: Implement error summary stats
        return []
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error retrieving error summary: {str(e)}"
        )


@router.get("/sessions/activity")
def get_session_activity_statistics(
    days: Optional[int] = Query(None, description="Number of days to look back"),
    start_date: Optional[datetime] = Query(
        None, description="Start date for filtering"
    ),
    end_date: Optional[datetime] = Query(None, description="End date for filtering"),
    db: Session = Depends(get_db),
):
    """
    Get session activity statistics including active sessions, query counts, and success rates.
    """
    try:
        # Set date range if days parameter is provided
        if days and not start_date and not end_date:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)

        # Use the analytics summary function which provides session stats
        summary = crud.get_analytics_summary(
            db=db, start_date=start_date, end_date=end_date
        )
        return summary.get("session_stats", {})
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving session activity statistics: {str(e)}",
        )


@router.get("/summary")
def get_analytics_summary(
    days: Optional[int] = Query(7, description="Number of days to look back"),
    start_date: Optional[datetime] = Query(
        None, description="Start date for filtering"
    ),
    end_date: Optional[datetime] = Query(None, description="End date for filtering"),
    db: Session = Depends(get_db),
):
    """
    Get a comprehensive analytics summary including all key metrics.
    """
    try:
        # Set date range if days parameter is provided
        if not start_date and not end_date:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days or 7)

        time_period = f"{start_date.strftime('%Y-%m-%d') if start_date else 'N/A'} to {end_date.strftime('%Y-%m-%d') if end_date else 'N/A'}"

        # Get the analytics summary from CRUD
        summary = crud.get_analytics_summary(
            db=db, start_date=start_date, end_date=end_date
        )

        return {
            "time_period": time_period,
            "agent_stats": summary.get("agent_stats", []),
            "tool_stats": summary.get("tool_stats", []),
            "workflow_stats": [],  # TODO: Implement workflow stats
            "error_summary": [],  # TODO: Implement error summary
            "session_stats": summary.get("session_stats", {}),
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error retrieving analytics summary: {str(e)}"
        )


@router.get("/executions/{execution_id}")
def get_execution_details(execution_id: str, db: Session = Depends(get_db)):
    """
    Get detailed information about a specific execution (agent or workflow).
    Checks live executions first, then database records.
    """
    try:
        # First check live executions in analytics service
        from services.analytics_service import analytics_service

        live_execution = analytics_service.get_execution(execution_id)

        if live_execution:
            # Return live execution data with additional analytics
            return {
                "execution_id": live_execution.execution_id,
                "type": live_execution.type,
                "status": live_execution.status,
                "progress": live_execution.progress,
                "current_step": live_execution.current_step,
                "agent_id": live_execution.agent_id,
                "workflow_id": live_execution.workflow_id,
                "session_id": live_execution.session_id,
                "user_id": live_execution.user_id,
                "query": live_execution.query,
                "input_data": live_execution.input_data,
                "result": live_execution.result,
                "error": live_execution.error,
                "tools_called": live_execution.tools_called,
                "created_at": live_execution.created_at,
                "started_at": live_execution.started_at,
                "completed_at": live_execution.completed_at,
                "estimated_completion": live_execution.estimated_completion,
                "workflow_trace": live_execution.workflow_trace,
                "source": "live",
            }

        # If not found in live executions, check database for historical records
        try:
            execution_uuid = uuid.UUID(execution_id)
            execution = crud.get_agent_execution_metrics(
                db=db, execution_id=execution_uuid
            )
            if execution:
                return {
                    "execution_id": str(execution.execution_id),
                    "type": "agent",
                    "agent_id": str(execution.agent_id),
                    "agent_name": execution.agent_name,
                    "status": execution.status,
                    "query": execution.query,
                    "response": execution.response,
                    "error_message": execution.error_message,
                    "start_time": execution.start_time,
                    "end_time": execution.end_time,
                    "duration_ms": execution.duration_ms,
                    "tool_count": execution.tool_count,
                    "session_id": execution.session_id,
                    "user_id": execution.user_id,
                    "source": "database",
                }
        except ValueError:
            # Invalid UUID format, but that's okay - might be a workflow execution ID
            pass

        # Not found in either live or database
        raise HTTPException(status_code=404, detail="Execution not found")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error retrieving execution details: {str(e)}"
        )


@router.get("/sessions/{session_id}")
def get_session_details(session_id: str, db: Session = Depends(get_db)):
    """
    Get detailed information about a specific session.
    """
    try:
        session = crud.get_session_metrics(db=db, session_id=session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        return session
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error retrieving session details: {str(e)}"
        )

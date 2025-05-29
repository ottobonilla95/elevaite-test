from typing import List, Optional
from datetime import datetime, timedelta
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


@router.get("/agents/usage", response_model=List[schemas.AgentUsageStats])
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

        return crud.get_agent_usage_stats(
            db=db, start_date=start_date, end_date=end_date
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error retrieving agent usage statistics: {str(e)}"
        )


@router.get("/tools/usage", response_model=List[schemas.ToolUsageStats])
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

        return crud.get_tool_usage_stats(
            db=db, start_date=start_date, end_date=end_date
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error retrieving tool usage statistics: {str(e)}"
        )


@router.get(
    "/workflows/performance", response_model=List[schemas.WorkflowPerformanceStats]
)
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

        return crud.get_workflow_performance_stats(
            db=db, start_date=start_date, end_date=end_date
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving workflow performance statistics: {str(e)}",
        )


@router.get("/errors/summary", response_model=List[schemas.ErrorSummary])
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

        return crud.get_error_summary(db=db, start_date=start_date, end_date=end_date)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error retrieving error summary: {str(e)}"
        )


@router.get("/sessions/activity", response_model=schemas.SessionActivityStats)
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

        return crud.get_session_activity_stats(
            db=db, start_date=start_date, end_date=end_date
        )
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

        return {
            "time_period": time_period,
            "agent_stats": crud.get_agent_usage_stats(
                db=db, start_date=start_date, end_date=end_date
            ),
            "tool_stats": crud.get_tool_usage_stats(
                db=db, start_date=start_date, end_date=end_date
            ),
            "workflow_stats": crud.get_workflow_performance_stats(
                db=db, start_date=start_date, end_date=end_date
            ),
            "error_summary": crud.get_error_summary(
                db=db, start_date=start_date, end_date=end_date
            ),
            "session_stats": crud.get_session_activity_stats(
                db=db, start_date=start_date, end_date=end_date
            ),
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error retrieving analytics summary: {str(e)}"
        )


@router.get("/executions/{execution_id}")
def get_execution_details(execution_id: str, db: Session = Depends(get_db)):
    """
    Get detailed information about a specific agent execution.
    """
    try:
        execution = crud.get_agent_execution_by_id(db=db, execution_id=execution_id)
        if not execution:
            raise HTTPException(status_code=404, detail="Execution not found")
        return execution
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
        session = crud.get_session_by_id(db=db, session_id=session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        return session
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error retrieving session details: {str(e)}"
        )

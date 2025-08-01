"""
Execution status endpoints for async agent and workflow execution.
Provides status polling, listing, and management capabilities.
"""

from typing import List, Optional, Dict, Any, Literal
from fastapi import APIRouter, HTTPException, Query, Depends
from sqlalchemy.orm import Session
from services.analytics_service import analytics_service, ExecutionStatus
from db.database import get_db

router = APIRouter(prefix="/api/executions", tags=["executions"])


@router.get("/{execution_id}/status", response_model=ExecutionStatus)
def get_execution_status(execution_id: str, db: Session = Depends(get_db)):
    """
    Get the current status of an async execution by ID.
    Checks memory first, then database for historical executions.
    """
    execution = analytics_service.get_execution_with_fallback(execution_id, db)
    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")
    
    return execution


@router.get("/", response_model=List[ExecutionStatus])
def list_executions(
    status: Optional[Literal["queued", "running", "completed", "failed", "cancelled"]] = Query(None, description="Filter by status"),
    user_id: Optional[str] = Query(None, description="Filter by user_id"),
    limit: int = Query(100, description="Maximum number of executions to return")
):
    """
    List executions with optional filtering.
    """
    return analytics_service.list_executions(
        status=status,
        user_id=user_id,
        limit=limit
    )


@router.post("/{execution_id}/cancel")
def cancel_execution(execution_id: str):
    """
    Cancel a running or queued execution.
    Note: For FastAPI BackgroundTasks, this only marks as cancelled - 
    actual cancellation is limited since tasks can't be truly interrupted.
    """
    execution = analytics_service.get_execution(execution_id)
    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")
    
    if execution.status in ["completed", "failed"]:
        raise HTTPException(
            status_code=400, 
            detail=f"Cannot cancel execution with status: {execution.status}"
        )
    
    success = analytics_service.update_execution(
        execution_id,
        status="cancelled",
        current_step="Cancelled by user"
    )
    
    if not success:
        raise HTTPException(status_code=404, detail="Execution not found")
    
    return {"message": "Execution cancelled", "execution_id": execution_id}


@router.get("/{execution_id}/result")
def get_execution_result(execution_id: str, db: Session = Depends(get_db)):
    """
    Get the result of a completed execution.
    """
    execution = analytics_service.get_execution_with_fallback(execution_id, db)
    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")
    
    if execution.status == "running":
        raise HTTPException(status_code=202, detail="Execution still running")
    elif execution.status == "queued":
        raise HTTPException(status_code=202, detail="Execution queued")
    elif execution.status == "failed":
        raise HTTPException(
            status_code=500, 
            detail=f"Execution failed: {execution.error}"
        )
    elif execution.status == "cancelled":
        raise HTTPException(status_code=409, detail="Execution was cancelled")
    
    # Status is completed
    return execution.result


@router.get("/{execution_id}/trace")
def get_execution_trace(execution_id: str, db: Session = Depends(get_db)):
    """
    Get detailed workflow trace for an execution.
    Works for both live and historical executions.
    """
    execution = analytics_service.get_execution_with_fallback(execution_id, db)
    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")
    
    if execution.type != "workflow":
        raise HTTPException(status_code=400, detail="Tracing is only available for workflow executions")
    
    if not execution.workflow_trace:
        raise HTTPException(status_code=404, detail="No trace data available for this execution")
    
    return execution.workflow_trace


@router.get("/{execution_id}/steps")
def get_execution_steps(execution_id: str, db: Session = Depends(get_db)):
    """
    Get workflow steps for monitoring.
    Works for both live and historical executions.
    """
    execution = analytics_service.get_execution_with_fallback(execution_id, db)
    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")
    
    if execution.type != "workflow" or not execution.workflow_trace:
        return {"steps": [], "message": "No step data available"}
    
    steps_summary = []
    for step in execution.workflow_trace.steps:
        steps_summary.append({
            "step_id": step.step_id,
            "step_type": step.step_type,
            "agent_name": step.agent_name,
            "tool_name": step.tool_name,
            "status": step.status,
            "started_at": step.started_at.isoformat() if step.started_at else None,
            "completed_at": step.completed_at.isoformat() if step.completed_at else None,
            "duration_ms": step.duration_ms,
            "error": step.error,
            "metadata": step.metadata
        })
    
    return {
        "execution_id": execution_id,
        "current_step_index": execution.workflow_trace.current_step_index,
        "total_steps": execution.workflow_trace.total_steps,
        "steps": steps_summary,
        "execution_path": execution.workflow_trace.execution_path,
        "branch_decisions": execution.workflow_trace.branch_decisions
    }


@router.get("/{execution_id}/progress")
def get_execution_progress(execution_id: str):
    """
    Get simplified progress information for UI polling.
    Optimized for frequent polling by frontend.
    """
    execution = analytics_service.get_execution(execution_id)
    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")
    
    response = {
        "execution_id": execution_id,
        "status": execution.status,
        "progress": execution.progress,
        "current_step": execution.current_step,
        "type": execution.type
    }
    
    # Add workflow-specific progress details
    if execution.type == "workflow" and execution.workflow_trace:
        current_step_info = None
        if execution.workflow_trace.steps and execution.workflow_trace.current_step_index < len(execution.workflow_trace.steps):
            current_step = execution.workflow_trace.steps[execution.workflow_trace.current_step_index]
            current_step_info = {
                "step_type": current_step.step_type,
                "agent_name": current_step.agent_name,
                "status": current_step.status
            }
        
        response["workflow_progress"] = {
            "current_step_index": execution.workflow_trace.current_step_index,
            "total_steps": execution.workflow_trace.total_steps,
            "current_step_info": current_step_info,
            "execution_path": execution.workflow_trace.execution_path[-3:] if execution.workflow_trace.execution_path else []  # Last 3 agents
        }
    
    return response


@router.get("/stats")
def get_execution_stats():
    """
    Get execution manager statistics.
    """
    return analytics_service.get_execution_stats()


@router.get("/analytics")
def get_execution_analytics(
    execution_type: Optional[Literal["agent", "workflow"]] = Query(None, description="Filter by type"),
    status: Optional[Literal["queued", "running", "completed", "failed", "cancelled"]] = Query(None, description="Filter by status")
):
    """
    Get comprehensive execution analytics including historical data.
    Combines live execution data with persisted analytics.
    """
    live_stats = analytics_service.get_execution_stats()
    live_executions = analytics_service.list_executions(limit=1000)
    
    # Group executions by various dimensions
    by_hour = {}
    by_type = {"agent": 0, "workflow": 0}
    by_status = {"completed": 0, "failed": 0, "running": 0, "queued": 0, "cancelled": 0}
    avg_duration = {"agent": [], "workflow": []}
    
    for execution in live_executions:
        # Apply filters
        if execution_type and execution.type != execution_type:
            continue
        if status and execution.status != status:
            continue
        
        # Count by type
        by_type[execution.type] += 1
        
        # Count by status
        by_status[execution.status] += 1
        
        # Calculate durations for completed executions
        if execution.status == "completed" and execution.started_at and execution.completed_at:
            duration = (execution.completed_at - execution.started_at).total_seconds()
            avg_duration[execution.type].append(duration)
        
        # Group by hour
        hour_key = execution.created_at.strftime("%Y-%m-%d %H:00")
        if hour_key not in by_hour:
            by_hour[hour_key] = {"agent": 0, "workflow": 0}
        by_hour[hour_key][execution.type] += 1
    
    # Calculate averages
    avg_agent_duration = sum(avg_duration["agent"]) / len(avg_duration["agent"]) if avg_duration["agent"] else 0
    avg_workflow_duration = sum(avg_duration["workflow"]) / len(avg_duration["workflow"]) if avg_duration["workflow"] else 0
    
    return {
        "live_stats": live_stats,
        "analytics": {
            "by_type": by_type,
            "by_status": by_status,
            "by_hour": by_hour,
            "average_duration_seconds": {
                "agent": round(avg_agent_duration, 2),
                "workflow": round(avg_workflow_duration, 2)
            },
            "total_analyzed": len(live_executions)
        }
    }


@router.post("/cleanup")
def cleanup_completed_executions():
    """
    Manually trigger cleanup of old completed executions.
    Returns the number of executions removed.
    """
    removed_count = analytics_service.cleanup_completed()
    return {
        "message": f"Cleaned up {removed_count} completed executions",
        "removed_count": removed_count
    }


@router.get("/{execution_id}/input-output")
def get_execution_input_output(execution_id: str, db: Session = Depends(get_db)):
    """
    Get input and output data for an execution and all its steps.
    Works for both live and historical executions.
    """
    execution = analytics_service.get_execution_with_fallback(execution_id, db)
    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")
    
    response = {
        "execution_id": execution_id,
        "execution_input": execution.input_data,
        "execution_output": execution.result,
        "query": execution.query,
        "status": execution.status,
        "error": execution.error,
        "steps": []
    }
    
    # Add step input/output data if available
    if execution.workflow_trace and execution.workflow_trace.steps:
        for step in execution.workflow_trace.steps:
            step_data = {
                "step_id": step.step_id,
                "step_type": step.step_type,
                "agent_name": step.agent_name,
                "tool_name": step.tool_name,
                "status": step.status,
                "input_data": step.input_data,
                "output_data": step.output_data,
                "error": step.error,
                "duration_ms": step.duration_ms
            }
            response["steps"].append(step_data)
    
    return response



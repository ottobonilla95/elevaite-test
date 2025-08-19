"""
Execution status and results endpoints
"""
import logging
from fastapi import APIRouter, Request, HTTPException
from typing import Optional

from ..workflow_engine import WorkflowEngine

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/executions", tags=["executions"])


@router.get("/{execution_id}")
async def get_execution_status(execution_id: str, request: Request):
    """Get the status of a workflow execution"""
    try:
        workflow_engine: WorkflowEngine = request.app.state.workflow_engine
        execution_context = await workflow_engine.get_execution_context(execution_id)

        if not execution_context:
            raise HTTPException(status_code=404, detail="Execution not found")

        return execution_context.get_status_summary()

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get execution status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{execution_id}/results")
async def get_execution_results(execution_id: str, request: Request):
    """Get the detailed results of a workflow execution"""
    try:
        workflow_engine: WorkflowEngine = request.app.state.workflow_engine
        execution_context = await workflow_engine.get_execution_context(execution_id)

        if not execution_context:
            raise HTTPException(status_code=404, detail="Execution not found")

        # Convert step results to serializable format
        step_results = {}
        for step_id, result in execution_context.step_results.items():
            step_results[step_id] = {
                "step_id": result.step_id,
                "status": result.status.value,
                "output_data": result.output_data,
                "error_message": result.error_message,
                "execution_time_ms": result.execution_time_ms,
                "started_at": result.started_at.isoformat() if result.started_at else None,
                "completed_at": (
                    result.completed_at.isoformat() if result.completed_at else None
                ),
            }

        return {
            "execution_id": execution_id,
            "status": execution_context.status.value,
            "step_results": step_results,
            "global_variables": execution_context.global_variables,
            "execution_summary": execution_context.get_status_summary(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get execution results: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/")
async def get_execution_analytics(
    limit: int = 100, offset: int = 0, status: Optional[str] = None, request: Request = None
):
    """Get execution analytics and history"""
    try:
        workflow_engine: WorkflowEngine = request.app.state.workflow_engine
        executions = await workflow_engine.get_execution_history(
            limit=limit, offset=offset, status=status
        )

        # Convert to serializable format
        execution_list = []
        for execution in executions:
            execution_list.append(execution.get_status_summary())

        return {
            "executions": execution_list,
            "total": len(execution_list),
            "limit": limit,
            "offset": offset,
            "filter": {"status": status} if status else None,
        }

    except Exception as e:
        logger.error(f"Failed to get execution analytics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

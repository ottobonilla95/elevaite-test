"""
Monitoring, metrics, and analytics endpoints
"""

import logging
from fastapi import APIRouter, Request, HTTPException, Response
from typing import Optional

from workflow_core_sdk.monitoring import monitoring
from workflow_core_sdk.error_handling import error_handler

logger = logging.getLogger(__name__)

router = APIRouter(tags=["monitoring"])


@router.get("/metrics")
async def get_metrics():
    """Get Prometheus metrics"""
    try:
        metrics_data = monitoring.get_metrics()
        return Response(content=metrics_data, media_type="text/plain")
    except Exception as e:
        logger.error(f"Failed to get metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/monitoring/traces")
async def get_traces(limit: int = 100):
    """Get trace data for debugging"""
    try:
        traces = monitoring.get_traces()

        # Limit the number of traces returned
        limited_traces = traces[-limit:] if len(traces) > limit else traces

        return {"traces": limited_traces, "total": len(traces), "limit": limit}
    except Exception as e:
        logger.error(f"Failed to get traces: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/monitoring/summary")
async def get_monitoring_summary():
    """Get monitoring system summary"""
    try:
        summary = monitoring.get_monitoring_summary()

        return {
            "monitoring_status": "active",
            "summary": summary,
            "components": {
                "traces": "active",
                "metrics": "active",
                "error_tracking": "active",
            },
        }
    except Exception as e:
        logger.error(f"Failed to get monitoring summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analytics/executions")
async def get_execution_analytics(
    limit: int = 100,
    offset: int = 0,
    status: Optional[str] = None,
    request: Request = None,
):
    """Get execution analytics and history"""
    try:
        workflow_engine = request.app.state.workflow_engine
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


@router.get("/analytics/errors")
async def get_error_analytics(component: Optional[str] = None):
    """Get error analytics and statistics"""
    try:
        error_stats = error_handler.get_error_statistics()

        # Filter by component if specified
        if component:
            component_errors = error_stats.get("errors_by_component", {}).get(
                component, []
            )
            return {
                "component": component,
                "errors": component_errors,
                "total": len(component_errors),
            }

        return error_stats
    except Exception as e:
        logger.error(f"Failed to get error analytics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

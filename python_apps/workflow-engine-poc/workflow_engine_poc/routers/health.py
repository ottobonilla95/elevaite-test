"""
Health and system status endpoints
"""

import logging
from fastapi import APIRouter, Request

from ..step_registry import StepRegistry
from workflow_core_sdk.monitoring import monitoring
from ..error_handling import error_handler

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/")
async def root():
    """Health check endpoint"""
    return {
        "message": "Unified Workflow Execution Engine PoC",
        "version": "1.0.0-poc",
        "status": "running",
    }


@router.get("/health")
async def health_check(request: Request):
    """Detailed health check"""
    step_registry: StepRegistry = request.app.state.step_registry
    registered_steps = await step_registry.get_registered_steps()

    return {
        "status": "healthy",
        "registered_steps": len(registered_steps),
        "step_types": list(set(step["step_type"] for step in registered_steps)),
    }


@router.get("/health/detailed")
async def detailed_health_check():
    """Detailed health check with error statistics"""
    try:
        error_stats = error_handler.get_error_statistics()

        return {
            "status": "healthy",
            "timestamp": error_stats.get("last_updated"),
            "error_statistics": {
                "total_errors": error_stats.get("total_errors", 0),
                "errors_by_component": error_stats.get("errors_by_component", {}),
                "recent_errors": error_stats.get("recent_errors", []),
            },
            "system_info": {
                "uptime": "N/A",  # Could add actual uptime tracking
                "memory_usage": "N/A",  # Could add memory monitoring
            },
        }
    except Exception as e:
        logger.error(f"Failed to get detailed health check: {e}")
        return {
            "status": "degraded",
            "error": str(e),
        }


@router.get("/health/monitoring")
async def monitoring_health_check():
    """Health check specifically for monitoring components"""
    try:
        summary = monitoring.get_monitoring_summary()

        return {
            "status": "healthy",
            "monitoring": {
                "active_traces": summary.get("active_traces", 0),
                "total_requests": summary.get("total_requests", 0),
                "error_rate": summary.get("error_rate", 0.0),
                "avg_response_time": summary.get("avg_response_time", 0.0),
            },
        }
    except Exception as e:
        logger.error(f"Failed to get monitoring health check: {e}")
        return {
            "status": "degraded",
            "error": str(e),
        }

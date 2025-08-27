"""
Execution status and results endpoints
"""

import logging
from fastapi import APIRouter, Request, HTTPException
from typing import Optional, List
from fastapi import Depends
from sqlmodel import Session
from ..db.models import WorkflowExecutionRead, WorkflowExecutionUpdate, ExecutionStatus
from ..db.database import get_db_session
from ..db.service import DatabaseService

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

        # Return the in-memory execution context summary
        return execution_context.get_execution_summary()

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
            }

        return {
            "execution_id": execution_id,
            "status": execution_context.status.value,
            "step_results": step_results,
            "global_variables": execution_context.global_variables,
            "execution_summary": execution_context.get_execution_summary(),
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
):
    """Get execution analytics and history"""
    try:
        workflow_engine: WorkflowEngine = request.app.state.workflow_engine
        analytics = await workflow_engine.get_execution_analytics(limit=limit, offset=offset, status=status)
        return analytics
    except Exception as e:
        logger.error(f"Failed to get execution analytics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# New SQLModel-based execution endpoints


@router.post("/{workflow_id}/execute", response_model=WorkflowExecutionRead)
async def create_execution(
    workflow_id: str, execution_data: dict, session: Session = Depends(get_db_session)
) -> WorkflowExecutionRead:
    """Create a new workflow execution using SQLModel and return ORM entity"""
    try:
        db_service = DatabaseService()

        # Create execution data
        execution_request = {
            "workflow_id": workflow_id,
            "user_id": execution_data.get("user_id"),
            "session_id": execution_data.get("session_id"),
            "organization_id": execution_data.get("organization_id"),
            "input_data": execution_data.get("input_data", {}),
            "metadata": execution_data.get("metadata", {}),
        }

        # Create the execution and return ORM
        execution_obj = db_service.create_execution_entity(session, execution_request)
        return execution_obj  # type: ignore[return-value]

    except Exception as e:
        logger.error(f"Failed to create execution: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sqlmodel/{execution_id}", response_model=WorkflowExecutionRead)
async def get_execution_sqlmodel(execution_id: str, session: Session = Depends(get_db_session)) -> WorkflowExecutionRead:
    """Get execution details using SQLModel and return ORM entity"""
    try:
        db_service = DatabaseService()
        execution_obj = db_service.get_execution_entity(session, execution_id)

        if not execution_obj:
            raise HTTPException(status_code=404, detail="Execution not found")

        return execution_obj  # type: ignore[return-value]

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get execution {execution_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sqlmodel/", response_model=List[WorkflowExecutionRead])
async def list_executions_sqlmodel(
    workflow_id: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    session: Session = Depends(get_db_session),
) -> List[WorkflowExecutionRead]:
    """List executions using SQLModel and return ORM entities"""
    try:
        db_service = DatabaseService()
        return db_service.list_execution_entities(session, workflow_id=workflow_id, status=status, limit=limit, offset=offset)

    except Exception as e:
        logger.error(f"Failed to list executions: {e}")
        raise HTTPException(status_code=500, detail=str(e))

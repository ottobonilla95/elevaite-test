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
                "started_at": (
                    result.started_at.isoformat() if result.started_at else None
                ),
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
    limit: int = 100,
    offset: int = 0,
    status: Optional[str] = None,
    request: Request = None,
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


# New SQLModel-based execution endpoints
from fastapi import Depends
from sqlmodel import Session
from ..db.models import WorkflowExecutionRead, WorkflowExecutionUpdate, ExecutionStatus
from ..db.database import get_db_session
from ..db.service import DatabaseService
from typing import List


@router.post("/{workflow_id}/execute", response_model=WorkflowExecutionRead)
async def create_execution(
    workflow_id: str, execution_data: dict, session: Session = Depends(get_db_session)
) -> WorkflowExecutionRead:
    """Create a new workflow execution using SQLModel"""
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

        # Create the execution
        execution_id = db_service.create_execution(session, execution_request)

        # Get the created execution
        execution = db_service.get_execution(session, execution_id)
        if not execution:
            raise HTTPException(
                status_code=500, detail="Failed to retrieve created execution"
            )

        # Convert to response model
        import uuid

        return WorkflowExecutionRead(
            id=1,  # This would come from the database
            uuid=uuid.UUID(execution["execution_id"]),
            execution_id=uuid.UUID(execution["execution_id"]),
            workflow_id=uuid.UUID(execution["workflow_id"]),
            user_id=execution.get("user_id"),
            session_id=execution.get("session_id"),
            organization_id=execution.get("organization_id"),
            status=ExecutionStatus(execution["status"]),
            input_data=execution.get("input_data", {}),
            output_data=execution.get("output_data", {}),
            step_io_data=execution.get("step_io_data", {}),
            execution_metadata=execution.get("metadata", {}),
            error_message=execution.get("error_message"),
            started_at=execution.get("started_at"),
            completed_at=execution.get("completed_at"),
            execution_time_seconds=execution.get("execution_time_seconds"),
            created_at=execution["created_at"],
            updated_at=execution.get("updated_at"),
        )

    except Exception as e:
        logger.error(f"Failed to create execution: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sqlmodel/{execution_id}", response_model=WorkflowExecutionRead)
async def get_execution_sqlmodel(
    execution_id: str, session: Session = Depends(get_db_session)
) -> WorkflowExecutionRead:
    """Get execution details using SQLModel"""
    try:
        db_service = DatabaseService()
        execution = db_service.get_execution(session, execution_id)

        if not execution:
            raise HTTPException(status_code=404, detail="Execution not found")

        # Convert to response model
        import uuid

        return WorkflowExecutionRead(
            id=1,  # This would come from the database
            uuid=uuid.UUID(execution["execution_id"]),
            execution_id=uuid.UUID(execution["execution_id"]),
            workflow_id=uuid.UUID(execution["workflow_id"]),
            user_id=execution.get("user_id"),
            session_id=execution.get("session_id"),
            organization_id=execution.get("organization_id"),
            status=ExecutionStatus(execution["status"]),
            input_data=execution.get("input_data", {}),
            output_data=execution.get("output_data", {}),
            step_io_data=execution.get("step_io_data", {}),
            execution_metadata=execution.get("metadata", {}),
            error_message=execution.get("error_message"),
            started_at=execution.get("started_at"),
            completed_at=execution.get("completed_at"),
            execution_time_seconds=execution.get("execution_time_seconds"),
            created_at=execution["created_at"],
            updated_at=execution.get("updated_at"),
        )

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
    """List executions using SQLModel"""
    try:
        db_service = DatabaseService()
        executions = db_service.list_executions(
            session, workflow_id=workflow_id, status=status, limit=limit, offset=offset
        )

        # Convert to response models
        import uuid

        result = [
            WorkflowExecutionRead(
                id=1,
                uuid=uuid.UUID(exe["execution_id"]),
                execution_id=uuid.UUID(exe["execution_id"]),
                workflow_id=uuid.UUID(exe["workflow_id"]),
                user_id=exe.get("user_id"),
                session_id=exe.get("session_id"),
                organization_id=exe.get("organization_id"),
                status=ExecutionStatus(exe["status"]),
                input_data={},
                output_data={},
                step_io_data={},
                execution_metadata={},
                error_message=exe.get("error_message"),
                started_at=exe.get("started_at"),
                completed_at=exe.get("completed_at"),
                execution_time_seconds=exe.get("execution_time_seconds"),
                created_at=exe["created_at"],
                updated_at=exe.get("updated_at"),
            )
            for exe in executions
        ]
        return result

    except Exception as e:
        logger.error(f"Failed to list executions: {e}")
        raise HTTPException(status_code=500, detail=str(e))

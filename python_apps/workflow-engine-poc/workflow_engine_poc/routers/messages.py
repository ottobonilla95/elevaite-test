"""
Agent message endpoints for interactive per-agent chat
"""

import logging
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlmodel import Session

from workflow_core_sdk.db.database import get_db_session
from workflow_core_sdk.services.workflows_service import WorkflowsService
from workflow_core_sdk.services.executions_service import ExecutionsService
from ..util import api_key_or_user_guard
from ..services.queue_service import get_queue_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/executions", tags=["messages"])


class AgentMessageCreate(BaseModel):
    role: str
    content: str
    metadata: Optional[Dict[str, Any]] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None


class AgentMessageResponse(BaseModel):
    id: UUID
    execution_id: UUID
    step_id: str
    role: str
    content: str
    metadata: Optional[Dict[str, Any]] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    created_at: str


@router.get(
    "/{execution_id}/steps/{step_id}/messages",
    response_model=List[AgentMessageResponse],
)
async def list_step_messages(
    execution_id: str,
    step_id: str,
    limit: int = 100,
    offset: int = 0,
    session: Session = Depends(get_db_session),
    _principal: str = Depends(api_key_or_user_guard("view_message")),
):
    try:
        # Ensure execution exists
        details = ExecutionsService.get_execution(session, execution_id)
        if not details:
            raise HTTPException(status_code=404, detail="Execution not found")

        rows = WorkflowsService.list_agent_messages(
            session,
            execution_id=execution_id,
            step_id=step_id,
            limit=limit,
            offset=offset,
        )
        return [AgentMessageResponse.model_validate(r) for r in rows]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Failed to list messages for execution {execution_id} step {step_id}: {e}"
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/{execution_id}/steps/{step_id}/messages", response_model=AgentMessageResponse
)
async def create_step_message(
    execution_id: str,
    step_id: str,
    body: AgentMessageCreate,
    session: Session = Depends(get_db_session),
    _principal: str = Depends(api_key_or_user_guard("send_message")),
):
    try:
        # Validate execution exists
        details = ExecutionsService.get_execution(session, execution_id)
        if not details:
            raise HTTPException(status_code=404, detail="Execution not found")

        # Persist message
        WorkflowsService.create_agent_message(
            session,
            execution_id=execution_id,
            step_id=step_id,
            role=body.role,
            content=body.content,
            metadata=body.metadata,
            user_id=body.user_id,
            session_id=body.session_id,
        )

        # Get backend from execution metadata
        meta = (details.get("metadata") or {}) if isinstance(details, dict) else {}
        backend_val = str(meta.get("backend") or "").lower()

        # For local backend, queue resume for worker
        if backend_val != "dbos":
            decision_output = {
                "messages": [
                    {
                        "role": body.role,
                        "content": body.content,
                        "metadata": body.metadata,
                    }
                ],
                "final_turn": bool((body.metadata or {}).get("final_turn", False)),
            }

            queue_service = await get_queue_service()
            await queue_service.publish_workflow_resume(
                execution_id=execution_id,
                step_id=step_id,
                decision_output=decision_output,
            )
        # For DBOS backend, the workflow polls the database for messages; nothing to do

        # Persist 'running' to DB so status reads are consistent
        try:
            WorkflowsService.update_execution_status(session, execution_id, "running")
        except Exception as _upd:
            logger.debug(
                f"Non-fatal: failed to persist running status for {execution_id}: {_upd}"
            )

        # Emit status/step event to wake up clients
        from workflow_core_sdk.streaming import (
            stream_manager,
            create_step_event,
            create_status_event,
        )

        awaiting_evt = create_status_event(execution_id=execution_id, status="running")
        await stream_manager.emit_execution_event(awaiting_evt)

        step_evt = create_step_event(
            execution_id=execution_id,
            step_id=step_id,
            step_status="running",
            workflow_id=None,
            message_received=True,
        )
        await stream_manager.emit_execution_event(step_evt)

        # Return saved message
        rows = WorkflowsService.list_agent_messages(
            session, execution_id=execution_id, step_id=step_id, limit=1, offset=0
        )
        if not rows:
            raise HTTPException(
                status_code=500, detail="Message not found after creation"
            )
        row = rows[-1]
        return AgentMessageResponse.model_validate(row)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Failed to create message for execution {execution_id} step {step_id}: {e}"
        )
        raise HTTPException(status_code=500, detail=str(e))

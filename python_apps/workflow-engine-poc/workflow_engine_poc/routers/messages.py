"""
Agent message endpoints for interactive per-agent chat
"""

import logging
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel
from sqlmodel import Session

from ..db.database import get_db_session
from ..db.service import DatabaseService
from ..workflow_engine import WorkflowEngine

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


@router.get("/{execution_id}/steps/{step_id}/messages", response_model=List[AgentMessageResponse])
async def list_step_messages(
    execution_id: str,
    step_id: str,
    request: Request,
    limit: int = 100,
    offset: int = 0,
    session: Session = Depends(get_db_session),
):
    try:
        # Ensure execution exists (prefer engine context)
        workflow_engine: WorkflowEngine = request.app.state.workflow_engine
        ctx = await workflow_engine.get_execution_context(execution_id)
        if not ctx:
            db_service = DatabaseService()
            details = db_service.get_execution(session, execution_id)
            if not details:
                raise HTTPException(status_code=404, detail="Execution not found")

        db_service = DatabaseService()
        rows = db_service.list_agent_messages(session, execution_id=execution_id, step_id=step_id, limit=limit, offset=offset)
        return [AgentMessageResponse.model_validate(r) for r in rows]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to list messages for execution {execution_id} step {step_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{execution_id}/steps/{step_id}/messages", response_model=AgentMessageResponse)
async def create_step_message(
    execution_id: str,
    step_id: str,
    body: AgentMessageCreate,
    request: Request,
    session: Session = Depends(get_db_session),
):
    try:
        workflow_engine: WorkflowEngine = request.app.state.workflow_engine
        db_service = DatabaseService()

        # Validate execution exists
        ctx = await workflow_engine.get_execution_context(execution_id)
        if not ctx:
            details = db_service.get_execution(session, execution_id)
            if not details:
                raise HTTPException(status_code=404, detail="Execution not found")

        # Persist message
        msg_id = db_service.create_agent_message(
            session,
            execution_id=execution_id,
            step_id=step_id,
            role=body.role,
            content=body.content,
            metadata=body.metadata,
            user_id=body.user_id,
            session_id=body.session_id,
        )

        # Resume engine if paused on this step (local engine)
        try:
            if ctx:
                await workflow_engine.resume_execution(
                    execution_id=execution_id,
                    step_id=step_id,
                    decision_output={
                        "messages": [{"role": body.role, "content": body.content, "metadata": body.metadata}],
                        "final_turn": bool((body.metadata or {}).get("final_turn", False)),
                    },
                )
        except Exception as re:
            logger.warning(f"Resume attempt failed for {execution_id}/{step_id}: {re}")

        # Always signal DBOS event; if it fails, raise so the client sees the error
        from dbos import DBOS as _DBOS  # Let ImportError propagate

        decision_key = f"wf:{execution_id}:{step_id}:user_msg"
        try:
            # Send the message directly to the DBOS workflow instance using topic-based messaging
            details = db_service.get_execution(session, execution_id) or {}
            dbos_wfid = (details.get("metadata") or {}).get("dbos_workflow_id")
            if not isinstance(dbos_wfid, str) or not dbos_wfid:
                raise RuntimeError("DBOS workflow ID not recorded for this execution yet")
            _DBOS.send(destination_id=dbos_wfid, message={"message_id": msg_id}, topic=decision_key)
            logger.info(
                f"DBOS send done for exec={execution_id}/{step_id} wf_id={dbos_wfid} topic={decision_key} msg_id={msg_id}"
            )
        except Exception as _e2:
            logger.error(f"DBOS send failed: {_e2}")
            raise HTTPException(status_code=502, detail=f"Failed to signal DBOS message for {execution_id}/{step_id}: {_e2}")

        # Emit status/step event to wake up clients regardless (helps UI reflect running)
        from ..streaming import stream_manager, create_step_event, create_status_event

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
        rows = db_service.list_agent_messages(session, execution_id=execution_id, step_id=step_id, limit=1, offset=0)
        if not rows:
            raise HTTPException(status_code=500, detail="Message not found after creation")
        row = rows[-1]
        return AgentMessageResponse.model_validate(row)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create message for execution {execution_id} step {step_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

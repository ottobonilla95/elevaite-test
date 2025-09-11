"""
DBOS execution endpoints (POC)

Provides an API path to execute a saved workflow using the DBOS adapter
to achieve durable execution semantics.
"""

from typing import Any, Dict, Optional
from fastapi import APIRouter, Request, HTTPException, Depends, Form, File, UploadFile
from sqlmodel import Session
import logging

from ..db.service import DatabaseService
from ..db.database import get_db_session
from ..db.models import WorkflowExecutionRead, ExecutionStatus
from ..db.models import WorkflowRead
from ..db.models import Workflow

from ..dbos_impl import get_dbos_adapter

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/dbos", tags=["dbos"])


@router.post("/workflows/{workflow_id}/execute")
async def execute_workflow_dbos(
    workflow_id: str,
    request: Request,
    session: Session = Depends(get_db_session),
) -> Dict[str, Any]:
    """
    Execute a saved workflow using the DBOS adapter.

    Body JSON should include:
    - trigger: trigger payload (chat/webhook/etc.)
    - user_id, session_id, organization_id (optional)
    - input_data, metadata (optional)
    """
    try:
        db_service = DatabaseService()

        # Ensure workflow exists
        workflow = db_service.get_workflow(session, workflow_id)
        if not workflow:
            raise HTTPException(status_code=404, detail="Workflow not found")

        body = await request.json()
        trigger_payload: Dict[str, Any] = body.get("trigger", {})
        user_context: Dict[str, Any] = {
            "user_id": body.get("user_id"),
            "session_id": body.get("session_id"),
            "organization_id": body.get("organization_id"),
        }

        # Start DBOS execution (runs to completion in this POC)
        adapter = await get_dbos_adapter()
        result = await adapter.start_workflow(
            workflow_config=workflow,
            trigger_data=trigger_payload,
            user_context=user_context,
        )

        # Normalize response
        http_status = 200 if result.get("success") else 500
        return {"workflow_id": workflow_id, **result}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"DBOS execution failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

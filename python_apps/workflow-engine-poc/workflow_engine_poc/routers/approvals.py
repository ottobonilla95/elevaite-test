"""
Approvals API router: list, get, approve, deny
"""

from datetime import datetime, timezone
from typing import Any, Dict, Optional, List

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from workflow_core_sdk.db.database import get_db_session
from workflow_core_sdk.services.approvals_service import ApprovalsService
from workflow_core_sdk.db.models import ApprovalStatus, ApprovalRequestRead
from ..util import api_key_or_user_guard
from ..schemas import ApprovalDecisionRequest, ApprovalDecisionResponse
from ..services.queue_service import get_queue_service

router = APIRouter(prefix="/approvals", tags=["approvals"])


@router.get("/", response_model=List[ApprovalRequestRead])
@router.get("", response_model=List[ApprovalRequestRead])
async def list_approvals(
    execution_id: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    session: Session = Depends(get_db_session),
    _principal: str = Depends(api_key_or_user_guard("view_approval")),
):
    return ApprovalsService.list_approval_requests(
        session, execution_id=execution_id, status=status, limit=limit, offset=offset
    )


@router.get("/{approval_id}", response_model=ApprovalRequestRead)
async def get_approval(
    approval_id: str,
    session: Session = Depends(get_db_session),
    _principal: str = Depends(api_key_or_user_guard("view_approval")),
):
    rec = ApprovalsService.get_approval_request(session, approval_id)
    if not rec:
        raise HTTPException(status_code=404, detail="Approval not found")
    return rec


def _decision_output(decision: str, body: ApprovalDecisionRequest) -> Dict[str, Any]:
    return {
        "decision": decision,
        "payload": body.payload or {},
        "decided_by": body.decided_by,
        "decided_at": datetime.now(timezone.utc).isoformat(),
        "comment": body.comment,
    }


@router.post("/{approval_id}/approve", response_model=ApprovalDecisionResponse)
async def approve(
    approval_id: str,
    body: ApprovalDecisionRequest,
    session: Session = Depends(get_db_session),
    _principal: str = Depends(api_key_or_user_guard("approve_request")),
):
    rec = ApprovalsService.get_approval_request(session, approval_id)
    if not rec:
        raise HTTPException(status_code=404, detail="Approval not found")

    # Update DB record
    ApprovalsService.update_approval_request(
        session,
        approval_id,
        {
            "status": ApprovalStatus.APPROVED,
            "response_payload": body.payload or {},
            "decided_at": datetime.now(timezone.utc),
            "decided_by": body.decided_by,
        },
    )

    # Continue execution
    backend = (rec.get("approval_metadata") or {}).get("backend") or "local"
    execution_id = rec["execution_id"]
    step_id = rec["step_id"]

    if backend == "dbos":
        # No direct DBOS event signaling from the API. The DBOS step now polls the database
        # for this approval decision. We've already updated the DB record above.
        return ApprovalDecisionResponse(status="ok", backend=backend)
    else:
        # Queue resume for worker
        queue_service = await get_queue_service()
        await queue_service.publish_workflow_resume(
            execution_id=execution_id,
            step_id=step_id,
            decision_output=_decision_output("approved", body),
        )
        return ApprovalDecisionResponse(status="ok", backend=backend)


@router.post("/{approval_id}/deny", response_model=ApprovalDecisionResponse)
async def deny(
    approval_id: str,
    body: ApprovalDecisionRequest,
    session: Session = Depends(get_db_session),
    _principal: str = Depends(api_key_or_user_guard("deny_request")),
):
    rec = ApprovalsService.get_approval_request(session, approval_id)
    if not rec:
        raise HTTPException(status_code=404, detail="Approval not found")

    # Update DB record
    ApprovalsService.update_approval_request(
        session,
        approval_id,
        {
            "status": ApprovalStatus.DENIED,
            "response_payload": body.payload or {},
            "decided_at": datetime.now(timezone.utc),
            "decided_by": body.decided_by,
        },
    )

    backend = (rec.get("approval_metadata") or {}).get("backend") or "local"
    execution_id = rec["execution_id"]
    step_id = rec["step_id"]

    if backend == "dbos":
        # DBOS workflow now polls the database for the decision; nothing to signal here
        return ApprovalDecisionResponse(status="ok", backend=backend)
    else:
        # Queue resume for worker
        queue_service = await get_queue_service()
        await queue_service.publish_workflow_resume(
            execution_id=execution_id,
            step_id=step_id,
            decision_output=_decision_output("denied", body),
        )
        return ApprovalDecisionResponse(status="ok", backend=backend)

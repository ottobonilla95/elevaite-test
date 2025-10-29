"""
Approvals API router: list, get, approve, deny
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlmodel import Session
from rbac_sdk.fastapi_helpers import require_permission_async, resource_builders, principal_resolvers

from ..db.database import get_db_session
from ..services.approvals_service import ApprovalsService
from ..db.models import ApprovalStatus
from ..workflow_engine import WorkflowEngine

# RBAC header constants
HDR_PROJECT_ID = "X-elevAIte-ProjectId"
HDR_ACCOUNT_ID = "X-elevAIte-AccountId"
HDR_ORG_ID = "X-elevAIte-OrganizationId"

router = APIRouter(prefix="/approvals", tags=["approvals"])

# RBAC guards: view_project (list/get) and edit_project (approve/deny)
_guard_view_project = require_permission_async(
    action="view_project",
    resource_builder=resource_builders.project_from_headers(
        project_header=HDR_PROJECT_ID,
        account_header=HDR_ACCOUNT_ID,
        org_header=HDR_ORG_ID,
    ),
    principal_resolver=principal_resolvers.api_key_or_user(),
)

_guard_edit_project = require_permission_async(
    action="edit_project",
    resource_builder=resource_builders.project_from_headers(
        project_header=HDR_PROJECT_ID,
        account_header=HDR_ACCOUNT_ID,
        org_header=HDR_ORG_ID,
    ),
    principal_resolver=principal_resolvers.api_key_or_user(),
)


class DecisionBody(BaseModel):
    payload: Optional[Dict[str, Any]] = None
    decided_by: Optional[str] = None
    comment: Optional[str] = None


@router.get("/")
@router.get("")
async def list_approvals(
    execution_id: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    session: Session = Depends(get_db_session),
    _principal: str = Depends(_guard_view_project),
):
    return ApprovalsService.list_approval_requests(
        session, execution_id=execution_id, status=status, limit=limit, offset=offset
    )


@router.get("/{approval_id}")
async def get_approval(
    approval_id: str,
    session: Session = Depends(get_db_session),
    _principal: str = Depends(_guard_view_project),
):
    rec = ApprovalsService.get_approval_request(session, approval_id)
    if not rec:
        raise HTTPException(status_code=404, detail="Approval not found")
    return rec


def _decision_output(decision: str, body: DecisionBody) -> Dict[str, Any]:
    return {
        "decision": decision,
        "payload": body.payload or {},
        "decided_by": body.decided_by,
        "decided_at": datetime.now(timezone.utc).isoformat(),
        "comment": body.comment,
    }


@router.post("/{approval_id}/approve")
async def approve(
    approval_id: str,
    body: DecisionBody,
    request: Request,
    session: Session = Depends(get_db_session),
    _principal: str = Depends(_guard_edit_project),
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
    workflow_id = rec["workflow_id"]
    execution_id = rec["execution_id"]
    step_id = rec["step_id"]

    if backend == "dbos":
        # No direct DBOS event signaling from the API. The DBOS step now polls the database
        # for this approval decision. We've already updated the DB record above.
        return {"status": "ok", "backend": backend}
    else:
        # Resume local engine
        engine: WorkflowEngine = request.app.state.workflow_engine
        await engine.resume_execution(execution_id, step_id, _decision_output("approved", body))
        return {"status": "ok", "backend": backend}


@router.post("/{approval_id}/deny")
async def deny(
    approval_id: str,
    body: DecisionBody,
    request: Request,
    session: Session = Depends(get_db_session),
    _principal: str = Depends(_guard_edit_project),
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
        return {"status": "ok", "backend": backend}
    else:
        engine: WorkflowEngine = request.app.state.workflow_engine
        await engine.resume_execution(execution_id, step_id, _decision_output("denied", body))
        return {"status": "ok", "backend": backend}

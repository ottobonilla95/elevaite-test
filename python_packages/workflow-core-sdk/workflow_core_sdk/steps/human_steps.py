from __future__ import annotations

from typing import Dict, Any, Optional
from datetime import datetime
import uuid

from workflow_core_sdk.execution_context import StepResult, StepStatus, ExecutionContext, ExecutionStatus


async def human_approval_step(
    step_config: Dict[str, Any], input_data: Dict[str, Any], execution_context: ExecutionContext
) -> StepResult:
    """Pause execution and wait for human approval.

    Parameters in step_config["parameters"]:
    - prompt: str (what to show human)
    - timeout_seconds: Optional[int] (how long to wait)
    - approver_role: Optional[str]
    - require_comment: Optional[bool]
    """
    params = step_config.get("parameters", {}) or {}
    step_id = step_config.get("step_id") or f"human-{uuid.uuid4()}"
    backend = step_config.get("_backend") or step_config.get("backend") or "local"

    # Persist ApprovalRequest so UIs/APIs can list it
    approval_id = None
    try:
        from sqlmodel import Session as _SQLSession
        from workflow_core_sdk.db.database import engine
        from workflow_core_sdk.services.approvals_service import ApprovalsService as DatabaseService

        _dbs = DatabaseService()
        with _SQLSession(engine) as _session:
            approval_id = _dbs.create_approval_request(
                _session,
                {
                    "workflow_id": execution_context.workflow_id,
                    "execution_id": execution_context.execution_id,
                    "step_id": step_id,
                    "prompt": params.get("prompt"),
                    "approval_metadata": {
                        "approver_role": params.get("approver_role"),
                        "require_comment": params.get("require_comment"),
                        "backend": backend,
                    },
                },
            )
    except Exception:
        approval_id = None

    request_payload = {
        "approval_id": approval_id,
        "execution_id": execution_context.execution_id,
        "workflow_id": execution_context.workflow_id,
        "step_id": step_id,
        "prompt": params.get("prompt"),
        "approval_metadata": {
            "approver_role": params.get("approver_role"),
            "require_comment": params.get("require_comment"),
            "backend": backend,
        },
    }

    # If local backend and a decision was injected via resume_execution, complete immediately
    if backend != "dbos":
        injected = execution_context.step_io_data.get(step_id)
        if isinstance(injected, dict) and injected.get("decision") in ("approved", "denied"):
            return StepResult(step_id=step_id, status=StepStatus.COMPLETED, output_data=injected)

    if backend == "dbos":
        # For DBOS, wait by polling the database for the approval decision.
        # This keeps the wait within the step (DBOS context) and avoids external event signaling.
        import asyncio
        from workflow_core_sdk.services.approvals_service import ApprovalsService as DatabaseService
        from sqlmodel import Session as _SQLSession
        from workflow_core_sdk.db.database import engine

        timeout = params.get("timeout_seconds", 120)
        poll_interval = float(params.get("poll_interval_seconds", 0.5))
        deadline = (datetime.now().timestamp() + timeout) if timeout else None
        _dbs = DatabaseService()
        while True:
            try:
                with _SQLSession(engine) as _s:
                    rec = _dbs.get_approval_request(_s, approval_id) if approval_id else None
                    if not rec and approval_id is None:
                        # Fallback: lookup by execution_id+step_id
                        items = _dbs.list_approval_requests(_s, execution_id=str(execution_context.execution_id))
                        for it in items:
                            if (it.get("step_id") or "") == step_id:
                                rec = it
                                break
            except Exception:
                rec = None

            if rec:
                _st = rec.get("status")
                _st_str = _st.value if hasattr(_st, "value") else (str(_st) if _st is not None else None)
                if _st_str in ("approved", "denied"):
                    from datetime import timezone as _tz

                    out = {
                        "decision": _st_str,
                        "payload": rec.get("response_payload"),
                        "decided_by": rec.get("decided_by"),
                        "decided_at": rec.get("decided_at") or datetime.now(_tz.utc).isoformat(),
                        "comment": (rec.get("response_payload") or {}).get("comment")
                        if isinstance(rec.get("response_payload"), dict)
                        else None,
                    }
                    return StepResult(step_id=step_id, status=StepStatus.COMPLETED, output_data=out)

            # Check timeout
            if deadline and datetime.now().timestamp() >= deadline:
                # On timeout, keep the workflow alive but indicate waiting to callers via output payload
                execution_context.status = ExecutionStatus.WAITING
                return StepResult(step_id=step_id, status=StepStatus.WAITING, output_data=request_payload)

            await asyncio.sleep(poll_interval)

    # Local backend: mark waiting and let API resume later
    execution_context.status = ExecutionStatus.WAITING
    return StepResult(step_id=step_id, status=StepStatus.WAITING, output_data=request_payload)

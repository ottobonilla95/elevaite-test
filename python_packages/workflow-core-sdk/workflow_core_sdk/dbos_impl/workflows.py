from __future__ import annotations

import logging
from typing import Any, Dict, Optional, TypedDict, cast
from datetime import datetime
import uuid
from datetime import timezone as _tz
from sqlmodel import Session as _SQLSession

from dbos import DBOS
from .steps import DBOSStepResult, dbos_execute_step_durable

from ..streaming import stream_manager, create_status_event, create_step_event, create_error_event
from ..db.service import DatabaseService as _DBService
from ..db.models import ExecutionStatus as _ExecStatus
from . import get_dbos_adapter
from .messaging import make_decision_topic


logger = logging.getLogger(__name__)


class DBOSWorkflowResult(TypedDict, total=False):
    success: bool | None
    execution_id: str
    workflow_id: str
    step_results: Dict[str, DBOSStepResult]
    completed_at: str
    error: str | None
    failed_step: str
    _dbos: Dict[str, Any]


@DBOS.workflow()
async def dbos_execute_workflow_durable(
    workflow_config: Dict[str, Any],
    trigger_data: Dict[str, Any],
    user_context_data: Optional[Dict[str, Any]] = None,
    execution_id: Optional[str] = None,
) -> DBOSWorkflowResult:
    adapter = await get_dbos_adapter()
    if not adapter:
        raise RuntimeError("DBOS adapter not available")
    workflow_id = workflow_config.get("workflow_id") or str(uuid.uuid4())
    execution_id = execution_id or str(uuid.uuid4())

    # Construct execution context payload
    execution_context_data = {
        "execution_id": execution_id,
        "workflow_id": workflow_id,
        "workflow_config": workflow_config,
        "user_context": user_context_data or {},
        "step_io_data": {"trigger_raw": trigger_data},
        "started_at": datetime.now().isoformat(),
    }

    # Emit workflow start event
    try:
        start_event = create_status_event(
            execution_id=execution_id,
            status="running",
            workflow_id=workflow_id,
            step_count=len(workflow_config.get("steps", [])),
        )
        await stream_manager.emit_execution_event(start_event)
        await stream_manager.emit_workflow_event(start_event)
    except Exception:
        # Don't let streaming errors break execution
        pass
    # Record DBOS workflow_id on our execution immediately (before any waits)
    try:
        from ..db.service import DatabaseService as _DBSvc
        from ..db.database import get_db_session as _get_sess
        from dbos import DBOS as _DBOS

        _dbs = _DBSvc()
        _s = _get_sess()
        try:
            dbos_wfid = cast(str, _DBOS.workflow_id)
            details = _dbs.get_execution(_s, execution_id)
            if not details:
                # Create placeholder and rekey so router can find it
                logger.warning(f"Execution {execution_id} not found at start; creating placeholder to persist DBOS wf_id")
                ent = _dbs.create_execution_entity(
                    _s,
                    {
                        "workflow_id": workflow_id,
                        "user_id": (user_context_data or {}).get("user_id"),
                        "session_id": (user_context_data or {}).get("session_id"),
                        "organization_id": (user_context_data or {}).get("organization_id"),
                        "metadata": {"dbos_workflow_id": dbos_wfid},
                    },
                )
                _dbs.rekey_execution(_s, str(ent.id), execution_id)
                details = _dbs.get_execution(_s, execution_id) or {}
            meta = dict(details.get("metadata") or {})
            if meta.get("dbos_workflow_id") != dbos_wfid:
                meta["dbos_workflow_id"] = dbos_wfid
                _dbs.update_execution(_s, execution_id, {"execution_metadata": meta})
            logger.info(f"DBOS workflow_id recorded at start: exec={execution_id} wf_id={dbos_wfid}")
        finally:
            try:
                _s.close()
            except Exception:
                pass
    except Exception as _rec_err:
        logger.warning(f"Failed to record DBOS wf_id for exec={execution_id}: {_rec_err}")

    steps = workflow_config.get("steps", [])
    if not steps:
        # Emit error event
        try:
            error_event = create_error_event(
                execution_id=execution_id, error_message="No steps defined in workflow", workflow_id=workflow_id
            )
            await stream_manager.emit_execution_event(error_event)
            await stream_manager.emit_workflow_event(error_event)
        except Exception:
            pass
        return {"success": False, "error": "No steps defined in workflow"}

    step_results: Dict[str, Any] = {}

    def _prepare_step_input(step: Dict[str, Any]) -> Dict[str, Any]:
        data: Dict[str, Any] = {}
        data.update(trigger_data)
        for sid, res in step_results.items():
            if isinstance(res, dict) and res.get("success") and res.get("output_data"):
                data[f"step_{sid}"] = res["output_data"]
        step_input = step.get("input", {})
        if isinstance(step_input, dict):
            data.update(step_input)
        return data

    def _slugify(txt: str) -> str:
        s = (txt or "").strip().lower()
        import re

        s = re.sub(r"[^a-z0-9]+", "_", s)
        s = re.sub(r"_+", "_", s).strip("_")
        return s or "step"

    for step in steps:
        step_id = step.get("step_id")
        step_type = step.get("step_type")
        if not step_type:
            adapter.logger.error(f"Invalid step configuration: {step}")
            continue
        if not step_id:
            # Normalize: infer a step_id if missing
            if step_type == "trigger":
                step_id = "trigger"
            else:
                step_id = _slugify(step.get("name") or f"{step_type}")
            step = {**step, "step_id": step_id}

        # Inner loop to handle interactive WAITING steps by polling for new messages
        while True:
            input_data = _prepare_step_input(step)
            try:
                res = await dbos_execute_step_durable(
                    step_type=step_type,
                    step_config=step,
                    input_data=input_data,
                    execution_context_data=execution_context_data,
                )
                step_results[step_id] = res
                execution_context_data["step_io_data"][step_id] = res.get("output_data")

                # Emit step completion event
                try:
                    # Prefer explicit status from step result; fallback to success flag
                    step_status = (res.get("status") or ("completed" if res.get("success") else "failed")).lower()
                    step_event = create_step_event(
                        execution_id=execution_id,
                        step_id=step_id,
                        step_status=step_status,
                        workflow_id=workflow_id,
                        step_type=step_type,
                        output_data=res.get("output_data"),
                    )
                    await stream_manager.emit_execution_event(step_event)
                    await stream_manager.emit_workflow_event(step_event)
                except Exception:
                    pass

                # Completed -> proceed to next step
                if res.get("success"):
                    break

                # Not success -> either waiting or failed
                status_lower = str(res.get("status") or "").lower()
                if status_lower == "waiting":
                    # Emit explicit status=waiting so clients/DB reflect paused state
                    try:
                        waiting_event = create_status_event(
                            execution_id=execution_id,
                            status="waiting",
                            workflow_id=workflow_id,
                        )
                        await stream_manager.emit_execution_event(waiting_event)
                        await stream_manager.emit_workflow_event(waiting_event)
                    except Exception:
                        pass

                    # Also emit a step-level waiting event with the paused step_id so clients can route replies
                    try:
                        step_wait_evt = create_step_event(
                            execution_id=execution_id,
                            step_id=step_id,
                            step_status="waiting",
                            workflow_id=workflow_id,
                        )
                        await stream_manager.emit_execution_event(step_wait_evt)
                        await stream_manager.emit_workflow_event(step_wait_evt)
                    except Exception:
                        pass

                    # Persist execution status to DB as WAITING and record DBOS workflow_id for later resume
                    try:
                        from ..db.service import DatabaseService
                        from ..db.database import get_db_session
                        from ..db.models.executions import ExecutionStatus as DBExecStatus

                        _dbs = DatabaseService()
                        _sess0 = get_db_session()
                        try:
                            from dbos import DBOS as _DBOS

                            dbos_wfid = cast(str, _DBOS.workflow_id)
                            details = _dbs.get_execution(_sess0, execution_id)
                            if not details:
                                # Create execution row if missing (e.g., DBOS-first path), then rekey to our execution_id
                                logger.warning(
                                    f"Execution {execution_id} not found; creating placeholder to persist DBOS wf_id"
                                )
                                create_payload = {
                                    "workflow_id": workflow_id,
                                    "user_id": (user_context_data or {}).get("user_id"),
                                    "session_id": (user_context_data or {}).get("session_id"),
                                    "organization_id": (user_context_data or {}).get("organization_id"),
                                    "metadata": {"dbos_workflow_id": dbos_wfid},
                                }
                                ent = _dbs.create_execution_entity(_sess0, create_payload)
                                _dbs.rekey_execution(_sess0, str(ent.id), execution_id)
                                details = _dbs.get_execution(_sess0, execution_id) or {}

                            meta = dict(details.get("metadata") or {})
                            meta["dbos_workflow_id"] = dbos_wfid
                            ok = _dbs.update_execution(
                                _sess0,
                                execution_id,
                                {
                                    "status": DBExecStatus.WAITING.value,
                                    "execution_metadata": meta,
                                },
                            )
                            if not ok:
                                logger.error(f"Failed to update execution {execution_id} with DBOS WAITING metadata")
                            # Read-back to confirm persistence for debugging
                            details2 = _dbs.get_execution(_sess0, execution_id) or {}
                            meta2 = details2.get("metadata") or {}
                            logger.info(
                                f"DBOS WAITING persisted: exec={execution_id} dbos_wfid={dbos_wfid} saved_meta_wfid={meta2.get('dbos_workflow_id')}"
                            )
                        finally:
                            try:
                                _sess0.close()
                            except Exception:
                                pass
                    except Exception as persist_err:
                        logger.error(f"Error persisting DBOS WAITING state for exec={execution_id}: {persist_err}")

                    # Block on DBOS event instead of polling so the workflow truly WAITs under DBOS
                    try:
                        decision_key = f"wf:{execution_id}:{step_id}:user_msg"
                        from dbos import DBOS as _DBOS

                        # Block on DBOS event scoped to this workflow; long timeout with retry keeps it WAITING
                        payload = None
                        wid = cast(str, _DBOS.workflow_id)
                        adapter.logger.info(f"DBOS waiting: exec={execution_id} wf_id={wid} step={step_id} key={decision_key}")
                        while payload is None:
                            payload = await _DBOS.recv_async(topic=decision_key, timeout_seconds=3600)
                        adapter.logger.info(f"DBOS event received for step={step_id} execution={execution_id}: {bool(payload)}")
                    except Exception as _ev_err:
                        # If waiting fails, return waiting state (caller can decide next action)
                        adapter.logger.warning(f"DBOS get_event_async failed: {_ev_err}; retrying in 1s")
                        import asyncio as _asyncio

                        await _asyncio.sleep(1)
                        continue

                    # Event received -> loop to re-execute this step with updated DB messages
                    continue

                # Otherwise, emit error event for failed step
                error_msg = "Unknown error"
                try:
                    error_msg = res.get("error") or "Unknown error"
                    error_event = create_error_event(
                        execution_id=execution_id,
                        error_message=f"Step {step_id} failed: {error_msg}",
                        workflow_id=workflow_id,
                    )
                    await stream_manager.emit_execution_event(error_event)
                    await stream_manager.emit_workflow_event(error_event)
                except Exception:
                    pass
                return {
                    "success": False,
                    "error": f"Step {step_id} failed: {error_msg}",
                    "failed_step": step_id,
                    "step_results": step_results,
                }
            except Exception as e:
                # Emit error event for exception
                try:
                    error_event = create_error_event(
                        execution_id=execution_id,
                        error_message=f"Exception in step {step_id}: {str(e)}",
                        workflow_id=workflow_id,
                    )
                    await stream_manager.emit_execution_event(error_event)
                    await stream_manager.emit_workflow_event(error_event)
                except Exception:
                    pass
                return {
                    "success": False,
                    "error": f"Exception in step {step_id}: {str(e)}",
                    "failed_step": step_id,
                    "step_results": step_results,
                }

    # Emit workflow completion event
    try:
        completion_event = create_status_event(
            execution_id=execution_id,
            status="completed",
            workflow_id=workflow_id,
            step_count=len(steps),
            completed_steps=len(step_results),
        )
        await stream_manager.emit_execution_event(completion_event)
        await stream_manager.emit_workflow_event(completion_event)
    except Exception:
        pass

    return {
        "success": True,
        "execution_id": execution_id,
        "workflow_id": workflow_id,
        "step_results": step_results,
        "completed_at": datetime.now().isoformat(),
    }


# Helper to run DBOS and persist results (extracted from routers)


async def execute_and_persist_dbos_result(
    session: _SQLSession,
    db_service: _DBService,
    *,
    workflow: Dict[str, Any],
    trigger_payload: Dict[str, Any],
    user_context: Dict[str, Any],
    execution_id: str,
    wait: bool,
    metadata: Optional[Dict[str, Any]],
    chosen_backend: str,
) -> str:
    """
    Execute a workflow via DBOS and persist normalized results to the executions table.

    Returns the (possibly rekeyed) execution_id.
    """
    adapter = await get_dbos_adapter()
    if not adapter:
        raise RuntimeError("DBOS adapter not available")

    result = await adapter.start_workflow(
        workflow_config=workflow,
        trigger_data=trigger_payload,
        user_context=user_context,
        execution_id=execution_id,
        wait=wait,
    )

    if not isinstance(result, dict):
        raise RuntimeError(f"DBOS returned unexpected result type: {type(result)}")

    # If DBOS produced its own execution_id, rekey the DB row to match
    dbos_exec_id = result.get("execution_id")
    if isinstance(dbos_exec_id, str) and dbos_exec_id and dbos_exec_id != execution_id:
        try:
            db_service.rekey_execution(session, execution_id, dbos_exec_id)
            execution_id = dbos_exec_id
        except Exception as e:
            logger.warning(f"Rekeying execution {execution_id} to {dbos_exec_id} failed: {e}")

    # Map adapter result into execution record
    success_val = result.get("success")
    if success_val is True:
        status = _ExecStatus.COMPLETED
    elif success_val is False:
        status = _ExecStatus.FAILED
    else:
        # DBOS started (wait=False) and still in progress
        status = _ExecStatus.RUNNING

    step_results = result.get("step_results", {})

    # Construct step_io_data from outputs
    step_io_data: Dict[str, Any] = {}
    if isinstance(step_results, dict):
        for sid, sres in step_results.items():
            if isinstance(sres, dict) and "output_data" in sres:
                step_io_data[sid] = sres["output_data"]

    # Step summary for analytics
    steps_executed = len(step_results) if isinstance(step_results, dict) else 0
    completed_steps = 0
    failed_steps = 0
    if isinstance(step_results, dict):
        for sres in step_results.values():
            if isinstance(sres, dict):
                if sres.get("success") is True:
                    completed_steps += 1
                elif sres.get("success") is False:
                    failed_steps += 1

    try:
        steps_defined = len(workflow.get("steps", []) or [])
    except Exception:
        steps_defined = 0

    # Compute execution time using stored started_at and current UTC
    now_utc = datetime.now(_tz.utc)
    start_iso = None
    try:
        created_pre = db_service.get_execution(session, execution_id)
        start_iso = created_pre.get("started_at") if isinstance(created_pre, dict) else None
    except Exception:
        start_iso = None
    exec_secs = None
    if isinstance(start_iso, str):
        try:
            # Handle Z suffix
            s = start_iso.replace("Z", "+00:00")
            from datetime import datetime as _dt

            start_dt = _dt.fromisoformat(s)
            if start_dt.tzinfo is None:
                start_dt = start_dt.replace(tzinfo=_tz.utc)
            exec_secs = (now_utc - start_dt).total_seconds()
        except Exception:
            exec_secs = None

    update_payload: Dict[str, Any] = {
        "status": status,
        "output_data": {"success": success_val, "error": result.get("error")},
        "step_io_data": step_io_data,
        "execution_metadata": {
            **(result.get("_dbos") or {}),
            **(metadata or {}),
            "backend": chosen_backend,
            "summary": {
                "total_steps": steps_defined,
                "steps_executed": steps_executed,
                "completed_steps": completed_steps,
                "failed_steps": failed_steps,
            },
        },
        "error_message": result.get("error"),
    }

    # Only set completion timestamps for terminal states
    if status in (
        _ExecStatus.COMPLETED,
        _ExecStatus.FAILED,
        _ExecStatus.CANCELLED,
        _ExecStatus.TIMEOUT,
    ):
        update_payload["completed_at"] = now_utc
        update_payload["execution_time_seconds"] = exec_secs

    db_service.update_execution(session, execution_id, update_payload)

    return execution_id

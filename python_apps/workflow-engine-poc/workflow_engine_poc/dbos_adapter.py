"""
DBOS Adapter for Workflow Engine PoC

This module provides a DBOS-based durable execution backend that wraps our existing
step registry and execution context to provide fault-tolerant workflow execution.

Phase 0: Proof of Concept
- Demonstrates trigger -> agent -> tool -> subflow execution using DBOS
- Uses existing StepRegistry for step implementations
- Provides durable execution with automatic recovery
- No API changes required - runs locally for testing
"""

import asyncio
import inspect
import logging
from pprint import pprint
from typing import Dict, Any, Optional, TypedDict, cast
from datetime import datetime
import uuid
import os
from dbos import DBOS, DBOSConfig
from .step_registry import StepRegistry
from .execution_context import ExecutionContext, UserContext, StepStatus
from .streaming import (
    stream_manager,
    create_status_event,
    create_step_event,
    create_error_event,
)
# from .monitoring import monitoring  # currently unused


class DBOSStepResult(TypedDict):
    success: bool
    output_data: Any
    error: Optional[str]
    execution_time: Optional[int]
    step_id: Optional[str]
    step_type: Optional[str]


class DBOSWorkflowResult(TypedDict, total=False):
    success: bool | None
    execution_id: str
    workflow_id: str
    step_results: Dict[str, DBOSStepResult]
    completed_at: str
    error: str | None
    failed_step: str
    _dbos: Dict[str, Any]


# from .monitoring import monitoring  # currently unused
DBOS_AVAILABLE = True


logger = logging.getLogger(__name__)


class DBOSWorkflowAdapter:
    """
    Adapter that provides DBOS durable execution for our existing workflow engine.

    This adapter:
    1. Wraps our StepRegistry with DBOS decorators
    2. Converts our workflow configurations to DBOS workflows
    3. Provides automatic recovery and durability
    4. Maintains compatibility with existing step implementations
    """

    def __init__(self, step_registry: Optional[StepRegistry] = None):
        self.step_registry = step_registry or StepRegistry()
        self.logger = logger

        if not DBOS_AVAILABLE:
            self.logger.warning("DBOS not available - running in mock mode for development")

    async def initialize(self):
        """Initialize the adapter and register built-in steps"""
        await self.step_registry.register_builtin_steps()
        self.logger.info("DBOS Workflow Adapter initialized")

    async def execute_step_durable(
        self, step_type: str, step_config: Dict[str, Any], input_data: Dict[str, Any], execution_context_data: Dict[str, Any]
    ) -> DBOSStepResult:
        """
        DBOS step that wraps our existing step execution.

        This makes each step durable - if it fails, DBOS will retry it.
        Once it completes, it will never be re-executed.
        """
        # Reconstruct execution context from serializable data
        execution_context = self._reconstruct_execution_context(execution_context_data)

        # Execute the step using our existing step registry
        step_result = await self.step_registry.execute_step(
            step_type=step_type, step_config=step_config, input_data=input_data, execution_context=execution_context
        )

        # Store result in execution context for next steps
        execution_context.step_io_data[step_config.get("step_id", "unknown")] = step_result.output_data

        return {
            "success": step_result.status == StepStatus.COMPLETED,
            "output_data": step_result.output_data,
            "error": step_result.error_message,
            "execution_time": step_result.execution_time_ms,
            "step_id": step_config.get("step_id"),
            "step_type": step_type,
        }

    async def execute_workflow_durable(
        self, workflow_config: Dict[str, Any], trigger_data: Dict[str, Any], user_context_data: Optional[Dict[str, Any]] = None
    ) -> DBOSWorkflowResult:
        """
        DBOS workflow that executes our step graph durably.

        This workflow will automatically resume from the last completed step
        if interrupted at any point.
        """
        workflow_id = workflow_config.get("workflow_id", str(uuid.uuid4()))
        execution_id = str(uuid.uuid4())

        self.logger.info(f"Starting DBOS workflow execution: {execution_id}")

        # Create execution context payload
        execution_context_data = {
            "execution_id": execution_id,
            "workflow_id": workflow_id,
            "workflow_config": workflow_config,
            "user_context": user_context_data or {},
            "step_io_data": {"trigger_raw": trigger_data},
            "started_at": datetime.now().isoformat(),
        }

        # Get workflow steps
        steps = workflow_config.get("steps", [])
        if not steps:
            return {"error": "No steps defined in workflow", "success": False}

        # Execute steps sequentially (for POC - can be enhanced for parallel execution)
        step_results = {}

        for step in steps:
            step_id = step.get("step_id")
            step_type = step.get("step_type")

            if not step_id or not step_type:
                self.logger.error(f"Invalid step configuration: {step}")
                continue

            self.logger.info(f"Executing step {step_id} ({step_type})")

            # Prepare input data for this step
            input_data = self._prepare_step_input(step, step_results, trigger_data)

            # Execute step durably
            try:
                step_result = await self.execute_step_durable(
                    step_type=step_type, step_config=step, input_data=input_data, execution_context_data=execution_context_data
                )

                step_results[step_id] = step_result

                # Update execution context with step result
                execution_context_data["step_io_data"][step_id] = step_result["output_data"]

                if not step_result["success"]:
                    self.logger.error(f"Step {step_id} failed: {step_result.get('error')}")
                    return {
                        "success": False,
                        "error": f"Step {step_id} failed: {step_result.get('error')}",
                        "failed_step": step_id,
                        "step_results": step_results,
                    }

            except Exception as e:
                self.logger.error(f"Exception in step {step_id}: {e}")
                return {
                    "success": False,
                    "error": f"Exception in step {step_id}: {str(e)}",
                    "failed_step": step_id,
                    "step_results": step_results,
                }

        self.logger.info(f"DBOS workflow execution completed: {execution_id}")

        return {
            "success": True,
            "execution_id": execution_id,
            "workflow_id": workflow_id,
            "step_results": step_results,
            "completed_at": datetime.now().isoformat(),
        }

    def _prepare_step_input(
        self, step: Dict[str, Any], step_results: Dict[str, Any], trigger_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Prepare input data for a step based on previous step results and trigger data"""
        input_data = {}

        # Add trigger data
        input_data.update(trigger_data)

        # Add outputs from previous steps
        for step_id, result in step_results.items():
            if result.get("success") and result.get("output_data"):
                input_data[f"step_{step_id}"] = result["output_data"]

        # Add any static input from step configuration
        step_input = step.get("input", {})
        if isinstance(step_input, dict):
            input_data.update(step_input)

        return input_data

    def _reconstruct_execution_context(self, execution_context_data: Dict[str, Any]) -> ExecutionContext:
        """Reconstruct ExecutionContext from serializable data"""
        user_context_data = execution_context_data.get("user_context", {})
        user_context = UserContext(user_id=user_context_data.get("user_id"), session_id=user_context_data.get("session_id"))

        execution_context = ExecutionContext(
            workflow_config=execution_context_data["workflow_config"],
            user_context=user_context,
            execution_id=execution_context_data["execution_id"],
        )

        # Restore step I/O data
        execution_context.step_io_data = execution_context_data.get("step_io_data", {})

        return execution_context

    async def start_workflow(
        self,
        workflow_config: Dict[str, Any],
        trigger_data: Dict[str, Any],
        execution_id: str,
        user_context: Optional[Dict[str, Any]] = None,
        wait: bool = False,
    ) -> DBOSWorkflowResult:
        """
        Start a workflow execution using DBOS.

        This is the main entry point for executing workflows with DBOS durability.
        """
        if DBOS_AVAILABLE:
            # Try to start; if DBOS isn't created yet, lazily initialize and retry
            async def _start_once() -> DBOSWorkflowResult:
                handle = await DBOS.start_workflow_async(
                    dbos_execute_workflow_durable,
                    workflow_config,
                    trigger_data,
                    user_context,
                    execution_id,
                )

                # Prepare DBOS handle metadata for later persistence
                def _mk_dbos_meta(h: Any) -> Dict[str, Any]:
                    try:
                        attrs: Dict[str, Any] = {}
                        for a in ("id", "workflow_id", "instance_id", "uuid", "run_id"):
                            v = getattr(h, a, None)
                            if v is not None:
                                attrs[a] = str(v)
                        methods_present = [
                            m
                            for m in (
                                "result_async",
                                "wait_async",
                                "join_async",
                                "wait_result_async",
                                "result",
                                "wait",
                                "join",
                                "wait_result",
                                "get_result",
                                "get",
                            )
                            if hasattr(h, m)
                        ]
                        return {"handle_type": str(type(h)), "attributes": attrs, "methods": methods_present}
                    except Exception:
                        return {"handle_type": str(type(h))}

                if not wait:
                    # Return immediately with handle metadata; mark success=None to indicate in-progress
                    return {
                        "success": None,
                        "error": None,
                        "execution_id": execution_id,
                        "_dbos": _mk_dbos_meta(handle),
                        "step_results": {},
                    }

                dbos_meta = _mk_dbos_meta(handle)

                def _attach_dbos(val: Any) -> DBOSWorkflowResult:
                    res: Dict[str, Any] = val if isinstance(val, dict) else {"success": True, "result": val}
                    try:
                        res["_dbos"] = {"handle": dbos_meta}
                    except Exception:
                        pass
                    return cast(DBOSWorkflowResult, res)

                # DBOS 1.12.0 handle is typically awaitable; try multiple strategies
                # 1) Common async method patterns across versions
                async_methods = [
                    "result_async",
                    "wait_async",
                    "join_async",
                    "wait_result_async",
                ]
                for m in async_methods:
                    fn = getattr(handle, m, None)
                    if callable(fn):
                        try:
                            val = await fn()  # type: ignore[misc]
                            return _attach_dbos(val)
                        except Exception:
                            continue

                # 2) Common sync-like methods (may be coroutine functions in some builds)
                sync_methods = [
                    "result",
                    "wait",
                    "join",
                    "wait_result",
                    "get_result",
                    "get",
                ]
                for m in sync_methods:
                    fn = getattr(handle, m, None)
                    if callable(fn):
                        try:
                            if inspect.iscoroutinefunction(fn):
                                val = await fn()  # type: ignore[misc]
                                return _attach_dbos(val)
                            loop = asyncio.get_running_loop()
                            val = await loop.run_in_executor(None, fn)  # type: ignore[misc]
                            return _attach_dbos(val)
                        except Exception:
                            continue

                # 3) Generic awaitability checks
                if inspect.isawaitable(handle):
                    val = await handle  # type: ignore[misc]
                    return _attach_dbos(val)
                if asyncio.isfuture(handle) or isinstance(handle, asyncio.Task):
                    val = await handle  # type: ignore[misc]
                    return _attach_dbos(val)

                # 4) Last resort: try ensuring as a future (catch any exception)
                try:
                    val = await asyncio.ensure_future(handle)  # type: ignore[arg-type]
                    return _attach_dbos(val)
                except Exception:
                    pass

                if isinstance(handle, dict):
                    return _attach_dbos(handle)

                # Last resort: include attrs to help debugging
                attrs = [a for a in dir(handle) if not a.startswith("_")]
                raise RuntimeError(f"Unsupported DBOS workflow handle type: {type(handle)} with attrs={attrs}")

            try:
                return await _start_once()
            except Exception as e:
                if "No DBOS was created yet" in str(e):
                    try:
                        # Build config and create DBOS instance
                        from workflow_engine_poc.db.database import DATABASE_URL as _ENGINE_DB_URL

                        _dbos_db_url = os.getenv("DBOS_DATABASE_URL") or os.getenv("DATABASE_URL") or _ENGINE_DB_URL
                        _app_name = os.getenv("DBOS_APPLICATION_NAME") or os.getenv("DBOS_APP_NAME") or "workflow-engine-poc"
                        cfg = DBOSConfig(database_url=_dbos_db_url, name=_app_name)  # dbos 1.12.0 expects 'name'
                        DBOS(config=cfg)
                        try:
                            DBOS.launch()
                        except Exception:
                            pass
                    except Exception as init_err:
                        self.logger.error(f"DBOS initialization failed: {init_err}")
                        raise
                    # Retry once after init
                    return await _start_once()
                # Any other exception should propagate; raise to avoid returning None
                self.logger.error(f"DBOS start_workflow failed: {e}")
                raise

        else:
            # For development without DBOS, run directly
            return await self.execute_workflow_durable(workflow_config, trigger_data, user_context)


# ---------------- Module-level DBOS functions to avoid instance registration issues ----------------
@DBOS.step()
async def dbos_execute_step_durable(
    step_type: str,
    step_config: Dict[str, Any],
    input_data: Dict[str, Any],
    execution_context_data: Dict[str, Any],
) -> DBOSStepResult:
    print("Executing step under DBOS:", step_type)
    pprint(step_config)
    pprint(input_data)
    pprint(execution_context_data)
    adapter = await get_dbos_adapter()
    # Reconstruct execution context
    user_context_data = execution_context_data.get("user_context", {})
    user_context = UserContext(
        user_id=user_context_data.get("user_id"),
        session_id=user_context_data.get("session_id"),
    )
    execution_context = ExecutionContext(
        workflow_config=execution_context_data["workflow_config"],
        user_context=user_context,
        execution_id=execution_context_data["execution_id"],
    )
    execution_context.step_io_data = execution_context_data.get("step_io_data", {})

    # Execute using registry
    # Mark that this invocation is running under DBOS backend
    step_config = {**step_config, "_backend": "dbos"}
    step_result = await adapter.step_registry.execute_step(
        step_type=step_type,
        step_config=step_config,
        input_data=input_data,
        execution_context=execution_context,
    )

    execution_context.step_io_data[step_config.get("step_id", "unknown")] = step_result.output_data

    return {
        "success": step_result.status == StepStatus.COMPLETED,
        "status": getattr(step_result.status, "name", "").lower()
        if hasattr(step_result.status, "name")
        else ("completed" if step_result.execution_time_ms is not None else "unknown"),
        "output_data": step_result.output_data,
        "error": step_result.error_message,
        "execution_time": step_result.execution_time_ms,
        "step_id": step_config.get("step_id"),
        "step_type": step_type,
    }


@DBOS.workflow()
async def dbos_submit_approval(decision_key: str, payload: Dict[str, Any]) -> None:
    """Small DBOS workflow that sets an approval decision event."""
    DBOS.set_event(decision_key, payload)


@DBOS.workflow()
async def dbos_execute_workflow_durable(
    workflow_config: Dict[str, Any],
    trigger_data: Dict[str, Any],
    user_context_data: Optional[Dict[str, Any]] = None,
    execution_id: Optional[str] = None,
) -> DBOSWorkflowResult:
    adapter = await get_dbos_adapter()
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
        from .db.service import DatabaseService as _DBSvc
        from .db.database import get_db_session as _get_sess
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
                        from .db.service import DatabaseService
                        from .db.database import get_db_session
                        from .db.models.executions import ExecutionStatus as DBExecStatus

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
                            payload = await _DBOS.get_event_async(wid, decision_key, timeout_seconds=3600)
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


# Global adapter instance
_dbos_adapter: Optional[DBOSWorkflowAdapter] = None


async def get_dbos_adapter() -> DBOSWorkflowAdapter:
    """Get or create the global DBOS adapter instance"""
    global _dbos_adapter
    if _dbos_adapter is None:
        _dbos_adapter = DBOSWorkflowAdapter()
        await _dbos_adapter.initialize()
        # If DBOS is present, register this instance so bound @DBOS.workflow/@DBOS.step methods work
        if DBOS_AVAILABLE:
            try:
                # Ensure configured
                from workflow_engine_poc.db.database import DATABASE_URL as _ENGINE_DB_URL

                _dbos_db_url = os.getenv("DBOS_DATABASE_URL") or os.getenv("DATABASE_URL") or _ENGINE_DB_URL
                _app_name = os.getenv("DBOS_APPLICATION_NAME") or os.getenv("DBOS_APP_NAME") or "workflow-engine-poc"
                try:
                    DBOS(config=DBOSConfig(database_url=_dbos_db_url, name=_app_name))  # type: ignore[call-arg]
                except Exception:
                    # likely already configured
                    pass
                # Do not register our adapter instance with DBOS; we use module-level functions
            except Exception as e:
                logger.warning(f"DBOS register_instance failed: {e}")
    return _dbos_adapter

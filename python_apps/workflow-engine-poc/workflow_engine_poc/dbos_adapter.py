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
from typing import Dict, Any, Optional, TypedDict, cast
from datetime import datetime
import uuid
import os
from dbos import DBOS, DBOSConfig
from .step_registry import StepRegistry
from .execution_context import ExecutionContext, UserContext, StepStatus
# from .monitoring import monitoring  # currently unused


class DBOSStepResult(TypedDict):
    success: bool
    output_data: Any
    error: Optional[str]
    execution_time: Optional[int]
    step_id: Optional[str]
    step_type: Optional[str]


class DBOSWorkflowResult(TypedDict, total=False):
    success: bool
    execution_id: str
    workflow_id: str
    step_results: Dict[str, DBOSStepResult]
    completed_at: str
    error: str
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
        self, workflow_config: Dict[str, Any], trigger_data: Dict[str, Any], user_context: Optional[Dict[str, Any]] = None
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
    step_result = await adapter.step_registry.execute_step(
        step_type=step_type,
        step_config=step_config,
        input_data=input_data,
        execution_context=execution_context,
    )

    execution_context.step_io_data[step_config.get("step_id", "unknown")] = step_result.output_data

    return {
        "success": step_result.status == StepStatus.COMPLETED,
        "output_data": step_result.output_data,
        "error": step_result.error_message,
        "execution_time": step_result.execution_time_ms,
        "step_id": step_config.get("step_id"),
        "step_type": step_type,
    }


@DBOS.workflow()
async def dbos_execute_workflow_durable(
    workflow_config: Dict[str, Any],
    trigger_data: Dict[str, Any],
    user_context_data: Optional[Dict[str, Any]] = None,
) -> DBOSWorkflowResult:
    adapter = await get_dbos_adapter()
    workflow_id = workflow_config.get("workflow_id") or str(uuid.uuid4())
    execution_id = str(uuid.uuid4())

    # Construct execution context payload
    execution_context_data = {
        "execution_id": execution_id,
        "workflow_id": workflow_id,
        "workflow_config": workflow_config,
        "user_context": user_context_data or {},
        "step_io_data": {"trigger_raw": trigger_data},
        "started_at": datetime.now().isoformat(),
    }

    steps = workflow_config.get("steps", [])
    if not steps:
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

    for step in steps:
        step_id = step.get("step_id")
        step_type = step.get("step_type")
        if not step_id or not step_type:
            adapter.logger.error(f"Invalid step configuration: {step}")
            continue

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
            if not res.get("success"):
                return {
                    "success": False,
                    "error": f"Step {step_id} failed: {res.get('error')}",
                    "failed_step": step_id,
                    "step_results": step_results,
                }
        except Exception as e:
            return {
                "success": False,
                "error": f"Exception in step {step_id}: {str(e)}",
                "failed_step": step_id,
                "step_results": step_results,
            }

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

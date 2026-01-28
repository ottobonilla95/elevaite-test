from __future__ import annotations

from typing import Any, Dict, Optional, TypedDict

from dbos import DBOS

from ..execution_context import ExecutionContext, UserContext
from workflow_core_sdk.models import StepStatus
from . import get_dbos_adapter  # temporary import until adapter is split


class DBOSStepResult(TypedDict):
    success: bool
    output_data: Any
    error: Optional[str]
    execution_time: Optional[int]
    step_id: Optional[str]
    step_type: Optional[str]
    status: Optional[str]


@DBOS.step()
async def dbos_execute_step_durable(
    step_type: str,
    step_config: Dict[str, Any],
    input_data: Dict[str, Any],
    execution_context_data: Dict[str, Any],
) -> DBOSStepResult:
    print("Executing step under DBOS:", step_type)
    # pprint(step_config)
    # pprint(input_data)
    # pprint(execution_context_data)
    adapter = await get_dbos_adapter()
    if not adapter:
        raise RuntimeError("DBOS adapter not available")
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
    # Restore metadata (including dbos_workflow_id)
    execution_context.metadata.update(execution_context_data.get("metadata", {}))

    # Execute using registry
    # Mark that this invocation is running under DBOS backend
    step_config = {**step_config, "_backend": "dbos"}
    step_result = await adapter.step_registry.execute_step(
        step_type=step_type,
        step_config=step_config,
        input_data=input_data,
        execution_context=execution_context,
    )

    execution_context.step_io_data[step_config.get("step_id", "unknown")] = (
        step_result.output_data
    )

    # Derive a human-readable status for DBOS based primarily on the step output payload.
    # This allows domain-specific statuses like "ingesting" to propagate through, while
    # still falling back to the enum name when no explicit status is provided.
    if (
        isinstance(step_result.output_data, dict)
        and "status" in step_result.output_data
    ):
        status_val = str(step_result.output_data.get("status") or "").lower()
    else:
        status_val = (
            getattr(step_result.status, "name", "").lower()
            if hasattr(step_result.status, "name")
            else (
                "completed" if step_result.execution_time_ms is not None else "unknown"
            )
        )

    return {
        "success": step_result.status == StepStatus.COMPLETED,
        "status": status_val,
        "output_data": step_result.output_data,
        "error": step_result.error_message,
        "execution_time": step_result.execution_time_ms,
        "step_id": step_config.get("step_id"),
        "step_type": step_type,
    }

"""Input node step - data entry point with no execution logic."""

from typing import Any, Dict

from workflow_core_sdk.execution_context import ExecutionContext


async def input_step(
    step_config: Dict[str, Any], input_data: Dict[str, Any], execution_context: ExecutionContext
) -> Dict[str, Any]:
    """Pass through data from step config, step_io_data[step_id], or trigger_raw."""
    step_id = step_config.get("step_id", "input")
    config = step_config.get("config", step_config.get("parameters", {}))
    kind = config.get("kind", "manual")

    # First priority: use text/data from step config (configured in the canvas)
    text = config.get("text")
    if text:
        return {"kind": kind, "step_id": step_id, "text": text, "source": "config"}

    # Second priority: direct data for this input node from step_io_data
    if step_id in execution_context.step_io_data:
        return {"kind": kind, "step_id": step_id, "data": execution_context.step_io_data[step_id], "source": "direct"}

    # Third priority: use trigger_raw if available
    if "trigger_raw" in execution_context.step_io_data:
        return {
            "kind": kind,
            "step_id": step_id,
            "data": execution_context.step_io_data["trigger_raw"],
            "source": "trigger_raw",
        }

    # No data yet
    return {"kind": kind, "step_id": step_id, "data": {}, "source": "none", "awaiting_input": True}

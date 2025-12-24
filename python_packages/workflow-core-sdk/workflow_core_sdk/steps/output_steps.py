"""Output node step - pass-through endpoint for displaying workflow output on canvas."""

from typing import Any, Dict

from workflow_core_sdk.execution_context import ExecutionContext


async def output_step(
    step_config: Dict[str, Any], input_data: Dict[str, Any], execution_context: ExecutionContext
) -> Dict[str, Any]:
    """Pass through input data as output. Used to mark workflow endpoints on canvas.

    The output step acts as a simple pass-through:
    - Takes whatever data comes from its dependencies
    - Returns it unchanged for display purposes
    - Can optionally format or label the output

    Parameters (in step_config.parameters):
    - label: Optional label for the output (for UI display)
    - format: Optional format hint ("json", "text", "markdown", etc.)
    """
    step_id = step_config.get("step_id", "output")
    params = step_config.get("parameters", step_config.get("config", {}))
    label = params.get("label", "Output")
    output_format = params.get("format", "auto")

    # Pass through the input data unchanged
    return {
        "step_id": step_id,
        "label": label,
        "format": output_format,
        "data": input_data,
        "success": True,
    }


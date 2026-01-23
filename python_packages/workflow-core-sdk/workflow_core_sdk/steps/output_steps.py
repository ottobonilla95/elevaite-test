"""Output node step - pass-through endpoint for displaying workflow output on canvas."""

from typing import Any, Dict, List

from workflow_core_sdk.execution_context import ExecutionContext


async def output_step(
    step_config: Dict[str, Any], input_data: Dict[str, Any], execution_context: ExecutionContext
) -> Dict[str, Any]:
    """Pass through data from immediate dependencies only. Used to mark workflow endpoints on canvas.

    The output step only passes through data from its direct dependencies:
    - Takes data from the immediately preceding step(s) only
    - Ignores accumulated workflow data
    - Can optionally format or label the output

    Parameters (in step_config.parameters):
    - label: Optional label for the output (for UI display)
    - format: Optional format hint ("json", "text", "markdown", etc.)
    """
    step_id = step_config.get("step_id", "output")
    params = step_config.get("parameters", step_config.get("config", {}))
    label = params.get("label", "Output")
    output_format = params.get("format", "auto")

    # Only gather data from immediate dependencies, not all input_data
    dependencies: List[str] = step_config.get("dependencies", [])
    output_data: Dict[str, Any] = {}

    if dependencies and hasattr(execution_context, "step_io_data"):
        # Collect data only from direct dependencies
        for dep_id in dependencies:
            dep_data = execution_context.step_io_data.get(dep_id)
            if dep_data:
                # If single dependency, use its data directly
                if len(dependencies) == 1:
                    output_data = dep_data
                else:
                    # Multiple dependencies: nest under dependency ID
                    output_data[dep_id] = dep_data

    return {
        "step_id": step_id,
        "label": label,
        "format": output_format,
        "data": output_data,
        "success": True,
    }

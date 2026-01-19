"""Output node step - pass-through endpoint for displaying workflow output on canvas."""

from typing import Any, Dict, List

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

    # Gather data from dependencies if input_data is empty
    output_data = input_data
    if not output_data:
        dependencies: List[str] = step_config.get("dependencies", [])
        if dependencies and hasattr(execution_context, "step_io_data"):
            # Collect data from all dependencies
            for dep_id in dependencies:
                dep_data = execution_context.step_io_data.get(dep_id)
                if dep_data:
                    # If single dependency, use its data directly
                    if len(dependencies) == 1:
                        output_data = dep_data
                    else:
                        # Multiple dependencies: nest under dependency ID
                        if not output_data:
                            output_data = {}
                        output_data[dep_id] = dep_data

    return {
        "step_id": step_id,
        "label": label,
        "format": output_format,
        "data": output_data,
        "success": True,
    }

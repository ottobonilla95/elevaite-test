"""Merge node step - combines multiple inputs with OR/AND logic."""

from typing import Any, Dict

from workflow_core_sdk.execution_context import ExecutionContext


async def merge_step(
    step_config: Dict[str, Any], input_data: Dict[str, Any], execution_context: ExecutionContext
) -> Dict[str, Any]:
    """Combine outputs from completed dependencies based on mode and combine_mode."""
    params = step_config.get("parameters", step_config.get("config", {}))
    mode = params.get("mode", "first_available")
    combine_mode = params.get("combine_mode", "object")
    dependencies = step_config.get("dependencies", [])

    # Gather outputs from completed dependencies (preserving order)
    completed: Dict[str, Any] = {}
    for dep_id in dependencies:
        if dep_id in execution_context.completed_steps:
            result = execution_context.step_results.get(dep_id)
            if result:
                completed[dep_id] = result.output_data if hasattr(result, "output_data") else result

    # First available mode or first combine mode: return first completed
    if mode == "first_available" or combine_mode == "first":
        first_id = next(iter(completed), None)
        return {
            "mode": mode,
            "source_step": first_id,
            "data": completed.get(first_id),
            "completed_count": len(completed),
            "total_dependencies": len(dependencies),
        }

    # Array mode: return as list
    if combine_mode == "array":
        return {
            "mode": mode,
            "data": list(completed.values()),
            "sources": list(completed.keys()),
            "completed_count": len(completed),
            "total_dependencies": len(dependencies),
        }

    # Object mode (default): return as dict keyed by step_id
    return {
        "mode": mode,
        "data": completed,
        "sources": list(completed.keys()),
        "completed_count": len(completed),
        "total_dependencies": len(dependencies),
    }

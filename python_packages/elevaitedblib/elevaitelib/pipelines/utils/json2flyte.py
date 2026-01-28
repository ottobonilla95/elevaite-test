import json
import sys
from typing import Dict, Any, List
from flytekit import workflow, task
from papermill import execute_notebook


def load_json(file_path: str) -> Dict[str, Any]:
    with open(file_path, "r") as f:
        return json.load(f)


@task
def execute_script(
    task_id: str,
    task_type: str,
    src: str,
    output_vars: List[str],
    inputs: Dict[str, str],
) -> Dict[str, str]:
    # Create execution namespace with type-safe inputs
    exec_globals: Dict[str, Any] = {}
    exec_globals |= inputs

    try:
        if task_type == "pyscript":
            with open(src, "r") as script:
                exec(script.read(), exec_globals)
        elif task_type == "jupyternotebook":
            execute_notebook(
                input_path=src,
                output_path=f"/tmp/{task_id}_output.ipynb",
                parameters=inputs,
            )
    except Exception as e:
        raise RuntimeError(f"Task {task_id} failed: {str(e)}")

    # Validate outputs exist in namespace
    return {var: exec_globals.get(var, f"MISSING_OUTPUT_{var}") for var in output_vars}


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python flyte_workflow.py <json_file>")
        sys.exit(1)

    pipeline = load_json(sys.argv[1])
    variable_sources = {}

    # Build variable dependency graph
    for task_info in pipeline["tasks"]:
        for var in task_info.get("output", []):
            variable_sources[var] = task_info["id"]

    @workflow
    async def run_pipeline() -> Dict[str, str]:
        task_results = {}
        final_outputs = {}

        for task_info in pipeline["tasks"]:
            task_id = task_info["id"]
            inputs = {}

            # Resolve inputs from upstream tasks
            for var in task_info.get("input", []):
                if var not in variable_sources:
                    raise ValueError(f"Undefined input variable: {var}")
                source_task = variable_sources[var]
                inputs[var] = task_results[source_task].get(var, "")

            # Execute task with validated inputs
            task_output = execute_script(
                task_id=task_id,
                task_type=task_info["task_type"],
                src=task_info["src"],
                output_vars=task_info.get("output", []),
                inputs=inputs,
            )

            assert task_output is not None and task_output is Dict[str, str]

            task_results[task_id] = task_output

            final_outputs.update(
                {
                    var: task_output[var]
                    for var in task_info.get("output", [])
                    if var in task_output
                }
            )

        return final_outputs

    print("Pipeline execution result:", run_pipeline())

import ast
import json
import os
import re
import sys


def sanitize_pipeline_name(name: str) -> str:
    """
    Convert a python-style name with underscores into a CamelCase name.
    For example: "main_pipeline" becomes "MainPipeline".
    Any non-alphanumeric characters are removed.
    """
    words = name.split("_")
    sanitized_words = []
    for word in words:
        cleaned = re.sub(r"[^A-Za-z0-9]", "", word)
        if cleaned:
            sanitized_words.append(cleaned.capitalize())
    return "".join(sanitized_words)


def convert_script_to_pipeline_json(script_path: str, schedule: dict):
    """
    Parses a Python script to extract top-level function definitions and
    generates a pipeline JSON definition that runs these functions in order.

    Each function becomes a pyscript task:
      - The first function runs without dependencies.
      - Every subsequent function depends on the immediately preceding task.
      - For each task, an output variable is defined as <function_name>_output.
      - For tasks after the first, the input variable is the previous task's output.
      - The task's description is taken directly from the function's docstring.

    The generated JSON file is saved to ~/generated_pipelines with a filename
    based on the original script file name (e.g. buying_groceries.py → BuyingGroceries.json).
    """
    if not os.path.exists(script_path):
        raise FileNotFoundError(f"Script file {script_path} not found.")

    with open(script_path, "r") as f:
        node = ast.parse(f.read(), filename=script_path)

    # Extract each function and its docstring
    func_defs = [
        (n.name, ast.get_docstring(n) or "")
        for n in node.body
        if isinstance(n, ast.FunctionDef)
    ]

    if not func_defs:
        raise ValueError("No functions found in the script.")

    tasks = []
    variables = []

    for idx, (func, func_doc) in enumerate(func_defs):
        task_id = f"task{idx+1}"
        output_var = f"{func}_output"
        variables.append({"name": output_var, "var_type": "string"})

        task = {
            "id": task_id,
            "name": f"Task for {func}",
            "task_type": "pyscript",
            "src": os.path.abspath(script_path),
            "entrypoint": func,
            "dependencies": [],
            "input": [],
            "output": [output_var],
            "description": func_doc,
        }
        if idx > 0:
            prev_func, _ = func_defs[idx - 1]
            prev_task_id = f"task{idx}"
            prev_output = f"{prev_func}_output"
            task["dependencies"] = [prev_task_id]
            task["input"] = [prev_output]

        tasks.append(task)

    script_basename = os.path.basename(script_path)
    name_without_ext = os.path.splitext(script_basename)[0]
    pipeline_name = sanitize_pipeline_name(name_without_ext)

    pipeline = {
        "name": pipeline_name,
        "description": "",
        "variables": variables,
        "tasks": tasks,
    }

    if schedule is not None:
        pipeline["schedule"] = schedule

    out_dir = os.path.expanduser("~/generated_pipelines")
    os.makedirs(out_dir, exist_ok=True)

    output_file = os.path.join(out_dir, f"{pipeline_name}.json")

    # Safety check: prompt if the output file already exists.
    if os.path.exists(output_file):
        while True:
            choice = (
                input(
                    f"File {output_file} already exists. Overwrite? ([y]es (default), [n]o, [r]ename with increment): "
                )
                .strip()
                .lower()
            )
            if choice in ("", "y"):
                # Overwrite the file.
                break
            elif choice == "n":
                print("Skipping file creation.")
                return
            elif choice == "r":
                base = os.path.join(out_dir, pipeline_name)
                ext = ".json"
                counter = 1
                new_file = f"{base}{counter}{ext}"
                while os.path.exists(new_file):
                    counter += 1
                    new_file = f"{base}{counter}{ext}"
                output_file = new_file
                print(f"Renaming output file to {output_file}")
                break
            else:
                print("Invalid choice. Please enter 'y', 'n', or 'r'.")

    with open(output_file, "w") as f:
        json.dump(pipeline, f, indent=2)

    print(f"Pipeline JSON has been written to {output_file}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python convert_script.py <path_to_script.py> [cron_schedule]")
        sys.exit(1)

    script_file = sys.argv[1]
    # If a cron schedule is provided as a command-line argument, use it; otherwise, schedule is omitted.
    cron_schedule = sys.argv[2] if len(sys.argv) > 2 else None
    sched = {"cron": cron_schedule} if cron_schedule else None

    convert_script_to_pipeline_json(script_path=script_file, schedule=sched or {})

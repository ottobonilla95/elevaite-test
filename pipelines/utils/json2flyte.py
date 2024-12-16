import json
import sys
import requests
from flytekit import workflow, task, FlyteContext
from flytekit.types.file import FlyteFile
from flytekit.types.directory import FlyteDirectory

def load_json_from_path(file_path):
    with open(file_path, 'r') as f:
        data = json.load(f)  # Parse JSON data into a dictionary
        return data

# Define tasks dynamically based on the JSON schema
def create_task(task_info):
    @task
    def task_fn(**kwargs):
        # Execute the Python script or Jupyter notebook based on task type
        if task_info['type'] == 'pyscript':
            exec(open(task_info['src']).read())
        elif task_info['type'] == 'jupyternotebook':
            exec(open(task_info['src']).read())

        # Return outputs based on defined output variables
        return {output: kwargs.get(output) for output in task_info.get('output', [])}

    return task_fn

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python flyte_workflow.py <json_file_path>")
        sys.exit(1)

    json_file_path = sys.argv[1]
    pipeline = load_json_from_path(json_file_path)['pipeline']

    # Create a dictionary to store task references
    tasks = {}

    # Create tasks from the JSON schema
    for task_info in pipeline['tasks']:
        task_id = task_info['id']
        tasks[task_id] = create_task(task_info)

    # Define the workflow
    @workflow
    def run_pipeline(**kwargs):
        results = {}
        
        # Execute each task in order based on dependencies
        for task_info in pipeline['tasks']:
            task_id = task_info['id']
            input_values = {input_var: kwargs.get(input_var) for input_var in task_info.get('input', [])}
            results[task_id] = tasks[task_id](**input_values)

        # Return outputs of the last task or any other relevant outputs as needed
        return results

    # Run the workflow locally (optional)
    run_pipeline()

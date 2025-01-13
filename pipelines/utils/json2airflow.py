import json
import sys
import requests
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.papermill_operator import PapermillOperator
from airflow.models import Variable
from datetime import datetime, timedelta
import importlib.util
import os

def load_json_from_path(file_path):
    with open(file_path, 'r') as f:
        data = json.load(f)  # Parse JSON data into a dictionary
        return data

# Function to execute Python scripts
def run_python_script(script_path, entrypoint, ti):
    # Load the script as a module
    module_name = os.path.basename(script_path).replace('.py', '')
    
    # Specify the module's file path
    spec = importlib.util.spec_from_file_location(module_name, script_path)
    module = importlib.util.module_from_spec(spec)
    
    # Execute the module to make its functions available
    spec.loader.exec_module(module)
    
    # Call the specified entry point function
    if hasattr(module, entrypoint):
        getattr(module, entrypoint)(ti)
    else:
        raise AttributeError(f"Module '{module_name}' has no function '{entrypoint}'")

# def run_python_script(script_path, ti):  # ti: task instance
#     exec(open(script_path).read(), {'ti': ti})


json_file_paths = [
    # '/home/k/airflow/dags/dags/DEMO/pipeline.json',
    '/home/k/airflow/dags/dags/LOG_ANALYSIS/pipeline.json',
]

for json_file_path in json_file_paths:
    pipeline = load_json_from_path(json_file_path)['pipeline']

    default_args = {
        'owner': 'airflow',
        'depends_on_past': False,
        'start_date': datetime(2024, 12, 13),
        'retries': 1,
        'retry_delay': timedelta(minutes=5),
    }

    dag = DAG(
        pipeline['name'],
        description=pipeline['description'],
        default_args=default_args,
        schedule_interval='@daily',
    )

    # Create a dictionary to store task references
    tasks = {}

    # Create tasks from the JSON schema
    for task in pipeline['tasks']:
        task_id = task['id']
        
        # Define a callable for Python scripts
        if task['type'] == 'pyscript':
            op = PythonOperator(
                task_id=task_id,
                python_callable=run_python_script,
                op_kwargs={'script_path': task['src'], 'entrypoint': task['entrypoint']},
                dag=dag,
            )
        
        # Define a callable for Jupyter notebooks
        elif task['type'] == 'jupyternotebook':
            op = PapermillOperator(
                task_id=task_id,
                input_nb=task['src'],
                output_nb='/tmp/out_notebook_{{ execution_date }}.ipynb',
                parameters={x: f'{{{{ task_instance.xcom_pull(key="{x}")}}}}' for x in task['input']},
                dag=dag,
            )
        
        tasks[task_id] = op

    # Set dependencies between tasks based on inputs and outputs
    for task in pipeline['tasks']:
        for dep in task['dependencies']:
            tasks[task['id']].set_upstream(tasks[dep])

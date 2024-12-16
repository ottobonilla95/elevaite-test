import json
import sys
import requests
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.papermill_operator import PapermillOperator
from airflow.models import Variable
from datetime import datetime, timedelta

def load_json_from_path(file_path):
    with open(file_path, 'r') as f:
        data = json.load(f)  # Parse JSON data into a dictionary
        return data

# Function to execute Python scripts
def run_python_script(script_path):
    exec(open(script_path).read())

json_file_path = '/home/k/airflow/dags/dags/DEMO/pipeline.json'
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
            op_kwargs={'script_path': task['src']},
            dag=dag,
        )
    
    # Define a callable for Jupyter notebooks
    elif task['type'] == 'jupyternotebook':
        op = PapermillOperator(
            task_id=task_id,
            input_nb=task['src'],
            output_nb='/tmp/out.ipynb',
            dag=dag,
        )
    
    tasks[task_id] = op

# Set dependencies between tasks based on inputs and outputs
for task in pipeline['tasks']:
    for dep in task['dependencies']:
        tasks[task['id']].set_upstream(tasks[dep])

#     # Handle input and output variables for each task
#     if 'input' in task:
#         for input_var in task['input']:
#             # Use Airflow Variables to get input values
#             input_value = Variable.get(input_var)
#             tasks[task['id']].op_kwargs[input_var] = input_value
    
#     if 'output' in task:
#         for output_var in task['output']:
#             tasks[task['id']].op_kwargs[output_var] = f"{{{{ ti.xcom_pull(task_ids='{task_id}', key='{output_var}') }}}}"

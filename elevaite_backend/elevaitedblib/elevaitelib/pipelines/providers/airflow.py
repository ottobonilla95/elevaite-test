from datetime import datetime, timedelta
from airflow.models import DagBag, DAG
from airflow.operators.python import PythonOperator
from airflow.operators.papermill_operator import PapermillOperator

from ..utils.json2airflow import load_json_from_path, run_python_script


def create_dag_from_pipeline(pipeline: dict) -> DAG:
    default_args = {
        "owner": "airflow",
        "depends_on_past": False,
        "start_date": datetime(2024, 12, 13),
        "retries": 1,
        "retry_delay": timedelta(minutes=5),
    }
    dag = DAG(
        pipeline["name"],
        description=pipeline.get("description", ""),
        default_args=default_args,
        schedule_interval="@daily",
    )
    tasks = {}

    for task in pipeline["tasks"]:
        task_id = task["id"]
        if task["task_type"] == "pyscript":
            op = PythonOperator(
                task_id=task_id,
                python_callable=run_python_script,
                op_kwargs={
                    "script_path": task["src"],
                    "entrypoint": task["entrypoint"],
                },
                dag=dag,
            )
        elif task["task_type"] == "jupyternotebook":
            op = PapermillOperator(
                task_id=task_id,
                input_nb=task["src"],
                output_nb=f"/tmp/out_notebook_{{{{ execution_date }}}}.ipynb",
                parameters={
                    x: f'{{{{ task_instance.xcom_pull(key="{x}") }}}}'
                    for x in task.get("input", [])
                },
                dag=dag,
            )
        else:
            raise ValueError(f"Unsupported task type: {task['task_type']}")
        tasks[task_id] = op

    # Set dependencies between tasks
    for task in pipeline["tasks"]:
        for dep in task.get("dependencies", []):
            tasks[task["id"]].set_upstream(tasks[dep])

    return dag


def register_dag(dag: DAG) -> None:
    """
    Register the created DAG to Airflow's DagBag.
    Note: In a real-world scenario you might write the DAG to a file in the DAG folder.
    """
    dagbag = DagBag()
    dagbag.dags[dag.dag_id] = dag


def create_airflow_dags(request_count: int, json_files: list[str]) -> list[dict]:
    results = []
    if request_count != len(json_files):
        raise ValueError(
            "The number of json_files provided does not match the request_count."
        )

    for json_file in json_files:
        try:
            pipeline_def = load_json_from_path(json_file)
            dag = create_dag_from_pipeline(pipeline_def)
            register_dag(dag)
            results.append(
                {"json_file": json_file, "dag_id": dag.dag_id, "status": "created"}
            )
        except Exception as e:
            results.append({"json_file": json_file, "error": str(e)})
    return results


def get_airflow_dag_status(dag_id: str) -> dict:
    dagbag = DagBag()
    dag = dagbag.get_dag(dag_id)
    if not dag:
        return {"error": f"No DAG found with id {dag_id}"}
    # For demonstration purposes, return basic information
    return {
        "dag_id": dag_id,
        "description": dag.description,
        "tasks": list(dag.task_dict.keys()),
    }


def update_airflow_dag(json_file: str) -> dict:
    try:
        pipeline_def = load_json_from_path(json_file)
        dag = create_dag_from_pipeline(pipeline_def)
        # Overwrite the existing DAG registration
        register_dag(dag)
        return {"json_file": json_file, "dag_id": dag.dag_id, "status": "updated"}
    except Exception as e:
        return {"json_file": json_file, "error": str(e)}


def delete_airflow_dag(dag_id: str) -> dict:
    dagbag = DagBag()
    if dag_id in dagbag.dags:
        dagbag.dags.pop(dag_id)
        return {"dag_id": dag_id, "status": "deleted"}
    else:
        return {"error": f"No DAG found with id {dag_id}"}

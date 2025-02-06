import json
import os
import sys
import time
import boto3
from sagemaker.processing import ScriptProcessor
from sagemaker.workflow.pipeline import Pipeline
from sagemaker.workflow.steps import ProcessingStep

REQUIRED_ENV_VARS = [
    "AWS_ACCESS_KEY_ID",
    "AWS_SECRET_ACCESS_KEY",
    "AWS_REGION",
    "AWS_ROLE_ARN",
]

_missing = [var for var in REQUIRED_ENV_VARS if var not in os.environ]
if _missing:
    raise EnvironmentError(f"Missing environment variables: {', '.join(_missing)}")

boto3.setup_default_session(region_name=os.environ["AWS_REGION"])


def load_pipeline_definition(json_file: str) -> dict:
    """Load pipeline definition from a JSON file."""
    with open(json_file, "r") as f:
        return json.load(f)


def create_pipeline(
    pipeline_def: dict,
    persist_job_name_flag: bool,
    container_image: str = "",
    instance_type: str = "ml.m5.xlarge",
) -> Pipeline:
    """
    Create a SageMaker Pipeline from a JSON definition.

    Args:
        pipeline_def: The dictionary containing the pipeline definition.
        container_image: The URI of the container image to use for processing.
                         If None, the environment variable 'SAGEMAKER_CONTAINER_IMAGE'
                         will be used.
        instance_type: The SageMaker instance type to use (default: "ml.m5.xlarge").
        persist_job_name_flag: Boolean flag used if the pipeline JSON does not specify
                               the "persist_job_name" key.

    Returns:
        A sagemaker.workflow.pipeline.Pipeline object.
    """
    if container_image is None:
        container_image = os.getenv("SAGEMAKER_CONTAINER_IMAGE")
        if container_image is None:
            raise ValueError(
                "No container image provided and SAGEMAKER_CONTAINER_IMAGE is not set in the environment."
            )

    steps = {}
    step_list = []

    role = os.environ["AWS_ROLE_ARN"]

    for task in pipeline_def["tasks"]:
        task_id = task["id"]

        if task["task_type"] == "pyscript":
            command = ["python"]
        elif task["task_type"] == "jupyternotebook":
            command = ["papermill"]
        else:
            raise ValueError(f"Unknown task_type: {task['task_type']}")

        # File paths for input/output
        input_path = f"/opt/ml/processing/input/{task_id}.json"
        output_path = f"/opt/ml/processing/output/{task_id}.json"

        # Build job arguments
        job_args = ["--entrypoint", task["entrypoint"], "--output", output_path]

        for var in task.get("input", []):
            source_task = next(
                (t["id"] for t in pipeline_def["tasks"] if var in t.get("output", [])),
                None,
            )
            if not source_task:
                raise ValueError(f"Input variable {var} is not produced by any task")

            job_args.extend(
                [f"--{var}", f"/opt/ml/processing/output/{source_task}.json"]
            )

        # Define processor
        processor = ScriptProcessor(
            image_uri=container_image,
            command=command,
            instance_type=instance_type,
            instance_count=1,
            role=role,
        )

        # Resolve explicit dependencies.
        depends_on = [
            steps[dep] for dep in task.get("dependencies", []) if dep in steps
        ]

        step = ProcessingStep(
            name=task_id,
            processor=processor,
            code=task["src"],
            job_arguments=job_args,
            depends_on=depends_on,
        )

        steps[task_id] = step
        step_list.append(step)

    # Determine whether to persist the job name
    persist_job_name = pipeline_def.get("persist_job_name", persist_job_name_flag)

    pipeline_args = {
        "name": pipeline_def.get("name", "SageMakerPipeline"),
        "parameters": [],
        "steps": step_list,
    }

    if persist_job_name:
        try:
            from sagemaker.workflow.pipeline_definition_config import (
                PipelineDefinitionConfig,
            )

            pipeline_args["pipeline_definition_config"] = PipelineDefinitionConfig(
                use_custom_job_prefix=True
            )
        except Exception as e:
            print("Warning: Could not configure custom job prefixing. Error:", e)

    return Pipeline(**pipeline_args)


def upsert_pipeline(pipeline: Pipeline) -> dict:
    """
    Upsert the given pipeline to SageMaker.

    Args:
        pipeline: The Pipeline object to upsert.

    Returns:
        The upsert response dictionary.
    """
    role = os.environ["AWS_ROLE_ARN"]
    return pipeline.upsert(role_arn=role)


def start_pipeline(pipeline: Pipeline, parameters: dict = {}):
    """
    Start a pipeline execution.

    Args:
        pipeline: The Pipeline object to execute.
        parameters: (Optional) Dictionary of parameter names to values.

    Returns:
        The pipeline execution object.
    """
    if parameters is None:
        parameters = {}
    return pipeline.start(parameters=parameters)


def monitor_pipeline(execution_arn: str, poll_interval: int = 30):
    """
    Monitor a SageMaker pipeline execution until completion, displaying detailed step information.

    Args:
        execution_arn: The ARN of the pipeline execution.
        poll_interval: Time in seconds between status checks (default: 30).
    """
    client = boto3.client("sagemaker")
    print("Monitoring pipeline execution...")

    while True:
        # Describe the overall pipeline execution
        response = client.describe_pipeline_execution(
            PipelineExecutionArn=execution_arn
        )
        status = response.get("PipelineExecutionStatus")
        print(f"Current pipeline status: {status}")

        # List all steps in the pipeline execution
        steps_response = client.list_pipeline_execution_steps(
            PipelineExecutionArn=execution_arn
        )

        for step in steps_response.get("PipelineExecutionSteps", []):
            step_name = step.get("StepName")
            step_status = step.get("StepStatus")
            failure_reason = step.get("FailureReason", "N/A")
            print(f"Step '{step_name}' - Status: {step_status}")
            if step_status == "Failed":
                print(f"  Failure reason: {failure_reason}")

        if status in ["Succeeded", "Failed", "Stopped"]:
            break

        time.sleep(poll_interval)

    print(f"Pipeline execution finished with status: {status}")


if __name__ == "__main__":
    if len(sys.argv) < 2 or len(sys.argv) > 3:
        print("Usage: python json2sagemaker.py <json_file> [persist_job_name]")
        sys.exit(1)

    json_file = sys.argv[1]
    persist_flag = (
        sys.argv[2].lower() in ["true", "1", "yes"] if len(sys.argv) == 3 else False
    )

    pipeline_def = load_pipeline_definition(json_file)
    pipeline = create_pipeline(pipeline_def, persist_job_name_flag=persist_flag)

    print("SageMaker Pipeline definition:")
    print(pipeline.definition())

    print("Upserting pipeline...")
    upsert_response = upsert_pipeline(pipeline)
    print("Upsert response:", upsert_response)

    print("Starting pipeline execution...")
    execution = start_pipeline(pipeline)
    print("Pipeline execution started. Execution ARN:", execution.arn)

    # Start monitoring the pipeline execution
    monitor_pipeline(execution.arn)

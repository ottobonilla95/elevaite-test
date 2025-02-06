import json
import os
import sys
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

        # Build job arguments by looking up inputs from prior tasks.
        job_args = []
        for var in task.get("input", []):
            source_task = None
            for t in pipeline_def["tasks"]:
                if var in t.get("output", []):
                    source_task = t["id"]
                    break
            if source_task is None:
                raise ValueError(f"Input variable {var} is not produced by any task")
            job_args.extend([f"--{var}", f"{{{{ {source_task}.{var} }}}}"])

        if "entrypoint" in task:
            job_args.insert(0, task["entrypoint"])

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

    # Determine whether to persist the job name:
    #  - If the pipeline JSON explicitly provides "persist_job_name", use it.
    #  - Otherwise, use the provided persist_job_name_flag.
    persist_job_name = pipeline_def.get("persist_job_name")
    if persist_job_name is None:
        persist_job_name = persist_job_name_flag

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
            print(
                "Warning: Could not configure custom job prefixing. Falling back to default behavior. Error:",
                e,
            )

    pipeline = Pipeline(**pipeline_args)
    return pipeline


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


if __name__ == "__main__":
    if len(sys.argv) < 2 or len(sys.argv) > 3:
        print("Usage: python json2sagemaker.py <json_file> [persist_job_name]")
        sys.exit(1)

    json_file = sys.argv[1]
    if len(sys.argv) == 3:
        persist_flag_input = sys.argv[2].lower()
        if persist_flag_input in ["true", "1", "yes"]:
            user_persist_flag = True
        else:
            user_persist_flag = False
    else:
        user_persist_flag = False

    pipeline_def = load_pipeline_definition(json_file)
    pipeline = create_pipeline(pipeline_def, persist_job_name_flag=user_persist_flag)

    print("SageMaker Pipeline definition:")
    print(pipeline.definition())

    print("Upserting pipeline...")
    upsert_response = upsert_pipeline(pipeline)
    print("Upsert response:", upsert_response)

    print("Starting pipeline execution...")
    execution = start_pipeline(pipeline)
    print("Pipeline execution started. Execution ARN:", execution.arn)

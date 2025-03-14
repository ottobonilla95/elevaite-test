import json
import os
import sys
import subprocess
import time
import boto3
from botocore.config import Config
from sagemaker.session import Session
from sagemaker.workflow.pipeline import Pipeline
from sagemaker.workflow.steps import ProcessingStep

from common.cloudwatch import monitor_pipeline
from common.docker import (
    create_dockerfile,
    get_cached_processor,
    shutdown_processors,
)


REQUIRED_ENV_VARS = [
    "AWS_ACCESS_KEY_ID",
    "AWS_SECRET_ACCESS_KEY",
    "AWS_REGION",
    "AWS_ROLE_ARN",
    "ECR_BASE_REPO_URL",
]

_missing = [var for var in REQUIRED_ENV_VARS if var not in os.environ]
if _missing:
    raise EnvironmentError(f"Missing environment variables: {', '.join(_missing)}")

boto3.setup_default_session(region_name=os.environ["AWS_REGION"])


sagemaker_client = boto3.client(
    "sagemaker",
    config=Config(retries={"max_attempts": 5}, connect_timeout=240, read_timeout=240),
    region_name=os.environ["AWS_REGION"],
)

sagemaker_session = Session(
    boto_session=boto3.Session(region_name=os.environ["AWS_REGION"]),
    sagemaker_client=sagemaker_client,
)


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

    Reuses a persistent container. This means multiple pipeline steps
    may run in the same container.

    Args:
        pipeline_def: The dictionary containing the pipeline definition.
        container_image: The URI of the container image to use for processing.
                         If empty, the environment variable 'SAGEMAKER_CONTAINER_IMAGE'
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
        # Use a cached processor for the given command type
        processor = get_cached_processor(container_image, command, instance_type, role)

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

        # Truncate job_name after it got processed
        step.job_name = step.job_name[:63] if step.job_name else task_id

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

    return Pipeline(**pipeline_args, sagemaker_session=sagemaker_session)


def upsert_pipeline(pipeline: Pipeline) -> dict:
    """Upsert the given pipeline to SageMaker."""
    role = os.environ["AWS_ROLE_ARN"]

    print("Starting pipeline upsert...")
    start_time = time.time()

    try:
        response = pipeline.upsert(role_arn=role)
        print(f"Pipeline upsert completed in {time.time() - start_time:.2f} seconds")
        return response
    except Exception as e:
        print(f"Error during pipeline upsert: {e}")
        raise


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


def run_tasks_from_json(pipeline_def: dict, watch: bool = True):
    """Scans for dependencies, builds Docker images per task, and pushes them one by one."""

    if "tasks" not in pipeline_def or not pipeline_def["tasks"]:
        raise ValueError("Pipeline definition must contain at least one task.")

    # Get required environment variables
    aws_access_key = os.getenv("AWS_ACCESS_KEY_ID")
    aws_secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")
    aws_region = os.getenv("AWS_REGION")
    aws_role_arn = os.getenv("AWS_ROLE_ARN")
    ecr_base_repo = os.getenv("ECR_BASE_REPO_URL")

    if (
        not aws_access_key
        or not aws_secret_key
        or not aws_region
        or not aws_role_arn
        or not ecr_base_repo
    ):
        raise OSError("Missing required AWS environment variables.")

    ecr_base_repo = ecr_base_repo.rstrip("/")

    for idx, task in enumerate(pipeline_def["tasks"]):
        task_name = task.get("name", f"task_{idx}")
        dockerfile_path = f"/tmp/Dockerfile_{task_name}"
        image_name = f"{ecr_base_repo}:latest"

        print(f"\nProcessing Task: {task_name} | Creating Dockerfile...\n")

        # Dynamically create Dockerfile for this task
        create_dockerfile(task, dockerfile_path)

        try:
            registry = ecr_base_repo.split("/")[0]
            print(f"\nLogging in to ECR registry {registry}...")
            login_cmd = f"aws ecr get-login-password --region {aws_region} | docker login --username AWS --password-stdin {registry}"
            subprocess.run(login_cmd, shell=True, check=True)

            print(f"\nBuilding Docker image {image_name} from {dockerfile_path}...\n")

            process = subprocess.Popen(
                [
                    "docker",
                    "build",
                    "--progress=plain",
                    "-t",
                    image_name,
                    "-f",
                    dockerfile_path,
                    "--build-arg",
                    f"AWS_ACCESS_KEY_ID={aws_access_key}",
                    "--build-arg",
                    f"AWS_SECRET_ACCESS_KEY={aws_secret_key}",
                    "--build-arg",
                    f"AWS_REGION={aws_region}",
                    "--build-arg",
                    f"AWS_ROLE_ARN={aws_role_arn}",
                    ".",
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
            )

            assert process.stdout is not None

            for line in process.stdout:
                print(line, end="")

            process.wait()

            print(f"\nDocker build completed for {task_name}.\n")

            # Push the built Docker image to ECR.
            print(f"\nPushing Docker image {image_name} to ECR...\n")
            push_result = subprocess.run(
                ["docker", "push", image_name],
                check=True,
                capture_output=True,
                text=True,
            )
            print(f"Docker push output:\n{push_result.stdout}")

            # If errors occur, log them
            if push_result.stderr:
                print(f"Docker push errors:\n{push_result.stderr}")

            # Run the pipeline for this task using the pushed image
            print(f"\nCreating pipeline for task: {task_name}...\n")
            pipeline = create_pipeline(
                {"tasks": [task]},
                persist_job_name_flag=True,
                container_image=image_name,
                instance_type="ml.m5.xlarge",
            )

            upsert_response = upsert_pipeline(pipeline)
            print(f"Upsert response for {task_name}: {upsert_response}")

            execution = start_pipeline(pipeline)
            execution_arn = execution.arn
            print(f"Pipeline started for {task_name}. Execution ARN: {execution_arn}")

            if watch:
                monitor_pipeline(execution_arn)

        except subprocess.CalledProcessError as e:
            print(f"Error during Docker operations for task {task_name}: {e}")
            print(f"Output:\n{e.stdout}")
            print(f"Error:\n{e.stderr}")
            raise e

        finally:
            # Cleanup: remove Dockerfile
            if os.path.exists(dockerfile_path):
                os.remove(dockerfile_path)
                print(f"Deleted temporary Dockerfile: {dockerfile_path}")
            # remove_docker_image(image_name)
            shutdown_processors()

    print("\nAll tasks have been processed successfully!\n")


if __name__ == "__main__":
    if len(sys.argv) < 2 or len(sys.argv) > 3:
        print("Usage: python json2sagemaker.py <json_file> [persist_job_name]")
        sys.exit(1)

    json_file = sys.argv[1]
    persist_flag = (
        sys.argv[2].lower() in ["true", "1", "yes"] if len(sys.argv) == 3 else False
    )

    pipeline_def = load_pipeline_definition(json_file)
    run_tasks_from_json(pipeline_def)
    # pipeline = create_pipeline(pipeline_def, persist_job_name_flag=persist_flag)
    # upsert_response = upsert_pipeline(pipeline)

    # execution = start_pipeline(pipeline)
    # monitor_pipeline(execution.arn)

import json
import os
import sys
import subprocess
import boto3
from sagemaker.workflow.pipeline import Pipeline
from sagemaker.workflow.steps import ProcessingStep

from .common.cloudwatch import monitor_pipeline
from .common.docker import (
    create_dockerfile,
    get_cached_processor,
    remove_docker_image,
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


def run_pipeline_with_dynamic_dockerfile(pipeline_def: dict):
    dockerfile_path = "/tmp/Dockerfile"

    # Create the Dockerfile dynamically based on pipeline definition
    create_dockerfile(pipeline_def, dockerfile_path)

    # Get environment variables from the current environment
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
        raise OSError(
            "Missing environment variables: AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_REGION, AWS_ROLE_ARN, ECR_BASE_REPO_URL"
        )

    image_tag = "latest"
    ecr_base_repo = ecr_base_repo.rstrip("/")
    image_name = f"{ecr_base_repo}:{image_tag}"

    try:
        registry = ecr_base_repo.split("/")[0]
        print(f"Logging in to ECR registry {registry}...")
        login_cmd = f"aws ecr get-login-password --region {aws_region} | docker login --username AWS --password-stdin {registry}"
        subprocess.run(login_cmd, shell=True, check=True)

        print(f"Building Docker image {image_name} from {dockerfile_path}...")

        result = subprocess.run(
            [
                "docker",
                "build",
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
            check=True,
            capture_output=True,
            text=True,
        )

        print(f"Docker build output:\n{result.stdout}")
        print(f"Docker build errors:\n{result.stderr}")

        # Push the built Docker image to ECR.
        print(f"Pushing Docker image {image_name} to ECR...")
        push_result = subprocess.run(
            ["docker", "push", image_name],
            check=True,
            capture_output=True,
            text=True,
        )
        print(f"Docker push output:\n{push_result.stdout}")
        print(f"Docker push errors:\n{push_result.stderr}")

        # Use the pushed image in the SageMaker pipeline.
        pipeline = create_pipeline(
            pipeline_def,
            persist_job_name_flag=True,
            container_image=image_name,
            instance_type="ml.m5.xlarge",
        )

        upsert_response = upsert_pipeline(pipeline)
        print("Upsert response:", upsert_response)

        execution = start_pipeline(pipeline)
        execution_arn = execution.arn
        print(f"Pipeline started. Execution ARN: {execution_arn}")

        monitor_pipeline(execution_arn)

    except subprocess.CalledProcessError as e:
        print(f"Error during Docker operations: {e}")
        print(f"Output:\n{e.stdout}")
        print(f"Error:\n{e.stderr}")
        raise e

    finally:
        # Remove the temporary Dockerfile and the local Docker image.
        if os.path.exists(dockerfile_path):
            os.remove(dockerfile_path)
            print(f"Deleted the Dockerfile at {dockerfile_path}")
        remove_docker_image(image_name)
        shutdown_processors()


if __name__ == "__main__":
    if len(sys.argv) < 2 or len(sys.argv) > 3:
        print("Usage: python json2sagemaker.py <json_file> [persist_job_name]")
        sys.exit(1)

    json_file = sys.argv[1]
    persist_flag = (
        sys.argv[2].lower() in ["true", "1", "yes"] if len(sys.argv) == 3 else False
    )

    pipeline_def = load_pipeline_definition(json_file)
    run_pipeline_with_dynamic_dockerfile(pipeline_def)
    # pipeline = create_pipeline(pipeline_def, persist_job_name_flag=persist_flag)
    # upsert_response = upsert_pipeline(pipeline)

    # execution = start_pipeline(pipeline)
    # monitor_pipeline(execution.arn)

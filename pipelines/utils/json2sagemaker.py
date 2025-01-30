import json
import os
import sys
import boto3
import sagemaker
from typing import Dict, Any
from dotenv import load_dotenv
from sagemaker.processing import ScriptProcessor, ProcessingInput, ProcessingOutput
from sagemaker.workflow.pipeline import Pipeline
from sagemaker.workflow.parameters import ParameterString
from sagemaker.workflow.steps import ProcessingStep


def load_json(file_path: str) -> Dict[str, Any]:
    with open(file_path, "r") as f:
        return json.load(f)


def verify_aws_configuration():
    try:
        sts = boto3.client("sts")
        identity = sts.get_caller_identity()
        print("\nAWS Configuration Verified:")
        print(f"  Account ID: {identity['Account']}")
        print(f"  ARN: {identity['Arn']}")
        print(f"  Region: {boto3.Session().region_name}")
    except Exception as e:
        print("\nAWS Configuration Error!")
        raise ValueError(
            "Invalid AWS configuration - check credentials and region"
        ) from e


def create_sagemaker_pipeline(pipeline_config: Dict[str, Any]) -> Pipeline:
    boto_session = boto3.Session(
        region_name=pipeline_config.get("region"),
        profile_name=pipeline_config.get("aws_profile"),
        aws_access_key_id=os.environ["AWS_ACCESS_KEY_ID"],
        aws_secret_access_key=os.environ["AWS_SECRET_ACCESS_KEY"],
        # aws_session_token=os.environ["AWS_SESSION_TOKEN"],
    )

    region = boto_session.region_name or "us-west-2"
    if not boto_session.region_name:
        boto_session = boto3.Session(region_name=region)

    sagemaker_session = sagemaker.Session(
        boto_session=boto_session, default_bucket=pipeline_config.get("s3_bucket")
    )
    role = pipeline_config.get("role_arn")

    if not role:
        raise ValueError(
            "Missing execution role - provide 'role_arn' in pipeline config"
        )

    print("\nPipeline Configuration:")
    print(f"  Region: {region}")
    print(f"  SageMaker Bucket: {sagemaker_session.default_bucket()}")
    print(f"  Execution Role: {role}")

    variables = pipeline_config["variables"]
    tasks = pipeline_config["tasks"]
    parameter_dict = {
        var["name"]: ParameterString(name=var["name"]) for var in variables
    }

    steps = []
    task_results = {}

    for task in tasks:
        processor = ScriptProcessor(
            image_uri=task.get("image_uri", "python:3.8"),
            command=["python3"],
            role=role,
            instance_type=task.get("instance_type", "ml.m5.xlarge"),
            instance_count=task.get("instance_count", 1),
            sagemaker_session=sagemaker_session,
            base_job_name=f"{pipeline_config['name']}-{task['id']}",
        )

        # Input handling
        inputs = [
            ProcessingInput(
                source=parameter_dict.get(var) or task_results.get(var),
                destination=f"/opt/ml/processing/input/{var}",
            )
            for var in task.get("input", [])
        ]

        # Output handling
        outputs = [
            ProcessingOutput(
                output_name=output_var,
                source=f"/opt/ml/processing/output/{output_var}",
                destination=task.get("output_s3_uri", None),
            )
            for output_var in task.get("output", [])
        ]

        step = ProcessingStep(
            name=task["name"],
            processor=processor,
            inputs=inputs,
            outputs=outputs,
        )

        steps.append(step)
        task_results[task["id"]] = task.get("output", [])

    return Pipeline(
        name=pipeline_config["name"],
        parameters=list(parameter_dict.values()),
        steps=steps,
        sagemaker_session=sagemaker_session,
    )


if __name__ == "__main__":
    load_dotenv()
    # verify_aws_configuration()

    if len(sys.argv) != 2:
        print("Usage: python json2sagemaker.py <json_file>")
        sys.exit(1)

    try:
        config = load_json(sys.argv[1])
        pipeline = create_sagemaker_pipeline(config)
        print(f"\nSuccessfully created pipeline: {pipeline.name}")
        print(f"Pipeline ARN: {pipeline._get_latest_execution_arn()}")
    except Exception as e:
        print(f"\nPipeline creation failed: {str(e)}")
        sys.exit(1)

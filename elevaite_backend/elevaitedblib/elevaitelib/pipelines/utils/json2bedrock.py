import os
import sys
import json
import boto3
from datetime import datetime
from typing import Dict, Any, Union

from elevaitelib.pipelines.utils.common.cloudwatch import monitor_pipeline

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
stepfunctions = boto3.client("stepfunctions")


def load_pipeline_definition(json_file: str) -> dict:
    with open(json_file, "r") as f:
        return json.load(f)


def convert_to_step_functions(pipeline_def):
    states = {}
    start_state = None

    for task in pipeline_def["tasks"]:
        task_id = task["id"]
        output_var = task["output"][0] if task["output"] else None
        dependencies = task.get("dependencies", [])

        if task["task_type"] == "pyscript":
            task_resource = f"arn:aws:lambda:{os.environ['AWS_REGION']}:123456789012:function:{task_id}"
            parameters = {"FunctionName": task_id, "Payload.$": "$"}
        elif task["task_type"] == "jupyternotebook":
            task_resource = "arn:aws:states:::bedrock:invokeModel"
            parameters = {"ModelId": "amazon.titan-text-express-v1", "Input.$": "$"}
        else:
            raise ValueError(f"Unsupported task type: {task['task_type']}")

        state = {
            "Type": "Task",
            "Resource": task_resource,
            "Parameters": parameters,
            "ResultPath": f"$.{output_var}" if output_var else None,
        }

        next_tasks = [
            t["id"]
            for t in pipeline_def["tasks"]
            if task_id in t.get("dependencies", [])
        ]
        if next_tasks:
            state["Next"] = next_tasks[0]
        else:
            state["End"] = True

        states[task_id] = state

        if not dependencies:
            start_state = task_id

    return {
        "Comment": f"Step Functions pipeline for {pipeline_def['name']}",
        "StartAt": start_state,
        "States": states,
    }


def serialize_with_datetime_conversion(data):
    if isinstance(data, dict):
        return {
            key: serialize_with_datetime_conversion(value)
            for key, value in data.items()
        }
    elif isinstance(data, list):
        return [serialize_with_datetime_conversion(item) for item in data]
    elif isinstance(data, datetime):
        return data.isoformat()
    else:
        return data


def deploy_pipeline(pipeline_def):
    role_arn = os.environ["AWS_ROLE_ARN"]
    state_machine_definition = convert_to_step_functions(pipeline_def)

    state_machine_definition_json = json.dumps(
        serialize_with_datetime_conversion(state_machine_definition), indent=2
    )

    try:
        response = stepfunctions.create_state_machine(
            name=pipeline_def["name"],
            definition=state_machine_definition_json,
            roleArn=role_arn,
        )
        return response["stateMachineArn"]
    except Exception as e:
        print(f"Error deploying pipeline: {str(e)}")
        sys.exit(1)


def start_pipeline(state_machine_arn):
    try:
        response = stepfunctions.start_execution(stateMachineArn=state_machine_arn)
        return response["executionArn"]
    except Exception as e:
        print(f"Error starting pipeline execution: {str(e)}")
        sys.exit(1)


def run_pipeline(pipeline_def, watch: bool = True):
    state_machine_arn = deploy_pipeline(pipeline_def)
    print(f"\n✅ Pipeline deployed: {state_machine_arn}")

    execution_arn = start_pipeline(state_machine_arn)
    print(f"\n🚀 Pipeline started. Execution ARN: {execution_arn}")

    if watch:
        summary: Union[str, Dict[str, Any]] = monitor_pipeline(
            execution_arn, summarize=True
        )

        if isinstance(summary, dict):
            if summary.get("final_status") != "Succeeded":
                print(
                    f"\nPipeline execution failed with status: {summary.get('final_status')}"
                )
                print("Step details:")

                for step_info in summary.get("steps", []):
                    print(f"Step: {step_info.get('step_name')}")
                    print(f"  Status: {step_info.get('status')}")
                    if "failure_reason" in step_info:
                        print(f"  Failure Reason: {step_info.get('failure_reason')}")
                    if "logs" in step_info:
                        print(f"  Logs: {step_info.get('logs')}")
            else:
                print("\n✅ Pipeline execution succeeded.")
        else:
            print(f"\nPipeline execution status: {summary}")

    return execution_arn


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python json2bedrock.py <json_file>")
        sys.exit(1)

    json_file = sys.argv[1]
    pipeline_def = load_pipeline_definition(json_file)

    run_pipeline(pipeline_def, watch=True)

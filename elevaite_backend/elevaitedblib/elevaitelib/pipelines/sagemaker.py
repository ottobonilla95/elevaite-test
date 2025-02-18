import boto3
from pipelines.utils import json2sagemaker


def create_sagemaker_pipelines(
    request_count: int,
    json_files: list[str],
    persist_job_name: bool = False,
) -> list[dict]:
    results = []
    if request_count != len(json_files):
        raise ValueError(
            "The number of json_files provided does not match the request_count."
        )

    for json_file in json_files:
        try:
            pipeline_def = json2sagemaker.load_pipeline_definition(json_file)
            pipeline = json2sagemaker.create_pipeline(
                pipeline_def, persist_job_name_flag=persist_job_name
            )
            upsert_response = json2sagemaker.upsert_pipeline(pipeline)
            execution = json2sagemaker.start_pipeline(pipeline)
            results.append(
                {
                    "json_file": json_file,
                    "pipeline_execution_arn": execution.arn,
                    "upsert_response": upsert_response,
                }
            )
        except Exception as e:
            results.append(
                {
                    "json_file": json_file,
                    "error": str(e),
                }
            )
    return results


def get_sagemaker_pipeline_status(execution_arn: str) -> dict:
    client = boto3.client("sagemaker")
    return client.describe_pipeline_execution(PipelineExecutionArn=execution_arn)


def update_sagemaker_pipeline(
    json_file: str,
    persist_job_name: bool = False,
) -> dict:
    pipeline_def = json2sagemaker.load_pipeline_definition(json_file)
    pipeline = json2sagemaker.create_pipeline(
        pipeline_def, persist_job_name_flag=persist_job_name
    )
    upsert_response = json2sagemaker.upsert_pipeline(pipeline)
    execution = json2sagemaker.start_pipeline(pipeline)
    return {
        "json_file": json_file,
        "pipeline_execution_arn": execution.arn,
        "upsert_response": upsert_response,
    }


def delete_sagemaker_pipeline() -> dict:
    json2sagemaker.shutdown_processors()
    return {"message": "Cached processors have been shut down."}

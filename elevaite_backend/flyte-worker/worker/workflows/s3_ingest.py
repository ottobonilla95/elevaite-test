"Prebuilt workflow, ingesting data from an S3 Bucket"

from typing import Any, Dict
from flytekit import task, workflow
import lakefs
import boto3
from pydantic import BaseModel

from elevaite_client.util.s3url import S3Url
from elevaite_client.rpc.client import RPCClient
from elevaite_client.rpc.interfaces import (
    CreateDatasetVersionInput,
    LogInfo,
    RepoNameInput,
    SetInstanceChartDataInput,
    SetRedisValueInput,
    MaxDatasetVersionInput,
)
from elevaite_client.connectors import lakefs
from elevaite_client.util import func as util_func
from ..util.func import get_secrets, get_secrets_dict, path_leaf


class S3IngestData(BaseModel):
    type: str = "s3_ingest"
    projectId: str
    datasetId: str
    instanceId: str
    url: str
    useEC2: bool
    roleARN: str


@task(enable_deck=True, environment=get_secrets_dict())
def s3_ingest(_data: Dict[str, str | int | bool | Any]):
    data = S3IngestData.parse_obj(_data)
    secrets = get_secrets()
    LAKEFS_ACCESS_KEY_ID = secrets.LAKEFS_ACCESS_KEY_ID
    LAKEFS_SECRET_ACCESS_KEY = secrets.LAKEFS_SECRET_ACCESS_KEY
    LAKEFS_ENDPOINT_URL = secrets.LAKEFS_ENDPOINT_URL
    LAKEFS_STORAGE_NAMESPACE = secrets.LAKEFS_STORAGE_NAMESPACE
    S3_ACCESS_KEY_ID = secrets.S3_ACCESS_KEY_ID
    S3_SECRET_ACCESS_KEY = secrets.S3_SECRET_ACCESS_KEY

    rpc_client = RPCClient()

    if data.datasetId is None:
        raise Exception("No datasetId recieved")

    repo_name = rpc_client.get_repo_name(
        RepoNameInput(dataset_id=data.datasetId, project_id=data.projectId)
    )

    repo = lakefs.get_or_create_lakefs_repo(
        repo_name=repo_name,
        options={
            "key_id": LAKEFS_ACCESS_KEY_ID,
            "secret_key": LAKEFS_SECRET_ACCESS_KEY,
            "endpoint": LAKEFS_ENDPOINT_URL,
            "namespace": LAKEFS_STORAGE_NAMESPACE,
        },
    )
    rpc_client.log_info(LogInfo(msg="Initialized lake repository", key=data.instanceId))

    lakefs_branch = repo.branch("main")

    lakefs_s3 = boto3.client(
        "s3",
        aws_access_key_id=LAKEFS_ACCESS_KEY_ID,
        aws_secret_access_key=LAKEFS_SECRET_ACCESS_KEY,
        endpoint_url=LAKEFS_ENDPOINT_URL,
    )

    s3url = S3Url(data.url)

    src_bucket = (
        boto3.Session(
            aws_access_key_id=S3_ACCESS_KEY_ID,
            aws_secret_access_key=S3_SECRET_ACCESS_KEY,
        )
        .resource("s3")
        .Bucket(s3url.bucket)  # type: ignore
    )
    rpc_client.log_info(LogInfo(msg="Starting file ingestion", key=data.instanceId))
    for summary in src_bucket.objects.filter(Prefix=s3url.key):
        if not summary.key.endswith("/"):
            rpc_client.set_redis_value(
                input=SetRedisValueInput(
                    name=data.instanceId,
                    path=".currentFile",
                    obj=path_leaf(summary.key),
                )
            )
            s3_object = src_bucket.Object(summary.key).get()
            stream = s3_object["Body"]
            lakefs_s3.upload_fileobj(
                Fileobj=stream, Bucket=repo_name, Key=f"main/{summary.key}"
            )
        rpc_client.set_redis_value(
            input=SetRedisValueInput(
                name=data.instanceId, path=".ingested_size", obj=summary.size
            )
        )
        rpc_client.set_redis_value(
            input=SetRedisValueInput(
                name=data.instanceId, path=".ingested_items", obj=1
            )
        )

    rpc_client.set_instance_chart_data(
        input=SetInstanceChartDataInput(instance_id=data.instanceId)
    )

    rpc_client.log_info(LogInfo(msg="Completed file ingestion", key=data.instanceId))
    print(lakefs_branch.uncommitted())
    __commit_flag__ = False

    for diff in lakefs_branch.uncommitted():
        rpc_client.hello({"test": diff.size_bytes})
        if diff is not None:
            __commit_flag__ = True
            break
        else:
            break
    curr_version = rpc_client.get_max_version_of_dataset(
        input=MaxDatasetVersionInput(dataset_id=data.datasetId)
    )

    if __commit_flag__:
        rpc_client.log_info(
            LogInfo(
                msg="Changes found, commiting to repository and creating new version",
                key=data.instanceId,
            )
        )
        ref = lakefs_branch.commit(
            data.instanceId,
            {
                "instanceId": data.instanceId,
                "timestamp": util_func.get_iso_datetime(),
            },
        )
        curr_version += 1
        rpc_client.create_dataset_version(
            input=CreateDatasetVersionInput(
                dataset_id=data.datasetId, ref_id=ref.id, version=curr_version
            )
        )
    else:
        rpc_client.log_info(
            LogInfo(
                msg="Dataset is identical, will not commit",
                key=data.instanceId,
            )
        )
        print("Dataset is identical")

    rpc_client.log_info(
        LogInfo(msg="Worker completed ingest pipeline", key=data.instanceId)
    )


@workflow()
def s3_ingest_poc_workflow(data: Dict[str, str | int | bool | Any]):
    s3_ingest(_data=data)

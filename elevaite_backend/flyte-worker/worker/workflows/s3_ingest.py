"Example workflow, ingesting data from an S3 Bucket"

import json
from elevaitelib.util.logger import ESLogger
from elevaitelib.util.s3url import S3Url
import flytekit
from flytekit import task, workflow, ImageSpec
from flytekit.configuration import Config
from flytekit.remote import FlyteRemote
from typing import Any, Dict, Optional
from lakefs import Branch, Client
import lakefs
import boto3
from pydantic import BaseModel

from elevaite_client.rpc.client import RPCClient
from elevaite_client.rpc.interfaces import (
    CreateDatasetVersionInput,
    LogInfo,
    PipelineStepStatusInput,
    RepoNameInput,
    SetInstanceChartDataInput,
    SetRedisValueInput,
    MaxDatasetVersionInput,
)
from elevaitelib.util import func as util_func
from ..util.func import path_leaf

# elevaite_image_spev = ImageSpec()


class ResourceRegistry(BaseModel):
    lakefs_repo_name: str
    lakefs_branch: Branch
    lakefs_s3_client: Any
    s3url: S3Url
    source_bucket: Any

    class Config:
        arbitrary_types_allowed = True


class S3IngestData(BaseModel):
    type: str = "s3_ingest"
    projectId: str
    applicationId: int
    datasetId: str
    instanceId: str
    url: str
    useEC2: bool
    roleARN: str


class Secrets(BaseModel):
    LAKEFS_ACCESS_KEY_ID: str
    LAKEFS_SECRET_ACCESS_KEY: str
    LAKEFS_ENDPOINT_URL: str
    LAKEFS_STORAGE_NAMESPACE: str
    S3_ACCESS_KEY_ID: str
    S3_SECRET_ACCESS_KEY: str
    ELASTIC_PASSWORD: str
    ELASTIC_SSL_FINGERPRINT: str
    ELASTIC_HOST: str


@task(enable_deck=True)
def initialize_resources(
    _data: Dict[str, str | int | bool], _secrets: Dict[str, str]
) -> ResourceRegistry:
    data = S3IngestData.parse_obj(_data)
    secrets = Secrets.parse_obj(_secrets)
    LAKEFS_ACCESS_KEY_ID = secrets.LAKEFS_ACCESS_KEY_ID
    LAKEFS_SECRET_ACCESS_KEY = secrets.LAKEFS_SECRET_ACCESS_KEY
    LAKEFS_ENDPOINT_URL = secrets.LAKEFS_ENDPOINT_URL
    LAKEFS_STORAGE_NAMESPACE = secrets.LAKEFS_STORAGE_NAMESPACE
    S3_ACCESS_KEY_ID = secrets.S3_ACCESS_KEY_ID
    S3_SECRET_ACCESS_KEY = secrets.S3_SECRET_ACCESS_KEY

    rpc_client = RPCClient()

    clt = Client(
        host=LAKEFS_ENDPOINT_URL,
        username=LAKEFS_ACCESS_KEY_ID,
        password=LAKEFS_SECRET_ACCESS_KEY,
    )

    if data.datasetId is None:
        raise Exception("No datasetId recieved")
    repo = None

    repo_name = rpc_client.get_repo_name(
        RepoNameInput(dataset_id=data.datasetId, project_id=data.projectId)
    )
    for _repo in lakefs.repositories(client=clt):
        if _repo.id == repo_name:
            repo = _repo
            break
    if repo is None:
        repo = lakefs.Repository(repo_name, client=clt).create(
            storage_namespace=f"s3://{LAKEFS_STORAGE_NAMESPACE}/{repo_name}"
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
        .Bucket(s3url.bucket)
    )

    res = ResourceRegistry(
        lakefs_repo_name=repo_name,
        lakefs_branch=lakefs_branch,
        lakefs_s3_client=lakefs_s3,
        source_bucket=src_bucket,
        s3url=s3url,
    )

    flytekit.current_context().task_id
    return res


@task(enable_deck=True)
def s3_worker(
    _data: Dict[str, str | int | bool], registry: ResourceRegistry
) -> ResourceRegistry:
    data = S3IngestData.parse_obj(_data)
    rpc_client = RPCClient()

    # rpc_client.set_pipeline_step_running(
    #     input = PipelineStepStatusInput(instance_id=data.instanceId, step_id=data.step_id)
    # )

    # _instance_resources = RESOURCE_REGISTRY[self.data.instanceId]

    rpc_client.log_info(LogInfo(msg="Starting file ingestion", key=data.instanceId))

    # branch = repo.branch("main")

    src_bucket = registry.source_bucket
    if src_bucket is None:
        raise Exception("Source Bucket has not been initialized.")

    s3url = registry.s3url
    if s3url is None:
        raise Exception("S3 URL object has not been initialized.")

    lakefs_s3 = registry.lakefs_s3_client
    if lakefs_s3 is None:
        raise Exception("LakeFS S3 client has not been initialized.")

    repo_name = registry.lakefs_repo_name
    if repo_name is None:
        raise Exception("LakeFS Repository Name has not been initialized.")

    for summary in src_bucket.objects.filter(Prefix=s3url.key):
        # print(f"Copying {summary.key} with size {summary.size}...")
        # pprint(summary)
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

    # rpc_client.set_pipeline_step_completed(
    #     PipelineStepStatusInput(instance_id=data.instanceId, step_id="")
    # )

    return registry


@task(enable_deck=True)
def commit_dif(_data: Dict[str, str | int | bool], registry: ResourceRegistry):
    data = S3IngestData.parse_obj(_data)
    rpc_client = RPCClient()
    for diff in registry.lakefs_branch.uncommitted():
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
        ref = registry.lakefs_branch.commit(
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

    # set_pipeline_step_meta(
    #     db=db,
    #     instance_id=data.instanceId,
    #     step_id=str(_final_step.id),
    #     meta=[
    #         InstancePipelineStepData(
    #             label=InstanceStepDataLabel.REPO_NAME, value=repo_name
    #         ),
    #         InstancePipelineStepData(
    #             label=InstanceStepDataLabel.DATASET_VERSION, value=curr_version
    #         ),
    #     ],
    # )
    rpc_client.log_info(
        LogInfo(msg="Worker completed ingest pipeline", key=data.instanceId)
    )


@workflow()
def s3_ingest_workflow(input: Dict[str, str | int | bool], secrets: Dict[str, str]):
    resources = initialize_resources(_data=input, _secrets=secrets)
    res2 = s3_worker(_data=input, registry=resources)
    res3 = commit_dif(_data=input, registry=res2)


def s3_ingest_callback(ch, method, properties, body):
    _data_raw = json.loads(body)
    _data = S3IngestData.parse_obj(_data_raw)
    print(f" [x] Received {_data.json()}")

    remote = FlyteRemote(
        config=Config.auto(),
        default_project="flytesnacks",
        default_domain="development",
    )

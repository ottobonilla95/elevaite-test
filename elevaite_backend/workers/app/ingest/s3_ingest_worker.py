import json
import os
import threading
from dotenv import load_dotenv
from elasticsearch import Elasticsearch
import boto3
import lakefs
from lakefs_sdk.exceptions import BadRequestException

from botocore.client import BaseClient
from botocore.client import Config as ClientConfig
from botocore.credentials import RefreshableCredentials
from botocore.session import get_session
import redis

from elevaitedb.db.database import SessionLocal
from elevaitedb.crud import (
    instance as instance_crud,
    pipeline as pipeline_crud,
    dataset as dataset_crud,
)
from elevaitedb.util import func as util_func
from elevaitedb.util.s3url import S3Url
from elevaitedb.util.logger import ESLogger
from elevaitedb.schemas.instance import (
    InstancePipelineStepData,
    InstanceStatus,
    InstanceUpdate,
    InstanceStepDataLabel,
)
from elevaitedb.schemas.dataset import DatasetVersionCreate

from .steps.base_step import get_initialized_step, register_resource_registry

from ..interfaces import S3IngestData, ServiceNowIngestData
from ..util.func import (
    path_leaf,
    set_instance_chart_data,
    set_instance_running,
    set_pipeline_step_completed,
    set_pipeline_step_meta,
    set_redis_stats,
    set_pipeline_step_running,
    set_instance_completed,
    get_repo_name,
)


def s3_ingest_callback(ch, method, properties, body):
    _data = json.loads(body)

    print(f" [x] Received {_data}")

    if _data["dto"]["type"] == "ingest":
        _formData = S3IngestData(
            **_data["dto"],
            instanceId=_data["id"],
            applicationId=_data["application_id"],
        )
    elif _data["dto"]["type"] == "service-now":
        _formData = ServiceNowIngestData(
            **_data["dto"],
            instanceId=_data["id"],
            applicationId=_data["application_id"],
        )
    t = threading.Thread(target=s3_lakefs_cp_stream, args=(_formData,))
    t.start()


def s3_lakefs_cp_stream(data: S3IngestData | ServiceNowIngestData) -> None:
    load_dotenv()
    db = SessionLocal()
    AWS_EXTERNAL_ID = os.getenv("AWS_ASSUME_ROLE_EXTERNAL_ID")

    # I haven't gotten this to work, we need to test it on a staging environment
    def _get_iam_s3_client(role_arn: str, endpoint: str | None) -> BaseClient:
        def refresh():
            client = boto3.client(
                "sts",
                aws_access_key_id=S3_ACCESS_KEY_ID,
                aws_secret_access_key=S3_SECRET_ACCESS_KEY,
            )
            if AWS_EXTERNAL_ID:
                role = client.assume_role(
                    RoleArn=role_arn,
                    RoleSessionName="airbyte-source-s3",
                    ExternalId=AWS_EXTERNAL_ID,
                )
            else:
                role = client.assume_role(
                    RoleArn=role_arn,
                    RoleSessionName="airbyte-source-s3",
                )

            creds = role.get("Credentials", {})
            return {
                "access_key": creds["AccessKeyId"],
                "secret_key": creds["SecretAccessKey"],
                "token": creds["SessionToken"],
                "expiry_time": creds["Expiration"].isoformat(),
            }

        session_credentials = RefreshableCredentials.create_from_metadata(
            metadata=refresh(),
            refresh_using=refresh,
            method="sts-assume-role",
        )

        session = get_session()
        session._credentials = session_credentials
        autorefresh_session = boto3.Session(botocore_session=session)

        client_kv_args = (
            {
                "config": ClientConfig(s3={"addressing_style": "auto"}),
                "endpoint_url": endpoint,
                "use_ssl": True,
                "verify": True,
            }
            if endpoint
            else {}
        )

        return autorefresh_session.client("s3", **client_kv_args)  # type: ignore | This is straight from documentation

    LAKEFS_ACCESS_KEY_ID = os.getenv("LAKEFS_ACCESS_KEY_ID")
    if LAKEFS_ACCESS_KEY_ID is None:
        raise Exception("LAKEFS_ACCESS_KEY_ID is null")
    LAKEFS_SECRET_ACCESS_KEY = os.getenv("LAKEFS_SECRET_ACCESS_KEY")
    if LAKEFS_SECRET_ACCESS_KEY is None:
        raise Exception("LAKEFS_SECRET_ACCESS_KEY is null")
    LAKEFS_ENDPOINT_URL = os.getenv("LAKEFS_ENDPOINT_URL")
    if LAKEFS_ENDPOINT_URL is None:
        raise Exception("LAKEFS_ENDPOINT_URL is null")
    S3_ACCESS_KEY_ID = os.getenv("S3_ACCESS_KEY_ID")
    if S3_ACCESS_KEY_ID is None:
        raise Exception("S3_ACCESS_KEY_ID is null")
    S3_SECRET_ACCESS_KEY = os.getenv("S3_SECRET_ACCESS_KEY")
    if S3_SECRET_ACCESS_KEY is None:
        raise Exception("S3_SECRET_ACCESS_KEY is null")
    REDIS_HOST = os.getenv("REDIS_HOST")
    if REDIS_HOST is None:
        raise Exception("REDIS_HOST is null")
    _REDIS_PORT = os.getenv("REDIS_PORT")
    if _REDIS_PORT is None:
        raise Exception("REDIS_PORT is null")
    try:
        REDIS_PORT = int(_REDIS_PORT)
    except ValueError:
        print("REDIS_PORT must be an integer")
    REDIS_USERNAME = os.getenv("REDIS_USERNAME")
    if REDIS_USERNAME is None:
        raise Exception("REDIS_USERNAME is null")
    REDIS_PASSWORD = os.getenv("REDIS_PASSWORD")
    if REDIS_PASSWORD is None:
        raise Exception("REDIS_PASSWORD is null")
    ELASTIC_PASSWORD = os.getenv("ELASTIC_PASSWORD")
    if ELASTIC_PASSWORD is None:
        raise Exception("ELASTIC_PASSWORD is null")
    ELASTIC_SSL_FINGERPRINT = os.getenv("ELASTIC_SSL_FINGERPRINT")
    if ELASTIC_SSL_FINGERPRINT is None:
        raise Exception("ELASTIC_SSL_FINGERPRINT is null")
    ELASTIC_HOST = os.getenv("ELASTIC_HOST")
    if ELASTIC_HOST is None:
        raise Exception("ELASTIC_HOST is null")

    logger = ESLogger(key=data.instanceId)
    logger.info(message="Initialized worker")

    try:
        _intance_registry = register_resource_registry(data.instanceId)
        set_instance_running(
            db=db, application_id=data.applicationId, instance_id=data.instanceId
        )

        r = redis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            decode_responses=True,
            username=REDIS_USERNAME,
            password=REDIS_PASSWORD,
        )

        _pipeline = pipeline_crud.get_pipeline_by_id(db, data.selectedPipelineId)
        _entry_step = None
        _first_step = None
        _final_step = None

        for s in _pipeline.steps:
            if s.id == _pipeline.entry:
                _entry_step = s
                break

        if _entry_step is None:
            raise Exception("Pipeline Entry step not found in steps")

        for s in _pipeline.steps:
            if _entry_step.id in s.previousStepIds:  # type: ignore | I mean... it works?
                _first_step = s
                break

        if _first_step is None:
            raise Exception("Pipeline first step not found in steps")

        for s in _pipeline.steps:
            if s.id == _pipeline.exit:
                _final_step = s
                break

        if _final_step is None:
            raise Exception("Pipeline Exit step not found in steps")
        if data.datasetId is None:
            raise Exception("No datasetId recieved")

        _entry_step_runner = get_initialized_step(
            step_id=_entry_step.id,
            data=data,
            db=db,
            logger=logger,
            r=r,
        )
        _entry_step_runner.run()

        _first_step_runner = get_initialized_step(
            step_id=_first_step.id,
            data=data,
            db=db,
            logger=logger,
            r=r,
        )
        _first_step_runner.run()

        set_pipeline_step_running(
            db=db, instance_id=data.instanceId, step_id=str(_final_step.id)
        )

        __commit_flag__ = False
        lakefs_branch = _intance_registry.lakefs_branch
        if lakefs_branch is None:
            raise Exception("LakeFS Branch Object has not been initialized")

        repo_name = _intance_registry.lakefs_repo_name
        if repo_name is None:
            raise Exception("LakeFS Repository Name has not been initialized.")

        for diff in lakefs_branch.uncommitted():
            if diff is not None:
                __commit_flag__ = True
                break
            else:
                break
        curr_version = dataset_crud.get_max_version_of_dataset(
            db=db, datasetId=data.datasetId
        )

        if __commit_flag__:
            logger.info(
                message="Changes found, commiting to repository and creating new version"
            )
            ref = lakefs_branch.commit(
                data.instanceId,
                {
                    "instanceId": data.instanceId,
                    "timestamp": util_func.get_iso_datetime(),
                },
            )
            curr_version += 1
            dataset_crud.create_dataset_version(
                db,
                data.datasetId,
                DatasetVersionCreate(commitId=ref.id, version=curr_version),
            )
        else:
            logger.info(message="Dataset is identical, will not commit")
            print("Dataset is identical")

        set_instance_completed(
            db=db, application_id=data.applicationId, instance_id=data.instanceId
        )

        set_pipeline_step_meta(
            db=db,
            instance_id=data.instanceId,
            step_id=str(_final_step.id),
            meta=[
                InstancePipelineStepData(
                    label=InstanceStepDataLabel.REPO_NAME, value=repo_name
                ),
                InstancePipelineStepData(
                    label=InstanceStepDataLabel.DATASET_VERSION, value=curr_version
                ),
            ],
        )

        set_pipeline_step_completed(
            db=db, instance_id=data.instanceId, step_id=str(_final_step.id)
        )

    except BadRequestException as e:
        print("Dataset is identical")
    except Exception as e:
        print("Error")
        print(e)
        logger.error(message="Error encountered, aborting ingestion")
        logger.error(message=str(e))
        print(e.with_traceback(None))
        instance_crud.update_instance(
            db,
            data.applicationId,
            data.instanceId,
            InstanceUpdate(
                status=InstanceStatus.FAILED,
                endTime=util_func.get_iso_datetime(),
                comment=str(e),
            ),
        )
    else:
        print("Done importing data")

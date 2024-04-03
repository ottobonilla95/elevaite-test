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
    InstanceStatus,
    InstanceUpdate,
    InstanceStepDataLabel,
)
from elevaitedb.schemas.dataset import DatasetVersionCreate

from ..interfaces import S3IngestData
from ..util.func import (
    set_instance_chart_data,
    set_instance_running,
    set_pipeline_step_completed,
    set_redis_stats,
    set_pipeline_step_running,
    set_instance_completed,
    get_repo_name,
)


def s3_ingest_callback(ch, method, properties, body):
    _data = json.loads(body)

    print(f" [x] Received {_data}")

    _formData = S3IngestData(
        **_data["dto"],
        instanceId=_data["id"],
        applicationId=_data["application_id"],
        configurationName=_data["configurationName"],
    )
    t = threading.Thread(target=s3_lakefs_cp_stream, args=(_formData,))
    t.start()


def s3_lakefs_cp_stream(data: S3IngestData) -> None:
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

        return autorefresh_session.client("s3", **client_kv_args)

    LAKEFS_ACCESS_KEY_ID = os.getenv("LAKEFS_ACCESS_KEY_ID")
    LAKEFS_SECRET_ACCESS_KEY = os.getenv("LAKEFS_SECRET_ACCESS_KEY")
    LAKEFS_ENDPOINT_URL = os.getenv("LAKEFS_ENDPOINT_URL")
    LAKEFS_STORAGE_NAMESPACE = os.getenv("LAKEFS_STORAGE_NAMESPACE")
    S3_ACCESS_KEY_ID = os.getenv("S3_ACCESS_KEY_ID")
    S3_SECRET_ACCESS_KEY = os.getenv("S3_SECRET_ACCESS_KEY")
    REDIS_HOST = os.getenv("REDIS_HOST")
    REDIS_PORT = os.getenv("REDIS_PORT")
    REDIS_USERNAME = os.getenv("REDIS_USERNAME")
    REDIS_PASSWORD = os.getenv("REDIS_PASSWORD")
    ELASTIC_PASSWORD = os.getenv("ELASTIC_PASSWORD")
    ELASTIC_SSL_FINGERPRINT = os.getenv("ELASTIC_SSL_FINGERPRINT")
    ELASTIC_HOST = os.getenv("ELASTIC_HOST")

    # Create the client instance
    client = Elasticsearch(
        ELASTIC_HOST,
        ssl_assert_fingerprint=ELASTIC_SSL_FINGERPRINT,
        basic_auth=("elastic", ELASTIC_PASSWORD),
    )

    logger = ESLogger(key=data.instanceId)
    logger.info(message="Initialized worker")

    try:
        r = redis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            decode_responses=True,
            username=REDIS_USERNAME,
            password=REDIS_PASSWORD,
        )

        # Create Repository

        clt = lakefs.Client(
            host=LAKEFS_ENDPOINT_URL,
            username=LAKEFS_ACCESS_KEY_ID,
            password=LAKEFS_SECRET_ACCESS_KEY,
        )
        _pipeline = pipeline_crud.get_pipeline_by_id(db, data.selectedPipelineId)
        _entry_step = None
        _first_step = None
        _final_step = None

        repo_name = get_repo_name(
            db=db, dataset_id=data.datasetId, project_id=data.projectId
        )

        for s in _pipeline.steps:
            if s.id == _pipeline.entry:
                _entry_step = s
                break

        for s in _pipeline.steps:
            if _entry_step.id in s.previousStepIds:
                _first_step = s
                break

        for s in _pipeline.steps:
            if s.id == _pipeline.exit:
                _final_step = s
                break

        repo = None

        for _repo in lakefs.repositories(client=clt):
            if _repo.id == repo_name:
                repo = _repo

        if not repo:
            repo = lakefs.Repository(repo_name, client=clt).create(
                storage_namespace=f"s3://{LAKEFS_STORAGE_NAMESPACE}/{repo_name}"
            )
        logger.info(message="Initialized lake repository")

        lakefs_branch = repo.branch("main")

        lakefs_s3 = boto3.client(
            "s3",
            aws_access_key_id=LAKEFS_ACCESS_KEY_ID,
            aws_secret_access_key=LAKEFS_SECRET_ACCESS_KEY,
            endpoint_url=LAKEFS_ENDPOINT_URL,
        )

        # src_bucket = _get_iam_s3_client(role_arn=formData.roleARN, endpoint=None).Bucket(
        #     formData.url
        # )

        s3url = S3Url(data.url)

        src_bucket = (
            boto3.Session(
                aws_access_key_id=S3_ACCESS_KEY_ID,
                aws_secret_access_key=S3_SECRET_ACCESS_KEY,
            )
            .resource("s3")
            .Bucket(s3url.bucket)
        )

        count = 0
        size = 0
        for o in src_bucket.objects.filter(Prefix=s3url.key):
            count += 1
            size += o.size

        avg_size = 0

        try:
            avg_size = size / count
        except:
            avg_size = 0

        set_redis_stats(
            r=r, instance_id=data.instanceId, count=count, avg_size=avg_size, size=size
        )

        set_instance_running(
            db=db, application_id=data.applicationId, instance_id=data.instanceId
        )

        set_pipeline_step_completed(
            db=db, instance_id=data.instanceId, step_id=_entry_step.id
        )

        logger.info(message="Completed Initialization")

        set_pipeline_step_running(
            db=db, instance_id=data.instanceId, step_id=_first_step.id
        )

        logger.info(message="Starting file ingestion")

        # branch = repo.branch("main")

        for summary in src_bucket.objects.filter(Prefix=s3url.key):
            # print(f"Copying {summary.key} with size {summary.size}...")
            # pprint(summary)
            if not summary.key.endswith("/"):
                r.json().set(
                    str(_first_step.id),
                    ".",
                    [{"label": InstanceStepDataLabel.CURR_DOC, "value": summary.key}],
                )
                s3_object = src_bucket.Object(summary.key).get()
                stream = s3_object["Body"]
                lakefs_s3.upload_fileobj(
                    Fileobj=stream, Bucket=repo_name, Key=f"main/{summary.key}"
                )
            r.json().numincrby(data.instanceId, ".ingested_size", summary.size)
            r.json().numincrby(data.instanceId, ".ingested_items", 1)

        set_instance_chart_data(r=r, db=db, instance_id=data.instanceId)

        set_instance_completed(
            db=db, application_id=data.applicationId, instance_id=data.instanceId
        )

        logger.info(message="Completed file ingestion")

        set_pipeline_step_completed(
            db=db, instance_id=data.instanceId, step_id=_first_step.id
        )

        set_pipeline_step_running(
            db=db, instance_id=data.instanceId, step_id=_final_step.id
        )

        __commit_flag__ = False

        for diff in lakefs_branch.uncommitted():
            if diff is not None:
                __commit_flag__ = True
                break
            else:
                break

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
            curr_version = dataset_crud.get_max_version_of_dataset(
                db=db, datasetId=data.datasetId
            )
            dataset_crud.create_dataset_version(
                db,
                data.datasetId,
                DatasetVersionCreate(commitId=ref.id, version=curr_version + 1),
            )
        else:
            logger.info(message="Dataset is identical, will not commit")
            print("Dataset is identical")

        set_pipeline_step_completed(
            db=db, instance_id=data.instanceId, step_id=_final_step.id
        )

    except BadRequestException as e:
        print("Dataset is identical")
    except Exception as e:
        print("Error")
        print(e)
        logger.error(message="Error encountered, aborting ingestion")
        logger.error(message=e)
        print(e.with_traceback())
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

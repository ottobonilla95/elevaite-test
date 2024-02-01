from datetime import datetime
import json
import os
from pprint import pprint
import sys
import threading
from dotenv import load_dotenv
from elasticsearch import Elasticsearch
import pika
import boto3
import lakefs

from botocore.client import BaseClient
from botocore.client import Config as ClientConfig
from botocore.credentials import RefreshableCredentials
from botocore.exceptions import ClientError
from botocore.session import get_session
import redis


class S3IngestData:
    creator: str
    name: str
    project: str
    version: str | None
    parent: str | None
    outputURI: str | None
    connectionName: str
    description: str | None
    url: str
    useEC2: bool
    roleARN: str
    datasetID: str
    applicationID: str

    def __init__(
        self,
        creator: str,
        name: str,
        project: str,
        version: str | None,
        parent: str | None,
        outputURI: str | None,
        connectionName: str,
        description: str | None,
        url: str,
        useEC2: bool,
        roleARN: str,
        datasetID: str,
        applicationID: str,
    ) -> None:
        self.creator = creator
        self.name = name
        self.project = project
        self.version = version
        self.parent = parent
        self.outputURI = outputURI
        self.connectionName = connectionName
        self.description = description
        self.url = url
        self.useEC2 = useEC2
        self.roleARN = roleARN
        self.datasetID = datasetID
        self.applicationID = applicationID


def main():
    load_dotenv()
    RABBITMQ_USER = os.getenv("RABBITMQ_USER")
    RABBITMQ_PASSWORD = os.getenv("RABBITMQ_PASSWORD")
    RABBITMQ_HOST = os.getenv("RABBITMQ_HOST")
    credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASSWORD)
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(
            host=RABBITMQ_HOST,
            port=5672,
            heartbeat=600,
            blocked_connection_timeout=300,
            credentials=credentials,
            virtual_host="elevaite_dev",
        )
    )
    channel = connection.channel()

    channel.queue_declare(queue="s3_ingest")

    def callback(ch, method, properties, body):
        _data = json.loads(body)

        print(f" [x] Received {_data}")

        _formData = S3IngestData(
            **_data["dto"], datasetID=_data["id"], applicationID=_data["application_id"]
        )
        t = threading.Thread(target=s3_lakefs_cp_stream, args=(_formData))
        # s3_lakefs_cp_stream(formData=_formData)
        t.start()

    channel.basic_consume(
        queue="s3_ingest", on_message_callback=callback, auto_ack=True
    )

    print("Awaiting Messages")

    channel.start_consuming()


def s3_lakefs_cp_stream(formData: S3IngestData) -> None:
    load_dotenv()
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
    print("REDIS_HOST: ", REDIS_HOST)
    print("REDIS_PORT: ", REDIS_PORT)

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

    repo = None

    for _repo in lakefs.repositories(client=clt):
        if _repo.id == formData.project:
            repo = _repo

    if not repo:
        repo = lakefs.Repository(formData.project, client=clt).create(
            storage_namespace=f"s3://{LAKEFS_STORAGE_NAMESPACE}/{formData.project}"
        )

    lakefs_s3 = boto3.client(
        "s3",
        aws_access_key_id=LAKEFS_ACCESS_KEY_ID,
        aws_secret_access_key=LAKEFS_SECRET_ACCESS_KEY,
        endpoint_url=LAKEFS_ENDPOINT_URL,
    )

    # Create the client instance
    client = Elasticsearch(
        ELASTIC_HOST,
        ssl_assert_fingerprint=ELASTIC_SSL_FINGERPRINT,
        basic_auth=("elastic", ELASTIC_PASSWORD),
    )

    # src_bucket = _get_iam_s3_client(role_arn=formData.roleARN, endpoint=None).Bucket(
    #     formData.url
    # )

    src_bucket = (
        boto3.Session(
            aws_access_key_id=S3_ACCESS_KEY_ID,
            aws_secret_access_key=S3_SECRET_ACCESS_KEY,
        )
        .resource("s3")
        .Bucket(formData.url)
    )
    # lakefs_bucket = boto3.Session(...).resource("s3").Bucket("###")

    count = 0
    size = 0
    for o in src_bucket.objects.all():
        count += 1
        size += o.size

    # size = sum(1 for _ in src_bucket.objects.all())

    _data = {
        "total_items": count,
        "ingested_items": 0,
        "ingested_size": 0,
        "avg_size": size / count,
        "total_size": size,
    }

    r.json().set(formData.datasetID, ".", _data)

    resp = client.get(index="application", id=formData.applicationID)
    instances = resp["_source"]["instances"]
    for instance in instances:
        if instance["id"] == formData.datasetID:
            instance["status"] = "running"

    client.update(
        index="application",
        id=formData.applicationID,
        body=json.dumps({"doc": {"instances": instances}}, default=vars),
    )

    branch = repo.branch("main")

    for summary in src_bucket.objects.all():
        # print(f"Copying {summary.key} with size {summary.size}...")
        # pprint(summary)
        if not summary.key.endswith("/"):
            s3_object = src_bucket.Object(summary.key).get()
            stream = s3_object["Body"]
            lakefs_s3.upload_fileobj(
                Fileobj=stream, Bucket=formData.project, Key=f"main/{summary.key}"
            )
        r.json().numincrby(formData.datasetID, ".ingested_size", summary.size)
        r.json().numincrby(formData.datasetID, ".ingested_items", 1)
        # branch.object(path=f"main/{summary.key}").upload(
        #     content_type=s3_object["ContentType"], data=stream
        # )

    res = r.json().get(formData.datasetID)
    resp = client.get(index="application", id=formData.applicationID)
    instances = resp["_source"]["instances"]
    for instance in instances:
        if instance["id"] == formData.datasetID:
            instance["status"] = "completed"
            instance["endTime"] = datetime.utcnow().isoformat()
            instance["chartData"] = {
                "totalItems": res["total_items"],
                "ingestedItems": res["ingested_items"],
                "avgSize": res["avg_size"],
                "totalSize": res["total_size"],
                "ingestedSize": res["ingested_size"],
            }

    client.update(
        index="application",
        id=formData.applicationID,
        body=json.dumps({"doc": {"instances": instances}}, default=vars),
    )
    print("Done importing data")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Interrupted")
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)

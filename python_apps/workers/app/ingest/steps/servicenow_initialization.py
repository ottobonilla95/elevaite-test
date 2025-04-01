import sys
import os
from elevaitelib.util.logger import ESLogger
from pydantic import UUID4
from redis import Redis
import lakefs
import boto3
from sqlalchemy.orm import Session
from ...interfaces import (
    S3IngestData,
    ServiceNowIngestData,
    isServiceNowIngestData,
)
from .base_step import (
    RESOURCE_REGISTRY,
    BaseIngestStep,
)
from ...util.func import (
    get_repo_name,
    set_pipeline_step_completed,
    set_redis_stats,
)


class ServiceNowInitialization(BaseIngestStep):
    def __init__(
        self,
        data: S3IngestData | ServiceNowIngestData,
        db: Session,
        r: Redis,
        logger: ESLogger,
        step_id: UUID4,
    ) -> None:
        super().__init__(data, db, r, logger, step_id)

    def run(self):
        if not isServiceNowIngestData(self.data):
            raise Exception("Data malformed")
        global RESOURCE_REGISTRY
        _instance_registry = RESOURCE_REGISTRY[self.data.instanceId]
        LAKEFS_ACCESS_KEY_ID = os.getenv("LAKEFS_ACCESS_KEY_ID")
        if LAKEFS_ACCESS_KEY_ID is None:
            raise Exception("LAKEFS_ACCESS_KEY_ID is null")
        LAKEFS_SECRET_ACCESS_KEY = os.getenv("LAKEFS_SECRET_ACCESS_KEY")
        if LAKEFS_SECRET_ACCESS_KEY is None:
            raise Exception("LAKEFS_SECRET_ACCESS_KEY is null")
        LAKEFS_ENDPOINT_URL = os.getenv("LAKEFS_ENDPOINT_URL")
        if LAKEFS_ENDPOINT_URL is None:
            raise Exception("LAKEFS_ENDPOINT_URL is null")
        LAKEFS_STORAGE_NAMESPACE = os.getenv("LAKEFS_STORAGE_NAMESPACE")
        if LAKEFS_STORAGE_NAMESPACE is None:
            raise Exception("LAKEFS_STORAGE_NAMESPACE is null")

        clt = lakefs.Client(
            host=LAKEFS_ENDPOINT_URL,
            username=LAKEFS_ACCESS_KEY_ID,
            password=LAKEFS_SECRET_ACCESS_KEY,
        )

        if self.data.datasetId is None:
            raise Exception("No datasetId recieved")
        repo = None

        repo_name = get_repo_name(db=self.db, dataset_id=self.data.datasetId, project_id=self.data.projectId)

        _instance_registry.lakefs_repo_name = repo_name

        for _repo in lakefs.repositories(client=clt):
            if _repo.id == repo_name:
                repo = _repo
                break
        if repo is None:
            repo = lakefs.Repository(repo_name, client=clt).create(
                storage_namespace=f"s3://{LAKEFS_STORAGE_NAMESPACE}/{repo_name}"
            )
        self.logger.info(message="Initialized lake repository")

        lakefs_branch = repo.branch("main")
        _instance_registry.lakefs_branch = lakefs_branch

        lakefs_s3 = boto3.client(
            "s3",
            aws_access_key_id=LAKEFS_ACCESS_KEY_ID,
            aws_secret_access_key=LAKEFS_SECRET_ACCESS_KEY,
            endpoint_url=LAKEFS_ENDPOINT_URL,
        )
        _instance_registry.lakefs_s3_client = lakefs_s3

        count = 0
        size = 0
        for ticket in self.data.tickets:
            count += 1
            size += sys.getsizeof(ticket.json())

        avg_size = 0

        try:
            avg_size = size / count
        except:  # noqa: E722
            avg_size = 0

        set_redis_stats(
            r=self.r,
            instance_id=self.data.instanceId,
            count=count,
            avg_size=avg_size,
            size=size,
        )

        set_pipeline_step_completed(db=self.db, instance_id=self.data.instanceId, step_id=self.step_id)

        self.logger.info(message="Completed Initialization")

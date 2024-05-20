from elevaitelib.util.logger import ESLogger
from pydantic import UUID4
from redis import Redis
from sqlalchemy.orm import Session

from .base_step import BaseIngestStep, RESOURCE_REGISTRY
from ...interfaces import S3IngestData, ServiceNowIngestData
from ...util.func import (
    path_leaf,
    set_instance_chart_data,
    set_instance_completed,
    set_pipeline_step_completed,
    set_pipeline_step_running,
)


class S3WorkerStep(BaseIngestStep):
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
        set_pipeline_step_running(
            db=self.db, instance_id=self.data.instanceId, step_id=self.step_id
        )

        _instance_resources = RESOURCE_REGISTRY[self.data.instanceId]

        self.logger.info(message="Starting file ingestion")

        # branch = repo.branch("main")

        src_bucket = _instance_resources.source_bucket
        if src_bucket is None:
            raise Exception("Source Bucket has not been initialized.")

        s3url = _instance_resources.s3url
        if s3url is None:
            raise Exception("S3 URL object has not been initialized.")

        lakefs_s3 = _instance_resources.lakefs_s3_client
        if lakefs_s3 is None:
            raise Exception("LakeFS S3 client has not been initialized.")

        repo_name = _instance_resources.lakefs_repo_name
        if repo_name is None:
            raise Exception("LakeFS Repository Name has not been initialized.")

        for summary in src_bucket.objects.filter(Prefix=s3url.key):
            # print(f"Copying {summary.key} with size {summary.size}...")
            # pprint(summary)
            if not summary.key.endswith("/"):
                self.r.json().set(
                    self.data.instanceId, ".current_file", path_leaf(summary.key)
                )
                s3_object = src_bucket.Object(summary.key).get()
                stream = s3_object["Body"]
                lakefs_s3.upload_fileobj(
                    Fileobj=stream, Bucket=repo_name, Key=f"main/{summary.key}"
                )
            self.r.json().numincrby(
                self.data.instanceId, ".ingested_size", summary.size
            )
            self.r.json().numincrby(self.data.instanceId, ".ingested_items", 1)

        set_instance_chart_data(r=self.r, db=self.db, instance_id=self.data.instanceId)

        self.logger.info(message="Completed file ingestion")

        set_pipeline_step_completed(
            db=self.db, instance_id=self.data.instanceId, step_id=self.step_id
        )

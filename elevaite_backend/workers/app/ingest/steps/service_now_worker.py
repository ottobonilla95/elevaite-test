import json
import sys
from elevaitedb.util.logger import ESLogger
from pydantic import UUID4
from redis import Redis
from sqlalchemy.orm import Session

from .base_step import BaseIngestStep, RESOURCE_REGISTRY
from ...interfaces import S3IngestData, ServiceNowIngestData, isServiceNowIngestData
from ...util.func import (
    path_leaf,
    set_instance_chart_data,
    set_pipeline_step_completed,
    set_pipeline_step_running,
)


class ServiceNowWorker(BaseIngestStep):
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
        set_pipeline_step_running(
            db=self.db, instance_id=self.data.instanceId, step_id=self.step_id
        )

        _instance_resources = RESOURCE_REGISTRY[self.data.instanceId]

        self.logger.info(message="Starting file ingestion")

        lakefs_branch = _instance_resources.lakefs_branch
        if lakefs_branch is None:
            raise Exception("LakeFS Branch Object has not been initialized")

        repo_name = _instance_resources.lakefs_repo_name
        if repo_name is None:
            raise Exception("LakeFS Repository Name has not been initialized.")

        for ticket in self.data.tickets:
            # print(f"Copying {summary.key} with size {summary.size}...")
            # pprint(summary)
            self.r.json().set(
                self.data.instanceId, ".current_file", path_leaf(ticket.source_ref_id)
            )
            obj = lakefs_branch.object(f"{ticket.source_ref_id}.json")
            with obj.writer(
                mode="w", pre_sign=True, content_type="application/json"
            ) as fd:
                json.dump(ticket, fd, ensure_ascii=False, indent=4)
            self.r.json().numincrby(
                self.data.instanceId, ".ingested_size", sys.getsizeof(ticket.json())
            )
            self.r.json().numincrby(self.data.instanceId, ".ingested_items", 1)

        set_instance_chart_data(r=self.r, db=self.db, instance_id=self.data.instanceId)

        self.logger.info(message="Completed file ingestion")

        set_pipeline_step_completed(
            db=self.db, instance_id=self.data.instanceId, step_id=self.step_id
        )

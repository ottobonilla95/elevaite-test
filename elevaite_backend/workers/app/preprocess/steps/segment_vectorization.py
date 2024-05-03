from typing import List
from elevaitedb.util.logger import ESLogger
from pydantic import UUID4
from redis import Redis
from sqlalchemy.orm import Session


from ...interfaces import PreProcessForm
from ...preprocess import vectordb
from ...util.func import (
    set_instance_chart_data,
    set_pipeline_step_completed,
    set_pipeline_step_running,
)
from .base_step import RESOURCE_REGISTRY, BasePreprocessStep


class SegmentVectorization(BasePreprocessStep):
    def __init__(
        self,
        data: PreProcessForm,
        db: Session,
        r: Redis,
        logger: ESLogger,
        step_id: UUID4,
    ) -> None:
        super().__init__(data, db, r, logger, step_id)

    async def run(self):
        set_pipeline_step_running(
            db=self.db, instance_id=self.data.instanceId, step_id=self.step_id
        )
        global RESOURCE_REGISTRY
        _instance_registry = RESOURCE_REGISTRY[self.data.instanceId]
        collection_name = _instance_registry.collection_name
        if collection_name is None:
            raise Exception(
                f"Vector DB Collection Name has not been set. Make sure the Initialization step has run."
            )
        chunks_as_json = _instance_registry.chunks_as_json
        if chunks_as_json is None:
            raise Exception(
                f"Chunks as JSON has not been set. Make sure the Segmentation step has run."
            )

        self.logger.info(message="Starting segment vectorization")
        await vectordb.insert_records(
            db=self.db,
            instance_id=self.data.instanceId,
            step_id=self.step_id,
            collection=collection_name,
            payload_with_contents=chunks_as_json,
            emb_info=self.data.embedding_info,
        )
        self.logger.info(message="Completed segment vectorization")

        set_instance_chart_data(r=self.r, db=self.db, instance_id=self.data.instanceId)

        set_pipeline_step_completed(
            db=self.db, instance_id=self.data.instanceId, step_id=self.step_id
        )

import sys
from typing import List
from redis import Redis
from pydantic import UUID4
from sqlalchemy.orm import Session

from elevaitelib.schemas.instance import InstancePipelineStepData, InstanceStepDataLabel
from elevaitelib.util.logger import ESLogger

from ..preprocess import (
    ChunkAsJson,
    get_file_elements_internal,
)
from ...util.func import (
    path_leaf,
    set_instance_chart_data,
    set_pipeline_step_completed,
    set_pipeline_step_meta,
    set_pipeline_step_running,
)
from .base_step import RESOURCE_REGISTRY, BasePreprocessStep
from ...interfaces import PreProcessForm


class DocumentSegmentation(BasePreprocessStep):

    def __init__(
        self,
        data: PreProcessForm,
        db: Session,
        r: Redis,
        logger: ESLogger,
        step_id: UUID4,
    ) -> None:
        super().__init__(data=data, db=db, logger=logger, r=r, step_id=step_id)

    async def run(self):
        set_pipeline_step_running(
            db=self.db, instance_id=self.data.instanceId, step_id=self.step_id
        )
        global RESOURCE_REGISTRY
        _instance_registry = RESOURCE_REGISTRY[self.data.instanceId]
        ref = _instance_registry.lakefs_ref
        if ref is None:
            raise Exception(
                f"LakeFS Reference has not been set. Make sure the Initialization step has run."
            )
        repo_name = _instance_registry.lakefs_repo_name
        if repo_name is None:
            raise Exception(
                f"LakeFS Repository Name has not been set. Make sure the Initialization step has run."
            )
        dataset_version = _instance_registry.dataset_version
        if dataset_version is None:
            raise Exception(
                f"Dataset Version has not been set. Make sure the Initialization step has run."
            )
        chunks_as_json: List[ChunkAsJson] = []
        findex = 0
        self.logger.info(message="Starting file segmentation")
        total_chunk_size = 0
        avg_chunk_size = 0
        max_chunk_size = 0
        num_chunk = 0
        for object in ref.objects():
            # print(object)
            object.physical_address  # type: ignore | Typing seems to be wrong
            with ref.object(object.path).reader(pre_sign=False, mode="rb") as fd:
                self.r.json().set(
                    self.data.instanceId, ".current_doc", path_leaf(object.path)
                )
                input = fd.read()
                file_chunks = get_file_elements_internal(
                    file=input,
                    filepath=object.path,
                    content_type=object.content_type,  # type: ignore | Typing seems to be wrong
                )
                chunks_as_json.extend(file_chunks)
                for chunk in file_chunks:
                    _chunk_size = sys.getsizeof(chunk.page_content)
                    num_chunk += 1
                    total_chunk_size += _chunk_size
                    avg_chunk_size = str(total_chunk_size / num_chunk)
                    if _chunk_size > max_chunk_size:
                        max_chunk_size = _chunk_size
                self.r.json().numincrby(self.data.instanceId, ".ingested_size", object.size_bytes)  # type: ignore | Typing seems to be wrong
                self.r.json().numincrby(self.data.instanceId, ".ingested_items", 1)
                self.r.json().numincrby(
                    self.data.instanceId, ".ingested_chunks", len(file_chunks)
                )
            findex += 1
            if findex % 10 == 0:
                # print(findex)

                set_pipeline_step_meta(
                    db=self.db,
                    instance_id=self.data.instanceId,
                    step_id=self.step_id,
                    meta=[
                        InstancePipelineStepData(
                            label=InstanceStepDataLabel.REPO_NAME, value=repo_name
                        ),
                        InstancePipelineStepData(
                            label=InstanceStepDataLabel.DATASET_VERSION,
                            value=dataset_version.version,
                        ),
                        InstancePipelineStepData(
                            label=InstanceStepDataLabel.INGEST_DATE,
                            value=dataset_version.createDate.isoformat(),
                        ),
                        InstancePipelineStepData(
                            label=InstanceStepDataLabel.TOTAL_CHUNK_SIZE,
                            value=total_chunk_size,
                        ),
                        InstancePipelineStepData(
                            label=InstanceStepDataLabel.AVG_CHUNK_SIZE,
                            value=avg_chunk_size,
                        ),
                        InstancePipelineStepData(
                            label=InstanceStepDataLabel.LRGST_CHUNK_SIZE,
                            value=max_chunk_size,
                        ),
                    ],
                )
        self.logger.info(message="Completed file segmentation")

        set_instance_chart_data(r=self.r, db=self.db, instance_id=self.data.instanceId)

        set_pipeline_step_completed(
            db=self.db, instance_id=self.data.instanceId, step_id=self.step_id
        )

        set_pipeline_step_meta(
            db=self.db,
            instance_id=self.data.instanceId,
            step_id=self.step_id,
            meta=[
                InstancePipelineStepData(
                    label=InstanceStepDataLabel.REPO_NAME, value=repo_name
                ),
                InstancePipelineStepData(
                    label=InstanceStepDataLabel.DATASET_VERSION,
                    value=dataset_version.version,
                ),
                InstancePipelineStepData(
                    label=InstanceStepDataLabel.INGEST_DATE,
                    value=dataset_version.createDate.isoformat(),
                ),
                InstancePipelineStepData(
                    label=InstanceStepDataLabel.TOTAL_CHUNK_SIZE,
                    value=total_chunk_size,
                ),
                InstancePipelineStepData(
                    label=InstanceStepDataLabel.AVG_CHUNK_SIZE,
                    value=avg_chunk_size,
                ),
                InstancePipelineStepData(
                    label=InstanceStepDataLabel.LRGST_CHUNK_SIZE,
                    value=max_chunk_size,
                ),
            ],
        )
        _instance_registry.chunks_as_json = chunks_as_json

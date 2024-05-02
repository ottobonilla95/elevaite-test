import os
from elevaitedb.schemas.instance import InstancePipelineStepData, InstanceStepDataLabel
from elevaitedb.util.logger import ESLogger
from pydantic import UUID4
from redis import Redis
import lakefs
from sqlalchemy.orm import Session
from ...interfaces import PreProcessForm
from .base_step import (
    RESOURCE_REGISTRY,
    BasePreprocessStep,
)
from ...util.func import (
    get_repo_name,
    set_pipeline_step_completed,
    set_pipeline_step_meta,
    set_redis_stats,
)
from elevaitedb.crud import (
    collection as collection_crud,
    dataset as dataset_crud,
)
from elevaitedb.util import func as util_func


class GeneralInitialization(BasePreprocessStep):

    def __init__(
        self,
        data: PreProcessForm,
        db: Session,
        r: Redis,
        logger: ESLogger,
        step_id: UUID4,
    ) -> None:
        super().__init__(data, db, r, logger, step_id)

    def run(self):
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

        clt = lakefs.Client(
            host=LAKEFS_ENDPOINT_URL,
            username=LAKEFS_ACCESS_KEY_ID,
            password=LAKEFS_SECRET_ACCESS_KEY,
        )

        if self.data.datasetId is None:
            raise Exception("No datasetId recieved")
        repo = None

        repo_name = get_repo_name(
            db=self.db, dataset_id=self.data.datasetId, project_id=self.data.projectId
        )

        _instance_registry.lakefs_repo_name = repo_name

        for _repo in lakefs.repositories(client=clt):
            if _repo.id == repo_name:
                repo = _repo
                break
        if repo is None:
            raise Exception("LakeFS Repository not found")

        _version = (
            self.data.datasetVersion
            if self.data.datasetVersion
            else dataset_crud.get_max_version_of_dataset(
                db=self.db, datasetId=self.data.datasetId
            )
        )

        dataset_version = dataset_crud.get_dataset_version(
            db=self.db, datasetId=self.data.datasetId, version=_version
        )
        if dataset_version is None:
            raise Exception("Dataset Version not found.")
        _instance_registry.dataset_version = dataset_version

        ref = lakefs.Reference(repo.id, dataset_version.commitId, client=clt)

        _instance_registry.lakefs_ref = ref

        self.logger.info(message="Dataset found")
        _collection = collection_crud.get_collection_by_id(
            db=self.db, collectionId=self.data.collectionId
        )
        collection_name = util_func.to_kebab_case(_collection.name)

        _instance_registry.collection_name = collection_name

        count = 0
        size = 0
        for o in ref.objects():
            count += 1
            size += o.size_bytes  # type: ignore | Typing seems to be wrong

        # size = sum(1 for _ in src_bucket.objects.all())

        avg_size = 0

        try:
            avg_size = size / count
        except:
            avg_size = 0

        set_redis_stats(
            r=self.r,
            instance_id=self.data.instanceId,
            count=count,
            avg_size=avg_size,
            size=size,
        )

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
            ],
        )

        self.logger.info(message="Completed Initialization")

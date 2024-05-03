from abc import ABC, abstractmethod
from typing import Dict, List, Optional

from elevaitedb.schemas.dataset import DatasetVersion
from elevaitedb.util.logger import ESLogger
from pydantic import UUID4
from redis import Redis
from sqlalchemy.orm import Session
from lakefs import Reference

from ..preprocess import ChunkAsJson
from ...interfaces import PreProcessForm

STEP_REGISTRY: Dict[str, type["BasePreprocessStep"]] = {}
RESOURCE_REGISTRY: Dict[str, "ResourceRegistry"] = {}


def register_step(step_id: UUID4 | str, cls: type["BasePreprocessStep"]):
    global STEP_REGISTRY
    _step_id = str(step_id)
    if _step_id in STEP_REGISTRY:
        raise ValueError(
            f"Error while registering class {cls.__name__} already taken by {STEP_REGISTRY[_step_id].__name__}"
        )
    STEP_REGISTRY[_step_id] = cls


def get_initialized_step(
    step_id: UUID4,
    data: PreProcessForm,
    db: Session,
    r: Redis,
    logger: ESLogger,
) -> "BasePreprocessStep":
    _step_id = str(step_id)
    if _step_id not in STEP_REGISTRY:
        raise ValueError(
            f"Error while retrieving runner for step with id {_step_id}. This step has not be registered"
        )
    _step_runner = STEP_REGISTRY[_step_id]
    return _step_runner(data=data, db=db, logger=logger, r=r, step_id=step_id)


class BasePreprocessStep(ABC):
    """Interface for preprocess steps."""

    data: PreProcessForm
    db: Session
    r: Redis
    logger: ESLogger
    step_id: str

    def __init__(
        self,
        data: PreProcessForm,
        db: Session,
        r: Redis,
        logger: ESLogger,
        step_id: UUID4,
    ) -> None:
        super().__init__()
        self.data = data
        self.db = db
        self.r = r
        self.logger = logger
        self.step_id = str(step_id)

    @abstractmethod
    async def run(self):
        """Step code"""


class ResourceRegistry:
    collection_name: Optional[str]
    chunks_as_json: Optional[List[ChunkAsJson]]
    lakefs_ref: Optional[Reference]
    lakefs_repo_name: Optional[str]
    dataset_version: Optional[DatasetVersion]

    def __init__(
        self,
        collection_name,
        chunks_as_json,
        lakefs_ref,
        lakefs_repo_name,
        dataset_version,
    ) -> None:
        self.collection_name = collection_name
        self.chunks_as_json = chunks_as_json
        self.lakefs_ref = lakefs_ref
        self.lakefs_repo_name = lakefs_repo_name
        self.dataset_version = dataset_version


def register_resource_registry(instance_id: str) -> "ResourceRegistry":
    global RESOURCE_REGISTRY
    if instance_id in RESOURCE_REGISTRY:
        raise ValueError(
            f"Error while registering for instance {instance_id}. Registry already exists"
        )
    RESOURCE_REGISTRY[instance_id] = ResourceRegistry(
        chunks_as_json=None,
        collection_name=None,
        dataset_version=None,
        lakefs_ref=None,
        lakefs_repo_name=None,
    )
    return RESOURCE_REGISTRY[instance_id]

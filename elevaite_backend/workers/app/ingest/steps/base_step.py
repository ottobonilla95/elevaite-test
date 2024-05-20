from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from elevaitelib.util.logger import ESLogger
from elevaitelib.util.s3url import S3Url
from pydantic import UUID4
from redis import Redis
from sqlalchemy.orm import Session
from lakefs import Branch

from ...interfaces import S3IngestData, ServiceNowIngestData

STEP_REGISTRY: Dict[str, type["BaseIngestStep"]] = {}
RESOURCE_REGISTRY: Dict[str, "ResourceRegistry"] = {}


def register_step(step_id: UUID4 | str, cls: type["BaseIngestStep"]):
    global STEP_REGISTRY
    _step_id = str(step_id)
    if _step_id in STEP_REGISTRY:
        raise ValueError(
            f"Error while registering class {cls.__name__} already taken by {STEP_REGISTRY[_step_id].__name__}"
        )
    STEP_REGISTRY[_step_id] = cls


def get_initialized_step(
    step_id: UUID4,
    data: S3IngestData | ServiceNowIngestData,
    db: Session,
    r: Redis,
    logger: ESLogger,
) -> "BaseIngestStep":
    _step_id = str(step_id)
    if _step_id not in STEP_REGISTRY:
        raise ValueError(
            f"Error while retrieving runner for step with id {_step_id}. This step has not be registered"
        )
    _step_runner = STEP_REGISTRY[_step_id]
    return _step_runner(data=data, db=db, logger=logger, r=r, step_id=step_id)


class BaseIngestStep(ABC):
    """Interface for ingestion steps."""

    data: S3IngestData | ServiceNowIngestData
    db: Session
    r: Redis
    logger: ESLogger
    step_id: str

    def __init__(
        self,
        data: S3IngestData | ServiceNowIngestData,
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
    def run(self):
        """Step code"""


class ResourceRegistry:
    collection_name: Optional[str]
    lakefs_repo_name: Optional[str]
    lakefs_branch: Optional[Branch]
    lakefs_s3_client: Optional[Any]
    s3url: Optional[S3Url]
    source_bucket: Optional[Any]

    def __init__(
        self,
        collection_name,
        lakefs_repo_name,
    ) -> None:
        self.collection_name = collection_name
        self.lakefs_repo_name = lakefs_repo_name


def register_resource_registry(instance_id: str) -> "ResourceRegistry":
    global RESOURCE_REGISTRY
    if instance_id in RESOURCE_REGISTRY:
        raise ValueError(
            f"Error while registering for instance {instance_id}. Registry already exists"
        )
    RESOURCE_REGISTRY[instance_id] = ResourceRegistry(
        collection_name=None,
        lakefs_repo_name=None,
    )
    return RESOURCE_REGISTRY[instance_id]

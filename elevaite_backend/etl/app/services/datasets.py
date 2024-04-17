from typing import List
from elevaitedb.db import models
from sqlalchemy.orm import Session

from app.util.name_generator import get_random_name
from app.util import func as util_func
from elevaitedb.schemas.dataset import (
    DatasetCreate,
    DatasetTagCreate,
    DatasetVersionCreate,
    is_dataset,
)
from elevaitedb.crud import (
    dataset as dataset_crud,
)


def get_datasets_of_project(
    db: Session, projectId: str, skip: int, limit: int
) -> List[models.Dataset]:
    return dataset_crud.get_datasets_of_project(
        db=db, project_id=projectId, skip=skip, limit=limit
    )


def get_dataset_by_id(db: Session, datasetId: str) -> models.Dataset:
    return dataset_crud.get_dataset_by_id(db, datasetId)


def create_dataset(db: Session, _dataset_create: DatasetCreate) -> models.Dataset:
    return dataset_crud.create_dataset(db, _dataset_create)


def create_dataset_tag(
    db: Session, _dataset_create: DatasetTagCreate
) -> models.DatasetTag:
    return dataset_crud.create_dataset_tag(db, _dataset_create)


def create_dataset_version(
    db: Session, dataset_id: str, _dataset_create: DatasetVersionCreate
) -> models.DatasetVersion:
    return dataset_crud.create_dataset_version(
        db=db, datasetId=dataset_id, dsvc=_dataset_create
    )


def get_latest_version_of_dataset(db: Session, datasetId: str) -> int:
    return dataset_crud.get_max_version_of_dataset(db, datasetId)


def add_tag_to_dataset(db: Session, datasetId: str, tagId: str) -> models.Dataset:
    return dataset_crud.add_tag_to_dataset(db, datasetId, tagId)

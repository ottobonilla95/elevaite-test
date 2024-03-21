from sqlalchemy.orm import Session

from app.util.name_generatior import get_random_name
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


def get_datasets_of_project(db: Session, projectId: str, skip: int, limit: int):
    return dataset_crud.get_datasets_of_project(
        db=db, project_id=projectId, skip=skip, limit=limit
    )


def get_dataset_by_id(db: Session, datasetId: str):
    return dataset_crud.get_dataset_by_id(db, datasetId)


def create_dataset(db: Session, _dataset_create: DatasetCreate):
    return dataset_crud.create_dataset(db, _dataset_create)


def create_dataset_tag(db: Session, _dataset_create: DatasetTagCreate):
    return dataset_crud.create_dataset_tag(db, _dataset_create)


def create_dataset_version(db: Session, _dataset_create: DatasetVersionCreate):
    return dataset_crud.create_dataset_version(db, _dataset_create)


def get_latest_version_of_dataset(db: Session, datasetId: str):
    return dataset_crud.get_max_version_of_dataset(db, datasetId)


def add_tag_to_dataset(db: Session, datasetId: str, tagId: str):
    return dataset_crud.add_tag_to_dataset(db, datasetId, tagId)

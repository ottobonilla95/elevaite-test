from sqlalchemy.orm import Session, Query
from sqlalchemy import func, select
from typing import Type, Callable
import uuid
from ..db import models
from ..schemas.dataset import DatasetCreate, DatasetTagCreate, DatasetVersionCreate

def get_datasets_of_project(
    db: Session,
    project_id: str,
    # filter_function: Callable[[Query], Query], # uncomment this when using validator
    skip: int = 0,
    limit: int = 100
):
    query = db.query(models.Dataset)

    # if filter_function is not None: # uncomment this when using validator
        # query = filter_function(query)

    return (
        query.filter(models.Dataset.projectId == project_id)
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_dataset_by_id(db: Session, dataset_id: str):
    return db.query(models.Dataset).filter(models.Dataset.id == dataset_id).first()


def create_dataset(db: Session, dataset_create: DatasetCreate):
    _dataset = models.Dataset(
        name=dataset_create.name, projectId=dataset_create.projectId
    )
    db.add(_dataset)
    db.commit()
    db.refresh(_dataset)
    return _dataset


def get_dataset_by_name(db: Session, name: str) -> models.Dataset | None:
    return db.query(models.Dataset).filter(models.Dataset.name == name).first()


def get_dataset_tags(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.DatasetTag).offset(skip).limit(limit).all()


def get_dataset_tag_by_id(db: Session, tag_id: str):
    return db.query(models.DatasetTag).filter(models.DatasetTag.id == tag_id).first()


def create_dataset_tag(db: Session, dstc: DatasetTagCreate):
    _dataset_tag = models.DatasetTag(name=dstc.name)

    db.add(_dataset_tag)
    db.commit()
    db.refresh(_dataset_tag)
    return _dataset_tag


def add_tag_to_dataset(db: Session, dataset_id: str, tag_id: str):
    _tag = get_dataset_tag_by_id(db, tag_id)
    _dataset = get_dataset_by_id(db, dataset_id)
    if _dataset is None:
        raise Exception("Dataset not found")

    _dataset.tags.append(_tag)
    db.add(_dataset)
    db.commit()
    db.refresh(_dataset)

    return _dataset


def get_dataset_version(db: Session, datasetId: str, version: int):
    return (
        db.query(models.DatasetVersion)
        .filter(models.DatasetVersion.datasetId == datasetId)
        .filter(models.DatasetVersion.version == version)
        .first()
    )


def get_max_version_of_dataset(db: Session, datasetId: str):
    curr_ver = db.scalar(
        select(func.max(models.DatasetVersion.version)).where(
            models.DatasetVersion.datasetId == datasetId
        )
    )
    return curr_ver if curr_ver is not None else 0


def create_dataset_version(db: Session, datasetId: str, dsvc: DatasetVersionCreate):
    _dsv = models.DatasetVersion(
        commitId=dsvc.commitId,
        version=dsvc.version,
        datasetId=datasetId,
    )
    db.add(_dsv)
    db.commit()
    db.refresh(_dsv)
    return _dsv

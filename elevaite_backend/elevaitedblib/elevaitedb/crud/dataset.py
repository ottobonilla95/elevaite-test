from sqlalchemy.orm import Session

from ..db import models
from ..schemas.dataset import DatasetCreate


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

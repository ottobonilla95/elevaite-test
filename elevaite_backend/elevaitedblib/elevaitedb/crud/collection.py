from sqlalchemy.orm import Session

from ..schemas.collection import CollectionCreate

from ..db import models


def get_collections(db: Session, projectId: str, skip: int = 0, limit: int = 100):
    return (
        db.query(models.Collection)
        .filter(models.Collection.projectId == projectId)
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_collection_by_id(db: Session, collectionId: str):
    return (
        db.query(models.Collection).filter(models.Collection.id == collectionId).first()
    )


def create_collection(db: Session, projectId: str, cc: CollectionCreate):
    _collection = models.Collection(name=cc.name, projectId=projectId)

    db.add(_collection)
    db.commit()
    db.refresh(_collection)
    return _collection

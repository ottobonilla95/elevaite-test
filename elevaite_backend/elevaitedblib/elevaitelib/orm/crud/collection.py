from typing import List, Callable, Type
from sqlalchemy.orm import Session, Query
import uuid
from ...schemas.collection import CollectionCreate

from ..db import models


def get_collections(
    db: Session,
    projectId: str,
    # filter_function: Callable[[Query], Query], # uncomment this when using validator
    skip: int = 0,
    limit: int = 100,
) -> List[models.Collection]:
    query = db.query(models.Collection)

    # if filter_function is not None: # uncomment this when using validator
    # query = filter_function(query)

    return (
        query.filter(models.Collection.projectId == projectId)
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_collection_by_id(db: Session, collectionId: str) -> models.Collection:
    return (
        db.query(models.Collection).filter(models.Collection.id == collectionId).first()
    )


def create_collection(
    db: Session, projectId: str, cc: CollectionCreate
) -> models.Collection:
    _collection = models.Collection(
        name=cc.name, projectId=projectId, distance=cc.distance, size=cc.size
    )

    db.add(_collection)
    db.commit()
    db.refresh(_collection)
    return _collection

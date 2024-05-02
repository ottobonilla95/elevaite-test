from typing import List, Dict, Any
from sqlalchemy.orm import Session

from ..schemas.collection import CollectionCreate

from ..db import models

# from rbac_api import rbac_instance


def get_collections(
    db: Session,
    projectId: str,
    # filters_list: List[Dict[str, Any]], # uncomment this when using validator
    skip: int = 0,
    limit: int = 100,
) -> List[models.Collection]:
    query = db.query(models.Collection)
    # query = rbac_instance.apply_post_validation_type_filters_for_all_query(model_class=models.Collection, filters_list=filters_list, query=query) # uncomment this when using validator

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

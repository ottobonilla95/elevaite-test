from typing import List
from elevaitedb.db import models
from sqlalchemy.orm import Session
from elevaitedb.schemas.collection import Collection, CollectionCreate
from elevaitedb.crud import collection as collection_crud


def getCollectionsOfProject(
    db: Session, projectId: str, skip: int = 0, limit: int = 100
) -> List[models.Collection]:
    return collection_crud.get_collections(
        db=db, projectId=projectId, skip=skip, limit=limit
    )


def getCollectionById(db: Session, collectionId: str) -> models.Collection:
    return collection_crud.get_collection_by_id(db=db, collectionId=collectionId)


def createCollection(
    db: Session, projectId: str, dto: CollectionCreate
) -> models.Collection:
    return collection_crud.create_collection(db=db, projectId=projectId, cc=dto)

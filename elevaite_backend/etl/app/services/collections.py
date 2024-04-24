import asyncio
from typing import List
from elevaitedb.db import models
from elevaitedb.util.func import to_kebab_case
from qdrant_client import AsyncQdrantClient
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


def getCollectionChunks(
    db: Session,
    collectionId: str,
    qdrant_client: AsyncQdrantClient,
    limit: int = 10,
    offset: str | None = None,
):
    _collection = collection_crud.get_collection_by_id(db=db, collectionId=collectionId)
    try:
        res = asyncio.run(
            qdrant_client.scroll(
                collection_name=to_kebab_case(_collection.name),
                with_vectors=True,
                limit=limit,
                offset=offset,
            )
        )
        return res
    except Exception as e:
        print(f"{type(e)} occured: {e}")
        return []

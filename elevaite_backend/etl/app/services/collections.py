import asyncio
from typing import List, Tuple, Optional, Callable, Type
from elevaitedb.db import models
from elevaitedb.util.func import to_kebab_case
from qdrant_client import AsyncQdrantClient
from qdrant_client.conversions import common_types as types
from qdrant_client.http.models import Distance, VectorParams
from sqlalchemy.orm import Session, Query
from elevaitedb.schemas.collection import Collection, CollectionCreate
from elevaitedb.crud import collection as collection_crud
from elevaitedb.util import func as util_func


def getCollectionsOfProject(
    db: Session,
    projectId: str,
    # filter_function: Callable[[Type[models.Base], Query], Query], # uncomment this when using validator
    skip: int = 0,
    limit: int = 100,
) -> List[models.Collection]:

    return collection_crud.get_collections(
        db=db,
        projectId=projectId,
        # filter_function=filter_function, # uncomment this when using validator 
        skip=skip,
        limit=limit,
    )


def getCollectionById(db: Session, collectionId: str) -> models.Collection:
    return collection_crud.get_collection_by_id(db=db, collectionId=collectionId)


async def createCollection(
    db: Session,
    projectId: str,
    dto: CollectionCreate,
    qdrant_client: AsyncQdrantClient,
) -> models.Collection:
    collection_name = util_func.to_kebab_case(dto.name)
    vector_params = VectorParams(size=dto.size, distance=dto.distance)
    await qdrant_client.create_collection(
        collection_name=collection_name, vectors_config=vector_params
    )
    return collection_crud.create_collection(db=db, projectId=projectId, cc=dto)


def getCollectionChunks(
    db: Session,
    collectionId: str,
    qdrant_client: AsyncQdrantClient,
    limit: int | None = 10,
    offset: str | None = None,
    with_vectors: bool | None = False,
    with_payload: bool | None = False,
) -> Tuple[List[types.Record], Optional[types.PointId]]:
    _collection = collection_crud.get_collection_by_id(db=db, collectionId=collectionId)
    if limit is None:
        limit = 10
    if with_vectors is None:
        with_vectors = False
    if with_payload is None:
        with_payload = True
    try:
        res = asyncio.run(
            qdrant_client.scroll(
                collection_name=to_kebab_case(_collection.name),
                with_vectors=with_vectors,
                with_payload=with_payload,
                limit=limit,
                offset=offset,
            )
        )
        return res
    except Exception as e:
        print(f"{type(e)} occured: {e}")
        return tuple()

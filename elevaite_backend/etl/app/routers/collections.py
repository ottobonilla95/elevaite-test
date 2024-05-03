from fastapi import APIRouter
from typing import Annotated, Any, List, Dict
from fastapi import APIRouter, Body, Depends
from sqlalchemy.orm import Session
from ..services import collections as collection_service
from .deps import get_db, get_qdrant_connection
from elevaitedb.schemas import collection as collection_schemas
from rbac_api import validators, rbac_instance
from elevaitedb.db import models
from qdrant_client.conversions import common_types as types

router = APIRouter(prefix="/project/{project_id}/collection", tags=["collections"])


@router.get("", response_model=list[collection_schemas.Collection])
def getCollectionsOfProject(
    project_id: str,
    db: Session = Depends(get_db),  # comment when using validator
    skip: int = 0,
    limit: int = 100,
    # validation_info:dict[str, Any] = Depends(validators.validate_get_project_collections_factory(models.Collection, ("READ",))),
):
    # db: Session = validation_info.get("db", None) # uncomment this when using validator

    # typenames = validation_info.get("target_entity_typename_combinations", tuple()) # uncomment this when using validator
    # typevalues = validation_info.get("target_entity_typevalue_combinations", tuple()) # uncomment this when using validator

    # filters_list: List[Dict[str, Any]] = rbac_instance.generate_post_validation_type_filters_for_all_query(models.Collection, typenames, typevalues, validation_info) # uncomment this when using validator

    return collection_service.getCollectionsOfProject(
        db=db,
        projectId=project_id,
        # filters_list=filters_list, # uncomment this when using validator
        skip=skip,
        limit=limit,
    )


@router.get("/{collection_id}", response_model=collection_schemas.Collection)
def getCollectionById(
    project_id: str,
    collection_id: str,
    db: Session = Depends(get_db),
    # validation_info:dict[str, Any] = Depends(validators.validate_get_project_collection_factory(models.Collection, ("READ",))), # uncomment this to use validator
):
    # collection = validation_info.get('Collection', None)  # uncomment this when using validator
    # return collection # uncomment this when using validator

    return collection_service.getCollectionById(
        db=db, collectionId=collection_id
    )  # comment this when using validator


@router.post("", response_model=collection_schemas.Collection)
async def createCollection(
    project_id: str,
    dto: Annotated[collection_schemas.CollectionCreate, Body()],
    qdrant_connection=Depends(get_qdrant_connection),
    db: Session = Depends(get_db),  # comment this when using validator
    # validation_info:dict[str, Any] = Depends(validators.validate_create_project_collection_factory(models.Collection, ("CREATE",))), # uncomment this to use validator
):
    # db: Session = validation_info.get("db", None) # uncomment this when using validator
    return await collection_service.createCollection(
        db=db, projectId=project_id, dto=dto, qdrant_client=qdrant_connection
    )


@router.get(
    "/{collection_id}/scroll",
    # response_model=collection_schemas.QdrantResponse,
)
def getCollectionScroll(
    project_id: str,
    collection_id: str,
    after: str | None = None,
    limit: int | None = None,
    with_vectors: bool | None = None,
    with_payload: bool | None = None,
    db: Session = Depends(get_db),
    qdrant_connection=Depends(get_qdrant_connection),
    # validation_info:dict[str, Any] = Depends(validators.validate_get_project_collection_factory(models.Collection, ("READ",))), # uncomment this to use validator
):
    # db: Session = validation_info.get("db", None) # uncomment this when using validator
    return collection_service.getCollectionChunks(
        db=db,
        collectionId=collection_id,
        qdrant_client=qdrant_connection,
        limit=limit,
        offset=after,
        with_payload=with_payload,
        with_vectors=with_vectors,
    )

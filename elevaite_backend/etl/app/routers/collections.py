from fastapi import APIRouter, Request, Header
from typing import Annotated, Type, Callable, Dict, List, Any, Optional
from fastapi import APIRouter, Body, Depends
from sqlalchemy.orm import Session, Query

from ..services import collections as collection_service
from .deps import get_db, get_qdrant_connection
from elevaitedb.schemas import (
    collection as collection_schemas,
    #    api as api_schemas,
)

# from rbac_api import (
#    route_validator_map,
#    RBACValidatorProvider
# )
# rbacValidator = RBACValidatorProvider.get_instance()
from elevaitedb.db import models
from qdrant_client.conversions import common_types as types

router = APIRouter(prefix="/project/{project_id}/collection", tags=["collections"])


@router.get("", response_model=list[collection_schemas.Collection])
def getCollectionsOfProject(
    # request: Request, #uncomment this when using validator
    project_id: str,
    db: Session = Depends(get_db),  # comment when using validator
    skip: int = 0,
    limit: int = 100,
    # validation_info:dict[str, Any] = Depends(route_validator_map[(api_schemas.APINamespace.ETL_API, 'getCollectionsOfProject')]), # uncomment this to use validator
):
    # db: Session = request.state.db # uncomment this when using validator
    # all_query_authorized_types_filter_function = rbacValidator.get_post_validation_types_filter_function_for_all_query(models.Collection, validation_info) # uncomment this when using validator

    return collection_service.getCollectionsOfProject(
        db=db,
        projectId=project_id,
        # filter_function=all_query_authorized_types_filter_function, # uncomment this when using validator
        skip=skip,
        limit=limit,
    )


@router.get("/{collection_id}", response_model=collection_schemas.Collection)
def getCollectionById(
    project_id: str,
    collection_id: str,
    db: Session = Depends(get_db),
    # validation_info:dict[str, Any] = Depends(route_validator_map[(api_schemas.APINamespace.ETL_API, 'getCollectionById')]), # uncomment this to use validator
):
    # collection = validation_info.get('Collection', None)  # uncomment this when using validator
    # return collection # uncomment this when using validator

    return collection_service.getCollectionById(
        db=db, collectionId=collection_id
    )  # comment this when using validator


@router.post("", response_model=collection_schemas.Collection)
async def createCollection(
    # request: Request, #uncomment when using validator
    project_id: str,
    dto: Annotated[collection_schemas.CollectionCreate, Body()],
    # validation_info:dict[str, Any] = Depends(route_validator_map[(api_schemas.APINamespace.ETL_API, 'createCollection')]), # uncomment this to use validator
    qdrant_connection=Depends(get_qdrant_connection),
    db: Session = Depends(get_db),  # comment this when using validator
):

    # db: Session = request.state.db # uncomment this when using validator
    return await collection_service.createCollection(
        db=db, projectId=project_id, dto=dto, qdrant_client=qdrant_connection
    )


@router.get(
    "/{collection_id}/scroll",
    # response_model=collection_schemas.QdrantResponse,
)
def getCollectionScroll(
    # request: Request, #uncomment when using validator
    project_id: str,
    collection_id: str,
    after: str | None = None,
    limit: int | None = None,
    with_vectors: bool | None = None,
    with_payload: bool | None = None,
    db: Session = Depends(get_db),
    # validation_info:dict[str, Any] = Depends(route_validator_map[(api_schemas.APINamespace.ETL_API, 'getCollectionScroll')]), # uncomment this to use validator
    qdrant_connection=Depends(get_qdrant_connection),
):
    # db: Session = request.state.db # uncomment this when using validator
    return collection_service.getCollectionChunks(
        db=db,
        collectionId=collection_id,
        qdrant_client=qdrant_connection,
        limit=limit,
        offset=after,
        with_payload=with_payload,
        with_vectors=with_vectors,
    )

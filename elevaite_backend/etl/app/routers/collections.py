from fastapi import APIRouter
from typing import Annotated, Any
from fastapi import APIRouter, Body, Depends
from sqlalchemy.orm import Session
from ..services import collections as collection_service
from .deps import get_db
from elevaitedb.schemas import collection as collection_schemas
from rbac_api import validators
from elevaitedb.db import models

router = APIRouter(prefix="/project/{project_id}/collection", tags=["collections"])


@router.get("", response_model=list[collection_schemas.Collection])
def getCollectionsOfProject(
    project_id: str,
    db: Session = Depends(get_db),
    skip: int = 0, 
    limit: int = 100,
    # validation_info:dict[str, Any] = Depends(validators.validate_get_project_collections_factory(models.Collection, ("READ",))),
):
    # db: Session = validation_info.get("db", None)
    return collection_service.getCollectionsOfProject(
        db=db, projectId=project_id, skip=skip, limit=limit
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

    return collection_service.getCollectionById(db=db, collectionId=collection_id) # comment this when using validator


@router.post("", response_model=collection_schemas.Collection)
def createCollection(
    project_id: str,
    dto: Annotated[collection_schemas.CollectionCreate, Body()],
    db: Session = Depends(get_db), # comment this when using validator
    # validation_info:dict[str, Any] = Depends(validators.validate_create_project_collection_factory(models.Collection, ("CREATE",))), # uncomment this to use validator
):
    # db: Session = validation_info.get("db", None) # uncomment this when using validator
    return collection_service.createCollection(db=db, projectId=project_id, dto=dto)

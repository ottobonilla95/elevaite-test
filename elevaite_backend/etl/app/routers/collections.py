from fastapi import APIRouter
from typing import Annotated
from fastapi import APIRouter, Body, Depends
from sqlalchemy.orm import Session
from app.services import collections as collection_service
from app.routers.deps import get_db
from elevaitedb.schemas import collection as collection_schemas


router = APIRouter(prefix="/project/{project_id}/collection", tags=["collections"])


@router.get("", response_model=list[collection_schemas.Collection])
def getCollectionsOfProject(
    project_id: str, db: Session = Depends(get_db), skip: int = 0, limit: int = 100
):
    return collection_service.getCollectionsOfProject(
        db=db, projectId=project_id, skip=skip, limit=limit
    )


@router.get("/{collection_id}", response_model=collection_schemas.Collection)
def getCollectionById(
    project_id: str, collection_id: str, db: Session = Depends(get_db)
):
    return collection_service.getCollectionById(db=db, collectionId=collection_id)


@router.post("", response_model=collection_schemas.Collection)
def createCollection(
    project_id: str,
    dto: Annotated[collection_schemas.CollectionCreate, Body()],
    db: Session = Depends(get_db),
):
    return collection_service.createCollection(db=db, projectId=project_id, dto=dto)

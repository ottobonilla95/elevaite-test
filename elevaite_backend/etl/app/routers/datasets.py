from typing import Annotated
from fastapi import APIRouter, Body, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from ..services import datasets as dataset_service
from .deps import get_db
from elevaitedb.schemas import (
    dataset as dataset_schemas,
)


router = APIRouter(prefix="/project/{project_id}/datasets", tags=["datasets"])


@router.get("", response_model=list[dataset_schemas.Dataset])
def getProjectDatasets(
    project_id: str, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)
):
    return dataset_service.get_datasets_of_project(
        db=db, projectId=project_id, skip=skip, limit=limit
    )


@router.get("/{dataset_id}", response_model=dataset_schemas.Dataset)
def getDatasetById(project_id: str, dataset_id: str, db: Session = Depends(get_db)):
    return dataset_service.get_dataset_by_id(db=db, datasetId=dataset_id)


class AddTagToDatasetDto(BaseModel):
    tagId: str


@router.post("/{dataset_id}/tags", response_model=dataset_schemas.Dataset)
def addTagToDataset(
    project_id: str,
    dataset_id: str,
    dto: Annotated[AddTagToDatasetDto, Body()],
    db: Session = Depends(get_db),
):
    return dataset_service.add_tag_to_dataset(
        db=db, datasetId=dataset_id, tagId=dto.tagId
    )

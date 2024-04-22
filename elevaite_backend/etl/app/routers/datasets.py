from pprint import pprint
from typing import Annotated, Any
from fastapi import APIRouter, Body, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from ..services import datasets as dataset_service
from .deps import get_db
from elevaitedb.schemas import (
    dataset as dataset_schemas,
)
from rbac_api import validators
from elevaitedb.db import models
router = APIRouter(prefix="/project/{project_id}/datasets", tags=["datasets"])


@router.get("", response_model=list[dataset_schemas.Dataset])
def getProjectDatasets(
    project_id: str,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db), # comment this when using validator
    # validation_info:dict[str, Any] = Depends(validators.validate_get_project_datasets_factory(models.Dataset, ("READ",))), # uncomment this to use validator
):
    # db: Session = validation_info.get("db", None) # comment this when using validator
    return dataset_service.get_datasets_of_project(
        db=db, projectId=project_id, skip=skip, limit=limit
    )


@router.get("/{dataset_id}", response_model=dataset_schemas.Dataset)
def getDatasetById(
    project_id: str,
    dataset_id: str,
    db: Session = Depends(get_db), # comment this when using validator
    # validation_info:dict[str, Any] = Depends(validators.validate_get_project_dataset_factory(models.Dataset, ("READ",))), # uncomment this to use validator
):
    # dataset = validation_info.get('Dataset', None) # uncomment this when using validator
    # return dataset # uncomment this when using validator

    return dataset_service.get_dataset_by_id(db=db, datasetId=dataset_id) # comment this when using validator


class AddTagToDatasetDto(BaseModel):
    tagId: str


@router.post("/{dataset_id}/tags", response_model=dataset_schemas.Dataset)
def addTagToDataset(
    project_id: str,
    dataset_id: str,
    dto: Annotated[AddTagToDatasetDto, Body()],
    db: Session = Depends(get_db), # comment this when using validator
    # validation_info:dict[str, Any] = Depends(validators.validate_get_project_dataset_factory(models.Dataset, ("TAG",))), # uncomment this when using validator
):
    # db: Session = validation_info.get("db", None) # uncomment this when using validator
    return dataset_service.add_tag_to_dataset(
        db=db, datasetId=dataset_id, tagId=dto.tagId
    )

from pprint import pprint
import uuid
from typing import Annotated, Any, Dict, List, Type, Callable, Optional
from fastapi import APIRouter, Body, Depends, Request, Header
from pydantic import BaseModel
from sqlalchemy.orm import Session, Query
from ..services import datasets as dataset_service
from .deps import get_db
from elevaitedb.schemas import (
    dataset as dataset_schemas,
)
# from rbac_api import (
#    routes_to_middleware_imple_map,
#    RBACProvider
# )
from elevaitedb.db import models
router = APIRouter(prefix="/project/{project_id}/datasets", tags=["datasets"])


@router.get("", response_model=list[dataset_schemas.Dataset])
def getProjectDatasets(
    # request: Request, #uncomment when using validator
    project_id: str,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db), # comment this when using validator
    # validation_info:dict[str, Any] = Depends(routes_to_middleware_imple_map['getProjectDatasets']), # uncomment this to use validator
):
    # db: Session = request.state.db # uncomment this when using validator
    # all_query_authorized_types_filter_function = RBACProvider.get_instance().get_post_validation_types_filter_function_for_all_query(models.Dataset, validation_info) # uncomment this when using validator

    return dataset_service.get_datasets_of_project(
        db=db, 
        projectId=project_id,
        # filter_function=all_query_authorized_types_filter_function, # uncomment this when using validator
        skip=skip,
        limit=limit
    )


@router.get("/{dataset_id}", response_model=dataset_schemas.Dataset)
def getDatasetById(
    project_id: str,
    dataset_id: str,
    db: Session = Depends(get_db), # comment this when using validator
    # validation_info:dict[str, Any] = Depends(routes_to_middleware_imple_map['getDatasetById']), # uncomment this to use validator
):
    # dataset = validation_info.get('Dataset', None) # uncomment this when using validator
    # return dataset # uncomment this when using validator

    return dataset_service.get_dataset_by_id(db=db, datasetId=dataset_id) # comment this when using validator


class AddTagToDatasetDto(BaseModel):
    tagId: str


@router.post("/{dataset_id}/tags", response_model=dataset_schemas.Dataset)
def addTagToDataset(
    # request: Request, #uncomment when using validator
    project_id: str,
    dataset_id: str,
    dto: Annotated[AddTagToDatasetDto, Body()],
    db: Session = Depends(get_db), # comment this when using validator
    # validation_info:dict[str, Any] = Depends(routes_to_middleware_imple_map['addTagToDataset']), # uncomment this when using validator
):
    # db: Session = request.state.db # uncomment this when using validator
    return dataset_service.add_tag_to_dataset(
        db=db, datasetId=dataset_id, tagId=dto.tagId
    )

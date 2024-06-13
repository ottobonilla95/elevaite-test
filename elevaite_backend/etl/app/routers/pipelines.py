from pprint import pprint
from typing import Annotated, Any, List, Dict, Sequence, Type, Callable, Optional
from fastapi import APIRouter, Body, Depends, Request, Header
from sqlalchemy import UUID
from sqlalchemy.orm import Session, Query
from ..services import (
    configurations as conf_service,
    instances as instance_service,
    pipelines as pipeline_service,
)
from .deps import get_db
from elevaitelib.orm.db import models
from elevaitelib.schemas import (
    configuration as configuration_schemas,
    instance as instance_schemas,
    pipeline as pipeline_schemas,
)

from rbac_api import route_validator_map, RBACValidatorProvider

router = APIRouter(prefix="/pipeline", tags=["pipelines"])


@router.get("", response_model=list[pipeline_schemas.Pipeline])
def getPipelines(skip: int = 0, limit: int = 10, db=Depends(get_db)):
    return pipeline_service.getPipelines(db=db, skip=skip, limit=limit)


@router.post("", response_model=pipeline_schemas.Pipeline)
def registerFlytePipeline(
    createPipelineDto: Annotated[pipeline_schemas.PipelineCreate, Body()],
    db: Session = Depends(get_db),
):
    return pipeline_service.createPipeline(db=db, dto=createPipelineDto)


@router.get(
    "/{pipeline_id}/configuration",
    response_model=list[configuration_schemas.Configuration],
)
def getPipelineConfigurations(
    # request: Request, #uncomment when using validator
    pipeline_id: str,
    db: Session = Depends(get_db),  # comment this when using validator
    # validation_info:dict[str, Any] = Depends(routes_to_middleware_imple_map['getApplicationConfigurations']), # uncomment this to use validator
):

    # db: Session = request.state.db # uncomment this when using validator
    # all_query_authorized_types_filter_function = RBACProvider.get_instance().get_post_validation_types_filter_function_for_all_query(models.Configuration, validation_info) # uncomment this when using validator

    return conf_service.getConfigurationsOfPipeline(
        db=db,
        # filter_function=all_query_authorized_types_filter_function, # uncomment this when using validator
        pipeline_id=pipeline_id,
    )


@router.get("/{pipeline_id}/instance", response_model=list[instance_schemas.Instance])
def getPipelineInstances(
    # request: Request,
    pipeline_id: str,
    db=Depends(get_db),
    # validation_info: dict[str, Any] = Depends(
    #     routes_to_middleware_imple_map["getInstancesOfPipeline"]
    # ),
    # project_id: UUID = Header(
    #     ...,
    #     alias="X-elevAIte-ProjectId",
    #     description="project_id under which connector instances are queried",
    # ),
) -> Sequence[instance_schemas.Instance]:

    # db: Session = request.state.db
    # all_query_authorized_types_filter_function = RBACProvider.get_instance().get_post_validation_types_filter_function_for_all_query(
    #     models.Instance, validation_info
    # )

    return instance_service.getInstancesOfPipeline(
        db=db,
        pipeline_id=pipeline_id,
        # project_id=project_id,
        # filter_function=all_query_authorized_types_filter_function,
    )

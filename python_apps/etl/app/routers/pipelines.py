from typing import Annotated, Any, Sequence
from fastapi import APIRouter, Body, Depends, Request, Header
from uuid import UUID
from sqlalchemy.orm import Session

from .deps import get_db
from ..services import (
    configurations as conf_service,
    instances as instance_service,
    pipelines as pipeline_service,
)
from elevaitelib.orm.db import models
from elevaitelib.schemas import (
    configuration as configuration_schemas,
    instance as instance_schemas,
    pipeline as pipeline_schemas,
    api as api_schemas,
)
from rbac_sdk.fastapi_helpers import require_permission, resource_builders

# Guard: require project-level view permission via RBAC service
_guard_view_project = require_permission(
    action="view_project",
    resource_builder=resource_builders.project_from_headers(),
)


# from rbac_lib import route_validator_map, RBACValidatorProvider

# rbacValidator = RBACValidatorProvider.get_instance()

# router = APIRouter(prefix="/pipeline", tags=["pipelines"])


@router.get("", response_model=list[pipeline_schemas.Pipeline], dependencies=[Depends(_guard_view_project)])
def getPipelines(
    request: Request,  # uncomment this when using validator
    skip: int = 0,
    limit: int = 10,
    db=Depends(get_db),
    # validation_info: dict[str, Any] = Depends(route_validator_map[(api_schemas.APINamespace.ETL_API, "getPipelines")]),
):
    # db: Session = request.state.db  # uncomment this when using validator
    # all_query_authorized_types_filter_function = rbacValidator.get_post_validation_types_filter_function_for_all_query(
    # models.Pipeline, validation_info
    # )  # uncomment this when using validator
    return pipeline_service.getPipelinesOfProject(
        db=db,
        skip=skip,
        limit=limit,
        # filter_function=all_query_authorized_types_filter_function,
        filter_function=None,
    )


@router.get("/{pipeline_id}", response_model=pipeline_schemas.Pipeline)
def getPipelineById(
    request: Request,  # uncomment this when using validator
    pipeline_id: str,
    db=Depends(get_db),
    # validation_info: dict[str, Any] = Depends(route_validator_map[(api_schemas.APINamespace.ETL_API, "getPipelineById")]),
):
    # db: Session = request.state.db  # uncomment this when using validator
    # print(validation_info)
    # all_query_authorized_types_filter_function = rbacValidator.get_post_validation_types_filter_function_for_all_query(
    # models.Collection, validation_info
    # )  # uncomment this when using validator
    return pipeline_service.getPipelineById(
        db=db,
        id=pipeline_id,
        # filter_function=all_query_authorized_types_filter_function,
        filter_function=None,
    )


# @router.post("", response_model=pipeline_schemas.Pipeline)
# def registerFlytePipeline(
#     request: Request,  # uncomment when using validator
#     createPipelineDto: Annotated[pipeline_schemas.PipelineCreate, Body()],
#     # db: Session = Depends(get_db),
#     validation_info: dict[str, Any] = Depends(
#         route_validator_map[(api_schemas.APINamespace.ETL_API, "registerFlytePipeline")]
#     ),  # uncomment this to use validator
# ):
#     db = request.state.db
#     return pipeline_service.createPipeline(db=db, dto=createPipelineDto)


@router.get(
    "/{pipeline_id}/configuration",
    response_model=list[configuration_schemas.Configuration],
)
def getPipelineConfigurations(
    request: Request,  # uncomment when using validator
    pipeline_id: str,
    # db: Session = Depends(get_db),  # comment this when using validator
    validation_info: dict[str, Any] = Depends(
        route_validator_map[(api_schemas.APINamespace.ETL_API, "getPipelineConfigurations")]
    ),  # uncomment this to use validator
):
    db: Session = request.state.db  # uncomment this when using validator
    all_query_authorized_types_filter_function = rbacValidator.get_post_validation_types_filter_function_for_all_query(
        models.Configuration, validation_info
    )  # uncomment this when using validator


#     return conf_service.getConfigurationsOfPipeline(
#         db=db,
#         filter_function=all_query_authorized_types_filter_function,  # uncomment this when using validator
#         pipeline_id=pipeline_id,
#     )


@router.get("/{pipeline_id}/instance", response_model=list[instance_schemas.Instance])
def getPipelineInstances(
    request: Request,
    pipeline_id: str,
    # db=Depends(get_db),
    validation_info: dict[str, Any] = Depends(route_validator_map[(api_schemas.APINamespace.ETL_API, "getPipelineInstances")]),
    project_id: UUID = Header(
        ...,
        alias="X-elevAIte-ProjectId",
        description="project_id under which connector instances are queried",
    ),
) -> Sequence[instance_schemas.Instance]:
    db: Session = request.state.db
    all_query_authorized_types_filter_function = rbacValidator.get_post_validation_types_filter_function_for_all_query(
        models.Instance, validation_info
    )


#     return instance_service.getInstancesOfPipeline(
#         db=db,
#         pipeline_id=pipeline_id,
#         project_id=project_id,
#         filter_function=all_query_authorized_types_filter_function,
#     )

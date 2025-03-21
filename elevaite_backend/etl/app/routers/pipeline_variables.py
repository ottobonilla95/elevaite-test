from typing import Annotated
from elevaitelib.schemas import pipeline as pipeline_schemas
from fastapi import APIRouter, Body, Depends
# from rbac_api import RBACValidatorProvider

from ..services import pipeline_variables as service
from .deps import get_db

# rbacValidator = RBACValidatorProvider.get_instance()

router = APIRouter(prefix="/pipeline/var", tags=["pipeline variables"])


@router.get("", response_model=list[pipeline_schemas.PipelineVariable])
def getPipelineVariables(
    skip: int = 0,
    limit: int = 10,
    db=Depends(get_db),
):
    return service.getPipelineVariables(db=db, filter_function=None, limit=limit, skip=skip)


@router.post("", response_model=pipeline_schemas.PipelineVariable)
def createPipelineVariable(
    dto: Annotated[pipeline_schemas.PipelineVariableCreate, Body()], db=Depends(get_db)
) -> pipeline_schemas.PipelineVariable:
    return service.createPipelineVariable(db=db, dto=dto)


@router.put("{var_id}", response_model=pipeline_schemas.PipelineVariable)
def updatePipelineVariable(
    var_id: str, dto: Annotated[pipeline_schemas.PipelineVariableUpdate, Body()], db=Depends(get_db)
) -> pipeline_schemas.PipelineVariable:
    return service.updatePipelineVariable(db=db, dto=dto, id=var_id)


@router.delete("{var_id}", response_model=pipeline_schemas.PipelineVariable)
def deletePipelineVariable(var_id: str, db=Depends(get_db)) -> pipeline_schemas.PipelineVariable:
    return service.deletePipelineVariable(db=db, id=var_id)

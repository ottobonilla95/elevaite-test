from typing import Callable, List, Union

from elevaitelib.orm.crud import pipeline as pipeline_crud
from elevaitelib.orm.db import models
from elevaitelib.schemas.pipeline import PipelineVariableCreate, PipelineVariableUpdate
from sqlalchemy.orm import Query, Session


def getPipelineVariables(
    db: Session,
    filter_function: Union[Callable[[Query], Query], None],
    skip: int = 0,
    limit: int = 10,
) -> List[models.PipelineVariable]:
    return pipeline_crud.get_pipeline_variables(db=db, filter_function=filter_function, limit=limit, skip=skip)


def createPipelineVariable(db: Session, dto: PipelineVariableCreate) -> models.PipelineVariable:
    return pipeline_crud.create_pipeline_variable(db=db, dto=dto)


def updatePipelineVariable(db: Session, id: str, dto: PipelineVariableUpdate) -> models.PipelineVariable:
    return pipeline_crud.update_pipeline_variable(db=db, dto=dto, variable_id=id)


def deletePipelineVariable(db: Session, id: str) -> models.PipelineVariable:
    return pipeline_crud.delete_pipeline_variable(db=db, variable_id=id)

from enum import Enum
from typing import Any, TypeGuard

from pydantic import UUID4, BaseModel


class PipelineStepStatus(str, Enum):
    IDLE = "idle"
    RUNNING = "running"
    FAILED = "failed"
    COMPLETED = "completed"


class PipelineStepDataBase(BaseModel):
    stepId: UUID4
    title: str
    value: str


class PipelineStepDataCreate(PipelineStepDataBase):
    pass


class PipelineStepData(PipelineStepDataBase):
    pass

    class Config:
        orm_mode = True


class PipelineStepBase(BaseModel):
    previousStepIds: list[UUID4]
    nextStepIds: list[UUID4]
    title: str
    data: list[PipelineStepDataBase]


class PipelineStepCreate(PipelineStepBase):
    pass


class PipelineStep(PipelineStepBase):
    id: UUID4
    pipelineId: UUID4

    class Config:
        orm_mode = True


class PipelineBase(BaseModel):
    steps: list[PipelineStep]
    entry: UUID4
    exit: UUID4
    label: str


class PipelineCreate(PipelineBase):
    pass


class Pipeline(PipelineBase):
    id: UUID4

    class Config:
        orm_mode = True


def is_pipeline(var: Any) -> TypeGuard[Pipeline]:
    return var is not None and var.id is not None

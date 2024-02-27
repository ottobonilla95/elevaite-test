from enum import Enum
from typing import TypeGuard

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


class PipelineStepBase(BaseModel):
    dependsOn: list[str]
    title: str
    data: list[PipelineStepDataBase]


class PipelineStepCreate(PipelineStepBase):
    pass


class PipelineStep(PipelineStepBase):
    id: UUID4
    pipelineId: UUID4


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


def is_pipeline(var: object) -> TypeGuard[Pipeline]:
    return var is not None and var.id is not None

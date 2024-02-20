from enum import Enum
from typing import TypeGuard

from pydantic import BaseModel


class PipelineStepStatus(str, Enum):
    IDLE = "idle"
    RUNNING = "running"
    FAILED = "failed"
    COMPLETED = "completed"


class PipelineStepDataBase(BaseModel):
    stepId: str
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
    id: str


class PipelineBase(BaseModel):
    steps: list[PipelineStep]
    entry: str
    label: str


class PipelineCreate(PipelineBase):
    pass


class Pipeline(PipelineBase):
    id: str


def is_pipeline(var: object) -> TypeGuard[Pipeline]:
    return var is not None and var["id"] is not None

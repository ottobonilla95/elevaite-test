from enum import Enum
from typing import Any, List, TypeGuard

from pydantic import UUID4, BaseModel


class PipelineStepStatus(str, Enum):
    IDLE = "idle"
    RUNNING = "running"
    FAILED = "failed"
    COMPLETED = "completed"


class PipelineTaskType(str, Enum):
    PYSCRIPT = "pyscript"
    JUPYTER = "jupyternotebook"


class PipelineVariableBase(BaseModel):
    name: str
    var_type: str


class PipelineVariableCreate(PipelineVariableBase):
    pass


class PipelineVariable(PipelineVariableBase):
    pass

    class Config:
        orm_mode = True


class PipelineScheduleBase(BaseModel):
    frequency: str
    time: str


class PipelineScheduleCreate(PipelineScheduleBase):
    pass


class PipelineSchedule(PipelineScheduleBase):
    pass

    class Config:
        orm_mode = True


class PipelineTaskBase(BaseModel):
    name: str
    task_type: PipelineTaskType
    src: str


class PipelineTaskCreate(PipelineTaskBase):
    pass


class PipelineTask(PipelineTaskBase):
    id: UUID4
    dependencies: List["PipelineTask"]
    input: List["PipelineVariable"]

    class Config:
        orm_mode = True


class PipelineBase(BaseModel):
    name: str
    description: str
    entrypoint: str


class PipelineCreate(PipelineBase):
    pass


class Pipeline(PipelineBase):
    id: UUID4
    tasks: List[PipelineTask]
    schedule: PipelineSchedule

    class Config:
        orm_mode = True


def is_pipeline(var: Any) -> TypeGuard[Pipeline]:
    return var is not None and var.id is not None

from enum import Enum
from typing import Any, Dict, List, Optional, TypeGuard

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


class PipelineVariableUpdate(BaseModel):
    name: Optional[str] = None
    var_type: Optional[str] = None


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
    config: Dict[str, Any]


class PipelineTaskCreate(PipelineTaskBase):
    pass


class PipelineTaskUpdate(PipelineTaskBase):
    dependencies: List["PipelineTask"]
    input: List["PipelineVariable"]
    output: List["PipelineVariable"]


class PipelineTask(PipelineTaskBase):
    id: UUID4
    dependencies: List["PipelineTask"]
    input: List["PipelineVariable"]
    output: List["PipelineVariable"]

    class Config:
        orm_mode = True


class PipelineTaskDependency(BaseModel):
    task_id: str


class PipelineSource(Enum):
    ELEVAITE = "elevaite"
    EXPERIMENT = "experiment"


class PipelineBase(BaseModel):
    name: str
    description: str
    entrypoint: str


class PipelineCreate(PipelineBase):
    pass


class PipelineUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    entrypoint: Optional[str] = None


class Pipeline(PipelineBase):
    id: UUID4
    tasks: List[PipelineTask]
    schedule: PipelineSchedule

    class Config:
        orm_mode = True


def is_pipeline(var: Any) -> TypeGuard[Pipeline]:
    return var is not None and var.id is not None

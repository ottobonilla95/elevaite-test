from enum import Enum
from typing import TypeGuard, Union

from pydantic import UUID4, BaseModel

from .pipeline import PipelineStepStatus
from .configuration import Configuration


class InstanceStatus(str, Enum):
    STARTING = "starting"
    RUNNING = "running"
    FAILED = "failed"
    COMPLETED = "completed"


class InstanceStepDataLabel(str, Enum):
    CURR_DOC = "CURR_DOC"
    AVG_CHUNK_SIZE = "AVG_CHUNK_SIZE"
    LRGST_CHUNK_SIZE = "LRGST_CHUNK_SIZE"
    AVG_TOKEN_SIZE = "AVG_TOKEN_SIZE"
    LRGST_TOKEN_SIZE = "LRGST_TOKEN_SIZE"


class InstanceBase(BaseModel):
    creator: str
    name: str
    comment: Union[str, None]
    startTime: Union[str, None]
    endTime: Union[str, None]
    status: InstanceStatus
    datasetId: UUID4
    projectId: UUID4
    selectedPipelineId: UUID4
    configurationId: UUID4
    applicationId: int
    configurationRaw: str


class InstanceChartData(BaseModel):
    totalItems: int
    ingestedItems: int
    avgSize: int
    totalSize: int
    ingestedSize: int
    ingestedChunks: int

    class Config:
        orm_mode = True


class InstancePipelineStepStatus(BaseModel):
    instanceId: UUID4
    stepId: UUID4
    status: PipelineStepStatus
    startTime: Union[str, None]
    endTime: Union[str, None]

    class Config:
        orm_mode = True


class InstancePipelineStepData(BaseModel):
    label: InstanceStepDataLabel
    value: str | int


class InstancePipelineStepStatusUpdate(BaseModel):
    status: PipelineStepStatus | None = None
    startTime: str | None = None
    endTime: str | None = None


class InstanceCreate(InstanceBase):
    pass


class InstanceCreateDTO(BaseModel):
    creator: str
    configurationId: UUID4
    projectId: UUID4
    selectedPipelineId: UUID4
    instanceName: str


class InstanceUpdate(BaseModel):
    comment: Union[str, None] = None
    endTime: Union[str, None] = None
    status: Union[InstanceStatus, None] = None


class Instance(InstanceBase):
    id: UUID4
    chartData: InstanceChartData
    pipelineStepStatuses: list[InstancePipelineStepStatus]
    configuration: Configuration

    class Config:
        orm_mode = True


def is_instance(var: object) -> TypeGuard[Instance]:
    return var is not None and var.id and var.status

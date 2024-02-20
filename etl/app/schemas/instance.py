from enum import Enum
from typing import TypeGuard, Union

from pydantic import BaseModel

from app.schemas.pipeline import PipelineStepStatus


class InstanceStatus(str, Enum):
    STARTING = "starting"
    RUNNING = "running"
    FAILED = "failed"
    COMPLETED = "completed"


class InstanceBase(BaseModel):
    creator: str
    name: str
    comment: Union[str, None]
    startTime: Union[str, None]
    endTime: Union[str, None]
    status: InstanceStatus
    datasetId: Union[str, None]
    selectedPipelineId: Union[str, None]
    applicationId: Union[str, None]


class InstanceChartData(BaseModel):
    totalItems: int
    ingestedItems: int
    avgSize: int
    totalSize: int
    ingestedSize: int
    ingestedChunks: int


class InstancePipelineStepStatus(BaseModel):
    instanceId: str
    stepId: str
    status: PipelineStepStatus
    startTime: Union[str, None]
    endTime: Union[str, None]


class InstancePipelineStepStatusUpdate(BaseModel):
    status: PipelineStepStatus | None = None
    startTime: str | None = None
    endTime: str | None = None


class InstanceCreate(InstanceBase):
    pass


class InstanceUpdate(BaseModel):
    comment: Union[str, None] = None
    endTime: Union[str, None] = None
    status: Union[InstanceStatus, None] = None


class Instance(InstanceBase):
    id: str
    chartData: InstanceChartData
    pipelineStepStatuses: list[InstancePipelineStepStatus]


def is_instance(var: object) -> TypeGuard[Instance]:
    return var is not None and var["id"]

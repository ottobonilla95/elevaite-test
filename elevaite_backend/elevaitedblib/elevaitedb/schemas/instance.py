from enum import Enum
from typing import Any, Dict, List, TypeGuard, Union

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
    TOTAL_CHUNK_SIZE = "TOTAL_CHUNK_SIZE"
    AVG_TOKEN_SIZE = "AVG_TOKEN_SIZE"
    LRGST_TOKEN_SIZE = "LRGST_TOKEN_SIZE"
    REPO_NAME = "REPO_NAME"
    DATASET_VERSION = "DATASET_VERSION"
    INGEST_DATE = "INGEST_DATE"
    TOTAL_FILES_INGESTED = "TOTAL_FILES_INGESTED"
    TOTAL_SEGMENTS_TOKENIZED = "TOTAL_SEGMENTS_TOKENIZED"
    EMB_MODEL = "EMB_MODEL"
    EMB_MODEL_DIM = "EMB_MODEL_DIM"
    TOTAL_FILES_TOKENIZED = "TOTAL_FILES_TOKENIZED"


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
    avgChunk: Union[str, None] = None
    largestChunk: Union[str, None] = None
    currentDoc: Union[str, None] = None

    class Config:
        orm_mode = True


class InstancePipelineStepData(BaseModel):
    label: InstanceStepDataLabel
    value: str | int


class InstancePipelineStepStatus(BaseModel):
    instanceId: UUID4
    stepId: UUID4
    status: PipelineStepStatus
    startTime: Union[str, None]
    endTime: Union[str, None]
    meta: List[InstancePipelineStepData] = []

    class Config:
        orm_mode = True


class InstancePipelineStepStatusUpdate(BaseModel):
    status: PipelineStepStatus | None = None
    startTime: str | None = None
    endTime: str | None = None
    meta: List[InstancePipelineStepData] = []


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


class LogLevel(str, Enum):
    INFO = "info"
    ERROR = "error"


class InstanceLogs(BaseModel):
    timestamp: str
    message: str
    level: LogLevel


def is_instance(var: Any) -> TypeGuard[Instance]:
    return var is not None and var.id and var.status

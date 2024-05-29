from enum import Enum
from typing import Any, Dict, List, Union
from pydantic import BaseModel


class RPCResponse(BaseModel):
    response: Union[str, bool, int, Dict[str, Any], None]


class InstanceTaskDataLabel(str, Enum):
    CURR_DOC = "CURR_DOC"
    AVG_CHUNK_SIZE = "AVG_CHUNK_SIZE"
    LRGST_CHUNK_SIZE = "LRGST_CHUNK_SIZE"
    TOTAL_CHUNK_SIZE = "TOTAL_CHUNK_SIZE"
    AVG_TOKEN_SIZE = "AVG_TOKEN_SIZE"
    LRGST_TOKEN_SIZE = "LRGST_TOKEN_SIZE"
    MIN_TOKEN_SIZE = "MIN_TOKEN_SIZE"
    REPO_NAME = "REPO_NAME"
    DATASET_VERSION = "DATASET_VERSION"
    INGEST_DATE = "INGEST_DATE"
    TOTAL_FILES_INGESTED = "TOTAL_FILES_INGESTED"
    TOTAL_SEGMENTS_TOKENIZED = "TOTAL_SEGMENTS_TOKENIZED"
    EMB_MODEL = "EMB_MODEL"
    EMB_MODEL_DIM = "EMB_MODEL_DIM"
    TOTAL_FILES_TOKENIZED = "TOTAL_FILES_TOKENIZED"


class InstanceTaskData(BaseModel):
    label: InstanceTaskDataLabel
    value: str | int


class SetRedisStatsInput(BaseModel):
    instance_id: str
    count: int
    avg_size: float
    size: int


class SetRedisValueInput(BaseModel):
    name: str
    path: str
    obj: Union[str, int, float, bool, None, Dict[str, Any], List[Any]]


class InstanceStatusInput(BaseModel):
    application_id: int
    instance_id: str


class InstanceStepMetaInput(BaseModel):
    instance_id: str
    step_id: str
    meta: List[InstanceTaskData]


class PipelineStepStatusInput(BaseModel):
    instance_id: str
    step_id: str


class MaxDatasetVersionInput(BaseModel):
    dataset_id: str


class CreateDatasetVersionInput(BaseModel):
    dataset_id: str
    ref_id: str
    version: int


class SetInstanceChartDataInput(BaseModel):
    instance_id: str


class RepoNameInput(BaseModel):
    project_id: str
    dataset_id: str


class LogInfo(BaseModel):
    msg: str
    key: str


class DatasetCurrVersionInput(BaseModel):
    dataset_id: str

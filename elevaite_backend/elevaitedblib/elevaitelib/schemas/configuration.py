from datetime import datetime
from enum import Enum
from typing import Any, List, Optional, TypeGuard
from .service_now import ServiceNowIngestBody, ServiceNowTicket
from pydantic import UUID4, BaseModel, Json


class EmbeddingType(str, Enum):
    OPENAI = "openai"
    LOCAL = "local"
    EXTERNAL = "external"


class PreprocessEmbeddingInfo(BaseModel):
    type: EmbeddingType
    inference_url: Optional[str]
    name: str
    dimensions: int


class BaseDatasetInformationForm(BaseModel):
    creator: str
    datasetName: str | None
    projectId: str
    version: str | None
    parent: str | None
    datasetId: str | None
    selectedPipelineId: str


class S3IngestFormDataDTO(BaseDatasetInformationForm):
    type: str = "ingest"
    description: str | None
    url: str
    useEC2: bool
    roleARN: str


class PreProcessFormDTO(BaseDatasetInformationForm):
    type: str = "preprocess"
    datasetVersion: int | None
    collectionId: str | None
    embedding_info: Optional[PreprocessEmbeddingInfo]
    queue: str
    maxIdleTime: str


class ServiceNowIngestDataDTO(BaseDatasetInformationForm):
    type: str = "service-now"
    tickets: List[ServiceNowTicket]


class ConfigurationBase(BaseModel):
    pipelineId: str
    datasetId: str
    raw: Json
    name: str
    isTemplate: bool


class ConfigurationCreate(ConfigurationBase):
    pass


class ConfigurationUpdate(BaseModel):
    raw: S3IngestFormDataDTO | PreProcessFormDTO | str | None
    name: str | None
    isTemplate: bool | None


class Configuration(ConfigurationBase):
    id: UUID4
    createDate: datetime
    updateDate: datetime | None

    class Config:
        orm_mode = True


def is_configuration(var: Any) -> TypeGuard[Configuration]:
    return var is not None and var.id

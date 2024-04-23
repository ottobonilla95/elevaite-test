from datetime import datetime
from typing import Any, TypeGuard
from pydantic import UUID4, BaseModel, Json


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
    queue: str
    maxIdleTime: str


class ConfigurationBase(BaseModel):
    applicationId: int
    raw: S3IngestFormDataDTO | PreProcessFormDTO
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

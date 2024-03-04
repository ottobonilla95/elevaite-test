from typing import TypeGuard
from pydantic import UUID4, BaseModel, Json


class BaseDatasetInformationForm(BaseModel):
    creator: str
    name: str
    projectId: str
    version: str | None
    parent: str | None
    outputURI: str | None
    datasetId: str | None
    selectedPipelineId: str


class S3IngestFormDataDTO(BaseDatasetInformationForm):
    connectionName: str
    description: str | None
    url: str
    useEC2: bool
    roleARN: str


class PreProcessFormDTO(BaseDatasetInformationForm):
    datasetVersion: str | None
    queue: str
    maxIdleTime: str


class ConfigurationBase(BaseModel):
    instanceId: UUID4
    applicationId: int
    raw: S3IngestFormDataDTO | PreProcessFormDTO | str


class ConfigurationCreate(ConfigurationBase):
    pass


class Configuration(ConfigurationBase):
    id: UUID4

    class Config:
        orm_mode = True


def is_configuration(var: object) -> TypeGuard[Configuration]:
    return var is not None and var.id

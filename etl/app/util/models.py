from pydantic import BaseModel


class BaseDatasetInformationForm(BaseModel):
    creator: str
    name: str
    projectId: str | None
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
    datasetName: str
    datasetProject: str
    datasetVersion: str | None
    queue: str
    maxIdleTime: str

from enum import Enum
from typing import Union
from pydantic import BaseModel


class BaseApplicationDTO(BaseModel):
    id: str
    title: str
    icon: str
    description: str
    version: str
    creator: str


class InstanceStatus(str, Enum):
    STARTING = "starting"
    RUNNING = "running"
    FAILED = "failed"
    COMPLETED = "completed"


class PipelineStepStatus(str, Enum):
    IDLE = "idle"
    RUNNING = "running"
    FAILED = "failed"
    COMPLETED = "completed"


class ApplicationType(str, Enum):
    INGEST = "ingest"
    PREPROCESS = "preprocess"


class ApplicationPipelineStepDataDTO(BaseModel):
    title: str
    value: str


class ApplicationPipelineStepDTO(BaseModel):
    id: str
    dependsOn: list[str]
    title: str
    data: list[ApplicationPipelineStepDataDTO]


class ApplicationPipelineDTO(BaseModel):
    id: str
    steps: list[ApplicationPipelineStepDTO]
    entry: str
    label: str


class ApplicationFormFieldDTO(BaseModel):
    fieldType: str
    fieldOrder: int
    fieldInput: Union[str, None]
    fieldLabel: str
    required: bool


class IngestApplicationChartDataDTO(BaseModel):
    totalItems: int = 0
    ingestedItems: int = 0
    avgSize: int = 0
    totalSize: int = 0
    ingestedSize: int = 0
    ingestedChunks: int = 0


class ApplicationInstancePipelineStepStatus(BaseModel):
    step: str
    status: PipelineStepStatus
    startTime: Union[str, None]
    endTime: Union[str, None]


class ApplicationInstanceDTO(BaseModel):
    id: str
    creator: str
    name: str
    comment: Union[str, None]
    startTime: Union[str, None]
    endTime: Union[str, None]
    status: InstanceStatus
    datasetId: Union[str, None]
    chartData: IngestApplicationChartDataDTO
    selectedPipeline: Union[str, None]
    pipelineStepStatuses: list[ApplicationInstancePipelineStepStatus]


class ApplicationFormDTO(BaseModel):
    topFields: list[ApplicationFormFieldDTO]
    bottomFields: list[ApplicationFormFieldDTO]


class IngestApplicationDTO(BaseApplicationDTO):
    applicationType: ApplicationType


class IngestApplication(BaseApplicationDTO):
    instances: list[ApplicationInstanceDTO]
    form: ApplicationFormDTO
    pipelines: list[ApplicationPipelineDTO]
    applicationType: ApplicationType

    def toDto(self) -> IngestApplicationDTO:
        return IngestApplicationDTO(
            applicationType=self.applicationType,
            id=self.id,
            title=self.title,
            icon=self.icon,
            description=self.description,
            version=self.version,
            creator=self.creator,
        )


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

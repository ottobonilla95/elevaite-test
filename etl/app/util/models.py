from enum import Enum
from typing import Union
from uuid import UUID
from pydantic import BaseModel

from app.util.BaseApplication import BaseApplicationDTO


class InstanceStatus(str, Enum):
    STARTING = "starting"
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
    id: UUID
    dependsOn: list[UUID]
    title: str
    data: list[ApplicationPipelineStepDataDTO]


class ApplicationPipelineDTO(BaseModel):
    id: UUID
    steps: list[ApplicationPipelineStepDTO]
    entry: UUID
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


class ApplicationInstanceDTO(BaseModel):
    id: str
    creator: str
    startTime: Union[str, None]
    endTime: Union[str, None]
    status: InstanceStatus
    datasetId: Union[str, None]
    chartData: IngestApplicationChartDataDTO


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
    project: str
    version: str | None
    parent: str | None
    outputURI: str | None


class S3IngestFormDataDTO(BaseDatasetInformationForm):
    connectionName: str
    description: str | None
    url: str
    useEC2: bool
    roleARN: str


class CreateApplicationInstanceDTO(BaseModel):
    creator: str
    formData: S3IngestFormDataDTO

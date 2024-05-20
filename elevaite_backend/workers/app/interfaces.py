from typing import TypeGuard
from elevaitelib.schemas.configuration import (
    S3IngestFormDataDTO,
    PreProcessFormDTO,
    ServiceNowIngestDataDTO,
)


class S3IngestData(S3IngestFormDataDTO):
    applicationId: int
    instanceId: str


def isS3IngestData(obj) -> TypeGuard[S3IngestData]:
    return obj.type == "ingest"


class ServiceNowIngestData(ServiceNowIngestDataDTO):
    applicationId: int
    instanceId: str


def isServiceNowIngestData(obj) -> TypeGuard[ServiceNowIngestData]:
    return obj.type == "service-now"


class PreProcessForm(PreProcessFormDTO):
    instanceId: str
    applicationId: int
    collectionId: str

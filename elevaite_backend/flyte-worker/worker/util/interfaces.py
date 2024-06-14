from typing import TypeGuard
from pydantic import BaseModel


class S3IngestData(BaseModel):
    type: str = "s3_ingest"
    projectId: str
    applicationId: int
    datasetId: str
    instanceId: str
    url: str
    useEC2: bool
    roleARN: str


def isS3IngestData(obj) -> TypeGuard[S3IngestData]:
    return obj.type == "s3_ingest"


# class ServiceNowIngestData(ServiceNowIngestDataDTO):
#     applicationId: int
#     instanceId: str


# def isServiceNowIngestData(obj) -> TypeGuard[ServiceNowIngestData]:
#     return obj.type == "service-now"


# class PreProcessForm(PreProcessFormDTO):
#     instanceId: str
#     applicationId: int
#     collectionId: str


class Secrets(BaseModel):
    LAKEFS_ACCESS_KEY_ID: str
    LAKEFS_SECRET_ACCESS_KEY: str
    LAKEFS_ENDPOINT_URL: str
    LAKEFS_STORAGE_NAMESPACE: str
    S3_ACCESS_KEY_ID: str
    S3_SECRET_ACCESS_KEY: str
    ELASTIC_PASSWORD: str
    ELASTIC_SSL_FINGERPRINT: str
    ELASTIC_HOST: str

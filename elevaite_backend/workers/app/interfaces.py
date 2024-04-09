from elevaitedb.schemas.configuration import S3IngestFormDataDTO, PreProcessFormDTO


class S3IngestData(S3IngestFormDataDTO):
    applicationId: str
    instanceId: str


class PreProcessForm(PreProcessFormDTO):
    instanceId: str
    applicationId: int
    collectionId: str

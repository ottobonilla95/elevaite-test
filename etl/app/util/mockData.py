from .models import (
    ApplicationFormDTO,
    ApplicationFormFieldDTO,
    ApplicationType,
    IngestApplication,
)


applications_list: list[IngestApplication] = [
    IngestApplication(
        id="1",
        title="S3 Ingest",
        creator="elevAIte",
        applicationType=ApplicationType.INGEST,
        description="Ingest data from an S3 bucket",
        version="1.0",
        icon="",
        instances=[],
        pipelines=[],
        form=ApplicationFormDTO(
            bottomFields=[
                ApplicationFormFieldDTO(
                    fieldInput="alphanumeric",
                    fieldOrder=1,
                    fieldType="text",
                    fieldLabel="url",
                    required=True,
                )
            ],
            topFields=[
                ApplicationFormFieldDTO(
                    fieldInput="alphanumeric",
                    fieldOrder=1,
                    fieldType="text",
                    fieldLabel="url",
                    required=True,
                )
            ],
        ),
    ),
    IngestApplication(
        id="2",
        title="Preprocess #1",
        creator="elevAIte",
        applicationType=ApplicationType.PREPROCESS,
        description="Preprocess ingested data",
        version="1.0",
        icon="",
        instances=[],
        pipelines=[],
        form=ApplicationFormDTO(
            bottomFields=[
                ApplicationFormFieldDTO(
                    fieldInput="alphanumeric",
                    fieldOrder=1,
                    fieldType="text",
                    fieldLabel="url",
                    required=True,
                )
            ],
            topFields=[],
        ),
    ),
]

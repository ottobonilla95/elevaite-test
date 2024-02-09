from .models import (
    ApplicationFormDTO,
    ApplicationFormFieldDTO,
    ApplicationPipelineDTO,
    ApplicationPipelineStepDTO,
    ApplicationType,
    IngestApplication,
)


applications_list: list[IngestApplication] = [
    IngestApplication(
        id="1",
        title="S3 Connector",
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
        title="Preprocess Pipelines",
        creator="elevAIte",
        applicationType=ApplicationType.PREPROCESS,
        description="Preprocess ingested data",
        version="1.0",
        icon="",
        instances=[],
        pipelines=[
            ApplicationPipelineDTO(
                label="Documents",
                id="8470d675-6752-4446-8f07-fe7a99949e42",
                entry="14fc347b-aa19-4a2a-9d9b-3b3a630c9d5c",
                steps=[
                    ApplicationPipelineStepDTO(
                        title="Start",
                        data=[],
                        dependsOn=[],
                        id="14fc347b-aa19-4a2a-9d9b-3b3a630c9d5c",
                    ),
                    ApplicationPipelineStepDTO(
                        title="Partition Data",
                        data=[],
                        dependsOn=["14fc347b-aa19-4a2a-9d9b-3b3a630c9d5c"],
                        id="647427ef-2654-4585-8aaa-e03c66915c91",
                    ),
                    ApplicationPipelineStepDTO(
                        title="Vectorize Data",
                        data=[],
                        dependsOn=["647427ef-2654-4585-8aaa-e03c66915c91"],
                        id="19feed33-c233-44c4-83ea-8d5dd54e7ec1",
                    ),
                    ApplicationPipelineStepDTO(
                        title="Approve",
                        data=[],
                        dependsOn=["19feed33-c233-44c4-83ea-8d5dd54e7ec1"],
                        id="547b4b9d-7ea5-414a-a2bf-a691c3e97954",
                    ),
                ],
            )
        ],
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

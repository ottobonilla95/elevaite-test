from elevaitelib.schemas.application import Application, ApplicationType
from elevaitelib.schemas.pipeline import Pipeline, PipelineStep
from elevaitelib.orm.db import models


pipeline_step_1 = models.PipelineStep(
    title="Start",
    data=[],
    dependsOn=[],
    id="14fc347b-aa19-4a2a-9d9b-3b3a630c9d5c",
)


pipeline_step_2 = models.PipelineStep(
    title="Partition Data",
    data=[],
    dependsOn=[],
    id="647427ef-2654-4585-8aaa-e03c66915c91",
)
pipeline_step_2.dependsOn.append(pipeline_step_1)

pipeline_step_3 = models.PipelineStep(
    title="Vectorize Data.",
    data=[],
    dependsOn=[],
    id="19feed33-c233-44c4-83ea-8d5dd54e7ec1",
)
pipeline_step_3.dependsOn.append(pipeline_step_2)

pipeline_step_4 = models.PipelineStep(
    title="Approve",
    data=[],
    dependsOn=[],
    id="547b4b9d-7ea5-414a-a2bf-a691c3e97954",
)

pipeline_step_4.dependsOn.append(pipeline_step_3)


pipeline_steps = [
    pipeline_step_1,
    pipeline_step_2,
    pipeline_step_3,
    pipeline_step_4,
]

# pipeline_1 = models.Pipeline(
#     label="Documents",
#     id="8470d675-6752-4446-8f07-fe7a99949e42",
#     entry="14fc347b-aa19-4a2a-9d9b-3b3a630c9d5c",
#     steps=[
#         pipeline_step_1,
#         pipeline_step_2,
#         pipeline_step_3,
#         pipeline_step_4,
#     ],
# )

applications_list: list[models.Application] = [
    models.Application(
        id="1",
        title="S3 Connector",
        creator="elevAIte 2",
        applicationType=ApplicationType.INGEST,
        description="Ingest data from an S3 bucket",
        version="1.0",
        icon="",
        instances=[],
        pipelines=[],
        # form=ApplicationFormDTO(
        #     bottomFields=[
        #         ApplicationFormFieldDTO(
        #             fieldInput="alphanumeric",
        #             fieldOrder=1,
        #             fieldType="text",
        #             fieldLabel="url",
        #             required=True,
        #         )
        #     ],
        #     topFields=[
        #         ApplicationFormFieldDTO(
        #             fieldInput="alphanumeric",
        #             fieldOrder=1,
        #             fieldType="text",
        #             fieldLabel="url",
        #             required=True,
        #         )
        #     ],
        # ),
    ),
    models.Application(
        id="2",
        title="Preprocess Pipelines",
        creator="elevAIte",
        applicationType=ApplicationType.PREPROCESS,
        description="Preprocess ingested data",
        version="1.0",
        icon="",
        instances=[],
        # pipelines=[pipeline_1],
        # form=ApplicationFormDTO(
        #     bottomFields=[
        #         ApplicationFormFieldDTO(
        #             fieldInput="alphanumeric",
        #             fieldOrder=1,
        #             fieldType="text",
        #             fieldLabel="url",
        #             required=True,
        #         )
        #     ],
        #     topFields=[],
        # ),
    ),
]

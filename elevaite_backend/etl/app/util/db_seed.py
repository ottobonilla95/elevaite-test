from sqlalchemy import text
from sqlalchemy.orm import Session

from elevaitedb.schemas.application import ApplicationType
from elevaitedb.db import models


def seed_db(db: Session):
    res = []

    db.execute(
        text(
            "TRUNCATE {} RESTART IDENTITY;".format(
                ", ".join(
                    table.name for table in reversed(models.Base.metadata.sorted_tables)
                )
            )
        )
    )

    db.commit()

    project_1 = models.Project(
        id="7f66ade4-2bf0-4d46-a2dc-c2aee9e9e043", name="Default Project"
    )
    db.add(project_1)
    db.commit()

    pre_process_pipeline_step_1 = models.PipelineStep(
        title="Dataset Configuration",
        data=[],
        _dependsOn=[],
        id="14fc347b-aa19-4a2a-9d9b-3b3a630c9d5c",
    )
    db.add(pre_process_pipeline_step_1)

    pre_process_pipeline_step_2 = models.PipelineStep(
        title="Document Segmentation",
        data=[],
        _dependsOn=[],
        id="647427ef-2654-4585-8aaa-e03c66915c91",
    )
    pre_process_pipeline_step_2._dependsOn.append(pre_process_pipeline_step_1)
    db.add(pre_process_pipeline_step_2)

    pre_process_pipeline_step_3 = models.PipelineStep(
        title="Document Vectorization",
        data=[],
        _dependsOn=[],
        id="19feed33-c233-44c4-83ea-8d5dd54e7ec1",
    )
    pre_process_pipeline_step_3._dependsOn.append(pre_process_pipeline_step_2)
    db.add(pre_process_pipeline_step_3)

    pre_process_pipeline_step_4 = models.PipelineStep(
        title="Vector DB",
        data=[],
        _dependsOn=[],
        id="547b4b9d-7ea5-414a-a2bf-a691c3e97954",
    )
    pre_process_pipeline_step_4._dependsOn.append(pre_process_pipeline_step_3)
    db.add(pre_process_pipeline_step_4)

    ingest_pipeline_step_1 = models.PipelineStep(
        title="Data Source Configuration",
        data=[],
        _dependsOn=[],
        id="9966b76c-5a5a-4eeb-924f-bd5983b4610a",
    )
    db.add(ingest_pipeline_step_1)

    ingest_pipeline_step_2 = models.PipelineStep(
        title="Worker Process",
        data=[],
        _dependsOn=[],
        id="9fb4ebe8-a679-40a7-90a7-e14f26e6f397",
    )
    ingest_pipeline_step_2._dependsOn.append(ingest_pipeline_step_1)
    db.add(ingest_pipeline_step_2)

    ingest_pipeline_step_3 = models.PipelineStep(
        title="Data Lake Storage",
        data=[],
        _dependsOn=[],
        id="f3427f14-ac54-4bb8-b681-5e2d3e9bbad8",
    )
    ingest_pipeline_step_3._dependsOn.append(ingest_pipeline_step_2)
    db.add(ingest_pipeline_step_3)

    db.commit()
    db.refresh(pre_process_pipeline_step_1)
    db.refresh(pre_process_pipeline_step_2)
    db.refresh(pre_process_pipeline_step_3)
    db.refresh(pre_process_pipeline_step_4)
    db.refresh(ingest_pipeline_step_1)
    db.refresh(ingest_pipeline_step_2)
    db.refresh(ingest_pipeline_step_3)

    pre_process_pipeline_1 = models.Pipeline(
        label="Documents",
        id="8470d675-6752-4446-8f07-fe7a99949e42",
        entry=pre_process_pipeline_step_1.id,
        exit=pre_process_pipeline_step_4.id,
        steps=[
            pre_process_pipeline_step_1,
            pre_process_pipeline_step_2,
            pre_process_pipeline_step_3,
            pre_process_pipeline_step_4,
        ],
    )
    db.add(pre_process_pipeline_1)

    ingest_pipeline_1 = models.Pipeline(
        label="S3 Ingest",
        id="a141911b-7430-44a5-915e-4a4e469799ae",
        entry=ingest_pipeline_step_1.id,
        exit=ingest_pipeline_step_3.id,
        steps=[
            ingest_pipeline_step_1,
            ingest_pipeline_step_2,
            ingest_pipeline_step_3,
        ],
    )
    db.add(ingest_pipeline_1)

    db.commit()
    db.refresh(pre_process_pipeline_1)
    db.refresh(ingest_pipeline_1)

    pre_process_application_1 = models.Application(
        id="2",
        title="Preprocess Pipelines",
        creator="elevAIte",
        applicationType=ApplicationType.PREPROCESS,
        description="Preprocess ingested data",
        version="1.0",
        icon="",
        instances=[],
        pipelines=[pre_process_pipeline_1],
    )
    db.add(pre_process_application_1)

    ingest_application_1 = models.Application(
        id="1",
        title="S3 Connector",
        creator="elevAIte 2",
        applicationType=ApplicationType.INGEST,
        description="Ingest data from an S3 bucket",
        version="1.0",
        icon="",
        instances=[],
        pipelines=[ingest_pipeline_1],
    )
    db.add(ingest_application_1)

    db.commit()
    db.refresh(pre_process_application_1)
    db.refresh(ingest_application_1)
    res.append(pre_process_application_1)
    res.append(ingest_application_1)
    return res

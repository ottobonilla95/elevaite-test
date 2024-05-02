from elevaitedb.db import models
from sqlalchemy.orm import Session


def service_now_seed(db: Session):
    servicenow_preprocess_pipeline_step_1 = models.PipelineStep(
        title="Dataset Configuration",
        data=[],
        _dependsOn=[],
        id="423a197c-7f5b-45bc-be1e-12667e95979e",
    )

    servicenow_preprocess_pipeline_step_2 = models.PipelineStep(
        title="Ticket Segmentation",
        data=[],
        _dependsOn=[],
        id="82d68b0d-f602-4643-ba38-fccb1b7410eb",
    )
    servicenow_preprocess_pipeline_step_2._dependsOn.append(
        servicenow_preprocess_pipeline_step_1
    )

    servicenow_preprocess_pipeline_step_3 = models.PipelineStep(
        title="Segment Vectorization",
        data=[],
        _dependsOn=[],
        id="b3b65582-c792-438a-b0bf-f034f6585a8c",
    )
    servicenow_preprocess_pipeline_step_3._dependsOn.append(
        servicenow_preprocess_pipeline_step_2
    )

    servicenow_preprocess_pipeline_step_4 = models.PipelineStep(
        title="Vector DB",
        data=[],
        _dependsOn=[],
        id="e13f3c40-183a-4fa8-ab36-a7aa30732f4b",
    )
    servicenow_preprocess_pipeline_step_4._dependsOn.append(
        servicenow_preprocess_pipeline_step_3
    )

    servicenow_ingest_pipeline_step_1 = models.PipelineStep(
        title="Data Source Configuration",
        data=[],
        _dependsOn=[],
        id="e97d9ddc-707e-47a4-8a15-00ca8c00f5fb",
    )

    servicenow_ingest_pipeline_step_2 = models.PipelineStep(
        title="Worker Process",
        data=[],
        _dependsOn=[],
        id="0daffa6c-653c-46c5-b511-eac4f6d91333",
    )
    servicenow_ingest_pipeline_step_2._dependsOn.append(
        servicenow_ingest_pipeline_step_1
    )

    servicenow_ingest_pipeline_step_3 = models.PipelineStep(
        title="Data Lake Storage",
        data=[],
        _dependsOn=[],
        id="dcc7f381-fa5a-4106-968f-2e7d6b2658b9",
    )
    servicenow_ingest_pipeline_step_3._dependsOn.append(
        servicenow_ingest_pipeline_step_2
    )
    db.add_all(
        [
            servicenow_ingest_pipeline_step_1,
            servicenow_ingest_pipeline_step_2,
            servicenow_ingest_pipeline_step_3,
            servicenow_preprocess_pipeline_step_1,
            servicenow_preprocess_pipeline_step_2,
            servicenow_preprocess_pipeline_step_3,
            servicenow_preprocess_pipeline_step_4,
        ]
    )

    db.commit()
    db.refresh(servicenow_preprocess_pipeline_step_1)
    db.refresh(servicenow_preprocess_pipeline_step_2)
    db.refresh(servicenow_preprocess_pipeline_step_3)
    db.refresh(servicenow_preprocess_pipeline_step_4)
    db.refresh(servicenow_ingest_pipeline_step_1)
    db.refresh(servicenow_ingest_pipeline_step_2)
    db.refresh(servicenow_ingest_pipeline_step_3)

    servicenow_preprocess_pipeline_1 = models.Pipeline(
        label="ServiceNow",
        id="69728926-1b85-4bfc-aefd-25064184ce36",
        entry=servicenow_preprocess_pipeline_step_1.id,
        exit=servicenow_preprocess_pipeline_step_4.id,
        applicationId=2,
        steps=[
            servicenow_preprocess_pipeline_step_1,
            servicenow_preprocess_pipeline_step_2,
            servicenow_preprocess_pipeline_step_3,
            servicenow_preprocess_pipeline_step_4,
        ],
    )

    # db.commit()

    servicenow_ingest_pipeline_1 = models.Pipeline(
        label="ServiceNow Ingest",
        id="97661e5f-3eb4-450e-9671-b961b51bcd8a",
        entry=servicenow_ingest_pipeline_step_1.id,
        exit=servicenow_ingest_pipeline_step_3.id,
        steps=[
            servicenow_ingest_pipeline_step_1,
            servicenow_ingest_pipeline_step_2,
            servicenow_ingest_pipeline_step_3,
        ],
    )

    db.add_all(
        [
            servicenow_ingest_pipeline_1,
            servicenow_preprocess_pipeline_1,
        ]
    )

    db.commit()

    db.refresh(servicenow_preprocess_pipeline_1)
    db.refresh(servicenow_ingest_pipeline_1)

import { Logos } from "@repo/ui/components";
import type { AppInstanceFormStructure, PipelineStep, S3PreprocessFormDTO } from "./interfaces";
import { AppInstanceFieldTypes, ApplicationType, StepDataSource, StepDataType } from "./interfaces";




export const S3PreprocessFormInitializer: S3PreprocessFormDTO = {
    type: ApplicationType.PREPROCESS,
    selectedPipelineId: "",
    creator: "",
    // ^ Hidden    
    datasetId: "",
    datasetName: "",
    projectId: "",
    parent: "",
    datasetVersion: "",
    collectionId: "",
    queue: "Default",
    maxIdleTime: "Default",
}


export const S3PreprocessingAppInstanceForm: AppInstanceFormStructure<S3PreprocessFormDTO> = {
    title: "Preprocess Functions",
    icon: <Logos.Preprocess/>,
    initializer: S3PreprocessFormInitializer,
    requiredFields: ["datasetId#datasetName", "projectId", "collectionId"],
    fields: [
        // { import: true, export: true },
        {
            field: "name",
            label: "Pipeline Name",
            type: AppInstanceFieldTypes.INPUT,
        },

        // GROUP - Output Dataset
        {
            type: AppInstanceFieldTypes.GROUP,
            label: "Input Dataset",
            fields: [
                {
                    field: "projectId",
                    label: "Dataset Project",
                    required: true,
                    type: AppInstanceFieldTypes.INPUT,
                },
                {
                    field: "datasetName",
                    label: "Dataset Name",
                    required: true,
                    type: AppInstanceFieldTypes.INPUT,
                },
                {
                    field: "datasetVersion",
                    label: "Dataset Version",
                    type: AppInstanceFieldTypes.INPUT,
                },
            ],
        },


        // GROUP - Output Dataset
        {
            type: AppInstanceFieldTypes.GROUP,
            label: "Output Dataset",
            fields: [
                {
                    field: "collectionId",
                    label: "Collection",
                    type: AppInstanceFieldTypes.INPUT,
                },
            ]
        },

        {
            field: "queue",
            label: "Queue",
            type: AppInstanceFieldTypes.INPUT,
            disabled: true,
        },
        {
            field: "maxIdleTime",
            label: "Maximum Idle Time",
            type: AppInstanceFieldTypes.INPUT,
            disabled: true,
        },

    ],
}





export const S3PreprocessingAppPipelineStructure: PipelineStep[][] = [
    [{
        id: "S3PreprocessingAppPipelineStructure_1.1",
        title: "Dataset Configuration",
        previousStepIds: [],
        nextStepIds: [],
        data: [],
        addedInfo: [
            {label: "Dataset Project", field: "projectId", source: StepDataSource.CONFIG},
        ],
        sideDetails: {
            details: [
                {label: "Dataset Name", field: "datasetId"},
                {label: "Dataset Version", field: "datasetVersion", source: StepDataSource.CONFIG},
                {label: "Dataset Ingest Date", field: "startTime", type: StepDataType.DATE},
                {label: "Repo Name", field: ""},
                {label: "Datasource Location", field: ""},
            ],
            configuration: "test",
        }
    }],
    [{
        id: "S3PreprocessingAppPipelineStructure_2.1",
        title: "Document Segmentation",
        previousStepIds: ["S3PreprocessingAppPipelineStructure_1.1"],
        nextStepIds: [],
        data: [],
        addedInfo: [
            {label: "Total Files Processed", field: "totalItems", source: StepDataSource.CHART}
        ],
        sideDetails: {
            details: [
                {label: "Step Started", field: "startTime", source: StepDataSource.STEP, type: StepDataType.DATE},
                {label: "Step Ended", field: "endTime", source: StepDataSource.STEP, type: StepDataType.DATE},
                {label: "Time Elapsed", field: "startTime", secondaryField: "endTime", source: StepDataSource.STEP, type: StepDataType.DURATION},
                {label: "Total Files Ingested", field: "totalItems", source: StepDataSource.CHART},
                {label: "Total File Segments", field: "ingestedChunks", source: StepDataSource.CHART},
                {label: "Average Segment Size", field: "avgChunk", source: StepDataSource.CHART},
                {label: "Largest Segmentation Size", field: "largestChunk", source: StepDataSource.CHART},
            ],
        }
    }],
    [{
        id: "S3PreprocessingAppPipelineStructure_3.1",
        title: "Document Vectorization",
        previousStepIds: ["S3PreprocessingAppPipelineStructure_2.1"],
        nextStepIds: [],
        data: [],
        addedInfo: [
            {label: "Repo Name", field: ""}
        ],
        sideDetails: {
            details: [
                {label: "Step Started", field: "startTime", source: StepDataSource.STEP, type: StepDataType.DATE},
                {label: "Step Ended", field: "endTime", source: StepDataSource.STEP, type: StepDataType.DATE},
                {label: "Time Elapsed", field: "startTime", secondaryField: "endTime", source: StepDataSource.STEP, type: StepDataType.DURATION},
                {label: "Total Files Ingested", field: "totalItems", source: StepDataSource.CHART},
                {label: "Total File Segments", field: "ingestedChunks", source: StepDataSource.CHART},
                {label: "Average Token Size", field: "avgChunk", source: StepDataSource.CHART},
                {label: "Largest Token Size", field: "avgChunk", source: StepDataSource.CHART},
                {label: "Embedding Model Used", field: ""},
                {label: "Embedding Model Dimension", field: ""},
            ],
        }
    }],
    [{
        id: "S3PreprocessingAppPipelineStructure_4.1",
        title: "Vector DB",
        previousStepIds: ["S3PreprocessingAppPipelineStructure_3.1"],
        nextStepIds: [],
        data: [],
        addedInfo: [
            {label: "Repo Name", field: ""}
        ],
        sideDetails: {
            details: [
                {label: "Source URL", field: ""},
                {label: "Source ID", field: ""},
                {label: "Source Version", field: ""},
                {label: "Source Doc Created", field: ""},
                {label: "Source Last Modified", field: ""},
                {label: "Document File Name", field: ""},
                {label: "Document Type", field: ""},
                {label: "Document Version", field: ""},
                {label: "Languages", field: ""},
                {label: "Page Number", field: ""},
            ],
            chunks: true,
        }
    }],
];


import { Logos } from "@repo/ui/components";
import { AppInstanceFieldTypes, AppInstanceFormStructure, S3IngestFormDTO, S3PreprocessFormDTO } from "./interfaces";




export const S3PreprocessFormInitializer: S3PreprocessFormDTO = {
    creator: "test user", // TODO: Apply proper value here
    pipelineName: "",
    datasetId: "",
    datasetName: "",
    project: "",
    version: "",
    outputURI: "",
    queue: "",
    maximumIdleTime: "",
}

export const S3PreprocessingAppInstanceForm: AppInstanceFormStructure<S3PreprocessFormDTO> = {
    title: "Preprocess Functions",
    icon: <Logos.Preprocess/>,
    initializer: S3PreprocessFormInitializer,
    fields: [
        { import: true, export: true },
        {
            field: "pipelineName",
            label: "Pipeline Name",
            info: "Main identifier",
            required: true,
            type: AppInstanceFieldTypes.INPUT,
        },
        {
            field: "datasetId",
            label: "elevAIte Dataset ID",
            info: "Dataset id",
            type: AppInstanceFieldTypes.INPUT,
        },

        // GROUP - Output Dataset
        {
            type: AppInstanceFieldTypes.GROUP,
            label: "Output Dataset",
            fields: [
                {
                    field: "datasetName",
                    info: "The name of the dataset",
                    label: "Dataset Name",
                    required: true,
                    type: AppInstanceFieldTypes.INPUT,
                },
                {
                    field: "project",
                    label: "Dataset Project",
                    info: "The project the dataset is attached to",
                    type: AppInstanceFieldTypes.INPUT,
                },
                {
                    field: "version",
                    label: "Dataset Version",
                    type: AppInstanceFieldTypes.INPUT,
                },
                {
                    field: "outputURI",
                    label: "Dataset Output URI",
                    type: AppInstanceFieldTypes.INPUT,
                },
            ],
        },

        {
            field: "queue",
            info: "Queue order type",
            label: "Queue",
            required: true,
            type: AppInstanceFieldTypes.INPUT,
        },
        {
            field: "maximumIdleTime",
            info: "Maximum time before shutting down (in hours)",
            label: "Maximum Idle Time",
            required: true,
            type: AppInstanceFieldTypes.INPUT,
        },

    ],
}
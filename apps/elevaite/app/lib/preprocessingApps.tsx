import { Logos } from "@repo/ui/components";
import type { AppInstanceFormStructure, S3PreprocessFormDTO } from "./interfaces";
import { AppInstanceFieldTypes } from "./interfaces";




export const S3PreprocessFormInitializer: S3PreprocessFormDTO = {
    creator: "",
    name: "",
    datasetId: "",
    datasetName: "",
    datasetProject: "",
    datasetVersion: "",
    datasetOutputURI: "",
    queue: "Default",
    maxIdleTime: "Default",
    selectedPipeline: "",
}

export const S3PreprocessingAppInstanceForm: AppInstanceFormStructure<S3PreprocessFormDTO> = {
    title: "Preprocess Functions",
    icon: <Logos.Preprocess/>,
    initializer: S3PreprocessFormInitializer,
    fields: [
        { import: true, export: true },
        {
            field: "name",
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
                    field: "datasetProject",
                    label: "Dataset Project",
                    info: "The project the dataset is attached to",
                    required: true,
                    type: AppInstanceFieldTypes.INPUT,
                },
                {
                    field: "datasetVersion",
                    label: "Dataset Version",
                    type: AppInstanceFieldTypes.INPUT,
                },
                {
                    field: "datasetOutputURI",
                    label: "Dataset Output URI",
                    type: AppInstanceFieldTypes.INPUT,
                },
            ],
        },

        {
            field: "queue",
            info: "Queue order type",
            label: "Queue",
            type: AppInstanceFieldTypes.INPUT,
            disabled: true,
        },
        {
            field: "maxIdleTime",
            info: "Maximum time before shutting down",
            label: "Maximum Idle Time",
            type: AppInstanceFieldTypes.INPUT,
            disabled: true,
        },

    ],
}
import { Logos } from "@repo/ui/components";
import type { AppInstanceFormStructure, S3IngestFormDTO } from "./interfaces";
import { AppInstanceFieldTypes } from "./interfaces";



export const S3DataRetrievalAppInstanceFormInitializer: S3IngestFormDTO = {
    creator: "",
    name: "",
    project: "",
    version: "",
    parent: "",
    outputURI: "",
    connectionName: "",
    description: "",
    url: "",
    useEC2: false,
    roleARN: ""
}


export const S3DataRetrievalAppInstanceForm: AppInstanceFormStructure<S3IngestFormDTO> = {
    title: "AWS S3 Document Ingest",
    icon: <Logos.Aws/>,
    initializer: S3DataRetrievalAppInstanceFormInitializer,
    fields: [
        { import: true, export: true },
        {
            field: "connectionName",
            label: "Connection Name",
            info: "Main identifier",
            required: true,
            type: AppInstanceFieldTypes.INPUT,
        },
        {
            field: "description",
            label: "Description",
            info: "Try to be descriptive...",
            type: AppInstanceFieldTypes.INPUT,
        },
        {
            field: "url",
            label: "S3 Url",
            info: "Full link",
            placeholder: "training.data.webex",
            required: true,
            type: AppInstanceFieldTypes.INPUT,
        },
        {
            field: "useEC2",
            label: "Use EC2 Instance Role",
            info: "...well, do you want to use the EC2 instance role?",
            type: AppInstanceFieldTypes.CHECKBOX
        },
        {
            field: "roleARN",
            label: "IAM Role ARN",
            info: "No idea.",
            type: AppInstanceFieldTypes.INPUT,
        },
        { testConnection: true },

        // GROUP - Dataset info
        {
            type: AppInstanceFieldTypes.GROUP,
            label: "Dataset Info",
            fields: [
                {
                    field: "name",
                    info: "The name of the dataset",
                    label: "Dataset Name",
                    required: true,
                    type: AppInstanceFieldTypes.INPUT,
                },
                {
                    field: "project",
                    label: "Dataset Project",
                    info: "The project the dataset is attached to",
                    required: true,
                    type: AppInstanceFieldTypes.INPUT,
                },
                // {
                //     field: "version",
                //     label: "Dataset Version",
                //     type: AppInstanceFieldTypes.INPUT,
                // },
                {
                    field: "parent",
                    label: "Dataset Parent",
                    type: AppInstanceFieldTypes.INPUT,
                },
                // {
                //     field: "outputURI",
                //     label: "Dataset Output URI",
                //     type: AppInstanceFieldTypes.INPUT,
                // },
            ],
        },

    ],
}


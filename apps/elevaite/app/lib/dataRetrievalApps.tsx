import { Logos } from "@repo/ui/components";
import type { AppInstanceFormStructure, PipelineStep, S3IngestFormDTO } from "./interfaces";
import { AppInstanceFieldTypes, ApplicationType, StepDataSource, StepDataType } from "./interfaces";



export const S3DataRetrievalAppInstanceFormInitializer: S3IngestFormDTO = {
    type: ApplicationType.INGEST,
    selectedPipelineId: "",
    creator: "",
    // ^ Hidden
    description: "",
    url: "",
    useEC2: false,
    roleARN: "",
    datasetId: "",
    datasetName: "",
    projectId: "",
    parent: "",
    outputURI: "",
}


export const S3DataRetrievalAppInstanceForm: AppInstanceFormStructure<S3IngestFormDTO> = {
    title: "AWS S3 Document Ingest",
    icon: <Logos.Aws/>,
    initializer: S3DataRetrievalAppInstanceFormInitializer,
    fields: [
        {
            field: "description",
            label: "Description",
            type: AppInstanceFieldTypes.INPUT,
        },
        {
            field: "url",
            label: "S3 Url",
            required: true,
            type: AppInstanceFieldTypes.INPUT,
        },
        {
            field: "useEC2",
            label: "Use EC2 Instance Role",
            type: AppInstanceFieldTypes.CHECKBOX
        },
        {
            field: "roleARN",
            label: "IAM Role ARN",
            required: true,
            type: AppInstanceFieldTypes.INPUT,
        },
        { testConnection: true },

        // GROUP - Dataset info
        {
            type: AppInstanceFieldTypes.GROUP,
            label: "Dataset Info",
            fields: [
                {
                    field: "projectId",
                    label: "Dataset Project",
                    required: true,
                    type: AppInstanceFieldTypes.INPUT,
                },
                {
                    field: "datasetId",
                    label: "Dataset Name",
                    required: true,
                    type: AppInstanceFieldTypes.INPUT,
                },
                {
                    field: "parent",
                    label: "Dataset Parent",
                    type: AppInstanceFieldTypes.INPUT,
                },
                {
                    field: "outputURI",
                    label: "Dataset Output URI",
                    type: AppInstanceFieldTypes.INPUT,
                },
            ],
        },

    ],
}





export const S3DataRetrievalAppPipelineStructure: PipelineStep[][] = [
    [{
        id: "S3DataRetrievalAppPipelineStructure_1.1",
        title: "Data Source Configuration",
        previousStepIds: [],
        nextStepIds: [],
        data: [],
        addedInfo: [
            {label: "Dataset Project", field: "project", source: StepDataSource.CONFIG},
        ],
        sideDetails: {
            configuration: "",
        }
    }],
    [{
        id: "S3DataRetrievalAppPipelineStructure_2.1",
        title: "Worker Process",
        previousStepIds: ["S3DataRetrievalAppPipelineStructure_1.1"],
        nextStepIds: [],
        data: [],
        addedInfo: [
            {label: "Total Files Processed", field: "ingestedItems", source: StepDataSource.CHART},
        ],
        sideDetails: {
            details: [
                {label: "Step Started", field: "startTime", source: StepDataSource.STEP, type: StepDataType.DATE},
                {label: "Step Ended", field: "endTime", source: StepDataSource.STEP, type: StepDataType.DATE},
                {label: "Time Elapsed", field: ""},
                {label: "Total Files Processed", field: "ingestedItems", source: StepDataSource.CHART},
                {label: "Current File Processed", field: ""},
            ],
            webhook: "http://elevaite-s3docingest.com",
        }
    }],
    [{
        id: "S3DataRetrievalAppPipelineStructure_3.1",
        title: "Data Lake Storage",
        previousStepIds: ["S3DataRetrievalAppPipelineStructure_2.1"],
        nextStepIds: [],
        data: [],
        addedInfo: [
            {label: "Repo Name", field: "outputURI", source: StepDataSource.CONFIG},
            {label: "Dataset Id", field: "datasetId"}
        ],
        sideDetails: {
            details: [
                {label: "Dataset Name", field: "name"},
                {label: "Dataset Id", field: "datasetId"},
                {label: "Dataset Version", field: "version"},
                {label: "Repo Name", field: "outputURI", source: StepDataSource.CONFIG},
                {label: "Datasource Location", field: "outputURI", source: StepDataSource.CONFIG},
            ],
            datalake: {
                totalFiles: 21,
                doc: 18,
                zip: 3,
            },
        }
    }],
];


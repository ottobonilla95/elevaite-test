
// Remember to change the discriminators if you change an interface!

import { CommonInputProps, CommonCheckboxProps } from "@repo/ui/components";


// ENUMS
////////////////

export enum ApplicationType {
    INGEST = "ingest",
    PREPROCESS = "preprocess",
}

export enum AppInstanceStatus {
    STARTING = "starting",
    RUNNING = "running",
    FAILED = "failed",
    COMPLETED = "completed",
}

export enum AppInstanceFieldTypes {
    INPUT = "input",
    CHECKBOX = "checkbox",
    GROUP = "group",
}


// COMMON INTERFACES
////////////////

export interface ApplicationObject {
    id: "string",
    applicationType: ApplicationType,
    creator: "string",
    description: "string",
    icon: "string",
    title: "string",
    version: "string",
}

export interface AppInstanceObject {
    id: string,
    datasetId: string,
    creator: string,
    startTime: string,
    endTime?: string,
    status: AppInstanceStatus,
    initialChartData?: {
      partsCompleted: number,
      avgSize: number,
      contextualTotal: number,
      totalChunks: number,
      percentage: number,
    }
}




// APP INSTANCE INTERFACES
////////////////

export type AppInstanceFieldStructure = 
    ( { import?: boolean; export?: boolean; } & ({import: boolean; } | {export: boolean;}) ) |
    { testConnection: boolean; } |
    CommonInputProps & { type: AppInstanceFieldTypes.INPUT; } |
    CommonCheckboxProps & { type: AppInstanceFieldTypes.CHECKBOX; } |
    {
        label: string;
        type: AppInstanceFieldTypes.GROUP;
        fields: AppInstanceFieldStructure[]
    }


export type AppInstanceFormStructure<InitializerType> = {
    title: string;
    icon: JSX.Element;
    initializer: InitializerType;
    fields: AppInstanceFieldStructure[];
};





// DTO INTERFACES
////////////////



export type Initializers = 
    S3IngestFormDTO |
    S3PreprocessFormDTO 
;



export interface S3IngestFormDTO {
    creator: string,
    name: string,
    project: string,
    version: string,
    parent: string,
    outputURO: string,
    connectionName: string,
    description: string,
    url: string,
    useEC2: boolean,
    roleARN: string,
}

export interface S3PreprocessFormDTO {
    creator: string,
    pipelineName: string,
    datasetId: string,
    datasetName: string,
    project: string,
    version: string,
    outputURI: string,
    queue: string;
    maximumIdleTime: string,
}




// Remember to change the discriminators if you change an interface!

import type { CommonInputProps, CommonCheckboxProps } from "@repo/ui/components";


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

export enum PipelineStatus {
    IDLE = "idle",
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
    creator: string,
    name?: string,
    comment?: string,
    startTime: string,
    endTime?: string,
    status: AppInstanceStatus,
    datasetId: string,
    chartData?: ChartDataObject,
    selectedPipeline?: string,
    pipelineStepStatuses?: PipelineStatusItem[];
}

export interface ChartDataObject {
    totalItems: number,
    ingestedItems: number,
    avgSize: number,
    totalSize: number,
    ingestedSize: number,
}

export interface PipelineObject {
    id: string;
    entry: string; 
    label: string; // Documents, Threads, Forums, etc
    steps: PipelineStep[];
}

export interface PipelineStep {
    id: string;
    dependsOn: string[];
    title: string;
    data: [];
}

export interface PipelineStepData {    
    status?: PipelineStatus;
    startTime?: string;
    endTime?: string;
}

export interface PipelineStatusItem {
    step: string;
    status: PipelineStatus;
    startTime: string;
    endTime: string;
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
        fields: AppInstanceFieldStructure[];
    }


export interface AppInstanceFormStructure<InitializerType> {
    title: string;
    icon: JSX.Element;
    initializer: InitializerType;
    fields: AppInstanceFieldStructure[];
}





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
    version: string, // Deprecated. Return ""
    parent: string,
    outputURI: string, // Deprecated. Return ""
    connectionName: string,
    description: string,
    url: string,
    useEC2: boolean,
    roleARN: string,
}

export interface S3PreprocessFormDTO {
    creator: string,
    name: string,
    datasetId: string,
    datasetName: string,
    datasetProject: string,
    datasetVersion: string,
    datasetOutputURI: string,
    queue: string;
    maxIdleTime: string,
    selectedPipeline: string,
}



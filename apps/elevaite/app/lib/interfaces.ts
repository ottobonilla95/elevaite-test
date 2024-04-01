
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

export enum StepDataSource {
    INSTANCE = "instance",
    CONFIG = "configuration",
    STEP = "step",
    CHART = "chartData",
}

export enum StepDataType {
    STRING = "string",
    DATE = "date",
}

export enum ModelsStatus {
    REGISTERING = "registering",
    ACTIVE = "registered",
    FAILED = "failed",
    DEPLOYED = "deployed",
}




// COMMON INTERFACES
////////////////

export interface ApplicationObject {
    id: "string";
    applicationType: ApplicationType;
    creator: "string";
    description: "string";
    icon: "string";
    title: "string";
    version: "string";
}

export interface ApplicationConfigurationObject {
    id: string;
    applicationId: string;
    name: string;
    isTemplate: boolean;
    createDate: string;
    updateDate: string;
    raw: Initializers;
}

export interface ApplicationConfigurationDto {    
    applicationId: string;
    name: string;
    isTemplate: boolean;
    raw: Initializers;
}

export interface AppInstanceObject {
    id: string;
    creator: string;
    name?: string;
    comment?: string;
    startTime: string;
    endTime?: string;
    status: AppInstanceStatus;
    projectId?: string;
    datasetId: string;
    chartData?: ChartDataObject;
    selectedPipelineId?: string;
    pipelineStepStatuses?: PipelineStatusItem[];
    configuration?: AppInstanceConfigurationObject;
}

export interface ChartDataObject {
    totalItems: number;
    ingestedItems: number;
    avgSize: number;
    totalSize: number;
    ingestedSize: number;
}

export interface AppInstanceConfigurationObject {
    id: string;
    applicationId: string | number;
    instanceId: string;
    raw: Initializers;
}

export interface PipelineObject {
    id: string;
    entry: string; 
    label: string; // Documents, Threads, Forums, etc
    steps: PipelineStep[];
}

export interface PipelineStep {
    id: string;
    previousStepIds: string[];
    nextStepIds: string[];
    title: string;
    data: [];
    addedInfo?: PipelineStepAddedInfo[];
    sideDetails?: PipelineStepSideDetails;
}

export interface PipelineStepData {    
    status?: PipelineStatus;
    startTime?: string;
    endTime?: string;
}

export interface PipelineStepAddedInfo {
    label: string;
    field: string;
    source?: StepDataSource;
    type?: StepDataType;
}

export interface PipelineStepSideDetails {
    details?: PipelineStepAddedInfo[];
    configuration?: string;
    webhook?: string;
    datalake?: { totalFiles: number; doc?: number; zip?: number};
}

export interface PipelineStatusItem {
    stepId: string;
    status: PipelineStatus;
    startTime: string;
    endTime: string;
    instanceId: string;
}



// MODELS
////////////////

export interface ModelObject {
    id: number | string;
    huggingface_repo?: string;
    name: string;
    status?: ModelsStatus; // enum? "registered", "failed"
    tags?: string[];
    task?: string;
    created_at?: string;
    endpointUrl?: string;
    ramToRun?: string | number;
    ramToTrain?: string | number;
}


export interface ModelParametersObject {
    activation_function?: string;
    architectures?: string[];
    attention_probs_dropout_prob?: number;
    attn_pdrop?: number;
    bos_token_id?: number;
    classifier_dropout?: unknown; // What's this?
    do_sample?: boolean;
    embd_pdrop?: number;
    eos_token_id?: number;
    finetuning_task?: string;
    gradient_checkpointing?: boolean;
    hidden_act?: string;
    hidden_dropout_prob?: number;
    hidden_size?: number;
    id2label?: unknown; // Object with lots of unknown fields
    initializer_range?: number;
    intermediate_size?: number;
    label2id?: unknown; // Object with lots of unknown fields
    layer_norm_epsilon?: number; // Two of those with very close names. >.<
    layer_norm_eps?: number;
    max_length?: number;
    max_position_embeddings?: number;
    model_type?: string;
    n_ctx?: number;
    n_embd?: number;
    n_head?: number;
    n_inner?: number;
    n_layer?: number;
    n_positions?: number;
    num_attention_heads?: number;
    num_hidden_layers?: number;
    pad_token_id?: number;
    position_embedding_type?: string;
    reorder_and_upcast_attn?: boolean;
    resid_pdrop?: number;
    scale_attn_by_inverse_layer_idx?: boolean;
    scale_attn_weights?: boolean;
    summary_activation?: unknown; // What's that?
    summary_first_dropout?: number;
    summary_proj_to_labels?: boolean;
    summary_type?: string;
    summary_use_proj?: boolean;
    task_specific_params?: unknown; // Nested object
    torch_dtype?: string;
    transformers_version?: string;
    type_vocab_size?: number;
    use_cache?: boolean;
    vocab_size?: number;
    _name_or_path?: string;
}


export interface AvailableModelObject {
    id: string;
    author: string;
    created_at: string;
    last_modified: string;
    gated: boolean | string;
    library_name: string;
    sha: string;
    memory_requirements?: {
        float16: MemoryLayers;
        float32: MemoryLayers;
    };
}
interface MemoryLayers { 
    largest_layer: MemoryBit;
    total_size: MemoryBit;
    training_using_adam: MemoryBit;
 }
interface MemoryBit { value_bytes: number; value_str: string; }



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
    projectId: string;
    creator: string;
    name: string;
    project: string;
    version: string; // Deprecated. Return ""
    parent: string;
    outputURI: string; // Deprecated. Return ""
    connectionName: string;
    description: string;
    url: string;
    useEC2: boolean;
    roleARN: string;
    selectedPipelineId: string;
    configurationName: string;
    isTemplate: boolean;
    type: ApplicationType;
}

export interface S3PreprocessFormDTO {
    projectId: string;
    creator: string;
    name: string;
    datasetId: string;
    datasetName: string;
    datasetProject: string;
    datasetVersion: string;
    datasetOutputURI: string;
    queue: string;
    maxIdleTime: string;
    selectedPipelineId: string;
    configurationName: string;
    isTemplate: boolean;
    type: ApplicationType;
}



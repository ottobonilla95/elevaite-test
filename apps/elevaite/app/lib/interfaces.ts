
// Remember to change the discriminators if you change an interface!

import type { CommonInputProps, CommonCheckboxProps } from "@repo/ui/components";


// STATICS

export const NEW_DATASET = "NEW_DATASET_NAME:";
export const REGISTERING_MODELS_REFRESH_PERIOD = 5000; // 5 seconds
export const REGISTERING_MODELS_LOG_REFRESH_PERIOD = 2000; // 2 seconds


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

export enum AppInstanceLogLevel {
    INFO = "info",
    ERROR = "error",
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
    DURATION = "duration",
}

export enum formDataType {
    STRING = "string",
    BOOLEAN = "boolean",
}

export enum ModelsStatus {
    REGISTERING = "registering",
    ACTIVE = "registered",
    FAILED = "failed",
    DEPLOYED = "deployed", // This is locally applied
}

export enum EvaluationStatus {
    EVALUATING = "allocating_compute",
    FAILED = "failed",
    SUCCESS = "success",
}

export enum CollectionDistanceType {
    COSINE = "Cosine",
    EUCLID = "Euclid",
    DOT = "Dot",
    MANHATTAN = "Manhattan",
}

export enum EmbeddingModelType {
    OPEN_AI = "openai",
    LOCAL = "local",
    EXTERNAL = "external",
}






// SYSTEM INTERFACES
////////////////


export interface FiltersStructure {
    label?: string;
    filters: (FilterUnitStructure|FilterGroupStructure)[];
}

export interface FilterUnitStructure {
    label: string;
    isSelected?: boolean;
    isActive?: boolean;
}

export interface FilterGroupStructure {
    label: string;
    isClosed?: boolean;
    filters: FilterUnitStructure[];
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
    configurationRaw?: string;
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

export interface AppInstanceLogObject {
    timestamp: string;
    message: string;
    level: AppInstanceLogLevel;
}

export interface CollectionObject {
    id: string;
    name: string;
    projectId: string;
    size: number;
    distance: CollectionDistanceType;
}

export type CollectionChunkWrapper = [] | [CollectionChunkObject[], string|null];

export interface CollectionChunkObject {
    id: string;
    shard_key: unknown;
    vector?: number[];
    payload?: {
        page_content?: string;
        metadata?: {
            document_title?: string;
            page_title?: string;
            source?: string;
            tokenSize?: number;
        }
    }
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
    secondaryField?: string;
    source?: StepDataSource;
    type?: StepDataType;
}

export interface PipelineStepSideDetails {
    details?: PipelineStepAddedInfo[];
    configuration?: string;
    webhook?: string;
    chunks?: boolean;
    datalake?: { totalFiles: number; doc?: number; zip?: number};
}

export interface PipelineStatusItem {
    stepId: string;
    status: PipelineStatus;
    startTime: string;
    endTime: string;
    instanceId: string;
}



// MODELS & DATASETS
////////////////

export interface ModelObject {
    id: number | string;
    huggingface_repo?: string;
    name: string;
    status: ModelsStatus;
    tags: string[] | null;
    task: string | null;
    created: string;
    endpointUrl?: string; // This is applied locally
    endpointId?: string; // This is applied locally
    memory_requirements?: MemoryLayers & (ParametersCountObject | undefined);
    running_evaluations: number[];
}
interface MemoryLayers { 
    total_size: MemoryBit;
    training_using_adam: MemoryBit;
 }
interface MemoryBit { value_bytes: number; value_str: string; }
interface ParametersCountObject {
    F64?: number,
    F32?: number,
    F16?: number,
    BF16?: number,
    I64?: number,
    I32?: number,
    I16?: number,
    I8?: number,
    U8?: number,
    BOOL?: number,
}


export interface ModelParametersObject {
    architectures: string[];
    model_type: string;
    // ^ Always present
    activation_function?: string;
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
    memory_requirements?: MemoryLayers;
}

export type ModelLogObject = ModelRegistrationLogObject | ModelEvaluationLogObject;

export interface ModelRegistrationLogObject {
    id: string|number;
    model_id: string|number;
    message: string;
    stream: string;
    time: string;
}

export interface ModelEvaluationLogObject {
    id: string|number;
    evaluation_id: string|number;
    message: string;
    stream: string;
    time: string;
}

export interface EvaluationObject {
    id: string|number;
    model_id: string|number;
    dataset_id: string|number;
    status: EvaluationStatus;
    results: unknown;
}

export interface ModelEndpointObject {
    endpoint_id: string|number;
    model_id: string|number;
    url: string;
}

export interface ModelEndpointCreationObject {
    endpoint_id: string|number;
}

export interface InferTextGenerationDto {
    results: {
        generated_text: string;
    }[]
}

export interface InferSummarizationDto {
    results: {
        summary_text: string;
    }[]
}

export interface InferEmbeddingDto {
    results: number[][];
}

export interface InferQuestionAnsweringDto {
    results: {
        answer: string;
        start: number;
        end: number;
        score: number;
    }
}

export interface ModelDatasetObject {
    id: string|number;
    name: string;
    status: string;
    huggingface_repo: string;
    tags: string[];
}

export interface HuggingfaceDatasetObject {
    id: string;
    author?: string;
    sha: string;
    created_at: string;
    last_modified: string;
    gated: boolean;
}




// RBAC
////////////////

export interface OrganizationObject {
    id: string;
    name: string;
    description: string;
    created_at: string;
    updated_at: string;
}

export interface AccountObject {
    id: string;
    organization_id: string;
    name: string;
    description: string;
    is_disabled?: boolean;
    created_at: string;
    updated_at: string;
}

export interface ProjectObject {
    id: string;
    account_id: string;
    name: string;
    description: string;
    creator: string;
    parent_project_id?: string;
    is_disabled?: boolean;
    datasets: RbacDatasetObject[],
    created_at: string;
    updated_at: string;
}

export interface RbacDatasetObject {
    id: string;
    projectId: string;
    description?: string;
    name: string;
    versions: {
        id: string;
        commitId: string;
        version: string|number;
        createDate: string;
    }[];
    tags: {
        id: string;
        name: string;
    }[];
    createDate: string;
    updateDate?: string;
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
    requiredFields: string[];
    fields: AppInstanceFieldStructure[];
}





// DTO INTERFACES
////////////////



export type Initializers = 
    S3IngestFormDTO |
    S3PreprocessFormDTO 
;


export interface ApplicationDto {
    creator: string;
    configurationId: string;
    projectId: string;
    selectedPipelineId: string;
    instanceName: string;
}


export interface ApplicationConfigurationDto {    
    applicationId: string;
    name: string;
    isTemplate: boolean;
    raw: Initializers;
}


export interface S3IngestFormDTO {
    type: ApplicationType.INGEST;
    selectedPipelineId: string;
    creator: string;
    description: string;
    url: string;
    useEC2: boolean;
    roleARN: string;
    datasetId?: string;
    datasetName?: string;
    projectId: string;
    parent: string;
    outputURI: string;
}

export interface S3PreprocessFormDTO {
    type: ApplicationType.PREPROCESS;
    selectedPipelineId: string;
    creator: string;
    datasetId?: string;
    datasetName?: string;
    projectId: string;
    parent: string;
    datasetVersion: string;
    collectionId: string;
    queue: string;
    maxIdleTime: string;
    embedding_info?: S3PreprocessFormEmbeddingInfo;
}

export interface S3PreprocessFormEmbeddingInfo {
    name: string;
    type: EmbeddingModelType;
    dimensions: string; // positive integer only
    inference_url?: string;
}



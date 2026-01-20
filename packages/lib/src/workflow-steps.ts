/**
 * Workflow Step Type Definitions
 *
 * TypeScript interfaces for all workflow step types used in the workflow engine.
 * These correspond to the Python step implementations in workflow-core-sdk.
 */

// =============================================================================
// Base Types
// =============================================================================

export type StepType =
  | "trigger"
  | "input"
  | "output"
  | "prompt"
  | "merge"
  | "agent_execution"
  | "tool_execution"
  | "human_approval"
  | "subflow"
  | "data_input"
  | "data_processing"
  | "data_merge"
  | "delay"
  | "conditional"
  | "file_reader"
  | "text_chunking"
  | "embedding_generation"
  | "vector_storage"
  | "vector_search"
  | "ingestion";

export type StepStatus =
  | "pending"
  | "running"
  | "completed"
  | "failed"
  | "waiting"
  | "skipped";

export type TriggerKind = "chat" | "api" | "schedule" | "webhook" | "manual";

// =============================================================================
// Base Step Configuration
// =============================================================================

export interface BaseStepConfig<
  TConfig = Record<string, unknown>,
  TParams = Record<string, unknown>,
> {
  step_id: string;
  step_type: StepType;
  step_name?: string;
  dependencies?: string[];
  step_order?: number;
  config?: TConfig;
  parameters?: TParams;
}

// =============================================================================
// Trigger Step
// =============================================================================

export interface TriggerStepParameters {
  kind: TriggerKind;
  schedule_cron?: string;
  webhook_secret?: string;
}

export interface TriggerStepConfig
  extends Omit<BaseStepConfig, "parameters"> {
  step_type: "trigger";
  parameters: TriggerStepParameters;
}

export interface TriggerStepOutput {
  kind: TriggerKind;
  messages?: { role: string; content: string }[];
  current_message?: string;
  attachments?: {
    name: string;
    path: string;
    mime_type: string;
    size: number;
  }[];
  data?: Record<string, unknown>;
}

// =============================================================================
// Input Step
// =============================================================================

export interface InputStepParameters {
  kind?: "manual" | "api" | "file";
}

export interface InputStepConfig
  extends Omit<BaseStepConfig, "parameters"> {
  step_type: "input";
  parameters?: InputStepParameters;
}

export interface InputStepOutput {
  kind: string;
  step_id: string;
  data: Record<string, unknown>;
  source: "direct" | "trigger_raw" | "none";
  awaiting_input?: boolean;
}

// =============================================================================
// Output Step
// =============================================================================

export interface OutputStepParameters {
  label?: string;
  format?: "json" | "text" | "markdown" | "auto";
}

export interface OutputStepConfig
  extends Omit<BaseStepConfig, "parameters"> {
  step_type: "output";
  parameters?: OutputStepParameters;
}

export interface OutputStepOutput {
  step_id: string;
  label: string;
  format: string;
  data: Record<string, unknown>;
  success: boolean;
}

// =============================================================================
// Prompt Step
// =============================================================================

export interface PromptVariableDefinition {
  name: string;
  source?: string;
  default_value?: unknown;
}

export interface PromptStepParameters {
  system_prompt?: string;
  query_template?: string;
  variables?: PromptVariableDefinition[];
  override_agent_prompt?: boolean;
  model_name?: string;
  temperature?: number;
  max_tokens?: number;
}

export interface PromptStepConfig
  extends Omit<BaseStepConfig, "parameters"> {
  step_type: "prompt";
  parameters?: PromptStepParameters;
}

export interface PromptStepOutput {
  step_id: string;
  step_type: "prompt";
  system_prompt?: string;
  query_template?: string;
  raw_system_prompt?: string;
  raw_query_template?: string;
  variables: Record<string, unknown>;
  model_overrides: {
    model_name?: string;
    temperature?: number;
    max_tokens?: number;
  };
  override_agent_prompt: boolean;
}

// =============================================================================
// Merge Step
// =============================================================================

export type MergeMode = "first_available" | "wait_all";
export type CombineMode = "object" | "array" | "first";

export interface MergeStepParameters {
  mode?: MergeMode;
  combine_mode?: CombineMode;
}

export interface MergeStepConfig
  extends Omit<BaseStepConfig, "parameters"> {
  step_type: "merge";
  parameters?: MergeStepParameters;
}

export interface MergeStepOutput {
  mode: MergeMode;
  data: Record<string, unknown> | unknown[];
  sources?: string[];
  source_step?: string;
  completed_count: number;
  total_dependencies: number;
}

// =============================================================================
// Agent Execution Step
// =============================================================================

export interface AgentFunction {
  type: "function";
  function: {
    name: string;
    description?: string;
    parameters?: Record<string, unknown>;
    agent_id?: string;
  };
}

export interface AgentExecutionStepConfig extends BaseStepConfig {
  step_type: "agent_execution";
  config: {
    agent_id?: string;
    agent_name?: string;
    system_prompt?: string;
    query?: string;
    tools?: string[];
    functions?: AgentFunction[];
    connected_agents?: (string | { id?: string; name?: string; tools?: string[] })[];
    interactive?: boolean;
    multi_turn?: boolean;
    force_real_llm?: boolean;
    a2a_agent_id?: string;
    stream?: boolean;
  };
}

export interface AgentExecutionStepOutput {
  agent_id: string;
  agent_name: string;
  query: string;
  response?: string;
  error?: string;
  tool_calls?: {
    tool_name: string;
    arguments: Record<string, unknown>;
    result?: unknown;
    success: boolean;
    duration_ms?: number;
  }[];
  execution_time_seconds: number;
  timestamp: string;
  success: boolean;
  mode: "llm" | "error" | "a2a" | "waiting";
  model?: { provider: string; name: string };
  usage?: {
    tokens_in: number;
    tokens_out: number;
    total_tokens: number;
    llm_calls: number;
  };
}

// =============================================================================
// Tool Execution Step
// =============================================================================

export interface ToolExecutionStepConfig extends BaseStepConfig {
  step_type: "tool_execution";
  config: {
    tool_name?: string;
    tool_id?: string;
    param_mapping?: Record<string, string>;
    static_params?: Record<string, unknown>;
  };
}

export interface ToolExecutionStepOutput {
  success: boolean;
  tool: { name: string; type?: "local" | "mcp"; remote_name?: string; server?: string };
  params: Record<string, unknown>;
  result?: unknown;
  error?: string;
  executed_at?: string;
}

// =============================================================================
// Human Approval Step
// =============================================================================

export type ApprovalDecision = "approved" | "denied" | "pending";

export interface HumanApprovalStepConfig extends BaseStepConfig {
  step_type: "human_approval";
  parameters: {
    prompt?: string;
    timeout_seconds?: number;
    approver_role?: string;
    require_comment?: boolean;
    poll_interval_seconds?: number;
  };
}

export interface HumanApprovalStepOutput {
  approval_id?: string;
  execution_id: string;
  workflow_id?: string;
  step_id: string;
  prompt?: string;
  decision?: ApprovalDecision;
  payload?: Record<string, unknown>;
  decided_by?: string;
  decided_at?: string;
  comment?: string;
  approval_metadata?: {
    approver_role?: string;
    require_comment?: boolean;
    backend?: string;
  };
}

// =============================================================================
// Subflow Step
// =============================================================================

export interface SubflowStepConfig extends BaseStepConfig {
  step_type: "subflow";
  config: {
    workflow_id: string;
    input_mapping?: Record<string, string>;
    output_mapping?: Record<string, string>;
    inherit_context?: boolean;
  };
}

export interface SubflowStepOutput {
  subflow_id: string;
  subflow_execution_id?: string;
  subflow_status: string;
  subflow_output?: Record<string, unknown>;
  execution_time_seconds?: number;
  started_at?: string;
  completed_at?: string;
  failed_at?: string;
  input_data: Record<string, unknown>;
  success: boolean;
  error?: string;
}

// =============================================================================
// Data Input Step
// =============================================================================

export interface DataInputStepConfig extends BaseStepConfig {
  step_type: "data_input";
  config: {
    input_type: "static" | "dynamic";
    data?: Record<string, unknown>;
    source?: string;
  };
}

export interface DataInputStepOutput {
  data: Record<string, unknown>;
  input_type: string;
  source?: string;
  timestamp: string;
  success: boolean;
}

// =============================================================================
// Data Processing Step
// =============================================================================

export type ProcessingType =
  | "identity"
  | "count"
  | "filter"
  | "sentiment_analysis"
  | "transform";

export interface DataProcessingStepConfig extends BaseStepConfig {
  step_type: "data_processing";
  config: {
    processing_type: ProcessingType;
    options?: {
      filter_key?: string;
      filter_value?: unknown;
      transformation?: string;
      metadata?: Record<string, unknown>;
    };
  };
}

export interface DataProcessingStepOutput {
  result: Record<string, unknown>;
  processing_type: ProcessingType;
  processed_at: string;
  success: boolean;
}

// =============================================================================
// Delay Step
// =============================================================================

export interface DelayStepConfig extends BaseStepConfig {
  step_type: "delay";
  config: {
    delay_seconds: number;
  };
}

export interface DelayStepOutput {
  delay_requested: number;
  delay_actual: number;
  started_at: string;
  completed_at: string;
  input_data: Record<string, unknown>;
  success: boolean;
}

// =============================================================================
// Conditional Step
// =============================================================================

export interface ConditionalStepConfig extends BaseStepConfig {
  step_type: "conditional";
  config: {
    condition: string;
    true_action?: { type: "pass" | "transform"; transformation?: Record<string, unknown> };
    false_action?: { type: "pass" | "transform"; transformation?: Record<string, unknown> };
  };
}

export interface ConditionalStepOutput {
  condition: string;
  condition_result: boolean;
  action_taken: { type: string; transformation?: Record<string, unknown> };
  result: Record<string, unknown>;
  evaluated_at: string;
  success: boolean;
}

// =============================================================================
// File Reader Step
// =============================================================================

export interface FileReaderStepConfig extends BaseStepConfig {
  step_type: "file_reader";
  config: {
    file_path?: string;
    file_type?: "text" | "json" | "csv" | "pdf" | "auto";
    encoding?: string;
    max_size_mb?: number;
  };
}

export interface FileReaderStepOutput {
  file_path: string;
  file_type: string;
  content: string | Record<string, unknown>;
  size_bytes: number;
  encoding: string;
  read_at: string;
  success: boolean;
  error?: string;
}

// =============================================================================
// Text Chunking Step
// =============================================================================

export type ChunkingStrategy = "fixed" | "sentence" | "paragraph" | "semantic";

export interface TextChunkingStepConfig extends BaseStepConfig {
  step_type: "text_chunking";
  config: {
    strategy?: ChunkingStrategy;
    chunk_size?: number;
    chunk_overlap?: number;
    separator?: string;
  };
}

export interface TextChunk {
  index: number;
  content: string;
  start_char: number;
  end_char: number;
  metadata?: Record<string, unknown>;
}

export interface TextChunkingStepOutput {
  chunks: TextChunk[];
  total_chunks: number;
  strategy: ChunkingStrategy;
  original_length: number;
  chunked_at: string;
  success: boolean;
}

// =============================================================================
// Embedding Generation Step
// =============================================================================

export interface EmbeddingGenerationStepConfig extends BaseStepConfig {
  step_type: "embedding_generation";
  config: {
    model?: string;
    provider?: "openai" | "cohere" | "huggingface" | "local";
    dimensions?: number;
    batch_size?: number;
  };
}

export interface EmbeddingResult {
  index: number;
  embedding: number[];
  text_preview?: string;
  token_count?: number;
}

export interface EmbeddingGenerationStepOutput {
  embeddings: EmbeddingResult[];
  model: string;
  provider: string;
  dimensions: number;
  total_tokens?: number;
  generated_at: string;
  success: boolean;
  error?: string;
}

// =============================================================================
// Vector Storage Step
// =============================================================================

export interface VectorStorageStepConfig extends BaseStepConfig {
  step_type: "vector_storage";
  config: {
    collection_name: string;
    vector_db?: "qdrant" | "pinecone" | "weaviate" | "chroma";
    connection_url?: string;
    upsert?: boolean;
    metadata_fields?: string[];
  };
}

export interface VectorStorageStepOutput {
  collection_name: string;
  vector_db: string;
  vectors_stored: number;
  operation: "insert" | "upsert";
  stored_at: string;
  success: boolean;
  error?: string;
}

// =============================================================================
// Vector Search Step
// =============================================================================

export interface VectorSearchStepConfig extends BaseStepConfig {
  step_type: "vector_search";
  config: {
    collection_name: string;
    vector_db?: "qdrant" | "pinecone" | "weaviate" | "chroma";
    connection_url?: string;
    top_k?: number;
    score_threshold?: number;
    filter?: Record<string, unknown>;
  };
}

export interface VectorSearchResult {
  id: string;
  score: number;
  content?: string;
  metadata?: Record<string, unknown>;
}

export interface VectorSearchStepOutput {
  results: VectorSearchResult[];
  collection_name: string;
  query_vector_preview?: number[];
  top_k: number;
  searched_at: string;
  success: boolean;
  error?: string;
}

// =============================================================================
// Ingestion Step
// =============================================================================

export interface IngestionStepConfig extends BaseStepConfig {
  step_type: "ingestion";
  config: {
    source_type: "file" | "url" | "s3" | "database";
    source_path?: string;
    destination_collection?: string;
    chunking_config?: {
      strategy: ChunkingStrategy;
      chunk_size: number;
      chunk_overlap: number;
    };
    embedding_config?: {
      model: string;
      provider: string;
    };
  };
}

export interface IngestionStepOutput {
  source_type: string;
  source_path?: string;
  documents_processed: number;
  chunks_created: number;
  vectors_stored: number;
  destination_collection?: string;
  ingested_at: string;
  success: boolean;
  error?: string;
}

// =============================================================================
// Union Types for Step Configurations
// =============================================================================

export type StepConfig =
  | TriggerStepConfig
  | InputStepConfig
  | OutputStepConfig
  | PromptStepConfig
  | MergeStepConfig
  | AgentExecutionStepConfig
  | ToolExecutionStepConfig
  | HumanApprovalStepConfig
  | SubflowStepConfig
  | DataInputStepConfig
  | DataProcessingStepConfig
  | DelayStepConfig
  | ConditionalStepConfig
  | FileReaderStepConfig
  | TextChunkingStepConfig
  | EmbeddingGenerationStepConfig
  | VectorStorageStepConfig
  | VectorSearchStepConfig
  | IngestionStepConfig;

export type StepOutput =
  | TriggerStepOutput
  | InputStepOutput
  | OutputStepOutput
  | PromptStepOutput
  | MergeStepOutput
  | AgentExecutionStepOutput
  | ToolExecutionStepOutput
  | HumanApprovalStepOutput
  | SubflowStepOutput
  | DataInputStepOutput
  | DataProcessingStepOutput
  | DelayStepOutput
  | ConditionalStepOutput
  | FileReaderStepOutput
  | TextChunkingStepOutput
  | EmbeddingGenerationStepOutput
  | VectorStorageStepOutput
  | VectorSearchStepOutput
  | IngestionStepOutput;

// =============================================================================
// Workflow Configuration Types
// =============================================================================

export interface StepConnection {
  from_step: string;
  to_step: string;
  label?: string;
  condition?: string;
}

export interface WorkflowConfig {
  workflow_id?: string;
  name: string;
  description?: string;
  version?: string;
  steps: StepConfig[];
  connections?: StepConnection[];
  global_config?: Record<string, unknown>;
  tags?: string[];
  timeout_seconds?: number;
  created_by?: string;
  created_at?: string;
  updated_at?: string;
}

// =============================================================================
// Execution Types
// =============================================================================

export interface StepExecutionResult {
  step_id: string;
  step_type: StepType;
  status: StepStatus;
  output?: StepOutput;
  error?: string;
  started_at?: string;
  completed_at?: string;
  duration_ms?: number;
  retry_count?: number;
}

export interface WorkflowExecutionState {
  execution_id: string;
  workflow_id: string;
  status: "pending" | "running" | "completed" | "failed" | "paused" | "cancelled";
  current_step?: string;
  step_results: Record<string, StepExecutionResult>;
  context: Record<string, unknown>;
  started_at: string;
  completed_at?: string;
  error?: string;
}

// =============================================================================
// Type Guards
// =============================================================================

export function isTriggerStep(step: StepConfig): step is TriggerStepConfig {
  return step.step_type === "trigger";
}

export function isAgentExecutionStep(step: StepConfig): step is AgentExecutionStepConfig {
  return step.step_type === "agent_execution";
}

export function isHumanApprovalStep(step: StepConfig): step is HumanApprovalStepConfig {
  return step.step_type === "human_approval";
}

export function isToolExecutionStep(step: StepConfig): step is ToolExecutionStepConfig {
  return step.step_type === "tool_execution";
}

export function isMergeStep(step: StepConfig): step is MergeStepConfig {
  return step.step_type === "merge";
}

export function isConditionalStep(step: StepConfig): step is ConditionalStepConfig {
  return step.step_type === "conditional";
}

export function isPromptStep(step: StepConfig): step is PromptStepConfig {
  return step.step_type === "prompt";
}

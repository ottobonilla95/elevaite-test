// Enums, Interfaces, Types, and initializer objects
////////////////////////////////////////////////////

import { AgentType } from "../components/type";

// OpenAI Function Calling Types
export interface ChatCompletionToolParam {
    type: "function";
    function: {
        name: string;
        description?: string;
        parameters?: Record<string, any>;
    };
}

// Agent Function Types (for backward compatibility and creation)
export interface AgentFunction {
    function: {
        name: string;
    };
}

export const SESSION_ID_PREFIX = "sessionId_";
export const USER_MESSAGE_ID_PREFIX = "userMessageId_";
export const CHATBOT_MESSAGE_ID_PREFIX = "chatbotMessageId_";

export enum ChatbotV {
    InWarranty = "in-warranty",
    OutOfWarranty = "out-of-warranty",
    AgentAssist = "agent-assist",
    Upsell = "upsell",
}
export const defaultChatbotV = ChatbotV.InWarranty;

export enum ChatBotGenAI {
    Pan = "pan",
    Cisco = "cisco",
    CiscoClo = "cisco_clo",
    ServiceNow = "servicenow",
    BGPInsights = "bgpinsights",
}
export const defaultGenAIBotOption = ChatBotGenAI.CiscoClo;

export interface SessionObject {
    id: string;
    label: string;
    messages: ChatMessageObject[];
    creationDate: string;
    summary?: SessionSummaryObject;
}

export interface SessionSummaryObject {
    title: string;
    problem: string;
    solution: string;
    sessionMessageLengthOnLastUpdate?: number;
    isExpectingDisplay?: boolean;
}

export const defaultSession: SessionObject = {
    id: `${SESSION_ID_PREFIX}0`,
    label: "Session 1",
    messages: [],
    creationDate: new Date().toISOString(),
}

export interface ChatMessageResponse {
    text: string;
    refs: string[];
}

export interface ChatMessageObject {
    id: string;
    userName: string;
    isBot: boolean;
    date: string;
    text: string;
    vote?: 0 | 1 | -1;
    feedback?: string;
    feedbackfiles?: ChatMessageFileObject[];
    files?: ChatMessageFileObject[];
}

export interface ChatMessageFileObject {
    id: string;
    filename: string;
    fileType?: ChatMessageFileTypes;
    isDownloadable?: boolean;
    isViewable?: boolean;
}

export enum ChatMessageFileTypes {
    DOC = "document",
}

// Agent-related interfaces
export interface PromptResponse {
    prompt_label: string;
    prompt: string;
    unique_label: string;
    app_name: string;
    version: string;
    ai_model_provider: string;
    ai_model_name: string;
    tags?: string[] | null;
    hyper_parameters?: Record<string, string> | null;
    variables?: Record<string, string> | null;
    id: number;
    pid: string;
    sha_hash: string;
    is_deployed: boolean;
    created_time: string;
    deployed_time?: string | null;
    last_deployed?: string | null;
}

export interface AgentResponse {
    name: string;
    agent_type?: AgentType | null;
    description?: string | null;
    parent_agent_id?: string | null;
    system_prompt_id: string;
    persona?: string | null;
    functions: ChatCompletionToolParam[];
    routing_options: Record<string, string>;
    short_term_memory: boolean;
    long_term_memory: boolean;
    reasoning: boolean;
    input_type: ("text" | "voice" | "image")[];
    output_type: ("text" | "voice" | "image")[];
    response_type: "json" | "yaml" | "markdown" | "HTML" | "None";
    max_retries: number;
    timeout?: number | null;
    deployed: boolean;
    status: "active" | "paused" | "terminated";
    priority?: number | null;
    failure_strategies?: string[] | null;
    collaboration_mode: "single" | "team" | "parallel" | "sequential";
    available_for_deployment: boolean;
    deployment_code?: string | null;
    id: number;
    agent_id: string;
    session_id?: string | null;
    last_active?: string | null;
    system_prompt: PromptResponse;
}

export interface AgentConfigData {
    agentName: string;
    deploymentType: string;
    modelProvider: string;
    model: string;
    outputFormat: string;
    selectedTools: string[];
}

// Agent creation interfaces that match backend structure

export interface AgentCreate {
    name: string;
    agent_type?: AgentType | null;
    description?: string | null;
    parent_agent_id?: string | null;
    system_prompt_id: string;
    persona?: string | null;
    routing_options: Record<string, string>;
    short_term_memory: boolean;
    long_term_memory: boolean;
    reasoning: boolean;
    input_type: ("text" | "voice" | "image")[];
    output_type: ("text" | "voice" | "image")[];
    response_type: "json" | "yaml" | "markdown" | "HTML" | "None";
    max_retries: number;
    timeout?: number | null;
    deployed: boolean;
    status: "active" | "paused" | "terminated";
    priority?: number | null;
    failure_strategies?: string[] | null;
    collaboration_mode: "single" | "team" | "parallel" | "sequential";
    available_for_deployment: boolean;
    deployment_code?: string | null;
    functions: AgentFunction[];
}

export interface AgentUpdate {
    name?: string;
    agent_type?: AgentType | null;
    description?: string | null;
    parent_agent_id?: string | null;
    system_prompt_id?: string;
    persona?: string | null;
    functions?: AgentFunction[];
    routing_options?: Record<string, string>;
    short_term_memory?: boolean;
    long_term_memory?: boolean;
    reasoning?: boolean;
    input_type?: ("text" | "voice" | "image")[];
    output_type?: ("text" | "voice" | "image")[];
    response_type?: "json" | "yaml" | "markdown" | "HTML" | "None";
    max_retries?: number;
    timeout?: number | null;
    deployed?: boolean;
    status?: "active" | "paused" | "terminated";
    priority?: number | null;
    failure_strategies?: string[] | null;
    collaboration_mode?: "single" | "team" | "parallel" | "sequential";
    available_for_deployment?: boolean;
    deployment_code?: string | null;
}

export interface AgentNodeData {
    id: string;
    shortId?: string;
    type: AgentType;
    name: string;
    prompt?: string;
    tools?: ChatCompletionToolParam[];
    config?: any;
    onDelete: (id: string) => void;
    onConfigure: (id: string) => void;
    tags?: string[];
    agent: AgentResponse;
    description?: string;
}

// Workflow-related interfaces
export interface WorkflowPosition {
    x: number;
    y: number;
}

export interface WorkflowAgentData {
    agent_id: string;
    position?: WorkflowPosition;
}

export interface WorkflowConnectionData {
    source_agent_id: string;
    target_agent_id: string;
    connection_type?: "default" | "conditional" | "parallel";
}

export interface WorkflowDeployRequest {
    workflow_name?: string;
    description?: string;
    agents: WorkflowAgentData[];
    connections: WorkflowConnectionData[];
}

export interface WorkflowDeployResponse {
    status: "success" | "error";
    message: string;
    workflow_id?: string;
    deployment_id?: string;
    deployment_name?: string;
}

export interface WorkflowExecutionRequest {
    query: string;
    uid?: string;
    sid?: string;
    collection?: string;
}

export interface WorkflowExecutionResponse {
    status: "ok" | "error";
    response?: string;
    message?: string;
}

// New workflow interfaces
export interface WorkflowAgent {
    workflow_id: string;
    agent_id: string;
    position_x?: number;
    position_y?: number;
    node_id: string;
    agent_config?: Record<string, any>;
    id: number;
    added_at: string;
    agent: AgentResponse;
}

export interface WorkflowConnection {
    workflow_id: string;
    source_agent_id: string;
    target_agent_id: string;
    connection_type: string;
    conditions?: Record<string, any>;
    priority: number;
    source_handle?: string;
    target_handle?: string;
    id: number;
    created_at: string;
    source_agent: AgentResponse;
    target_agent: AgentResponse;
}

export interface WorkflowDeployment {
    workflow_id: string;
    environment: string;
    deployment_name: string;
    deployed_by?: string;
    runtime_config?: Record<string, any>;
    id: number;
    deployment_id: string;
    status: "active" | "inactive" | "failed";
    deployed_at: string;
    stopped_at?: string;
    execution_count: number;
    error_count: number;
    last_executed?: string;
    last_error?: string;
    workflow: WorkflowResponse;
}

export interface WorkflowResponse {
    name: string;
    description?: string;
    version: string;
    configuration: Record<string, any>;
    created_by?: string;
    is_active: boolean;
    tags?: string[];
    id: number;
    workflow_id: string;
    created_at: string;
    updated_at: string;
    is_deployed: boolean;
    deployed_at?: string;
    workflow_agents: WorkflowAgent[];
    workflow_connections: WorkflowConnection[];
    workflow_deployments: WorkflowDeployment[];
}

export interface WorkflowCreateRequest {
    name: string;
    description?: string;
    version?: string;
    configuration: {
        agents: Array<{
            agent_type: string;
            agent_id?: string;
            position?: { x: number; y: number };
            config?: Record<string, any>;
        }>;
        connections: Array<{
            source_agent_id: string;
            target_agent_id: string;
            connection_type?: string;
            conditions?: Record<string, any>;
            priority?: number;
            source_handle?: string;
            target_handle?: string;
        }>;
    };
    created_by?: string;
    is_active?: boolean;
    tags?: string[];
}

export interface WorkflowDeploymentRequest {
    environment?: string;
    deployment_name: string;
    deployed_by?: string;
    runtime_config?: Record<string, any>;
}

export interface NewWorkflowExecutionRequest {
    workflow_id?: string;
    deployment_name?: string;
    query: string;
    chat_history?: Array<{ actor: string; content: string }>;
    runtime_overrides?: Record<string, any>;
}





// Prompts


export enum PromptInputTypes {
    DocumentHeader = "documentHeader",
    LineItemHeader = "lineItemHeader",
    UserFeedback = "userFeedback",
    LineItems = "lineItems",
    ExpectedOutput = "expectedOutput",
}


export interface UploadFileResponseObject {
    image: string;
    doc_type: string;
    num_pages: number;
    prompt: string;
    line_items: string;
    table_header: string;
    result: string;
}

export interface ProcessCurrentPageResponseObject {
    document_headers: string[],
    line_item_headers: string[],
    result: string,
    prompt: string
}

export interface PageChangeResponseObject {
    image: string;
    prompt: string;
}

export interface regenerateResponseObject {
    id?: string;
    prompt: string;
    result: string;
}

export type RunResponseObject = string[];

export type DeployResponse = "Done";


export interface PromptInputItem {
    id: string;
    type: PromptInputTypes;
    label?: string;
    prompt: string;
    values: string[];
}



// Tools-related interfaces
export interface ToolInfo {
    name: string;
    description: string;
    parameters: Record<string, any>;
    function_type: string;
}

export interface ToolsResponse {
    tools: ToolInfo[];
    total_count: number;
}

export interface ToolCategoryResponse {
    [category: string]: {
        tools: ToolInfo[];
        count: number;
    };
}

export interface ToolDetailResponse {
    name: string;
    schema: Record<string, any>;
    available: boolean;
    docstring?: string;
}

// Deployment operation response
export interface DeploymentOperationResponse {
    status: "success" | "error";
    message: string;
    deployment_name?: string;
    operation?: string;
}



export interface SavedWorkflow {
    workflow_id: string;
    name: string;
    description?: string;
    created_at: string;
    created_by?: string;
    is_active: boolean;
    is_deployed: boolean;
    deployed_at?: string;
    version: string;
    agent_count?: number;
    connection_count?: number;
}
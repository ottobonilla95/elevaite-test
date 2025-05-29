
// Enums, Interfaces, Types, and initializer objects
////////////////////////////////////////////////////


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

export type AgentType = "router" | "web_search" | "data" | "troubleshooting" | "api" | "weather";

export interface AgentResponse {
    name: string;
    agent_type?: AgentType | null;
    description?: string | null;
    parent_agent_id?: string | null;
    system_prompt_id: string;
    persona?: string | null;
    functions: object[];
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






// Prompts


export enum PromptInputTypes {
    UserInstructions = "userInstructions",
    TableHeader = "tableHeader",
    LineItems = "lineItems",
    ExpectedOutput = "expectedOutput",
}


export interface UploadFileResponseObject {
    image: string;
    doc_type: string;
    num_pages: number;
    prompt: string;
}

export interface PageChangeResponseObject {
    image: string;
    prompt: string;
}

export interface regenerateResponseObject {
    prompt: string;
    response: string;
}

export type RunResponseObject = string[];

export type DeployResponse = "Done";


export interface PromptInputItem {
    id: string;
    type: PromptInputTypes;
    label?: string;
    prompt: string;
}




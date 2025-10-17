import { type Edge as ReactFlowEdge, type Node as ReactFlowNode, } from "react-flow-renderer";
import { type AgentFunction, type ChatCompletionToolParam } from "./common";
import { type ToolNodeData } from "./tools";

// Define agent types as const object for better type safety and autocomplete
export const AGENT_TYPE = {
  ROUTER: "router",
  WEB_SEARCH: "web_search",
  WEATHER_SEARCH: "Weather Search Agent",
  DATA: "data",
  TROUBLESHOOTING: "troubleshooting",
  API: "api",
  TOSHIBA: "toshiba",
  CUSTOM: "custom",
} as const;

// Extract the union type from the const object
export type AgentType = (typeof AGENT_TYPE)[keyof typeof AGENT_TYPE] | "tool"; // Tool is an override for now.

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

export interface PromptCreate {
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
  sha_hash?: string | null;
}

export interface PromptUpdate {
  prompt_label?: string | null;
  prompt?: string | null;
  unique_label?: string | null;
  app_name?: string | null;
  version?: string | null;
  ai_model_provider?: string | null;
  ai_model_name?: string | null;
  is_deployed?: boolean | null;
  tags?: string[] | null;
  hyper_parameters?: Record<string, string> | null;
  variables?: Record<string, string> | null;
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
  agentType?: AgentType;
  description?: string;
  tags?: string;
  selectedPromptId?: string | null;
  deploymentType: string;
  modelProvider: string;
  model: string;
  outputFormat: string;
  selectedTools: ChatCompletionToolParam[];
  isNewAgent?: boolean; // Flag to indicate if this should create a new agent
}

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
  config?: AgentConfigData;
  onAction?: (id: string, action: string, nodeData?: AgentNodeData) => void;
  onDelete: (id: string) => void;
  onConfigure: (id: string) => void;
  tags?: string[];
  agent: AgentResponse;
  description?: string;
}

export interface AgentExecutionRequest {
  query: string;
  session_id?: string;
  user_id?: string;
  chat_history?: Record<string, string>[];
  enable_analytics?: boolean;
}

export interface AgentExecutionResponse {
  status: string;
  response: string;
  agent_id: string;
  execution_time?: number;
  timestamp: string;
}

export interface AgentStreamExecutionRequest {
  query: string;
  chat_history?: Record<string, string>[];
}

export interface CustomEdgeData {
  actionType?: "Action" | "Conditional" | "Notification" | "Delay" | "None";
}

export type Edge = ReactFlowEdge<CustomEdgeData>;
export type Node = ReactFlowNode<AgentNodeData|ToolNodeData>;

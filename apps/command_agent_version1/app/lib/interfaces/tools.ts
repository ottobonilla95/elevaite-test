


export type JSONScalarType = "integer" | "number" | "string";
export interface ToolParameterValueType {
    type: JSONScalarType;
    description?: string;
    title?: string;
    value?: number | string;
    error?: string;
    isEdited?: boolean;
    isUsingResponse?: boolean;
}
export interface ToolParametersSchema {
  tool_defaultName?: string;
  tool_name?: string;
  tool_description?: string;
  properties: Record<string, ToolParameterValueType>;
  required?: string[];
}



export interface Tool {
  id: number|string;
  tool_id: string;

  name: string;
  display_name?: string;
  description: string;
  version: string;
  tool_type: ToolType;
  execution_type: string;

  parameters_schema: ToolParametersSchema;
  return_schema?: Record<string, unknown>;
  param_mapping?: Record<string, unknown>;

  module_path?: string;
  function_name?: string;
  remote_name?: string;
  auth_required: boolean;

  category_id?: string;
  mcp_server_id?: string;

  is_active: boolean;
  is_available: boolean;

  created_by?: string;
  tags?: string[];
  created_at: string;
  updated_at: string;
  last_used?: string;

  usage_count: number;
  average_execution_time_ms?: number;

  category?: ToolCategory;
  mcp_server?: MCPServer;

  api_endpoint?: string;
  http_method?: string;
  headers?: Record<string, string>;
  documentation?: string;
  examples?: Record<string, unknown>[];
}


export interface ToolNodeData {
  id: string;
  type: ToolType;
  name: string;
  description?: string;
  tool: Tool;
  tags?: string[];
  config?: {
    tool_name?: string;
    tool_description?: string;
    param_mapping?: Record<string, unknown>;
    static_params?: Record<string, unknown>;
  };
  onAction?: (id: string, action: string, nodeData?: ToolNodeData) => void;
  onDelete: (id: string) => void;
  onConfigure: (id: string) => void;
}


export type ToolType = "local" | "remote" | "mcp";

export interface ToolCategory {
  id: number;
  category_id: string;
  name: string;
  description?: string;
  icon?: string;
  color?: string;
  created_at: string;
  updated_at: string;
}

export interface ToolCategoryCreate {
  name: string;
  description?: string;
  icon?: string;
  color?: string;
}

export interface ToolCategoryUpdate {
  name?: string;
  description?: string;
  icon?: string;
  color?: string;
}

export interface MCPServer {
  id: number;
  server_id: string;
  name: string;
  description?: string;
  host: string;
  port: number;
  protocol: string; // "http" or "https"
  endpoint?: string;
  auth_type?: string;
  auth_config?: Record<string, unknown>;
  version?: string;
  capabilities?: string[];
  tags?: string[];
  health_check_interval: number;
  status: string; // "active", "inactive", "error"
  last_health_check?: string;
  consecutive_failures: number;
  registered_at: string;
  last_seen?: string;
  updated_at: string;
}

export interface MCPServerCreate {
  name: string;
  description?: string;
  host: string;
  port: number;
  protocol?: string; // defaults to "http"
  endpoint?: string;
  auth_type?: string;
  auth_config?: Record<string, unknown>;
  version?: string;
  capabilities?: string[];
  tags?: string[];
  health_check_interval?: number; // defaults to 300
}

export interface MCPServerUpdate {
  name?: string;
  description?: string;
  host?: string;
  port?: number;
  protocol?: string;
  endpoint?: string;
  auth_type?: string;
  auth_config?: Record<string, unknown>;
  status?: string;
  version?: string;
  capabilities?: string[];
  tags?: string[];
  health_check_interval?: number;
}

export interface ToolExecutionRequest {
  tool_id: string; // UUID as string
  parameters: Record<string, unknown>;
  session_id?: string;
  user_id?: string;
  timeout_override?: number;
}

export interface ToolExecutionResponse {
  status: string; // "success", "error", "timeout"
  result?: unknown;
  error_message?: string;
  execution_time_ms: number;
  tool_id: string; // UUID as string
  timestamp: string; // ISO datetime string
}

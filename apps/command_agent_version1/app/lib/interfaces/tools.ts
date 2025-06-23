export interface Tool {
  id: number;
  tool_id: string;

  name: string;
  display_name?: string;
  description: string;
  version: string;
  tool_type: "local" | "remote" | "mcp";
  execution_type: string;

  parameters_schema: Record<string, any>;
  return_schema?: Record<string, any>;

  module_path?: string;
  function_name?: string;
  remote_name?: string;
  requires_auth: boolean;
  timeout_seconds: number;
  retry_count: number;
  rate_limit_per_minute?: number;

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
  success_count: number;
  error_count: number;
  average_execution_time_ms?: number;

  category?: ToolCategory;
  mcp_server?: MCPServer;
}

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
  auth_config?: Record<string, any>;
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
  auth_config?: Record<string, any>;
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
  auth_config?: Record<string, any>;
  status?: string;
  version?: string;
  capabilities?: string[];
  tags?: string[];
  health_check_interval?: number;
}

export interface ToolExecutionRequest {
  tool_id: string; // UUID as string
  parameters: Record<string, any>;
  session_id?: string;
  user_id?: string;
  timeout_override?: number;
}

export interface ToolExecutionResponse {
  status: string; // "success", "error", "timeout"
  result?: any;
  error_message?: string;
  execution_time_ms: number;
  tool_id: string; // UUID as string
  timestamp: string; // ISO datetime string
}

import { type AgentResponse } from "./agents";

// Mapping functions between frontend actionType and backend connection_type
export const mapActionTypeToConnectionType = (actionType: string): "default" | "conditional" | "notification" | "delay" => {
  switch (actionType) {
    case "Action": return "default";
    case "Conditional": return "conditional";
    case "Notification": return "notification";
    case "Delay": return "delay";
    default: return "default";
  }
};

export const mapConnectionTypeToActionType = (connectionType: string): "Action" | "Conditional" | "Notification" | "Delay" | "None" => {
  switch (connectionType) {
    case "action": return "Action";
    case "conditional": return "Conditional";
    case "notification": return "Notification";
    case "delay": return "Delay";
    default: return "None";
  }
};

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
  connection_type?: "default" | "conditional" | "notification" | "delay";
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

export interface WorkflowAgent {
  workflow_id: string;
  agent_id: string;
  position_x?: number;
  position_y?: number;
  node_id: string;
  agent_config?: Record<string, unknown>;
  id: number;
  added_at: string;
  agent: AgentResponse;
}

export interface WorkflowConnection {
  workflow_id: string;
  source_agent_id: string;
  target_agent_id: string;
  connection_type: string;
  conditions?: Record<string, unknown>;
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
  runtime_config?: Record<string, unknown>;
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
  configuration: Record<string, unknown>;
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
    agents: {
      agent_type: string;
      agent_id?: string;
      position?: { x: number; y: number };
      config?: Record<string, unknown>;
    }[];
    connections: {
      source_agent_id: string;
      target_agent_id: string;
      connection_type?: string;
      conditions?: Record<string, unknown>;
      priority?: number;
      source_handle?: string;
      target_handle?: string;
    }[];
  };
  created_by?: string;
  is_active?: boolean;
  tags?: string[];
}

export interface WorkflowDeploymentRequest {
  environment?: string;
  deployment_name: string;
  deployed_by?: string;
  runtime_config?: Record<string, unknown>;
}

export interface NewWorkflowExecutionRequest {
  workflow_id?: string;
  deployment_name?: string;
  query: string;
  chat_history?: { actor: string; content: string }[];
  runtime_overrides?: Record<string, unknown>;
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

import type {
  WorkflowConfig,
  ExecutionStatusResponse,
  ExecutionResultsResponse,
} from "../model/workflowSteps";

export interface WorkflowListRequest { }

export interface WorkflowListResponse extends Array<WorkflowConfig> { }

export interface WorkflowGetRequest {
  workflowId: string;
}

export interface WorkflowGetResponse extends WorkflowConfig { }

export interface WorkflowCreateRequest extends Partial<WorkflowConfig> {
  name: string;
  steps: WorkflowConfig["steps"];
}

export interface WorkflowCreateResponse extends WorkflowConfig { }

export interface WorkflowUpdateRequest extends Partial<WorkflowConfig> { }

export interface WorkflowUpdateResponse extends WorkflowConfig { }

export interface WorkflowDeleteRequest {
  workflowId: string;
}

export interface WorkflowDeleteResponse {
  success: boolean;
  message: string;
}

export interface WorkflowExecuteRequest {
  workflowId: string;
  input?: Record<string, unknown>;
}

export interface WorkflowExecuteResponse extends ExecutionResultsResponse { }

export interface WorkflowExecutionPollRequest {
  workflowId: string;
  executionId: string;
}

export interface WorkflowExecutionPollResponse extends ExecutionStatusResponse { }

export interface WorkflowExecutionStreamRequest {
  workflowId: string;
  executionId: string;
}

export interface AgentListRequest { }

export interface AgentListResponse extends Array<{ id: string; name: string; description?: string }> { }

export interface AgentGetRequest {
  agentId: string;
}

export interface AgentGetResponse {
  id: string;
  name: string;
  description?: string;
  tools?: string[];
}

export interface ToolListRequest { }

export interface ToolListResponse extends Array<{ id: string; name: string; type?: string }> { }

export interface ToolGetRequest {
  toolId: string;
}

export interface ToolGetResponse {
  id: string;
  name: string;
  type?: string;
  schema?: Record<string, unknown>;
}

export interface ApiErrorResponse {
  error: string;
  message: string;
  status: number;
  details?: Record<string, unknown>;
}

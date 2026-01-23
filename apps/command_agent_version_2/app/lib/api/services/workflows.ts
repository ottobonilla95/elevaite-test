import { createApiClient, type ApiClient } from "../client";
import type { WorkflowConfig, ExecutionStatusResponse, ExecutionResultsResponse } from "../../model/workflowSteps";
import type {
  WorkflowCreateRequest,
  WorkflowDeleteResponse,
  WorkflowUpdateRequest,
} from "../contracts";

// Backend returns WorkflowRead (extends WorkflowConfig with id, created_at, updated_at)
export interface WorkflowRead extends WorkflowConfig {
  id: string;
  created_at: string;
  updated_at?: string;
  total_executions?: number;
  successful_executions?: number;
  last_executed?: string;
}

export interface WorkflowsService {
  fetchAll: () => Promise<WorkflowRead[]>;
  fetchOne: (workflowId: string) => Promise<WorkflowRead>;
  create: (payload: WorkflowCreateRequest) => Promise<WorkflowRead>;
  update: (workflowId: string, payload: WorkflowUpdateRequest) => Promise<WorkflowRead>;
  delete: (workflowId: string) => Promise<WorkflowDeleteResponse>;
  execute: (workflowId: string, input: Record<string, unknown>) => Promise<ExecutionResultsResponse>;
  pollExecution: (workflowId: string, executionId: string) => Promise<ExecutionStatusResponse>;
}

export function createWorkflowsService(client: ApiClient = createApiClient({})): WorkflowsService {
  return {
    fetchAll(): Promise<WorkflowRead[]> {
      return client.get<WorkflowRead[]>("/workflows/");
    },
    fetchOne(workflowId: string): Promise<WorkflowRead> {
      return client.get<WorkflowRead>(`/workflows/${workflowId}`);
    },
    create(payload: WorkflowCreateRequest): Promise<WorkflowRead> {
      return client.post<WorkflowRead>("/workflows", payload);
    },
    update(workflowId: string, payload: WorkflowUpdateRequest): Promise<WorkflowRead> {
      return client.put<WorkflowRead>(`/workflows/${workflowId}`, payload);
    },
    delete(workflowId: string): Promise<WorkflowDeleteResponse> {
      return client.del<WorkflowDeleteResponse>(`/workflows/${workflowId}`);
    },
    execute(workflowId: string, input: Record<string, unknown>): Promise<ExecutionResultsResponse> {
      return client.post<ExecutionResultsResponse>(`/workflows/${workflowId}/execute`, { input });
    },
    pollExecution(workflowId: string, executionId: string): Promise<ExecutionStatusResponse> {
      return client.get<ExecutionStatusResponse>(`/workflows/${workflowId}/executions/${executionId}`);
    },
  };
}

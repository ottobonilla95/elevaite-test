import { createApiClient, type ApiClient } from "../client";
import type {
  WorkflowConfig,
  ExecutionStatusResponse,
  ExecutionResultsResponse,
  StepConfig,
  StepConnection,
} from "../../model/workflowSteps";
import type {
  WorkflowCreateRequest,
  WorkflowDeleteResponse,
  WorkflowUpdateRequest,
} from "../contracts";

// Backend API response structure (different from WorkflowConfig)
interface WorkflowReadResponse {
  id: string;
  name: string;
  description?: string | null;
  version?: string;
  execution_pattern?: string;
  configuration: {
    name?: string;
    description?: string | null;
    version?: string;
    steps: StepConfig[];
    connections?: StepConnection[];
    global_config?: Record<string, unknown>;
    tags?: string[];
    timeout_seconds?: number | null;
    created_by?: string | null;
  };
  global_config?: Record<string, unknown>;
  tags?: string[];
  timeout_seconds?: number | null;
  status?: string;
  created_by?: string | null;
  created_at: string;
  updated_at?: string | null;
  total_executions?: number | null;
  successful_executions?: number | null;
  last_executed?: string | null;
}

// Normalized response that matches WorkflowConfig
export interface WorkflowRead extends WorkflowConfig {
  id: string;
  created_at: string;
  updated_at?: string;
  total_executions?: number;
  successful_executions?: number;
  last_executed?: string;
}

/**
 * Normalize backend WorkflowReadResponse to frontend WorkflowConfig structure.
 * Extracts steps/connections from configuration to top level.
 */
function normalizeWorkflowResponse(
  response: WorkflowReadResponse,
): WorkflowRead {
  const { configuration, ...rest } = response;
  return {
    ...rest,
    id: rest.id,
    name: rest.name,
    description: rest.description ?? configuration.description,
    version: rest.version ?? configuration.version ?? "1.0.0",
    steps: configuration.steps ?? [],
    connections: configuration.connections ?? [],
    global_config: rest.global_config ?? configuration.global_config ?? {},
    tags: rest.tags ?? configuration.tags ?? [],
    timeout_seconds: rest.timeout_seconds ?? configuration.timeout_seconds,
    created_by: rest.created_by ?? configuration.created_by,
    created_at: rest.created_at,
    updated_at: rest.updated_at ?? undefined,
    total_executions: rest.total_executions ?? undefined,
    successful_executions: rest.successful_executions ?? undefined,
    last_executed: rest.last_executed ?? undefined,
  };
}

export interface WorkflowsService {
  fetchAll: () => Promise<WorkflowRead[]>;
  fetchOne: (workflowId: string) => Promise<WorkflowRead>;
  create: (payload: WorkflowCreateRequest) => Promise<WorkflowRead>;
  update: (
    workflowId: string,
    payload: WorkflowUpdateRequest,
  ) => Promise<WorkflowRead>;
  delete: (workflowId: string) => Promise<WorkflowDeleteResponse>;
  execute: (
    workflowId: string,
    input: Record<string, unknown>,
  ) => Promise<ExecutionResultsResponse>;
  pollExecution: (
    workflowId: string,
    executionId: string,
  ) => Promise<ExecutionStatusResponse>;
}

export function createWorkflowsService(
  client: ApiClient = createApiClient({}),
): WorkflowsService {
  return {
    async fetchAll(): Promise<WorkflowRead[]> {
      const responses = await client.get<WorkflowReadResponse[]>("/workflows/");
      return responses.map(normalizeWorkflowResponse);
    },
    async fetchOne(workflowId: string): Promise<WorkflowRead> {
      const response = await client.get<WorkflowReadResponse>(
        `/workflows/${workflowId}`,
      );
      return normalizeWorkflowResponse(response);
    },
    async create(payload: WorkflowCreateRequest): Promise<WorkflowRead> {
      const response = await client.post<WorkflowReadResponse>(
        "/workflows",
        payload,
      );
      return normalizeWorkflowResponse(response);
    },
    async update(
      workflowId: string,
      payload: WorkflowUpdateRequest,
    ): Promise<WorkflowRead> {
      const response = await client.put<WorkflowReadResponse>(
        `/workflows/${workflowId}`,
        payload,
      );
      return normalizeWorkflowResponse(response);
    },
    delete(workflowId: string): Promise<WorkflowDeleteResponse> {
      return client.del<WorkflowDeleteResponse>(`/workflows/${workflowId}`);
    },
    execute(
      workflowId: string,
      input: Record<string, unknown>,
    ): Promise<ExecutionResultsResponse> {
      return client.post<ExecutionResultsResponse>(
        `/workflows/${workflowId}/execute`,
        { input },
      );
    },
    pollExecution(
      workflowId: string,
      executionId: string,
    ): Promise<ExecutionStatusResponse> {
      return client.get<ExecutionStatusResponse>(
        `/workflows/${workflowId}/executions/${executionId}`,
      );
    },
  };
}

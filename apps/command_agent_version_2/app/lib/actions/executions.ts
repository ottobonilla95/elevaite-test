"use server";
import { createApiClient } from "../api/client";
import { type NodeStatus } from "../model/uiEnums";


const client = createApiClient({});

export interface ExecutionStatus {
  execution_id: string;
  workflow_id: string;
  status: string;
  current_step?: string | null;
  completed_steps?: number | null;
  failed_steps?: number | null;
  pending_steps?: number | null;
  total_steps?: number | null;
  started_at?: string | null;
  completed_at?: string | null;
  error_message?: string | null;
  execution_time_seconds?: number | null;
  execution_summary?: Record<string, unknown>;
  step_io_data?: Record<string, unknown>;
  step_statuses?: Record<string, NodeStatus>;
}

export interface StepResult {
  step_id: string;
  status: string;
  output_data: Record<string, unknown> | null;
  error_message: string | null;
  execution_time_ms: number | null;
}

export interface ExecutionResults {
  execution_id: string;
  status: string;
  step_results: Record<string, StepResult>;
  step_io_data?: Record<string, unknown>;
  global_variables?: Record<string, unknown>;
  execution_summary?: Record<string, unknown>;
}

export interface ExecutionAnalytics {
  executions?: unknown[];
  db_executions?: unknown[];
  total?: number;
}

function isExecutionStatus(data: unknown): data is ExecutionStatus {
  return (
    typeof data === "object" &&
    data !== null &&
    typeof (data as ExecutionStatus).execution_id === "string" &&
    typeof (data as ExecutionStatus).status === "string"
  );
}

function isExecutionResults(data: unknown): data is ExecutionResults {
  return (
    typeof data === "object" &&
    data !== null &&
    typeof (data as ExecutionResults).execution_id === "string" &&
    typeof (data as ExecutionResults).status === "string"
  );
}

export async function getExecutionStatus(executionId: string) {
  const data = await client.get<ExecutionStatus>(`/api/executions/${executionId}`);
  if (!isExecutionStatus(data)) throw new Error("Invalid execution status payload");
  return data;
}

export async function getExecutionResults(executionId: string) {
  const data = await client.get<ExecutionResults>(`/api/executions/${executionId}/results`);
  if (!isExecutionResults(data)) throw new Error("Invalid execution results payload");
  return data;
}

export async function listExecutions(params?: {
  limit?: number;
  offset?: number;
  status?: string;
  workflow_id?: string;
  exclude_db?: boolean;
}) {
  const query = new URLSearchParams();
  if (params?.limit) query.set("limit", String(params.limit));
  if (params?.offset) query.set("offset", String(params.offset));
  if (params?.status) query.set("status", params.status);
  if (params?.workflow_id) query.set("workflow_id", params.workflow_id);
  if (params?.exclude_db) query.set("exclude_db", "true");
  const url = `/api/executions${query.toString() ? `?${query.toString()}` : ""}`;
  const data = await client.get<ExecutionAnalytics>(url);
  return data;
}

export async function executionStepCallback(executionId: string, stepId: string, callbackData: Record<string, unknown>) {
  const data = await client.post<{ status: string; message?: string }>(
    `/api/executions/${executionId}/steps/${stepId}/callback`,
    callbackData,
  );
  return data;
}

import type * as WorkflowSteps from "../workflowSteps";

/**
 * Runtime validation helpers for workflow step types.
 * Plain type guards (no external dependencies).
 * Used to validate incoming payloads from backend and catch shape mismatches early.
 */

function isRecord(data: unknown): data is Record<string, unknown> {
  return Boolean(data) && typeof data === "object" && !Array.isArray(data);
}

function isStringArray(data: unknown): data is string[] {
  return Array.isArray(data) && data.every((item) => typeof item === "string");
}

function isNumberArray(data: unknown): data is number[] {
  return Array.isArray(data) && data.every((item) => typeof item === "number");
}

export function isWorkflowConfig(
  data: unknown,
): data is WorkflowSteps.WorkflowConfig {
  if (!isRecord(data)) return false;
  if (typeof data.name !== "string") return false;
  if (!Array.isArray(data.steps)) return false;
  // Allow null or undefined for optional string fields (backend may return null)
  if (
    data.description !== undefined &&
    data.description !== null &&
    typeof data.description !== "string"
  )
    return false;
  if (
    data.version !== undefined &&
    data.version !== null &&
    typeof data.version !== "string"
  )
    return false;
  if (
    data.timeout_seconds !== undefined &&
    data.timeout_seconds !== null &&
    typeof data.timeout_seconds !== "number"
  )
    return false;
  return true;
}

export function isWorkflowConfigArray(
  data: unknown,
): data is WorkflowSteps.WorkflowConfig[] {
  return Array.isArray(data) && data.every(isWorkflowConfig);
}

export function isStepExecutionResult(
  data: unknown,
): data is WorkflowSteps.StepExecutionResult {
  if (!isRecord(data)) return false;
  if (typeof data.step_id !== "string") return false;
  if (typeof data.step_type !== "string") return false;
  if (typeof data.status !== "string") return false;
  if (data.error !== undefined && typeof data.error !== "string") return false;
  if (data.duration_ms !== undefined && typeof data.duration_ms !== "number")
    return false;
  return true;
}

export function isExecutionStatusResponse(
  data: unknown,
): data is WorkflowSteps.ExecutionStatusResponse {
  if (!isRecord(data)) return false;
  if (typeof data.id !== "string") return false;
  if (typeof data.workflow_id !== "string") return false;
  if (typeof data.status !== "string") return false;
  if (
    data.error_message !== undefined &&
    typeof data.error_message !== "string"
  )
    return false;
  if (data.started_at !== undefined && typeof data.started_at !== "string")
    return false;
  if (data.completed_at !== undefined && typeof data.completed_at !== "string")
    return false;
  return true;
}

export function isExecutionResultsResponse(
  data: unknown,
): data is WorkflowSteps.ExecutionResultsResponse {
  if (!isRecord(data)) return false;
  if (typeof data.id !== "string") return false;
  if (typeof data.workflow_id !== "string") return false;
  if (typeof data.status !== "string") return false;
  if (data.output_data !== undefined && !isRecord(data.output_data))
    return false;
  if (data.step_io_data !== undefined && !isRecord(data.step_io_data))
    return false;
  if (data.started_at !== undefined && typeof data.started_at !== "string")
    return false;
  // if (data.completed_at !== undefined && typeof data.completed_at !== "string") return false;
  return true;
}

export function safeValidateWorkflowConfig(
  data: unknown,
): [WorkflowSteps.WorkflowConfig | null, string | null] {
  if (!isWorkflowConfig(data)) {
    return [null, "Workflow config shape mismatch"];
  }
  return [data, null];
}

export function safeValidateExecutionStatusResponse(
  data: unknown,
): [WorkflowSteps.ExecutionStatusResponse | null, string | null] {
  if (!isExecutionStatusResponse(data)) {
    return [null, "Execution status response shape mismatch"];
  }
  return [data, null];
}

export function safeValidateExecutionResultsResponse(
  data: unknown,
): [WorkflowSteps.ExecutionResultsResponse | null, string | null] {
  if (!isExecutionResultsResponse(data)) {
    return [null, "Execution results response shape mismatch"];
  }
  return [data, null];
}

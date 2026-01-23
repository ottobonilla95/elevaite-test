import type { WorkflowConfig, ExecutionStatusResponse } from "../model/workflowSteps";
import { safeValidateWorkflowConfig, safeValidateExecutionStatusResponse } from "../model/schemas/workflowSteps.schema";
import { isObject } from "./common";

export function isWorkflowConfig(data: unknown): data is WorkflowConfig {
  if (!isObject(data) || typeof data.name !== "string" || !Array.isArray(data.steps ?? [])) {
    return false;
  }
  const [, error] = safeValidateWorkflowConfig(data);
  return !error;
}

export function isWorkflowConfigArray(data: unknown): data is WorkflowConfig[] {
  return Array.isArray(data) && data.every(isWorkflowConfig);
}

export function isExecutionStatusResponse(data: unknown): data is ExecutionStatusResponse {
  if (!isObject(data) || typeof data.id !== "string" || typeof data.workflow_id !== "string") {
    return false;
  }
  const [, error] = safeValidateExecutionStatusResponse(data);
  return !error;
}

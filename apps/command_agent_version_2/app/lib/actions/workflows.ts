"use server";

import { createWorkflowsService } from "../api/services/workflows";
import { isWorkflowConfig, isWorkflowConfigArray } from "../discriminators/workflows";
import { safeValidateWorkflowConfig, safeValidateExecutionResultsResponse } from "../model/schemas/workflowSteps.schema";
import type { WorkflowConfig, ExecutionResultsResponse } from "../model/workflowSteps";

const service = createWorkflowsService();

export async function listWorkflows(): Promise<WorkflowConfig[]> {
  const data = await service.fetchAll();
  if (!isWorkflowConfigArray(data)) throw new Error("Invalid workflow list payload");
  return data;
}

export async function getWorkflow(workflowId: string): Promise<WorkflowConfig> {
  const data = await service.fetchOne(workflowId);
  if (!isWorkflowConfig(data)) throw new Error("Invalid workflow payload");
  return data;
}

export async function saveWorkflow(payload: WorkflowConfig): Promise<WorkflowConfig> {
  const [valid, error] = safeValidateWorkflowConfig(payload);
  if (error || !valid) throw new Error(`Workflow validation failed: ${error ?? "unknown"}`);
  const data = await service.create(valid);
  // if (!isWorkflowConfig(data)) throw new Error("Invalid workflow response");
  return data;
}

export async function updateWorkflow(workflowId: string, payload: Partial<WorkflowConfig>): Promise<WorkflowConfig> {
  const data = await service.update(workflowId, payload);
  if (!isWorkflowConfig(data)) throw new Error("Invalid workflow response");
  return data;
}

export async function deleteWorkflow(workflowId: string): Promise<void> {
  await service.delete(workflowId);
}

export async function executeWorkflow(workflowId: string, input: Record<string, unknown>): Promise<ExecutionResultsResponse> {
  const data = await service.execute(workflowId, input);
  console.log("Data", data);
  const [valid, error] = safeValidateExecutionResultsResponse(data);
  if (error || !valid) throw new Error(`Execution validation failed: ${error ?? "unknown"}`);
  return valid;
}

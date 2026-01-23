import type { StepConfig, StepType } from "../model/workflowSteps";
import { isAgentExecutionStepConfig } from "./agents";
import { isToolExecutionStepConfig } from "./tools";
import { isWorkflowConfig } from "./workflows";

export interface StepDiscriminatorResult {
  step_type: StepType;
  actionKey: string;
  displayName?: string;
}

export function getStepDiscriminator(step: StepConfig): StepDiscriminatorResult {
  if (isAgentExecutionStepConfig(step)) return { step_type: step.step_type, actionKey: "agentExecution", displayName: step.step_name ?? "Agent" };
  if (isToolExecutionStepConfig(step)) return { step_type: step.step_type, actionKey: "toolExecution", displayName: step.step_name ?? "Tool" };
  return { step_type: step.step_type, actionKey: step.step_type, displayName: step.step_name ?? step.step_type };
}

// Optional helpers for payload discrimination.
export const isWorkflowConfigLike = isWorkflowConfig;

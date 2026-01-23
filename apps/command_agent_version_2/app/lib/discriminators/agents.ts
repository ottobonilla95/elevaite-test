import type { AgentExecutionStepConfig } from "../model/workflowSteps";
import { isObject } from "./common";

export function isAgentSummary(data: unknown): data is { id: string; name: string } {
  return isObject(data) && typeof data.id === "string" && typeof data.name === "string";
}

export function isAgentExecutionStepConfig(step: unknown): step is AgentExecutionStepConfig {
  return isObject(step) && step.step_type === "agent_execution";
}

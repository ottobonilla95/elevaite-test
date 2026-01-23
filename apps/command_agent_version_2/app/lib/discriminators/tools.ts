import type { ToolExecutionStepConfig } from "../model/workflowSteps";
import { isObject } from "./common";

export function isToolSummary(data: unknown): data is { id: string; name: string } {
  return isObject(data) && typeof data.id === "string" && typeof data.name === "string";
}

export function isToolExecutionStepConfig(step: unknown): step is ToolExecutionStepConfig {
  return isObject(step) && step.step_type === "tool_execution";
}

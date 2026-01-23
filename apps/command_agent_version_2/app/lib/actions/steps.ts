"use server";

import { createApiClient } from "../api/client";

const client = createApiClient({});

export interface StepConfig {
  step_type: string;
  description?: string;
  input_schema?: Record<string, unknown>;
  output_schema?: Record<string, unknown>;
}

export interface StepInfo {
  step_type: string;
  description?: string;
  input_schema?: Record<string, unknown>;
  output_schema?: Record<string, unknown>;
}

export interface RegisteredStepsResponse {
  steps: StepInfo[];
  total: number;
}

export interface StepRegistrationResponse {
  message: string;
  step_type: string;
}

function isStepInfo(data: unknown): data is StepInfo {
  return typeof data === "object" && data !== null && typeof (data as StepInfo).step_type === "string";
}

export async function listSteps() {
  const data = await client.get<RegisteredStepsResponse>("/api/steps/");
  if (!data.steps || !Array.isArray(data.steps)) {
    throw new Error("Invalid steps list payload");
  }
  return data;
}

export async function getStep(stepType: string) {
  const data = await client.get<StepInfo>(`/api/steps/${stepType}`);
  if (!isStepInfo(data)) throw new Error("Invalid step info payload");
  return data;
}

export async function registerStep(config: StepConfig) {
  const data = await client.post<StepRegistrationResponse>("/api/steps/register", config);
  return data;
}

// Builtin Variables

export interface BuiltInVariable {
  name: string;
  description: string;
  example: string;
  category: string;
  source: "builtin";
}

export interface BuiltInVariablesResponse {
  variables: BuiltInVariable[];
  total: number;
}

export async function getBuiltInVariables(): Promise<BuiltInVariablesResponse> {
  const data = await client.get<BuiltInVariablesResponse>("/api/steps/variables/builtin");
  if (!Array.isArray(data.variables)) {
    throw new Error("Invalid builtin variables payload");
  }
  return data;
}

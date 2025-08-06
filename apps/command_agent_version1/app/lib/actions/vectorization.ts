"use server";

import { BACKEND_URL } from "../constants";

// Helper function to construct API URLs properly
function buildApiUrl(endpoint: string): string {
  if (!BACKEND_URL) {
    throw new Error("Backend URL is not configured");
  }

  // Remove trailing slash from backend URL and leading slash from endpoint
  const baseUrl = BACKEND_URL.replace(/\/$/, "");
  const cleanEndpoint = endpoint.replace(/^\//, "");

  return `${baseUrl}/${cleanEndpoint}`;
}

// Types for vectorization API
export interface VectorizationStepConfig {
  step_type: string;
  config: Record<string, unknown>;
}

export interface VectorizationPipelineRequest {
  steps: VectorizationStepConfig[];
  file_id?: string;
  pipeline_name?: string;
}

export interface VectorizationPipelineResponse {
  pipeline_id: string;
  status: string;
  message: string;
  steps_completed: number;
  total_steps: number;
  results?: Record<string, unknown>;
}

/**
 * Execute a vectorization pipeline with the provided steps and file
 */
export async function executeVectorizationPipeline(
  request: VectorizationPipelineRequest
): Promise<VectorizationPipelineResponse> {
  const url = buildApiUrl("api/vectorization/pipeline/execute");

  try {
    const response = await fetch(url, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`HTTP ${response.status}: ${errorText}`);
    }

    const data = await response.json();
    return data as VectorizationPipelineResponse;
  } catch (error) {
    console.error("Failed to execute vectorization pipeline:", error);
    throw error;
  }
}

/**
 * Get the status of a vectorization pipeline
 */
export async function getVectorizationPipelineStatus(
  pipelineId: string
): Promise<VectorizationPipelineResponse> {
  const url = buildApiUrl(`api/vectorization/pipeline/${pipelineId}/status`);

  try {
    const response = await fetch(url, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
      },
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`HTTP ${response.status}: ${errorText}`);
    }

    const data = await response.json();
    return data as VectorizationPipelineResponse;
  } catch (error) {
    console.error("Failed to get pipeline status:", error);
    throw error;
  }
}

/**
 * Get a template configuration for vectorization pipeline
 */
export async function getVectorizationConfigTemplate(): Promise<
  Record<string, unknown>
> {
  const url = buildApiUrl("api/vectorization/config/template");

  try {
    const response = await fetch(url, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
      },
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`HTTP ${response.status}: ${errorText}`);
    }

    const data = await response.json();
    return data as Record<string, unknown>;
  } catch (error) {
    console.error("Failed to get config template:", error);
    throw error;
  }
}

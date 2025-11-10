"use server";

import {
  isAgentResponseArray,
  isAgentResponse,
} from "../discriminators/agents";
import type {
  AgentResponse,
  AgentCreate,
  AgentUpdate,
  AgentExecutionRequest,
  AgentExecutionResponse,
  AgentStreamExecutionRequest,
} from "../interfaces/agents";
import type { ChatCompletionToolParam } from "../interfaces/common";
import { BACKEND_URL } from "../constants";

export async function fetchAllAgents(
  skip = 0,
  limit = 100,
  deployed?: boolean
): Promise<AgentResponse[]> {
  const url = new URL(`${BACKEND_URL ?? ""}api/agents/`);

  // Add query parameters
  url.searchParams.append("skip", skip.toString());
  url.searchParams.append("limit", limit.toString());
  if (deployed !== undefined) {
    url.searchParams.append("deployed", deployed.toString());
  }

  const response = await fetch(url);
  if (!response.ok) throw new Error("Failed to fetch agents");

  const data: unknown = await response.json();
  if (isAgentResponseArray(data)) return data;
  throw new Error("Invalid data type - expected array of agents");
}

export async function fetchAvailableAgents(): Promise<AgentResponse[]> {
  const url = new URL(`${BACKEND_URL ?? ""}api/agents/deployment/available`);

  const response = await fetch(url);
  if (!response.ok) throw new Error("Failed to fetch available agents");

  const data: unknown = await response.json();
  if (isAgentResponseArray(data)) return data;
  throw new Error("Invalid data type - expected array of agents");
}

export async function fetchAgent(agentId: string): Promise<AgentResponse> {
  const url = new URL(`${BACKEND_URL ?? ""}api/agents/${agentId}`);

  const response = await fetch(url);
  if (!response.ok) {
    if (response.status === 404) {
      throw new Error("Agent not found");
    }
    throw new Error("Failed to fetch agent");
  }

  const data: unknown = await response.json();
  if (isAgentResponse(data)) return data;
  throw new Error("Invalid data type - expected agent response");
}

export async function updateAgent(
  agentId: string,
  agentUpdate: AgentUpdate
): Promise<AgentResponse> {
  const url = new URL(`${BACKEND_URL ?? ""}api/agents/${agentId}`);

  console.log("=== UPDATE AGENT REQUEST ===");
  console.log("Agent ID:", agentId);
  console.log("Update payload:", JSON.stringify(agentUpdate, null, 2));
  console.log("===========================");

  const response = await fetch(url, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(agentUpdate),
  });

  if (!response.ok) throw new Error("Failed to update agent");

  const data: unknown = await response.json();
  if (isAgentResponse(data)) return data;
  throw new Error("Invalid data type - expected agent response");
}

export async function updateAgentFunctions(
  agentId: string,
  functions: ChatCompletionToolParam[]
): Promise<AgentResponse> {
  return updateAgent(agentId, { functions });
}

export async function createAgent(
  agentData: AgentCreate
): Promise<AgentResponse> {
  const url = new URL(`${BACKEND_URL ?? ""}api/agents/`);

  const response = await fetch(url, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(agentData),
  });

  if (!response.ok) throw new Error("Failed to create agent");

  const data: unknown = await response.json();
  if (isAgentResponse(data)) return data;
  throw new Error("Invalid data type - expected agent response");
}

// Execute a specific agent
export async function executeAgent(
  agentId: string,
  executionRequest: AgentExecutionRequest
): Promise<AgentExecutionResponse> {
  const url = new URL(`${BACKEND_URL ?? ""}api/agents/${agentId}/execute`);

  const response = await fetch(url, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(executionRequest),
  });

  if (!response.ok) {
    if (response.status === 404) {
      throw new Error("Agent not found");
    } else if (response.status === 400) {
      throw new Error("Agent is not available for execution");
    }
    throw new Error("Failed to execute agent");
  }

  const data: unknown = await response.json();
  // Basic validation - could be enhanced with proper discriminator
  if (typeof data === "object" && data !== null && "status" in data) {
    return data as AgentExecutionResponse;
  }
  throw new Error("Invalid data type - expected agent execution response");
}

// Execute a specific agent with streaming
export async function executeAgentStream(
  agentId: string,
  executionRequest: AgentStreamExecutionRequest
): Promise<ReadableStream<Uint8Array> | null> {
  const url = new URL(
    `${BACKEND_URL ?? ""}api/agents/${agentId}/execute/stream`
  );

  const response = await fetch(url, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(executionRequest),
  });

  if (!response.ok) {
    if (response.status === 404) {
      throw new Error("Agent not found");
    } else if (response.status === 400) {
      throw new Error("Agent is not available for execution");
    }
    throw new Error("Failed to execute agent stream");
  }

  return response.body;
}

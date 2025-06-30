import { type PromptResponse, type PromptCreate, type PromptUpdate } from "../interfaces";

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL;

// Type guards for prompt responses
function isPromptResponse(data: unknown): data is PromptResponse {
  return (
    typeof data === "object" &&
    data !== null &&
    typeof (data as PromptResponse).prompt_label === "string" &&
    typeof (data as PromptResponse).prompt === "string" &&
    typeof (data as PromptResponse).unique_label === "string" &&
    typeof (data as PromptResponse).app_name === "string" &&
    typeof (data as PromptResponse).version === "string" &&
    typeof (data as PromptResponse).ai_model_provider === "string" &&
    typeof (data as PromptResponse).ai_model_name === "string"
  );
}

function isPromptResponseArray(data: unknown): data is PromptResponse[] {
  return Array.isArray(data) && data.every(isPromptResponse);
}

// Fetch all prompts with optional filtering
export async function fetchAllPrompts(
  skip = 0,
  limit = 100,
  appName?: string
): Promise<PromptResponse[]> {
  const url = new URL(`${BACKEND_URL ?? ""}api/prompts/`);

  // Add query parameters
  url.searchParams.append("skip", skip.toString());
  url.searchParams.append("limit", limit.toString());
  if (appName) {
    url.searchParams.append("app_name", appName);
  }

  const response = await fetch(url);
  if (!response.ok) throw new Error("Failed to fetch prompts");

  const data: unknown = await response.json();
  if (isPromptResponseArray(data)) return data;
  throw new Error("Invalid data type - expected array of prompts");
}

// Fetch a specific prompt by ID
export async function fetchPrompt(promptId: string): Promise<PromptResponse> {
  const url = new URL(`${BACKEND_URL ?? ""}api/prompts/${promptId}`);

  const response = await fetch(url);
  if (!response.ok) {
    if (response.status === 404) {
      throw new Error("Prompt not found");
    }
    throw new Error("Failed to fetch prompt");
  }

  const data: unknown = await response.json();
  if (isPromptResponse(data)) return data;
  throw new Error("Invalid data type - expected prompt response");
}

// Fetch prompts by app name and label
export async function fetchPromptsByAppAndLabel(
  appName: string,
  promptLabel: string
): Promise<PromptResponse[]> {
  const url = new URL(`${BACKEND_URL ?? ""}api/prompts/app/${appName}/label/${promptLabel}`);

  const response = await fetch(url);
  if (!response.ok) throw new Error("Failed to fetch prompts by app and label");

  const data: unknown = await response.json();
  if (isPromptResponseArray(data)) return data;
  throw new Error("Invalid data type - expected array of prompts");
}

// Fetch deployed prompt for an app and label
export async function fetchDeployedPrompt(
  appName: string,
  promptLabel: string
): Promise<PromptResponse> {
  const url = new URL(`${BACKEND_URL ?? ""}api/prompts/app/${appName}/label/${promptLabel}/deployed`);

  const response = await fetch(url);
  if (!response.ok) {
    if (response.status === 404) {
      throw new Error("Deployed prompt not found");
    }
    throw new Error("Failed to fetch deployed prompt");
  }

  const data: unknown = await response.json();
  if (isPromptResponse(data)) return data;
  throw new Error("Invalid data type - expected prompt response");
}

// Create a new prompt
export async function createPrompt(promptData: PromptCreate): Promise<PromptResponse> {
  const url = new URL(`${BACKEND_URL ?? ""}api/prompts/`);

  const response = await fetch(url, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(promptData),
  });

  if (!response.ok) throw new Error("Failed to create prompt");

  const data: unknown = await response.json();
  if (isPromptResponse(data)) return data;
  throw new Error("Invalid data type - expected prompt response");
}

// Update an existing prompt
export async function updatePrompt(
  promptId: string,
  promptUpdate: PromptUpdate
): Promise<PromptResponse> {
  const url = new URL(`${BACKEND_URL ?? ""}api/prompts/${promptId}`);

  const response = await fetch(url, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(promptUpdate),
  });

  if (!response.ok) throw new Error("Failed to update prompt");

  const data: unknown = await response.json();
  if (isPromptResponse(data)) return data;
  throw new Error("Invalid data type - expected prompt response");
}

// Delete a prompt
export async function deletePrompt(promptId: string): Promise<boolean> {
  const url = new URL(`${BACKEND_URL ?? ""}api/prompts/${promptId}`);

  const response = await fetch(url, {
    method: "DELETE",
  });

  if (!response.ok) {
    if (response.status === 404) {
      throw new Error("Prompt not found");
    }
    throw new Error("Failed to delete prompt");
  }

  return await response.json() as boolean;
}

// Deploy a prompt
export async function deployPrompt(
  promptId: string,
  appName: string,
  environment = "production"
): Promise<PromptResponse> {
  const url = new URL(`${BACKEND_URL ?? ""}api/prompts/deploy`);

  const deployRequest = {
    pid: promptId,
    app_name: appName,
    environment,
  };

  const response = await fetch(url, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(deployRequest),
  });

  if (!response.ok) {
    if (response.status === 404) {
      throw new Error("Prompt not found or app name mismatch");
    }
    throw new Error("Failed to deploy prompt");
  }

  const data: unknown = await response.json();
  if (isPromptResponse(data)) return data;
  throw new Error("Invalid data type - expected prompt response");
}

// Fetch prompts for agent configuration (filtered for agent-studio app)
export async function fetchAgentPrompts(): Promise<PromptResponse[]> {
  return fetchAllPrompts(0, 100, "agent_studio");
}

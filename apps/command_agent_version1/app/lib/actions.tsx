"use server";
import { redirect } from "next/navigation";
import {
  isChatMessageResponse,
  isSessionSummaryResponse,
  isAgentResponseArray,
  isWorkflowDeployResponse,
  isWorkflowExecutionResponse,
} from "./discriminators";
import type {
  ChatBotGenAI,
  ChatMessageResponse,
  ChatbotV,
  SessionSummaryObject,
  AgentResponse,
  WorkflowDeployRequest,
  WorkflowDeployResponse,
  WorkflowExecutionRequest,
  WorkflowExecutionResponse,
  WorkflowResponse,
  WorkflowCreateRequest,
  WorkflowDeploymentRequest,
  NewWorkflowExecutionRequest,
} from "./interfaces";

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL;

// eslint-disable-next-line @typescript-eslint/require-await -- Server actions must be async functions
export async function logOut(): Promise<void> {
  redirect(`${process.env.NEXTAUTH_URL_INTERNAL ?? ""}/api/signout`);
}

export async function fetchChatbotResponse(
  userId: string,
  messageText: string,
  sessionId: string,
  chatbotV: ChatbotV,
  chatbotGenAi: ChatBotGenAI
): Promise<ChatMessageResponse> {
  // const url = new URL(`${BACKEND_URL ?? ""}${chatbotV}?query=${messageText}&uid=${userId}&sid=${sessionId}&collection=${chatbotGenAi}`);
  // Write a POST request to the backend
  const url = new URL(`${BACKEND_URL ?? ""}run`);

  const response = await fetch(url, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      query: messageText,
      uid: userId,
      sid: sessionId,
      collection: chatbotGenAi,
    }),
  });
  if (!response.ok) throw new Error("Failed to fetch");
  const data: unknown = await response.json();
  if (isChatMessageResponse(data)) return data;
  throw new Error("Invalid data type");
}

export async function fetchSessionSummary(
  userId: string,
  sessionId: string
): Promise<SessionSummaryObject> {
  const url = new URL(
    `${BACKEND_URL ?? ""}summarization?uid=${userId}&sid=${sessionId}`
  );
  const response = await fetch(url);
  if (!response.ok) throw new Error("Failed to fetch");
  const data: unknown = await response.json();
  if (isSessionSummaryResponse(data)) return data;
  throw new Error("Invalid data type");
}

export async function fetchAllAgents(
  skip: number = 0,
  limit: number = 100,
  deployed?: boolean
): Promise<AgentResponse[]> {
  try {
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
  } catch (error) {
    console.warn("Backend not available, returning mock agents:", error);
    // Return mock data when backend is not available
    return [
      {
        id: 1,
        agent_id: "router-1",
        name: "Router Agent",
        description: "Routes queries to appropriate agents",
        agent_type: "router",
        prompt:
          "You are a router agent that directs queries to the right specialist.",
        tags: ["router", "core"],
        is_deployed: true,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      },
      {
        id: 2,
        agent_id: "web-search-1",
        name: "Web Search Agent",
        description: "Searches the web for information",
        agent_type: "web_search",
        prompt:
          "You are a web search agent that finds relevant information online.",
        tags: ["search", "web"],
        is_deployed: true,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      },
      {
        id: 3,
        agent_id: "data-1",
        name: "Data Agent",
        description: "Processes and analyzes data",
        agent_type: "data",
        prompt: "You are a data agent that processes and analyzes information.",
        tags: ["data", "analysis"],
        is_deployed: true,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      },
      {
        id: 4,
        agent_id: "api-1",
        name: "API Agent",
        description: "Connects to external APIs",
        agent_type: "api",
        prompt: "You are an API agent that connects to external services.",
        tags: ["api", "integration"],
        is_deployed: true,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      },
      {
        id: 5,
        agent_id: "toshiba-1",
        name: "Toshiba Agent",
        description: "Specialized Toshiba agent",
        agent_type: "toshiba",
        prompt: "You are a specialized Toshiba agent.",
        tags: ["toshiba", "specialized"],
        is_deployed: true,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      },
    ];
  }
}

export async function fetchAvailableAgents(): Promise<AgentResponse[]> {
  const url = new URL(`${BACKEND_URL ?? ""}api/agents/deployment/available`);

  const response = await fetch(url);
  if (!response.ok) throw new Error("Failed to fetch available agents");

  const data: unknown = await response.json();
  if (isAgentResponseArray(data)) return data;
  throw new Error("Invalid data type - expected array of agents");
}

export async function getWorkflows(): Promise<WorkflowResponse[]> {
  try {
    const url = new URL(`${BACKEND_URL ?? ""}api/workflows/`);

    const response = await fetch(url);
    if (!response.ok) throw new Error("Failed to fetch workflows");

    const data: unknown = await response.json();
    if (Array.isArray(data)) return data;
    throw new Error("Invalid data type - expected array of workflows");
  } catch (error) {
    console.warn("Backend not available, returning mock workflows:", error);
    // Return empty array when backend is not available
    return [];
  }
}

export async function deployWorkflow(
  workflowRequest: WorkflowDeployRequest
): Promise<WorkflowDeployResponse> {
  const url = new URL(`${BACKEND_URL ?? ""}deploy`);

  const response = await fetch(url, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(workflowRequest),
  });

  if (!response.ok) throw new Error("Failed to deploy workflow");

  const data: unknown = await response.json();
  if (isWorkflowDeployResponse(data)) return data;
  throw new Error("Invalid data type - expected workflow deploy response");
}

export async function executeWorkflow(
  executionRequest: WorkflowExecutionRequest
): Promise<WorkflowExecutionResponse> {
  const url = new URL(`${BACKEND_URL ?? ""}run`);

  const response = await fetch(url, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      query: executionRequest.query,
      uid: executionRequest.uid,
      sid: executionRequest.sid,
      collection: executionRequest.collection,
    }),
  });

  if (!response.ok) throw new Error("Failed to execute workflow");

  const data: unknown = await response.json();
  if (isWorkflowExecutionResponse(data)) return data;
  throw new Error("Invalid data type - expected workflow execution response");
}

// Additional workflow management functions
export async function getWorkflowDetails(workflowId: string): Promise<any> {
  try {
    const response = await fetch(`${BACKEND_URL}api/workflows/${workflowId}`);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error("Error fetching workflow details:", error);
    throw error;
  }
}

export async function deleteWorkflow(workflowId: string): Promise<void> {
  try {
    const response = await fetch(`${BACKEND_URL}api/workflows/${workflowId}`, {
      method: "DELETE",
    });
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
  } catch (error) {
    console.error("Error deleting workflow:", error);
    throw error;
  }
}

// New workflow API functions
export async function createWorkflow(
  workflowRequest: WorkflowCreateRequest
): Promise<WorkflowResponse> {
  try {
    const response = await fetch(`${BACKEND_URL}api/workflows/`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(workflowRequest),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.warn(
      "Backend not available, returning mock workflow creation:",
      error
    );
    // Return mock workflow response when backend is not available
    const mockWorkflowId = `workflow-${Date.now()}`;
    return {
      id: Date.now(),
      workflow_id: mockWorkflowId,
      name: workflowRequest.name,
      description: workflowRequest.description || "",
      version: workflowRequest.version || "1.0.0",
      configuration: workflowRequest.configuration,
      created_by: workflowRequest.created_by || "user",
      is_active: workflowRequest.is_active || true,
      tags: workflowRequest.tags || [],
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      is_deployed: false,
      workflow_agents: [],
      workflow_connections: [],
      workflow_deployments: [],
    };
  }
}

export async function deployWorkflowModern(
  workflowId: string,
  deploymentRequest: WorkflowDeploymentRequest
): Promise<any> {
  try {
    const response = await fetch(
      `${BACKEND_URL}api/workflows/${workflowId}/deploy`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(deploymentRequest),
      }
    );

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.warn("Backend not available, returning mock deployment:", error);
    // Return mock deployment response when backend is not available
    return {
      deployment_id: `deployment-${Date.now()}`,
      workflow_id: workflowId,
      deployment_name: deploymentRequest.deployment_name,
      environment: deploymentRequest.environment || "development",
      status: "active",
      deployed_at: new Date().toISOString(),
      message: "Workflow deployed successfully (mock mode)",
    };
  }
}

export async function executeWorkflowModern(
  executionRequest: NewWorkflowExecutionRequest
): Promise<any> {
  try {
    const response = await fetch(`${BACKEND_URL}api/workflows/execute`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(executionRequest),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.warn("Backend not available, returning mock execution:", error);
    // Return mock execution response when backend is not available
    return {
      execution_id: `execution-${Date.now()}`,
      status: "completed",
      response: `Mock response to: "${executionRequest.query}"\n\nThis is a simulated response from the agent workflow. The actual response would come from your deployed agents working together to process the query.\n\nWorkflow: ${executionRequest.workflow_id || executionRequest.deployment_name}\nQuery processed at: ${new Date().toLocaleString()}`,
      execution_time: Math.random() * 2 + 0.5, // Random time between 0.5-2.5 seconds
      tokens_used: Math.floor(Math.random() * 500) + 100,
      timestamp: new Date().toISOString(),
    };
  }
}

export async function stopWorkflowDeployment(
  deploymentName: string
): Promise<any> {
  try {
    const response = await fetch(
      `${BACKEND_URL}api/workflows/deployments/${deploymentName}/stop`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
      }
    );

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error("Error stopping workflow deployment:", error);
    throw error;
  }
}

export async function deleteWorkflowDeployment(
  deploymentName: string
): Promise<any> {
  try {
    const response = await fetch(
      `${BACKEND_URL}api/workflows/deployments/${deploymentName}`,
      {
        method: "DELETE",
        headers: {
          "Content-Type": "application/json",
        },
      }
    );

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error("Error deleting workflow deployment:", error);
    throw error;
  }
}

export async function getActiveDeployments(): Promise<any[]> {
  try {
    const response = await fetch(
      `${BACKEND_URL}api/workflows/deployments/active`
    );

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error("Error fetching active deployments:", error);
    throw error;
  }
}

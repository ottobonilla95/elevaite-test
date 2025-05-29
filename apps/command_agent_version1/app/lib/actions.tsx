"use server";
import { redirect } from "next/navigation";
import { isChatMessageResponse, isSessionSummaryResponse, isAgentResponseArray, isWorkflowDeployResponse, isWorkflowExecutionResponse } from "./discriminators";
import type { ChatBotGenAI, ChatMessageResponse, ChatbotV, SessionSummaryObject, AgentResponse, WorkflowDeployRequest, WorkflowDeployResponse, WorkflowExecutionRequest, WorkflowExecutionResponse } from "./interfaces";



const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL;



// eslint-disable-next-line @typescript-eslint/require-await -- Server actions must be async functions
export async function logOut(): Promise<void> {
  redirect(`${process.env.NEXTAUTH_URL_INTERNAL ?? ""}/api/signout`);
}



export async function fetchChatbotResponse(userId: string, messageText: string, sessionId: string, chatbotV: ChatbotV, chatbotGenAi: ChatBotGenAI): Promise<ChatMessageResponse> {
  // const url = new URL(`${BACKEND_URL ?? ""}${chatbotV}?query=${messageText}&uid=${userId}&sid=${sessionId}&collection=${chatbotGenAi}`);
  // Write a POST request to the backend
  const url = new URL(`${BACKEND_URL ?? ""}run`);

  const response = await fetch(url
    , {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        "query": messageText,
        "uid": userId,
        "sid": sessionId,
        "collection": chatbotGenAi,
      }),
    });
  if (!response.ok) throw new Error("Failed to fetch");
  const data: unknown = await response.json();
  if (isChatMessageResponse(data)) return data;
  throw new Error("Invalid data type");
}



export async function fetchSessionSummary(userId: string, sessionId: string): Promise<SessionSummaryObject> {
  const url = new URL(`${BACKEND_URL ?? ""}summarization?uid=${userId}&sid=${sessionId}`);
  const response = await fetch(url);
  if (!response.ok) throw new Error("Failed to fetch");
  const data: unknown = await response.json();
  if (isSessionSummaryResponse(data)) return data;
  throw new Error("Invalid data type");
}

export async function fetchAllAgents(skip: number = 0, limit: number = 100, deployed?: boolean): Promise<AgentResponse[]> {
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

export async function deployWorkflow(workflowRequest: WorkflowDeployRequest): Promise<WorkflowDeployResponse> {
  const url = new URL(`${BACKEND_URL ?? ""}deploy`);

  const response = await fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(workflowRequest),
  });

  if (!response.ok) throw new Error("Failed to deploy workflow");

  const data: unknown = await response.json();
  if (isWorkflowDeployResponse(data)) return data;
  throw new Error("Invalid data type - expected workflow deploy response");
}

export async function executeWorkflow(executionRequest: WorkflowExecutionRequest): Promise<WorkflowExecutionResponse> {
  const url = new URL(`${BACKEND_URL ?? ""}run`);

  const response = await fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
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




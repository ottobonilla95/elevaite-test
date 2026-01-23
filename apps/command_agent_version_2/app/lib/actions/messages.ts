"use server";

import { createApiClient } from "../api/client";

const client = createApiClient({});

export interface AgentMessage {
  id: string;
  execution_id: string;
  step_id: string;
  role: string;
  content: string;
  metadata?: Record<string, unknown>;
  user_id?: string;
  session_id?: string;
  created_at: string;
}

export interface AgentMessageCreate {
  role: string;
  content: string;
  metadata?: Record<string, unknown>;
  user_id?: string;
  session_id?: string;
}

function isAgentMessage(data: unknown): data is AgentMessage {
  return (
    typeof data === "object" &&
    data !== null &&
    typeof (data as AgentMessage).id === "string" &&
    typeof (data as AgentMessage).role === "string" &&
    typeof (data as AgentMessage).content === "string"
  );
}

export async function listMessages(executionId: string, stepId: string, params?: { limit?: number; offset?: number }) {
  const query = new URLSearchParams();
  if (params?.limit) query.set("limit", String(params.limit));
  if (params?.offset) query.set("offset", String(params.offset));
  const url = `/api/executions/${executionId}/steps/${stepId}/messages${query.toString() ? `?${query.toString()}` : ""}`;
  const data = await client.get<AgentMessage[]>(url);
  if (!Array.isArray(data) || !data.every(isAgentMessage)) {
    throw new Error("Invalid message list payload");
  }
  return data;
}

export async function createMessage(executionId: string, stepId: string, payload: AgentMessageCreate) {
  const data = await client.post<AgentMessage>(
    `/api/executions/${executionId}/steps/${stepId}/messages`,
    payload,
  );
  if (!isAgentMessage(data)) throw new Error("Invalid message payload");
  return data;
}

"use server";

import { createApiClient } from "../api/client";

const client = createApiClient({});

export interface A2AAgent {
  id: string;
  name: string;
  description?: string;
  base_url: string;
  agent_card_url?: string;
  organization_id?: string;
  status?: string;
  auth_type?: string;
  auth_config?: Record<string, unknown>;
  tags?: string[];
  cached_agent_card?: Record<string, unknown>;
  is_healthy?: boolean;
  last_health_check?: string;
  health_error_message?: string;
  created_at?: string;
  updated_at?: string;
  created_by?: string;
}

export interface A2AAgentCreate {
  name: string;
  description?: string;
  base_url: string;
  agent_card_url?: string;
  organization_id?: string;
  auth_type?: string;
  auth_config?: Record<string, unknown>;
  tags?: string[];
}

export interface A2AAgentUpdate {
  name?: string;
  description?: string;
  base_url?: string;
  agent_card_url?: string;
  status?: string;
  auth_type?: string;
  auth_config?: Record<string, unknown>;
  tags?: string[];
}

function isA2AAgent(data: unknown): data is A2AAgent {
  return (
    typeof data === "object" &&
    data !== null &&
    typeof (data as A2AAgent).id === "string" &&
    typeof (data as A2AAgent).name === "string" &&
    typeof (data as A2AAgent).base_url === "string"
  );
}

export async function listA2AAgents(params?: {
  organization_id?: string;
  status?: string;
  tag?: string;
  q?: string;
  limit?: number;
  offset?: number;
}) {
  const query = new URLSearchParams();
  if (params?.organization_id) query.set("organization_id", params.organization_id);
  if (params?.status) query.set("status", params.status);
  if (params?.tag) query.set("tag", params.tag);
  if (params?.q) query.set("q", params.q);
  if (params?.limit) query.set("limit", String(params.limit));
  if (params?.offset) query.set("offset", String(params.offset));
  const url = `/api/a2a-agents${query.toString() ? `?${query.toString()}` : ""}`;
  const data = await client.get<A2AAgent[]>(url);
  if (!Array.isArray(data) || !data.every(isA2AAgent)) {
    throw new Error("Invalid A2A agent list payload");
  }
  return data;
}

export async function getA2AAgent(agentId: string) {
  const data = await client.get<A2AAgent>(`/api/a2a-agents/${agentId}`);
  if (!isA2AAgent(data)) throw new Error("Invalid A2A agent payload");
  return data;
}

export async function createA2AAgent(payload: A2AAgentCreate) {
  const data = await client.post<A2AAgent>("/api/a2a-agents/", payload);
  if (!isA2AAgent(data)) throw new Error("Invalid A2A agent response");
  return data;
}

export async function updateA2AAgent(agentId: string, payload: A2AAgentUpdate) {
  const data = await client.patch<A2AAgent>(`/api/a2a-agents/${agentId}`, payload);
  if (!isA2AAgent(data)) throw new Error("Invalid A2A agent response");
  return data;
}

export async function deleteA2AAgent(agentId: string) {
  const data = await client.delete<{ status: string; agent_id: string }>(`/api/a2a-agents/${agentId}`);
  return data;
}

export async function refreshA2AAgentCard(agentId: string) {
  const data = await client.post<A2AAgent>(`/api/a2a-agents/${agentId}/refresh-card`, {});
  if (!isA2AAgent(data)) throw new Error("Invalid A2A agent response");
  return data;
}

export async function checkA2AAgentHealth(agentId: string) {
  const data = await client.post<A2AAgent>(`/api/a2a-agents/${agentId}/health-check`, {});
  if (!isA2AAgent(data)) throw new Error("Invalid A2A agent response");
  return data;
}

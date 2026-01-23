"use server";

import { createApiClient } from "../api/client";

const client = createApiClient({});

export interface Prompt {
  id: string;
  name: string;
  unique_label?: string;
  description?: string;
  organization_id?: string;
  app_name?: string;
  provider?: string;
  model?: string;
  tags?: string[];
  content: string;
  created_at?: string;
  updated_at?: string;
}

export interface PromptCreate {
  name: string;
  unique_label?: string;
  description?: string;
  organization_id?: string;
  app_name?: string;
  provider?: string;
  model?: string;
  tags?: string[];
  content: string;
}

export interface PromptUpdate {
  name?: string;
  description?: string;
  app_name?: string;
  provider?: string;
  model?: string;
  tags?: string[];
  content?: string;
}

function isPrompt(data: unknown): data is Prompt {
  return (
    typeof data === "object" &&
    data !== null &&
    typeof (data as Prompt).id === "string" &&
    typeof (data as Prompt).name === "string"
  );
}

export async function listPrompts(params?: {
  organization_id?: string;
  app_name?: string;
  provider?: string;
  model?: string;
  tag?: string;
  q?: string;
  limit?: number;
  offset?: number;
}) {
  const query = new URLSearchParams();
  if (params?.organization_id) query.set("organization_id", params.organization_id);
  if (params?.app_name) query.set("app_name", params.app_name);
  if (params?.provider) query.set("provider", params.provider);
  if (params?.model) query.set("model", params.model);
  if (params?.tag) query.set("tag", params.tag);
  if (params?.q) query.set("q", params.q);
  if (params?.limit) query.set("limit", String(params.limit));
  if (params?.offset) query.set("offset", String(params.offset));
  const url = `/api/prompts${query.toString() ? `?${query.toString()}` : ""}`;
  const data = await client.get<Prompt[]>(url);
  if (!Array.isArray(data) || !data.every(isPrompt)) {
    throw new Error("Invalid prompt list payload");
  }
  return data;
}

export async function getPrompt(promptId: string) {
  const data = await client.get<Prompt>(`/api/prompts/${promptId}`);
  if (!isPrompt(data)) throw new Error("Invalid prompt payload");
  return data;
}

export async function createPrompt(payload: PromptCreate) {
  const data = await client.post<Prompt>("/api/prompts/", payload);
  if (!isPrompt(data)) throw new Error("Invalid prompt response");
  return data;
}

export async function updatePrompt(promptId: string, payload: PromptUpdate) {
  const data = await client.patch<Prompt>(`/api/prompts/${promptId}`, payload);
  if (!isPrompt(data)) throw new Error("Invalid prompt response");
  return data;
}

export async function deletePrompt(promptId: string) {
  const data = await client.delete<{ deleted: boolean }>(`/api/prompts/${promptId}`);
  return data;
}

"use server";

import { createApiClient } from "../api/client";

const client = createApiClient({});

export interface ApprovalRequest {
  id: string;
  execution_id: string;
  step_id: string;
  workflow_id: string;
  status: string;
  request_payload?: Record<string, unknown>;
  response_payload?: Record<string, unknown>;
  decided_at?: string;
  decided_by?: string;
  created_at: string;
}

export interface ApprovalDecisionPayload {
  decided_by?: string;
  comment?: string;
  payload?: Record<string, unknown>;
}

export interface ApprovalDecisionResponse {
  status: string;
  backend: string;
}

function isApprovalRequest(data: unknown): data is ApprovalRequest {
  return (
    typeof data === "object" &&
    data !== null &&
    typeof (data as ApprovalRequest).id === "string" &&
    typeof (data as ApprovalRequest).execution_id === "string"
  );
}

export async function listApprovals(params?: { execution_id?: string; status?: string; limit?: number; offset?: number }) {
  const query = new URLSearchParams();
  if (params?.execution_id) query.set("execution_id", params.execution_id);
  if (params?.status) query.set("status", params.status);
  if (params?.limit) query.set("limit", String(params.limit));
  if (params?.offset) query.set("offset", String(params.offset));
  const url = `/api/approvals${query.toString() ? `?${query.toString()}` : ""}`;
  const data = await client.get<ApprovalRequest[]>(url);
  if (!Array.isArray(data) || !data.every(isApprovalRequest)) {
    throw new Error("Invalid approval list payload");
  }
  return data;
}

export async function getApproval(approvalId: string) {
  const data = await client.get<ApprovalRequest>(`/api/approvals/${approvalId}`);
  if (!isApprovalRequest(data)) throw new Error("Invalid approval payload");
  return data;
}

export async function approveApproval(approvalId: string, payload: ApprovalDecisionPayload) {
  const data = await client.post<ApprovalDecisionResponse>(`/api/approvals/${approvalId}/approve`, payload);
  return data;
}

export async function denyApproval(approvalId: string, payload: ApprovalDecisionPayload) {
  const data = await client.post<ApprovalDecisionResponse>(`/api/approvals/${approvalId}/deny`, payload);
  return data;
}

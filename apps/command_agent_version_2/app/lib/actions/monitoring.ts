"use server";

import { createApiClient } from "../api/client";

const client = createApiClient({});

export interface TraceData {
  traces: unknown[];
  total: number;
  limit: number;
}

export interface MonitoringSummary {
  monitoring_status: string;
  summary: Record<string, unknown>;
  components: {
    traces: string;
    metrics: string;
    error_tracking: string;
  };
}

export interface ExecutionAnalyticsResponse {
  executions: unknown[];
  total: number;
  limit: number;
  offset: number;
  filter?: { status?: string } | null;
}

export interface ErrorAnalytics {
  component?: string;
  errors?: unknown[];
  total?: number;
  total_errors?: number;
  errors_by_component?: Record<string, unknown>;
  recent_errors?: unknown[];
}

export async function getMetrics() {
  // Metrics returns text/plain, use fetch directly
  const response = await fetch("/api/metrics");
  if (!response.ok) {
    throw new Error(`Failed to fetch metrics: ${response.statusText}`);
  }
  return response.text();
}

export async function getTraces(limit?: number) {
  const query = limit ? `?limit=${String(limit)}` : "";
  const data = await client.get<TraceData>(`/api/monitoring/traces${query}`);
  return data;
}

export async function getMonitoringSummary() {
  const data = await client.get<MonitoringSummary>("/api/monitoring/summary");
  return data;
}

export async function getExecutionAnalytics(params?: { limit?: number; offset?: number; status?: string }) {
  const query = new URLSearchParams();
  if (params?.limit) query.set("limit", String(params.limit));
  if (params?.offset) query.set("offset", String(params.offset));
  if (params?.status) query.set("status", params.status);
  const url = `/api/analytics/executions${query.toString() ? `?${query.toString()}` : ""}`;
  const data = await client.get<ExecutionAnalyticsResponse>(url);
  return data;
}

export async function getErrorAnalytics(component?: string) {
  const query = component ? `?component=${component}` : "";
  const data = await client.get<ErrorAnalytics>(`/api/analytics/errors${query}`);
  return data;
}

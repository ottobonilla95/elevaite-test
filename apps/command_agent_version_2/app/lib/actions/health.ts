"use server";

import { createApiClient } from "../api/client";

const client = createApiClient({});

export interface HealthStatus {
  message?: string;
  version?: string;
  status: string;
  registered_steps?: number;
  step_types?: string[];
}

export interface DetailedHealthStatus {
  status: string;
  timestamp?: string;
  error_statistics?: {
    total_errors: number;
    errors_by_component: Record<string, unknown>;
    recent_errors: unknown[];
  };
  system_info?: {
    uptime: string;
    memory_usage: string;
  };
  error?: string;
}

export interface MonitoringHealthStatus {
  status: string;
  monitoring?: {
    active_traces: number;
    total_requests: number;
    error_rate: number;
    avg_response_time: number;
  };
  error?: string;
}

export async function getHealthRoot() {
  const data = await client.get<HealthStatus>("/api/");
  return data;
}

export async function checkHealth() {
  const data = await client.get<HealthStatus>("/api/health");
  return data;
}

export async function getDetailedHealth() {
  const data = await client.get<DetailedHealthStatus>("/api/health/detailed");
  return data;
}

export async function getMonitoringHealth() {
  const data = await client.get<MonitoringHealthStatus>("/api/health/monitoring");
  return data;
}

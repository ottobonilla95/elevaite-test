import { createApiClient, type ApiClient } from "../client";

export interface ToolSummary {
  id: string;
  name: string;
  type?: string;
}

export interface ToolDetails extends ToolSummary {
  schema?: Record<string, unknown>;
}

export interface ToolsService {
  fetchAll: () => Promise<ToolSummary[]>;
  fetchOne: (toolId: string) => Promise<ToolDetails>;
}

export function createToolsService(client: ApiClient = createApiClient({})): ToolsService {
  return {
    fetchAll(): Promise<ToolSummary[]> {
      return client.get<ToolSummary[]>("/api/tools");
    },
    fetchOne(toolId: string): Promise<ToolDetails> {
      return client.get<ToolDetails>(`/api/tools/${toolId}`);
    },
  };
}

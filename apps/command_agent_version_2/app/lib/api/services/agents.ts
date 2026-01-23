import { createApiClient, type ApiClient } from "../client";

export interface AgentSummary {
  id: string;
  name: string;
  description?: string;
}

export interface AgentDetails extends AgentSummary {
  tools?: string[];
}

export interface AgentsService {
  fetchAll: () => Promise<AgentSummary[]>;
  fetchOne: (agentId: string) => Promise<AgentDetails>;
}

export function createAgentsService(client: ApiClient = createApiClient({})): AgentsService {
  return {
    fetchAll(): Promise<AgentSummary[]> {
      return client.get<AgentSummary[]>("/api/agents");
    },
    fetchOne(agentId: string): Promise<AgentDetails> {
      return client.get<AgentDetails>(`/api/agents/${agentId}`);
    },
  };
}

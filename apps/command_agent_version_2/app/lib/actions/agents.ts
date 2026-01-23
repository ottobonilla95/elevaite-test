"use server";

import { createAgentsService } from "../api/services/agents";
import { isAgentSummary } from "../discriminators/agents";

const service = createAgentsService();

export async function listAgents() {
  const data = await service.fetchAll();
  if (!Array.isArray(data) || !data.every(isAgentSummary)) throw new Error("Invalid agent list payload");
  return data;
}

export async function getAgent(agentId: string) {
  const data = await service.fetchOne(agentId);
  if (!isAgentSummary(data)) throw new Error("Invalid agent payload");
  return data;
}

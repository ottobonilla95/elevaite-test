"use server";

import { createToolsService } from "../api/services/tools";
import { isToolSummary } from "../discriminators/tools";

const service = createToolsService();

export async function listTools() {
  const data = await service.fetchAll();
  if (!Array.isArray(data) || !data.every(isToolSummary)) throw new Error("Invalid tool list payload");
  return data;
}

export async function getTool(toolId: string) {
  const data = await service.fetchOne(toolId);
  if (!isToolSummary(data)) throw new Error("Invalid tool payload");
  return data;
}

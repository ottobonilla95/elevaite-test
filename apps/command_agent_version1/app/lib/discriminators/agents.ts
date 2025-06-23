import type { AgentResponse } from "../interfaces/agents";
import { isObject, isChatCompletionToolParam } from "./common";

export function isAgentResponse(data: unknown): data is AgentResponse {
  return isAgentResponseObject(data);
}

export function isAgentResponseArray(data: unknown): data is AgentResponse[] {
  return (
    Array.isArray(data) && data.every((item) => isAgentResponseObject(item))
  );
}

function isAgentResponseObject(item: unknown): item is AgentResponse {
  return (
    isObject(item) &&
    "name" in item &&
    "system_prompt_id" in item &&
    "functions" in item &&
    "routing_options" in item &&
    "id" in item &&
    "agent_id" in item &&
    "system_prompt" in item &&
    typeof item.name === "string" &&
    typeof item.system_prompt_id === "string" &&
    Array.isArray(item.functions) &&
    item.functions.every((func) => isChatCompletionToolParam(func)) &&
    typeof item.routing_options === "object" &&
    typeof item.id === "number" &&
    typeof item.agent_id === "string" &&
    (!("agent_type" in item) ||
      item.agent_type === null ||
      [
        "router",
        "web_search",
        "data",
        "troubleshooting",
        "api",
        "weather",
        "toshiba",
      ].includes(item.agent_type as string)) &&
    (!("description" in item) ||
      item.description === null ||
      typeof item.description === "string")
  );
}

import type {
  Tool,
  ToolCategory,
  MCPServer,
  ToolExecutionResponse,
} from "../interfaces/tools";
import { isObject } from "./common";

export function isTool(data: unknown): data is Tool {
  return isToolObject(data);
}

export function isToolArray(data: unknown): data is Tool[] {
  return Array.isArray(data) && data.every((item) => isToolObject(item));
}

export function isToolCategory(data: unknown): data is ToolCategory {
  return isToolCategoryObject(data);
}

export function isToolCategoryArray(data: unknown): data is ToolCategory[] {
  return (
    Array.isArray(data) && data.every((item) => isToolCategoryObject(item))
  );
}

export function isMCPServer(data: unknown): data is MCPServer {
  return isMCPServerObject(data);
}

export function isMCPServerArray(data: unknown): data is MCPServer[] {
  return Array.isArray(data) && data.every((item) => isMCPServerObject(item));
}

export function isToolExecutionResponse(
  data: unknown
): data is ToolExecutionResponse {
  return isToolExecutionResponseObject(data);
}


function isToolObject(item: unknown): item is Tool {
  if (typeof item !== "object" || item === null) {
    console.log("❌ Failed: item is not an object or is null");
    return false;
  }

  type Validator = (v: unknown) => boolean;
  interface Check { key: string; validate: Validator; }

  function hasKey(obj: object, key: string): boolean {
    return key in obj;
  }

  const requiredChecks: Check[] = [
    { key: "id", validate: (v) => typeof v === "number" || typeof v === "string" },
    // { key: "tool_id", validate: (v) => typeof v === "string" },
    { key: "name", validate: (v) => typeof v === "string" },
    { key: "description", validate: (v) => typeof v === "string" },
    { key: "version", validate: (v) => typeof v === "string" },
    { key: "tool_type", validate: (v) => typeof v === "string" && ["local", "remote", "mcp"].includes(v) },
    { key: "execution_type", validate: (v) => typeof v === "string" },
    { key: "parameters_schema", validate: (v) => typeof v === "object" && v !== null },
    { key: "auth_required", validate: (v) => typeof v === "boolean" },
    { key: "is_active", validate: (v) => typeof v === "boolean" },
    { key: "is_available", validate: (v) => typeof v === "boolean" },
    { key: "created_at", validate: (v) => typeof v === "string" },
    { key: "updated_at", validate: (v) => typeof v === "string" },
    { key: "usage_count", validate: (v) => typeof v === "number" },
  ];

  for (const check of requiredChecks){
    const key = check.key;
    if (!hasKey(item, key)) {
      console.log(`❌ Failed: missing required key "${key}"`);
      return false;
    }
    const val = (item as Record<string, unknown>)[key];
    if (!check.validate(val)) {
      console.log(`❌ Failed: invalid type or value for "${key}" →`, val);
      return false;
    }
  }

  const optionalChecks: Check[] = [
    { key: "display_name", validate: (v) => v === null || typeof v === "string" },
    { key: "return_schema", validate: (v) => v === null || (typeof v === "object" && v !== null) },
    { key: "module_path", validate: (v) => v === null || typeof v === "string" },
    { key: "function_name", validate: (v) => v === null || typeof v === "string" },
    { key: "remote_name", validate: (v) => v === null || typeof v === "string" },
    { key: "rate_limit_per_minute", validate: (v) => v === null || typeof v === "number" },
    { key: "category_id", validate: (v) => v === null || typeof v === "string" },
    { key: "mcp_server_id", validate: (v) => v === null || typeof v === "string" },
    { key: "created_by", validate: (v) => v === null || typeof v === "string" },
    { key: "tags", validate: (v) => v === null || Array.isArray(v) },
    { key: "last_used", validate: (v) => v === null || typeof v === "string" },
    { key: "average_execution_time_ms", validate: (v) => v === null || typeof v === "number" },
    { key: "category", validate: (v) => v === null || isToolCategoryObject(v as unknown) },
    { key: "mcp_server", validate: (v) => v === null || isMCPServerObject(v as unknown) },
  ];

  for (const optionalCheck of optionalChecks) {
    const optKey = optionalCheck.key;
    if (!hasKey(item, optKey)) continue;
    const optVal = (item as Record<string, unknown>)[optKey];
    if (!optionalCheck.validate(optVal)) {
      console.log(`❌ Failed: optional key "${optKey}" has invalid value →`, optVal);
      return false;
    }
  }

  return true;
}



// function isToolObject(item: unknown): item is Tool {
//   return (
//     isObject(item) &&
//     "id" in item &&
//     "tool_id" in item &&
//     "name" in item &&
//     "description" in item &&
//     "version" in item &&
//     "tool_type" in item &&
//     "execution_type" in item &&
//     "parameters_schema" in item &&
//     "auth_required" in item &&
//     "is_active" in item &&
//     "is_available" in item &&
//     "created_at" in item &&
//     "updated_at" in item &&
//     "usage_count" in item &&
//     typeof item.id === "number" &&
//     typeof item.tool_id === "string" &&
//     typeof item.name === "string" &&
//     typeof item.description === "string" &&
//     typeof item.version === "string" &&
//     ["local", "remote", "mcp"].includes(item.tool_type as string) &&
//     typeof item.execution_type === "string" &&
//     typeof item.parameters_schema === "object" &&
//     typeof item.auth_required === "boolean" &&
//     typeof item.is_active === "boolean" &&
//     typeof item.is_available === "boolean" &&
//     typeof item.created_at === "string" &&
//     typeof item.updated_at === "string" &&
//     typeof item.usage_count === "number" &&
//     (!("display_name" in item) ||
//       item.display_name === null ||
//       typeof item.display_name === "string") &&
//     (!("return_schema" in item) ||
//       item.return_schema === null ||
//       typeof item.return_schema === "object") &&
//     (!("module_path" in item) ||
//       item.module_path === null ||
//       typeof item.module_path === "string") &&
//     (!("function_name" in item) ||
//       item.function_name === null ||
//       typeof item.function_name === "string") &&
//     (!("remote_name" in item) ||
//       item.remote_name === null ||
//       typeof item.remote_name === "string") &&
//     (!("rate_limit_per_minute" in item) ||
//       item.rate_limit_per_minute === null ||
//       typeof item.rate_limit_per_minute === "number") &&
//     (!("category_id" in item) ||
//       item.category_id === null ||
//       typeof item.category_id === "string") &&
//     (!("mcp_server_id" in item) ||
//       item.mcp_server_id === null ||
//       typeof item.mcp_server_id === "string") &&
//     (!("created_by" in item) ||
//       item.created_by === null ||
//       typeof item.created_by === "string") &&
//     (!("tags" in item) || item.tags === null || Array.isArray(item.tags)) &&
//     (!("last_used" in item) ||
//       item.last_used === null ||
//       typeof item.last_used === "string") &&
//     (!("average_execution_time_ms" in item) ||
//       item.average_execution_time_ms === null ||
//       typeof item.average_execution_time_ms === "number") &&
//     (!("category" in item) ||
//       item.category === null ||
//       isToolCategoryObject(item.category)) &&
//     (!("mcp_server" in item) ||
//       item.mcp_server === null ||
//       isMCPServerObject(item.mcp_server))
//   );
// }

function isToolCategoryObject(item: unknown): item is ToolCategory {
  return (
    isObject(item) &&
    "id" in item &&
    "category_id" in item &&
    "name" in item &&
    "created_at" in item &&
    "updated_at" in item &&
    typeof item.id === "number" &&
    typeof item.category_id === "string" &&
    typeof item.name === "string" &&
    typeof item.created_at === "string" &&
    typeof item.updated_at === "string" &&
    (!("description" in item) ||
      item.description === null ||
      typeof item.description === "string") &&
    (!("icon" in item) ||
      item.icon === null ||
      typeof item.icon === "string") &&
    (!("color" in item) ||
      item.color === null ||
      typeof item.color === "string")
  );
}

function isMCPServerObject(item: unknown): item is MCPServer {
  return (
    isObject(item) &&
    "id" in item &&
    "server_id" in item &&
    "name" in item &&
    "host" in item &&
    "port" in item &&
    "protocol" in item &&
    "status" in item &&
    "health_check_interval" in item &&
    "consecutive_failures" in item &&
    "registered_at" in item &&
    "updated_at" in item &&
    typeof item.id === "number" &&
    typeof item.server_id === "string" &&
    typeof item.name === "string" &&
    typeof item.host === "string" &&
    typeof item.port === "number" &&
    typeof item.protocol === "string" &&
    typeof item.status === "string" &&
    typeof item.health_check_interval === "number" &&
    typeof item.consecutive_failures === "number" &&
    typeof item.registered_at === "string" &&
    typeof item.updated_at === "string" &&
    (!("description" in item) ||
      item.description === null ||
      typeof item.description === "string") &&
    (!("endpoint" in item) ||
      item.endpoint === null ||
      typeof item.endpoint === "string") &&
    (!("auth_type" in item) ||
      item.auth_type === null ||
      typeof item.auth_type === "string") &&
    (!("auth_config" in item) ||
      item.auth_config === null ||
      typeof item.auth_config === "object") &&
    (!("version" in item) ||
      item.version === null ||
      typeof item.version === "string") &&
    (!("capabilities" in item) ||
      item.capabilities === null ||
      Array.isArray(item.capabilities)) &&
    (!("tags" in item) || item.tags === null || Array.isArray(item.tags)) &&
    (!("last_health_check" in item) ||
      item.last_health_check === null ||
      typeof item.last_health_check === "string") &&
    (!("last_seen" in item) ||
      item.last_seen === null ||
      typeof item.last_seen === "string")
  );
}

function isToolExecutionResponseObject(
  item: unknown
): item is ToolExecutionResponse {
  return (
    isObject(item) &&
    "status" in item &&
    "execution_time_ms" in item &&
    "tool_id" in item &&
    "timestamp" in item &&
    typeof item.status === "string" &&
    ["success", "error", "timeout"].includes(item.status) &&
    typeof item.execution_time_ms === "number" &&
    typeof item.tool_id === "string" &&
    typeof item.timestamp === "string" &&
    (!("result" in item) || item.result !== undefined) &&
    (!("error_message" in item) ||
      item.error_message === null ||
      typeof item.error_message === "string")
  );
}

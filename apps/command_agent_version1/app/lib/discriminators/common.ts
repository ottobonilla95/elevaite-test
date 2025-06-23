import type {
  ChatCompletionToolParam,
  DeploymentOperationResponse,
} from "../interfaces/common";

export function isObject(item: unknown): item is object {
  return Boolean(item) && item !== null && typeof item === "object";
}

export function isChatCompletionToolParam(
  item: unknown
): item is ChatCompletionToolParam {
  return (
    isObject(item) &&
    "type" in item &&
    "function" in item &&
    item.type === "function" &&
    isObject(item.function) &&
    "name" in item.function &&
    typeof item.function.name === "string"
  );
}

export function isDeploymentOperationResponse(
  data: unknown
): data is DeploymentOperationResponse {
  return isDeploymentOperationResponseObject(data);
}

function isDeploymentOperationResponseObject(
  item: unknown
): item is DeploymentOperationResponse {
  return (
    isObject(item) &&
    "status" in item &&
    "message" in item &&
    typeof item.status === "string" &&
    typeof item.message === "string" &&
    ["success", "error"].includes(item.status) &&
    (!("deployment_name" in item) ||
      item.deployment_name === null ||
      typeof item.deployment_name === "string") &&
    (!("operation" in item) ||
      item.operation === null ||
      typeof item.operation === "string")
  );
}

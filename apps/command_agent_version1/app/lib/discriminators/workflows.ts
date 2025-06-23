import type {
  WorkflowDeployResponse,
  WorkflowExecutionResponse,
  WorkflowResponse,
  SavedWorkflow,
} from "../interfaces/workflows";
import { isObject } from "./common";

export function isWorkflowDeployResponse(
  data: unknown
): data is WorkflowDeployResponse {
  return isWorkflowDeployResponseObject(data);
}

export function isWorkflowExecutionResponse(
  data: unknown
): data is WorkflowExecutionResponse {
  return isWorkflowExecutionResponseObject(data);
}

export function isWorkflowResponse(data: unknown): data is WorkflowResponse {
  return isWorkflowResponseObject(data);
}

export function isWorkflowResponseArray(
  data: unknown
): data is WorkflowResponse[] {
  return (
    Array.isArray(data) && data.every((item) => isWorkflowResponseObject(item))
  );
}

export function isSavedWorkflow(data: unknown): data is SavedWorkflow {
  return isSavedWorkflowObject(data);
}

export function isSavedWorkflowArray(data: unknown): data is SavedWorkflow[] {
  return (
    Array.isArray(data) && data.every((item) => isSavedWorkflowObject(item))
  );
}

function isWorkflowDeployResponseObject(
  item: unknown
): item is WorkflowDeployResponse {
  return (
    isObject(item) &&
    "status" in item &&
    "message" in item &&
    typeof item.status === "string" &&
    typeof item.message === "string" &&
    ["success", "error"].includes(item.status) &&
    (!("workflow_id" in item) || typeof item.workflow_id === "string") &&
    (!("deployment_id" in item) || typeof item.deployment_id === "string") &&
    (!("deployment_name" in item) || typeof item.deployment_name === "string")
  );
}

function isWorkflowExecutionResponseObject(
  item: unknown
): item is WorkflowExecutionResponse {
  return (
    isObject(item) &&
    "status" in item &&
    typeof item.status === "string" &&
    ["ok", "error"].includes(item.status) &&
    (!("response" in item) || typeof item.response === "string") &&
    (!("message" in item) || typeof item.message === "string")
  );
}

function isWorkflowResponseObject(item: unknown): item is WorkflowResponse {
  return (
    isObject(item) &&
    "name" in item &&
    "version" in item &&
    "configuration" in item &&
    "is_active" in item &&
    "id" in item &&
    "workflow_id" in item &&
    "created_at" in item &&
    "updated_at" in item &&
    "is_deployed" in item &&
    "workflow_agents" in item &&
    "workflow_connections" in item &&
    "workflow_deployments" in item &&
    typeof item.name === "string" &&
    typeof item.version === "string" &&
    typeof item.configuration === "object" &&
    typeof item.is_active === "boolean" &&
    typeof item.id === "number" &&
    typeof item.workflow_id === "string" &&
    typeof item.created_at === "string" &&
    typeof item.updated_at === "string" &&
    typeof item.is_deployed === "boolean" &&
    Array.isArray(item.workflow_agents) &&
    Array.isArray(item.workflow_connections) &&
    Array.isArray(item.workflow_deployments) &&
    (!("description" in item) ||
      item.description === null ||
      typeof item.description === "string") &&
    (!("created_by" in item) ||
      item.created_by === null ||
      typeof item.created_by === "string") &&
    (!("deployed_at" in item) ||
      item.deployed_at === null ||
      typeof item.deployed_at === "string") &&
    (!("tags" in item) || item.tags === null || Array.isArray(item.tags))
  );
}

function isSavedWorkflowObject(item: unknown): item is SavedWorkflow {
  return (
    isObject(item) &&
    "workflow_id" in item &&
    "name" in item &&
    "created_at" in item &&
    "is_active" in item &&
    "is_deployed" in item &&
    "version" in item &&
    typeof item.workflow_id === "string" &&
    typeof item.name === "string" &&
    typeof item.created_at === "string" &&
    typeof item.is_active === "boolean" &&
    typeof item.is_deployed === "boolean" &&
    typeof item.version === "string" &&
    (!("description" in item) ||
      item.description === null ||
      typeof item.description === "string") &&
    (!("created_by" in item) ||
      item.created_by === null ||
      typeof item.created_by === "string") &&
    (!("deployed_at" in item) ||
      item.deployed_at === null ||
      typeof item.deployed_at === "string") &&
    (!("agent_count" in item) ||
      item.agent_count === null ||
      typeof item.agent_count === "number") &&
    (!("connection_count" in item) ||
      item.connection_count === null ||
      typeof item.connection_count === "number")
  );
}

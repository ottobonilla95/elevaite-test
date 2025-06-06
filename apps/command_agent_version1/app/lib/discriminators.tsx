import type { ChatMessageResponse, SessionSummaryObject, AgentResponse, WorkflowDeployResponse, WorkflowExecutionResponse, ToolsResponse, ToolCategoryResponse, ToolDetailResponse, WorkflowResponse, SavedWorkflow, DeploymentOperationResponse } from "./interfaces";







export function isChatMessageResponse(data: unknown): data is ChatMessageResponse {
    return isChatMessageResponseObject(data);
}

export function isSessionSummaryResponse(data: unknown): data is SessionSummaryObject {
    return isSessionSummaryObject(data);
}

export function isAgentResponse(data: unknown): data is AgentResponse {
    return isAgentResponseObject(data);
}

export function isAgentResponseArray(data: unknown): data is AgentResponse[] {
    return Array.isArray(data) && data.every(item => isAgentResponseObject(item));
}

export function isWorkflowDeployResponse(data: unknown): data is WorkflowDeployResponse {
    return isWorkflowDeployResponseObject(data);
}

export function isWorkflowExecutionResponse(data: unknown): data is WorkflowExecutionResponse {
    return isWorkflowExecutionResponseObject(data);
}

export function isToolsResponse(data: unknown): data is ToolsResponse {
    return isToolsResponseObject(data);
}

export function isToolCategoryResponse(data: unknown): data is ToolCategoryResponse {
    return isToolCategoryResponseObject(data);
}

export function isToolDetailResponse(data: unknown): data is ToolDetailResponse {
    return isToolDetailResponseObject(data);
}

export function isWorkflowResponse(data: unknown): data is WorkflowResponse {
    return isWorkflowResponseObject(data);
}

export function isWorkflowResponseArray(data: unknown): data is WorkflowResponse[] {
    return Array.isArray(data) && data.every(item => isWorkflowResponseObject(item));
}

export function isSavedWorkflow(data: unknown): data is SavedWorkflow {
    return isSavedWorkflowObject(data);
}

export function isSavedWorkflowArray(data: unknown): data is SavedWorkflow[] {
    return Array.isArray(data) && data.every(item => isSavedWorkflowObject(item));
}

export function isDeploymentOperationResponse(data: unknown): data is DeploymentOperationResponse {
    return isDeploymentOperationResponseObject(data);
}



// OBJECTS
///////////



function isObject(item: unknown): item is object {
    return Boolean(item) && item !== null && typeof item === "object";
}


function isChatMessageResponseObject(item: unknown): item is ChatMessageResponse {
    return isObject(item) &&
        "text" in item &&
        "refs" in item &&
        Array.isArray(item.refs);
}

function isSessionSummaryObject(item: unknown): item is SessionSummaryObject {
    return isObject(item) &&
        "title" in item &&
        "problem" in item &&
        "solution" in item;
}

function isAgentResponseObject(item: unknown): item is AgentResponse {
    return isObject(item) &&
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
        typeof item.routing_options === "object" &&
        typeof item.id === "number" &&
        typeof item.agent_id === "string" &&
        // agent_type is optional, so we only check if it exists
        (!("agent_type" in item) || item.agent_type === null ||
            ["router", "web_search", "data", "troubleshooting", "api", "weather", "toshiba"].includes(item.agent_type as string)) &&
        // description is optional, so we only check if it exists
        (!("description" in item) || item.description === null || typeof item.description === "string");
}

function isWorkflowDeployResponseObject(item: unknown): item is WorkflowDeployResponse {
    return isObject(item) &&
        "status" in item &&
        "message" in item &&
        typeof item.status === "string" &&
        typeof item.message === "string" &&
        ["success", "error"].includes(item.status) &&
        // Optional fields
        (!("workflow_id" in item) || typeof item.workflow_id === "string") &&
        (!("deployment_id" in item) || typeof item.deployment_id === "string") &&
        (!("deployment_name" in item) || typeof item.deployment_name === "string");
}

function isWorkflowExecutionResponseObject(item: unknown): item is WorkflowExecutionResponse {
    return isObject(item) &&
        "status" in item &&
        typeof item.status === "string" &&
        ["ok", "error"].includes(item.status) &&
        // Optional fields
        (!("response" in item) || typeof item.response === "string") &&
        (!("message" in item) || typeof item.message === "string");
}

function isToolsResponseObject(item: unknown): item is ToolsResponse {
    return isObject(item) &&
        "tools" in item &&
        "total_count" in item &&
        Array.isArray(item.tools) &&
        typeof item.total_count === "number" &&
        item.tools.every(tool => isToolInfoObject(tool));
}

function isToolInfoObject(item: unknown): item is import("./interfaces").ToolInfo {
    return isObject(item) &&
        "name" in item &&
        "description" in item &&
        "parameters" in item &&
        "function_type" in item &&
        typeof item.name === "string" &&
        typeof item.description === "string" &&
        typeof item.parameters === "object" &&
        typeof item.function_type === "string";
}

function isToolCategoryResponseObject(item: unknown): item is ToolCategoryResponse {
    return isObject(item) &&
        Object.values(item).every(category =>
            isObject(category) &&
            "tools" in category &&
            "count" in category &&
            Array.isArray(category.tools) &&
            typeof category.count === "number" &&
            category.tools.every(tool => isToolInfoObject(tool))
        );
}

function isToolDetailResponseObject(item: unknown): item is ToolDetailResponse {
    return isObject(item) &&
        "name" in item &&
        "schema" in item &&
        "available" in item &&
        typeof item.name === "string" &&
        typeof item.schema === "object" &&
        typeof item.available === "boolean" &&
        // Optional fields
        (!("docstring" in item) || item.docstring === null || typeof item.docstring === "string");
}

function isWorkflowResponseObject(item: unknown): item is WorkflowResponse {
    return isObject(item) &&
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
        // Optional fields
        (!("description" in item) || item.description === null || typeof item.description === "string") &&
        (!("created_by" in item) || item.created_by === null || typeof item.created_by === "string") &&
        (!("deployed_at" in item) || item.deployed_at === null || typeof item.deployed_at === "string") &&
        (!("tags" in item) || item.tags === null || Array.isArray(item.tags));
}

function isSavedWorkflowObject(item: unknown): item is SavedWorkflow {
    return isObject(item) &&
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
        // Optional fields
        (!("description" in item) || item.description === null || typeof item.description === "string") &&
        (!("created_by" in item) || item.created_by === null || typeof item.created_by === "string") &&
        (!("deployed_at" in item) || item.deployed_at === null || typeof item.deployed_at === "string") &&
        (!("agent_count" in item) || item.agent_count === null || typeof item.agent_count === "number") &&
        (!("connection_count" in item) || item.connection_count === null || typeof item.connection_count === "number");
}

function isDeploymentOperationResponseObject(item: unknown): item is DeploymentOperationResponse {
    return isObject(item) &&
        "status" in item &&
        "message" in item &&
        typeof item.status === "string" &&
        typeof item.message === "string" &&
        ["success", "error"].includes(item.status) &&
        // Optional fields
        (!("deployment_name" in item) || item.deployment_name === null || typeof item.deployment_name === "string") &&
        (!("operation" in item) || item.operation === null || typeof item.operation === "string");
}


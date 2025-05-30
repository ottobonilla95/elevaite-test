import type { ChatMessageResponse, SessionSummaryObject, AgentResponse, WorkflowDeployResponse, WorkflowExecutionResponse } from "./interfaces";







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


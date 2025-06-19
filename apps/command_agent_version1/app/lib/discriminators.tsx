import type {
    ChatMessageResponse,
    SessionSummaryObject,
    AgentResponse,
    WorkflowDeployResponse,
    WorkflowExecutionResponse,

    WorkflowResponse,
    SavedWorkflow,
    DeploymentOperationResponse,
    ChatCompletionToolParam,
    // New tool system types
    Tool,
    ToolCategory,
    MCPServer,
    ToolExecutionResponse
} from "./interfaces";







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

// New tool system type guards
export function isTool(data: unknown): data is Tool {
    return isToolObject(data);
}

export function isToolArray(data: unknown): data is Tool[] {
    return Array.isArray(data) && data.every(item => isToolObject(item));
}

export function isToolCategory(data: unknown): data is ToolCategory {
    return isToolCategoryObject(data);
}

export function isToolCategoryArray(data: unknown): data is ToolCategory[] {
    return Array.isArray(data) && data.every(item => isToolCategoryObject(item));
}

export function isMCPServer(data: unknown): data is MCPServer {
    return isMCPServerObject(data);
}

export function isMCPServerArray(data: unknown): data is MCPServer[] {
    return Array.isArray(data) && data.every(item => isMCPServerObject(item));
}

export function isToolExecutionResponse(data: unknown): data is ToolExecutionResponse {
    return isToolExecutionResponseObject(data);
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

function isChatCompletionToolParam(item: unknown): item is ChatCompletionToolParam {
    return isObject(item) &&
        "type" in item &&
        "function" in item &&
        item.type === "function" &&
        isObject(item.function) &&
        "name" in item.function &&
        typeof item.function.name === "string";
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
        item.functions.every(func => isChatCompletionToolParam(func)) &&
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

// New tool system object validators
function isToolObject(item: unknown): item is Tool {
    return isObject(item) &&
        "id" in item &&
        "tool_id" in item &&
        "name" in item &&
        "description" in item &&
        "version" in item &&
        "tool_type" in item &&
        "execution_type" in item &&
        "parameters_schema" in item &&
        "requires_auth" in item &&
        "timeout_seconds" in item &&
        "retry_count" in item &&
        "is_active" in item &&
        "is_available" in item &&
        "created_at" in item &&
        "updated_at" in item &&
        "usage_count" in item &&
        "success_count" in item &&
        "error_count" in item &&
        typeof item.id === "number" &&
        typeof item.tool_id === "string" &&
        typeof item.name === "string" &&
        typeof item.description === "string" &&
        typeof item.version === "string" &&
        ["local", "remote", "mcp"].includes(item.tool_type as string) &&
        typeof item.execution_type === "string" &&
        typeof item.parameters_schema === "object" &&
        typeof item.requires_auth === "boolean" &&
        typeof item.timeout_seconds === "number" &&
        typeof item.retry_count === "number" &&
        typeof item.is_active === "boolean" &&
        typeof item.is_available === "boolean" &&
        typeof item.created_at === "string" &&
        typeof item.updated_at === "string" &&
        typeof item.usage_count === "number" &&
        typeof item.success_count === "number" &&
        typeof item.error_count === "number" &&
        // Optional fields
        (!("display_name" in item) || item.display_name === null || typeof item.display_name === "string") &&
        (!("return_schema" in item) || item.return_schema === null || typeof item.return_schema === "object") &&
        (!("module_path" in item) || item.module_path === null || typeof item.module_path === "string") &&
        (!("function_name" in item) || item.function_name === null || typeof item.function_name === "string") &&
        (!("remote_name" in item) || item.remote_name === null || typeof item.remote_name === "string") &&
        (!("rate_limit_per_minute" in item) || item.rate_limit_per_minute === null || typeof item.rate_limit_per_minute === "number") &&
        (!("category_id" in item) || item.category_id === null || typeof item.category_id === "string") &&
        (!("mcp_server_id" in item) || item.mcp_server_id === null || typeof item.mcp_server_id === "string") &&
        (!("created_by" in item) || item.created_by === null || typeof item.created_by === "string") &&
        (!("tags" in item) || item.tags === null || Array.isArray(item.tags)) &&
        (!("last_used" in item) || item.last_used === null || typeof item.last_used === "string") &&
        (!("average_execution_time_ms" in item) || item.average_execution_time_ms === null || typeof item.average_execution_time_ms === "number") &&
        (!("category" in item) || item.category === null || isToolCategoryObject(item.category)) &&
        (!("mcp_server" in item) || item.mcp_server === null || isMCPServerObject(item.mcp_server));
}

function isToolCategoryObject(item: unknown): item is ToolCategory {
    return isObject(item) &&
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
        // Optional fields
        (!("description" in item) || item.description === null || typeof item.description === "string") &&
        (!("icon" in item) || item.icon === null || typeof item.icon === "string") &&
        (!("color" in item) || item.color === null || typeof item.color === "string");
}

function isMCPServerObject(item: unknown): item is MCPServer {
    return isObject(item) &&
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
        // Optional fields
        (!("description" in item) || item.description === null || typeof item.description === "string") &&
        (!("endpoint" in item) || item.endpoint === null || typeof item.endpoint === "string") &&
        (!("auth_type" in item) || item.auth_type === null || typeof item.auth_type === "string") &&
        (!("auth_config" in item) || item.auth_config === null || typeof item.auth_config === "object") &&
        (!("version" in item) || item.version === null || typeof item.version === "string") &&
        (!("capabilities" in item) || item.capabilities === null || Array.isArray(item.capabilities)) &&
        (!("tags" in item) || item.tags === null || Array.isArray(item.tags)) &&
        (!("last_health_check" in item) || item.last_health_check === null || typeof item.last_health_check === "string") &&
        (!("last_seen" in item) || item.last_seen === null || typeof item.last_seen === "string");
}

function isToolExecutionResponseObject(item: unknown): item is ToolExecutionResponse {
    return isObject(item) &&
        "status" in item &&
        "execution_time_ms" in item &&
        "tool_id" in item &&
        "timestamp" in item &&
        typeof item.status === "string" &&
        ["success", "error", "timeout"].includes(item.status) &&
        typeof item.execution_time_ms === "number" &&
        typeof item.tool_id === "string" &&
        typeof item.timestamp === "string" &&
        // Optional fields
        (!("result" in item) || item.result !== undefined) &&
        (!("error_message" in item) || item.error_message === null || typeof item.error_message === "string");
}


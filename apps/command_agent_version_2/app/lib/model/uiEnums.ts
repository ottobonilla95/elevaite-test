



export enum CanvasNodeType {
    COMMAND = "command",
}

export enum NodeStatus {
    PENDING = "pending",
    RUNNING = "running",
    WAITING = "waiting",
    COMPLETED = "completed",
    FAILED = "failed",
    SKIPPED = "skipped",
}


export enum CategoryId {
    AGENTS = "agents",
    EXTERNAL_AGENTS = "extrnal_agents",
    PROMPTS = "prompts",
    TRIGGERS = "triggers",
    INPUTS = "inputs",
    OUTPUTS = "outputs",
    API = "api",
    ACTIONS = "actions",
    LOGIC = "logic",
    KNOWLEDGE = "knowledge",
    MEMORY = "memory",
    GUARDAILS = "guardrails",
}

export enum AgentNodeId {
    NEW = "agents_new",
    CONTRACT = "agents_contract",
    CHATBOT = "agents_chatbot",
    ROUTER = "agents_router",
    ESCALATION = "agents_escalation",
    IMAGE = "agents_image",
}

export enum ExternalAgentNodeId {
    NEW = "external_agents_new",
    CONTRACT = "external_agents_contract",
    CHATBOT = "external_agents_chatbot",
    ROUTER = "external_agents_router",
    ESCALATION = "external_agents_escalation",
    IMAGE = "external_agents_image",
}

export enum PromptNodeId {
    NEW = "prompts_new",
    CONTRACT = "prompts_contract",
    CHATBOT = "prompts_chatbot",
    ROUTER = "prompts_router",
    ESCALATION = "prompts_escalation",
}

export enum InputNodeId {
    NEW = "inputs_new",
    TEXT = "inputs_text",
    AUDIO = "inputs_audio",
    FILE = "inputs_file",
    URL = "inputs_url",
    IMAGE = "inputs_image",
}

export enum OutputNodeId {
    NEW = "outputs_new",
    TEXT = "outputs_text",
    AUDIO = "outputs_audio",
    TEMPLATE = "outputs_template",
    IMAGE = "outputs_image",
}

export enum ActionNodeId {
    NEW = "actions_new",
    MCP = "actions_mcp",
    REST_API = "actions_rest_api",
    PYTHON_FUNCTION = "actions_python_function",
}

export enum TriggerNodeId {
    NEW = "triggers_new",
    WEBHOOK = "triggers_webhook",
    EVENT_LISTENER = "triggers_event_listener",
    SCHEDULER = "triggers_scheduler",
}

export enum LogicNodeId {
    NEW = "logic_new",
    IF_ELSE = "logic_if_else",
    TRANSFORM = "logic_transform",
}

export enum ApiNodeId {
    NEW = "api_new",
    DEFAULT = "api_default",
    // Test API entries
    TEST_0 = "api_test_0",
    TEST_1 = "api_test_1",
    TEST_2 = "api_test_2",
    TEST_3 = "api_test_3",
    TEST_4 = "api_test_4",
    TEST_5 = "api_test_5",
    TEST_6 = "api_test_6",
    TEST_7 = "api_test_7",
    TEST_8 = "api_test_8",
    TEST_9 = "api_test_9",
    TEST_10 = "api_test_10",
    TEST_11 = "api_test_11",
    TEST_12 = "api_test_12",
    TEST_13 = "api_test_13",
    TEST_14 = "api_test_14",
    TEST_15 = "api_test_15",
    TEST_16 = "api_test_16",
    TEST_17 = "api_test_17",
    TEST_18 = "api_test_18",
    TEST_19 = "api_test_19",
}

export type AllNodeIds =
    | CategoryId
    | AgentNodeId
    | ExternalAgentNodeId
    | PromptNodeId
    | InputNodeId
    | OutputNodeId
    | ActionNodeId
    | TriggerNodeId
    | LogicNodeId
    | ApiNodeId;


/** Maps each CategoryId to its corresponding NEW node enum value */
export const NewNodeIdForCategory: Record<CategoryId, AllNodeIds> = {
    [CategoryId.AGENTS]: AgentNodeId.NEW,
    [CategoryId.EXTERNAL_AGENTS]: ExternalAgentNodeId.NEW,
    [CategoryId.PROMPTS]: PromptNodeId.NEW,
    [CategoryId.TRIGGERS]: TriggerNodeId.NEW,
    [CategoryId.INPUTS]: InputNodeId.NEW,
    [CategoryId.OUTPUTS]: OutputNodeId.NEW,
    [CategoryId.API]: ApiNodeId.NEW,
    [CategoryId.ACTIONS]: ActionNodeId.NEW,
    [CategoryId.LOGIC]: LogicNodeId.NEW,
    // Categories without specific node types use their CategoryId as the "new" id
    [CategoryId.KNOWLEDGE]: CategoryId.KNOWLEDGE,
    [CategoryId.MEMORY]: CategoryId.MEMORY,
    [CategoryId.GUARDAILS]: CategoryId.GUARDAILS,
};

/** Gets the NEW node ID for a given category */
export function getNewNodeId(categoryId: CategoryId): AllNodeIds {
    return NewNodeIdForCategory[categoryId];
}

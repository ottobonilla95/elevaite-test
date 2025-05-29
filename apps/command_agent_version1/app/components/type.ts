// types.ts - Contains all type definitions needed for the agent workflow

export type AgentType = "router" | "web_search" | "Weather Search Agent" | "data" | "troubleshooting" | "api";

export interface NodeData {
    id: string;
    shortId?: string;
    type: AgentType;
    name: string;
    prompt?: string;
    description?: string;
    tools?: string[];
    config?: any;
    onDelete: (id: string) => void;
    onConfigure: (id: string) => void;
    tags?: string[];

}

export interface NodeType {
    source: string;
    target: string;
    type?: string;
}

export interface Connection {
    source: string;
    target: string;
    sourceHandle?: string;
    targetHandle?: string;
}

export interface NodeItem {
    id: string;
    type: string;
    position: {
        x: number;
        y: number;
    };
    data: NodeData;
}


export interface AgentTypeDefinition {
    id: string;
    type: AgentType;
    name: string;
    description?: string;
}

export interface ChatMessage {
    id: number;
    text: string;
    sender: "user" | "bot";
}

export interface WorkflowConfig {
    workflowId: string;
    workflowName: string;
    agents: Array<{
        id: string;
        uuid: string;
        type: AgentType;
        name: string;
        prompt?: string;
        description?: string;
        tools?: string[];
        position: {
            x: number;
            y: number;
        };
    }>;
    connections: Array<{
        fromUuid: string;
        toUuid: string;
    }>;
}

// Agent styles map
export const AGENT_STYLES: Record<AgentType, { bgClass: string; textClass: string }> = {
    router: { bgClass: "bg-blue-100", textClass: "text-blue-600" },
    web_search: { bgClass: "bg-emerald-100", textClass: "text-emerald-600" },
    "Weather Search Agent": { bgClass: "bg-amber-100", textClass: "text-amber-600" },
    data: { bgClass: "bg-purple-100", textClass: "text-purple-600" },
    troubleshooting: { bgClass: "bg-red-100", textClass: "text-red-600" },
    api: { bgClass: "bg-red-100", textClass: "text-red-600" }
};

// Available agent types
export const AGENT_TYPES: AgentTypeDefinition[] = [
    {
        id: "router-1",
        type: "router",
        name: "Router Agent",
        description: "Routes queries to appropriate agents"
    },
    {
        id: "search-1",
        type: "web_search",
        name: "Web Search Agent",
        description: "Searches the web for information"
    },
    {
        id: "api-1",
        type: "Weather Search Agent",
        name: "Weather Serach Agent",
        description: "Connects to external APIs"
    },
    {
        id: "data-1",
        type: "data",
        name: "Data Agent",
        description: "Processes and analyzes data"
    },
    {
        id: "troubleshoot-1",
        type: "troubleshooting",
        name: "Troubleshooting Agent",
        description: "Helps solve problems"
    }
];
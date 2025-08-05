// types.ts - Contains all type definitions needed for the agent workflow

import {
  AGENT_TYPE,
  type AgentType,
  type AgentNodeData,
} from "../lib/interfaces";

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
  data: AgentNodeData;
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
  error?: boolean;
}

export interface WorkflowConfig {
  workflowId: string;
  workflowName: string;
  agents: {
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
  }[];
  connections: {
    fromUuid: string;
    toUuid: string;
  }[];
}

// Agent styles map using the const object for type safety
export const AGENT_STYLES: Record<
  AgentType,
  { bgClass: string; textClass: string }
> = {
  [AGENT_TYPE.ROUTER]: { bgClass: "bg-blue-100", textClass: "text-blue-600" },
  [AGENT_TYPE.WEB_SEARCH]: {
    bgClass: "bg-emerald-100",
    textClass: "text-emerald-600",
  },
  [AGENT_TYPE.WEATHER_SEARCH]: {
    bgClass: "bg-amber-100",
    textClass: "text-amber-600",
  },
  [AGENT_TYPE.DATA]: { bgClass: "bg-purple-100", textClass: "text-purple-600" },
  [AGENT_TYPE.TROUBLESHOOTING]: {
    bgClass: "bg-red-100",
    textClass: "text-red-600",
  },
  [AGENT_TYPE.API]: { bgClass: "bg-red-100", textClass: "text-red-600" },
  [AGENT_TYPE.TOSHIBA]: { bgClass: "bg-red-100", textClass: "text-red-600" },
  [AGENT_TYPE.CUSTOM]: { bgClass: "bg-gray-100", textClass: "text-gray-600" },
  [AGENT_TYPE.VECTORIZER]: {
    bgClass: "bg-orange-100",
    textClass: "text-orange-600",
  },
};

// Available agent types using the const object for type safety
export const AGENT_TYPES: AgentTypeDefinition[] = [
  {
    id: "router-1",
    type: AGENT_TYPE.ROUTER,
    name: "Router Agent",
    description: "Routes queries to appropriate agents",
  },
  {
    id: "search-1",
    type: AGENT_TYPE.WEB_SEARCH,
    name: "Web Search Agent",
    description: "Searches the web for information",
  },
  {
    id: "api-1",
    type: AGENT_TYPE.WEATHER_SEARCH,
    name: "Weather Search Agent",
    description: "Connects to external APIs",
  },
  {
    id: "data-1",
    type: AGENT_TYPE.DATA,
    name: "Data Agent",
    description: "Processes and analyzes data",
  },
  {
    id: "troubleshoot-1",
    type: AGENT_TYPE.TROUBLESHOOTING,
    name: "Troubleshooting Agent",
    description: "Helps solve problems",
  },
];

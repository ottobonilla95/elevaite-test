import type { DragEvent as ReactDragEvent, JSX } from "react";
import { Icons } from "../../components/icons";
import { ActionNodeId, AgentNodeId, type AllNodeIds, ApiNodeId, CategoryId, ExternalAgentNodeId, getNewNodeId, InputNodeId, LogicNodeId, NodeStatus, OutputNodeId, PromptNodeId, TriggerNodeId } from "../enums";
import { type CommandNodeTagProps, type DragPayloadMap, type NodeDetails, type SidePanelOption, type SidePanelPayload } from "../interfaces";



function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

function isSidePanelDragPayload(value: unknown): value is SidePanelPayload {
    if (!isRecord(value)) { return false; }

    if (typeof value.id !== "string") { return false; }
    if (typeof value.label !== "string") { return false; }

    return true;
}


export function getStatusDisplay(status: NodeStatus): CommandNodeTagProps {
    switch (status) {
        case NodeStatus.PENDING: return { label: "Idle", color: "#6C8271", background: "#EDF0EE", icon: <Icons.Status.SVGStatusIdle /> };
        case NodeStatus.RUNNING: return { label: "Running", color: "#FF681F", background: "#FFE1D2", icon: <Icons.Status.SVGStatusRunning /> };
        case NodeStatus.WAITING: return { label: "Waiting", color: "#873BCE", background: "#E7D8F5", icon: <Icons.Status.SVGStatusWaiting /> };
        case NodeStatus.COMPLETED: return { label: "Success", color: "#00B13E", background: "#D8F5EB", icon: <Icons.Status.SVGStatusSuccess /> };
        case NodeStatus.FAILED: return { label: "Error", color: "#F54B6B", background: "#FDDBE1", icon: <Icons.Status.SVGStatusFailed /> };
        case NodeStatus.SKIPPED: return { label: "Skipped", color: "#BAB400", background: "#FFF8EF", icon: <Icons.Status.SVGStatusSkipped /> };
    }
}


export function getCategoryLabel(categoryId: CategoryId, isSingular?: boolean): string {
    switch (categoryId) {
        case CategoryId.AGENTS: return isSingular ? "Agent" : "Agents";
        case CategoryId.EXTERNAL_AGENTS: return isSingular ? "External Agent" : "External Agents";
        case CategoryId.PROMPTS: return isSingular ? "Prompt" : "Prompts";
        case CategoryId.TRIGGERS: return isSingular ? "Trigger" : "Triggers";
        case CategoryId.INPUTS: return isSingular ? "Input" : "Inputs";
        case CategoryId.OUTPUTS: return isSingular ? "Output" : "Outputs";
        case CategoryId.API: return isSingular ? "API" : "API";
        case CategoryId.ACTIONS: return isSingular ? "Action" : "Actions";
        case CategoryId.LOGIC: return isSingular ? "Condition" : "Logic / Conditions";
        case CategoryId.KNOWLEDGE: return isSingular ? "Knowledge Base" : "Knowledge Base";
        case CategoryId.MEMORY: return isSingular ? "Memory Base" : "Memory Base";
        case CategoryId.GUARDAILS: return isSingular ? "Guardrail" : "Guardrails";
    }
}

export function getCategoryIcon(categoryId: CategoryId, isMain?: boolean): JSX.Element {
    switch (categoryId) {
        case CategoryId.AGENTS: return <Icons.SVGAgent color={getCategoryColor(CategoryId.AGENTS)} isCategory={isMain} />;
        case CategoryId.EXTERNAL_AGENTS: return <Icons.SVGAgent color={getCategoryColor(CategoryId.EXTERNAL_AGENTS)} isCategory={isMain} />;
        case CategoryId.PROMPTS: return <Icons.SVGPrompt color={getCategoryColor(CategoryId.PROMPTS)} isCategory={isMain} />;
        case CategoryId.TRIGGERS: return <Icons.SVGTrigger color={getCategoryColor(CategoryId.TRIGGERS)} isCategory={isMain} />;
        case CategoryId.INPUTS: return <Icons.SVGInput color={getCategoryColor(CategoryId.INPUTS)} isCategory={isMain} />;
        case CategoryId.OUTPUTS: return <Icons.SVGOutput color={getCategoryColor(CategoryId.OUTPUTS)} isCategory={isMain} />;
        case CategoryId.API: return <Icons.SVGApi color={getCategoryColor(CategoryId.API)} isCategory={isMain} />;
        case CategoryId.ACTIONS: return <Icons.SVGAction color={getCategoryColor(CategoryId.ACTIONS)} isCategory={isMain} />;
        case CategoryId.LOGIC: return <Icons.SVGCondition color={getCategoryColor(CategoryId.LOGIC)} isCategory={isMain} />;
        case CategoryId.KNOWLEDGE: return <Icons.SVGKnowledgeBase color={getCategoryColor(CategoryId.KNOWLEDGE)} isCategory={isMain} />;
        case CategoryId.MEMORY: return <Icons.SVGMemoryBase color={getCategoryColor(CategoryId.MEMORY)} isCategory={isMain} />;
        case CategoryId.GUARDAILS: return <Icons.SVGGuardrail color={getCategoryColor(CategoryId.GUARDAILS)} isCategory={isMain} />;
    }
}

export function getCategoryColor(categoryId?: CategoryId, background?: boolean): string {
    switch (categoryId) {
        case CategoryId.AGENTS: return background ? "#FFE1D2" : "#FF681F";
        case CategoryId.EXTERNAL_AGENTS: return background ? "#FBF4EB" : "#FFC811";
        case CategoryId.PROMPTS: return background ? "#E7D8F5" : "#DA82FF";
        case CategoryId.TRIGGERS: return background ? "#EBF2FE" : "#0950C3";
        case CategoryId.INPUTS: return background ? "#D8EBF5" : "#3B9BCE";
        case CategoryId.OUTPUTS: return background ? "#D8F5EB" : "#00B13E";
        case CategoryId.API: return background ? "#FFEED7" : "#FF950B";
        case CategoryId.ACTIONS: return background ? "#D0F8F6" : "#16DDD0";
        case CategoryId.LOGIC: return background ? "#FEE1F7" : "#FA67D8";
        case CategoryId.KNOWLEDGE: return background ? "#E7D8F5" : "#873BCE";
        case CategoryId.MEMORY: return background ? "#FDDBE1" : "#F54B6B";
        case CategoryId.GUARDAILS: return background ? "#FBF4EB" : "#DED700";
        default: return background ? "#FFE1D2" : "#FF681F";
    } 
}


export function getIcon(iconId: AllNodeIds): JSX.Element {
    switch (iconId) {
        // Agents
        case CategoryId.AGENTS:
        case AgentNodeId.NEW:
        case AgentNodeId.CONTRACT:
        case AgentNodeId.CHATBOT:
        case AgentNodeId.ROUTER:
        case AgentNodeId.ESCALATION:
        case AgentNodeId.IMAGE: return <Icons.SVGAgent color={getCategoryColor(CategoryId.AGENTS)} isCategory />;
        // External Agents
        case CategoryId.EXTERNAL_AGENTS:
        case ExternalAgentNodeId.CONTRACT:
        case ExternalAgentNodeId.CHATBOT:
        case ExternalAgentNodeId.ROUTER:
        case ExternalAgentNodeId.ESCALATION:
        case ExternalAgentNodeId.IMAGE: return <Icons.SVGAgent color={getCategoryColor(CategoryId.EXTERNAL_AGENTS)} isCategory />;
        // Prompts
        case CategoryId.PROMPTS:
        case PromptNodeId.CONTRACT:
        case PromptNodeId.CHATBOT:
        case PromptNodeId.ROUTER:
        case PromptNodeId.ESCALATION: return <Icons.Dark.SVGPrompt/>;
        // Actions
        case CategoryId.ACTIONS:
        case ActionNodeId.MCP: return <Icons.Dark.SVGMcp/>;
        case ActionNodeId.REST_API: return <Icons.Dark.SVGApi/>;
        case ActionNodeId.PYTHON_FUNCTION: return <Icons.Dark.SVGWebhook/>;
        // API
        case CategoryId.API:
        case ApiNodeId.DEFAULT: return <Icons.Dark.SVGApi/>;
        // Inputs
        case CategoryId.INPUTS:
        case InputNodeId.TEXT: return <Icons.Dark.SVGText/>;
        case InputNodeId.AUDIO: return <Icons.Dark.SVGAudio/>;
        case InputNodeId.FILE: return <Icons.Dark.SVGFile/>;
        case InputNodeId.URL: return <Icons.Dark.SVGUrl/>;
        case InputNodeId.IMAGE: return <Icons.Dark.SVGImage/>;
        // Logic
        case CategoryId.LOGIC:
        case LogicNodeId.IF_ELSE: return <Icons.Dark.SVGIfElse/>;
        case LogicNodeId.TRANSFORM: return <Icons.Dark.SVGTransform/>;
        // Outputs
        case CategoryId.OUTPUTS:
        case OutputNodeId.TEXT: return <Icons.Dark.SVGText/>;
        case OutputNodeId.AUDIO: return <Icons.Dark.SVGAudio/>;
        case OutputNodeId.TEMPLATE: return <Icons.Dark.SVGTemplate/>;
        case OutputNodeId.IMAGE: return <Icons.Dark.SVGImage/>;
        // Triggers
        case CategoryId.TRIGGERS:
        case TriggerNodeId.WEBHOOK: return <Icons.Dark.SVGWebhook/>;
        case TriggerNodeId.EVENT_LISTENER: return <Icons.Dark.SVGEventListener/>;
        case TriggerNodeId.SCHEDULER: return <Icons.Dark.SVGScheduler/>;
        // Knowledge/Memory/Guardrails (category-only, no specific node types yet)
        case CategoryId.KNOWLEDGE: return <Icons.SVGKnowledgeBase/>;
        case CategoryId.MEMORY: return <Icons.SVGMemoryBase/>;
        case CategoryId.GUARDAILS: return <Icons.SVGGuardrail/>

        default: return <Icons.SVGBrokenIcon/>;
    }
}


export function getPayloadFromOption(option: SidePanelOption, nodeDetails?: NodeDetails): SidePanelPayload {
    const { children: _children, ...payload } = option;
    
    if (!nodeDetails) { return payload; }
    
    return {
        ...payload,
        nodeDetails: {
            ...(payload.nodeDetails ?? {}),
            ...nodeDetails,
        },
    };
}

export function getNewOption(label: string, categoryId: CategoryId): SidePanelPayload {
    return {
        id: getNewNodeId(categoryId),
        label,
        icon: categoryId,
        nodeDetails: {
            categoryId,
            isNewItem: true,
        },
    }
}


export function setDragData<PayloadType extends keyof DragPayloadMap>(
    event: ReactDragEvent<HTMLElement>, type: PayloadType, payload: DragPayloadMap[PayloadType] 
): void {
    const dataTransfer = event.dataTransfer;
    dataTransfer.setData(type, JSON.stringify(payload));
}


export function getDragData<PayloadType extends keyof DragPayloadMap>(
    event: ReactDragEvent, type: PayloadType
): DragPayloadMap[PayloadType] | null {
    const dataTransfer = event.dataTransfer;
    const raw = dataTransfer.getData(type);
    if (!raw) { return null; }

    let parsed: unknown;
    try {
        parsed = JSON.parse(raw);
    } catch {
        return null;
    }

    // eslint-disable-next-line @typescript-eslint/no-unnecessary-condition -- We only have one type now, but we can expand later
    if (type === "application/command-node") {
        if (isSidePanelDragPayload(parsed)) {
            return parsed;
        }
            return null;
    }

    return null;
}

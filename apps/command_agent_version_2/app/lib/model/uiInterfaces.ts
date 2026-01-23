import type React from "react";
import type { AllNodeIds, CategoryId, NodeStatus } from "../enums";


export type SidePanelNodeId = AllNodeIds;


export interface SidePanelOption {
    id: SidePanelNodeId;
    label: string;
    icon: AllNodeIds;
    isCategory?: boolean;
    tag?: string;
    nodeDetails?: NodeDetails;
    children?: React.ReactElement<any>;
}


export interface NodeDetails {
    categoryId?: CategoryId;
    isNewItem?: boolean;
    isExpanded?: boolean;
    itemDetails?: ItemDetails;
}

export type ItemDetails = Record<string, ItemDetailsValue>;

export type ItemDetailsValue = 
  | string 
  | number 
  | boolean 
  | null
  | ItemDetailsValue[]
  | { [key: string]: ItemDetailsValue };


export interface CommandNodeTagProps {
    color?: string;
    background?: string;
    icon?: React.ReactNode;
    label: string;
}


export interface InnerNodeProps {
    nodeId?: string;
    nodeData: SidePanelPayload;
    info: NodeStatusInfo;
}

export interface ConfigPanelsProps {
    node: SidePanelOption;
}

export interface NodeStatusInfo {
    status: NodeStatus;
    message?: string;
    time?: number;
    tokens?: number;
    details?: Record<string, unknown>;
}

export type NodeStatusUpdate = NodeStatus | NodeStatusInfo;


export type DragMimeType = "application/command-node";
export interface DragPayloadMap {
    "application/command-node": SidePanelPayload;
}
export type SidePanelPayload = Omit<SidePanelOption, "children">;

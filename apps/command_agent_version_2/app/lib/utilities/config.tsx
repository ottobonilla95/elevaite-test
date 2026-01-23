import type { ItemDetails, ItemDetailsValue, SidePanelOption } from "../interfaces";


export function getItemDetail(node: SidePanelOption | null | undefined, key: string): ItemDetailsValue | undefined {
    if (!node) return undefined;
    if (!node.nodeDetails) return undefined;
    if (!node.nodeDetails.itemDetails) return undefined;
    
    return node.nodeDetails.itemDetails[key];
}

export function getItemDetailWithDefault<T extends ItemDetailsValue>(
    node: SidePanelOption | null | undefined,
    key: string,
    defaultValue: T,
    typeGuard?: (value: ItemDetailsValue) => value is T
): T {
    const value = getItemDetail(node, key);
    
    if (value === undefined) return defaultValue;
    
    if (typeGuard && !typeGuard(value)) return defaultValue;
    
    return value as T;
}

export function setItemDetail(
    node: SidePanelOption,
    key: string,
    value: ItemDetailsValue
): SidePanelOption {
    return {
        ...node,
        nodeDetails: {
            ...(node.nodeDetails ?? {}),
            itemDetails: {
                ...(node.nodeDetails?.itemDetails ?? {}),
                [key]: value,
            },
        },
    };
}

export function setItemDetails(
    node: SidePanelOption,
    updates: ItemDetails
): SidePanelOption {
    return {
        ...node,
        nodeDetails: {
            ...(node.nodeDetails ?? {}),
            itemDetails: {
                ...(node.nodeDetails?.itemDetails ?? {}),
                ...updates,
            },
        },
    };
}

export function removeItemDetail(
    node: SidePanelOption,
    key: string
): SidePanelOption {
    if (!node.nodeDetails?.itemDetails) return node;
    
    const { [key]: _, ...remainingDetails } = node.nodeDetails.itemDetails;
    
    return {
        ...node,
        nodeDetails: {
            ...node.nodeDetails,
            itemDetails: remainingDetails,
        },
    };
}

export const typeGuards = {
    isString: (value: ItemDetailsValue): value is string => typeof value === "string",
    isNumber: (value: ItemDetailsValue): value is number => typeof value === "number",
    isBoolean: (value: ItemDetailsValue): value is boolean => typeof value === "boolean",
    isArray: (value: ItemDetailsValue): value is ItemDetailsValue[] => Array.isArray(value),
    isObject: (value: ItemDetailsValue): value is Record<string, ItemDetailsValue> => 
        typeof value === "object" && value !== null && !Array.isArray(value),
};

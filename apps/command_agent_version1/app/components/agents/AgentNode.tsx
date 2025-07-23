"use client";

import React, { memo } from "react";
import { Handle, Position } from "react-flow-renderer";
import { PenLine, Trash2, EllipsisVertical, GripHorizontal } from "lucide-react";
import "./AgentNode.scss";
import { type AgentNodeData, type ChatCompletionToolParam } from "../../lib/interfaces";
import { getAgentIcon, getToolIcon } from "./iconUtils";
import { CommonButton } from "@repo/ui/components";

interface NodeProps {
    id: string;
    data: AgentNodeData;
    selected: boolean;
}

const AgentNode = memo(({ id, data, selected }: NodeProps) => {
    const { type, name, tools = [], config, onDelete, onAction, agent } = data;
    // const styles = AGENT_STYLES[type] || { bgClass: "bg-gray-100", textClass: "text-gray-600" };

    // Extract tool names from ChatCompletionToolParam array
    const toolNames = tools.map((tool: ChatCompletionToolParam) => tool.function.name);


    const handleDelete = (e: React.MouseEvent): void => {
        e.stopPropagation();
        onDelete(id);
    };

    function handlePanelView(e: React.MouseEvent): void {
        e.stopPropagation();
        handleAction("config");
    }

    function handleToolsView(e: React.MouseEvent): void {
        e.stopPropagation();
        handleAction("tools");
    }

    function handlePanelEdit(e: React.MouseEvent): void {
        e.stopPropagation();
        handleAction("configEdit");
    }

    function handleToolsEdit(e: React.MouseEvent): void {
        e.stopPropagation();
        handleAction("toolsEdit");
    }

    function handleAction(action: string): void {
        if (onAction) onAction(id, action, data);
    }

    // const handleOpenConfig = (e: React.MouseEvent): void => {
    //     e.stopPropagation();
    //     onConfigure(id);
    // };



    // Get model display name
    const getModelName = (): string => {
        const model = config?.model ?? "Claude 3";
        return model;
    };

    return (
        <div
            className={`agent-node ${selected ? "selected" : ""} grid grid-cols-1 justify-center`}
        >
            {/* Header with title and controls */}
            <GripHorizontal className="justify-self-center mt-1" />
            <div className="agent-node-header border-gray-200 border-b-[1px] px-4 pb-4 items-start">
                <div className="agent-icon-container">
                    <div className="agent-icon">
                        {getAgentIcon(type)}
                    </div>
                    <div className="agent-title">
                        <p className="agent-name">{name}</p>
                        <p className="agent-type">{agent.description}</p>
                    </div>
                </div>
                <div className="agent-controls pt-3">
                    <button
                        onClick={handlePanelEdit}
                        className="control-button edit-button"
                        type="button"
                    >
                        <PenLine size={16} />
                    </button>
                    <button
                        onClick={handleDelete}
                        className="control-button delete-button"
                        type="button"
                    >
                        <Trash2 size={16} />
                    </button>
                    {/* <button
                        onClick={(e) => { e.stopPropagation(); }}
                        className="control-button disabled-button"
                        type="button"
                        disabled
                    >
                        <EllipsisVertical size={16} />
                    </button> */}
                </div>
            </div>

            {/* Badge section */}
            <div className="agent-badges px-4 border-gray-200 border-b-[1px] py-1">
                <CommonButton className="pill-button" onClick={handlePanelView}>
                    <span className="badge">{getModelName()}</span>
                </CommonButton>
            </div>

            {/* Tools Section */}
            {(toolNames.length > 0) ? (
                <div className="agent-tools px-4 pt-1 pb-4">
                    <div className="tools-header">
                        <span className="tools-title">Tools</span>
                        <button
                            onClick={handleToolsEdit}
                            className="edit-tools-button"
                            type="button"
                        >
                            <PenLine size={16} />
                        </button>
                    </div>
                    <div className="tools-list">
                        {toolNames.map((toolName, index) => (
                            <CommonButton key={`tool-${index.toString()}`} className="pill-button" onClick={handleToolsView}>
                                <span className="tool-badge">
                                    {getToolIcon(toolName)}
                                    <span className="tool-name">{toolName}</span>
                                </span>
                            </CommonButton>
                        ))}
                    </div>
                </div>
            ) : null}

            {/* Input Handle - Blue dot at top */}
            <Handle
                type="target"
                position={Position.Top}
                className="input-handle"
                id={`${id}-target`}
            />

            {/* Output Handle - Blue dot at bottom */}
            <Handle
                type="source"
                position={Position.Bottom}
                className="output-handle"
                id={`${id}-source`}
            />
        </div>
    );
});

// Add display name to avoid React warnings
AgentNode.displayName = 'AgentNode';

export default AgentNode;
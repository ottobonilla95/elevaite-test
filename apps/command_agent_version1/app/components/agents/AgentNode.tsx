"use client";

import React, { memo, type SVGProps } from "react";
import { Handle, Position } from "react-flow-renderer";
import { Router, Globe, Database, Link2, Wrench, Edit, X, Zap, Search, Code, FileText, Calculator, Mail } from "lucide-react";
import "./AgentNode.scss";
import { type AgentNodeData, type AgentType, type ChatCompletionToolParam } from "../../lib/interfaces";

interface NodeProps {
    id: string;
    data: AgentNodeData;
    selected: boolean;
}
function Dots(props: SVGProps<SVGSVGElement>): JSX.Element {
    return <svg
        xmlns="http://www.w3.org/2000/svg"
        width={14}
        height={8}
        fill="none"
        {...props}
    >
        <path
            stroke="#212124"
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={1.5}
            d="M3 1.667a.667.667 0 1 0-1.333 0 .667.667 0 0 0 1.333 0ZM7.667 1.667a.667.667 0 1 0-1.333 0 .667.667 0 0 0 1.333 0ZM12.334 1.667a.667.667 0 1 0-1.334 0 .667.667 0 0 0 1.334 0ZM3 6.333a.667.667 0 1 0-1.333 0 .667.667 0 0 0 1.333 0ZM7.667 6.333a.667.667 0 1 0-1.333 0 .667.667 0 0 0 1.333 0ZM12.334 6.333a.667.667 0 1 0-1.334 0 .667.667 0 0 0 1.334 0Z"
        />
    </svg>
}
const AgentNode = memo(({ id, data, selected }: NodeProps) => {
    const { type, name, tools = [], config, onDelete, onConfigure } = data;
    // const styles = AGENT_STYLES[type] || { bgClass: "bg-gray-100", textClass: "text-gray-600" };

    // Extract tool names from ChatCompletionToolParam array
    const toolNames = tools.map((tool: ChatCompletionToolParam) => tool.function.name);

    // Get the appropriate icon based on agent type
    const getAgentIcon = (_type: AgentType): JSX.Element => {
        switch (_type) {
            case "router":
                return <Router size={20} className="text-blue-600" />;
            case "web_search":
                return <Globe size={20} className="text-blue-600" />;
            case "api":
                return <Link2 size={20} className="text-blue-600" />;
            case "data":
                return <Database size={20} className="text-blue-600" />;
            case "troubleshooting":
                return <Wrench size={20} className="text-blue-600" />;
            default:
                return <Router size={20} className="text-blue-600" />;
        }
    };

    // Get icon for tool - dynamic mapping based on tool functionality
    const getToolIcon = (toolName: string): JSX.Element => {
        const _name = toolName.toLowerCase();

        // Map icons based on keywords in tool names
        if (_name.includes('web') || _name.includes('search')) {
            return <Search size={16} className="text-orange-500" />;
        } else if (_name.includes('database') || _name.includes('data')) {
            return <Database size={16} className="text-orange-500" />;
        } else if (_name.includes('api') || _name.includes('http') || _name.includes('link')) {
            return <Link2 size={16} className="text-orange-500" />;
        } else if (_name.includes('code') || _name.includes('execution')) {
            return <Code size={16} className="text-orange-500" />;
        } else if (_name.includes('file') || _name.includes('document')) {
            return <FileText size={16} className="text-orange-500" />;
        } else if (_name.includes('math') || _name.includes('calculate')) {
            return <Calculator size={16} className="text-orange-500" />;
        } else if (_name.includes('mail') || _name.includes('email')) {
            return <Mail size={16} className="text-orange-500" />;
        }
        // Default icon for unknown tools
        return <Zap size={16} className="text-orange-500" />;

    };

    const handleDelete = (e: React.MouseEvent): void => {
        e.stopPropagation();
        onDelete(id);
    };

    const handleOpenConfig = (e: React.MouseEvent): void => {
        e.stopPropagation();
        onConfigure(id);
    };

    // Clean subtitle text
    const getSubtitle = (_type: AgentType): string => {
        if (_type === "web_search") return "web search";
        return _type.replace('_', ' ');
    };

    // Get model display name
    const getModelName = (): string => {
        const model = config?.model ?? "Claude 3";
        return model;
    };

    return (
        <div
            className={`agent-node ${selected ? "selected" : ""} flex justify-center`}
        >
            {/* Header with title and controls */}
            <Dots />
            <div className="agent-node-header">
                <div className="agent-icon-container">
                    <div className="agent-icon">
                        {getAgentIcon(type)}
                    </div>
                    <div className="agent-title">
                        <p className="agent-name">{name}</p>
                        <p className="agent-type">{getSubtitle(type)}</p>
                    </div>
                </div>
                <div className="agent-controls">
                    <button
                        onClick={handleOpenConfig}
                        className="control-button edit-button"
                        type="button"
                    >
                        <Edit size={16} />
                    </button>
                    <button
                        onClick={handleDelete}
                        className="control-button delete-button"
                        type="button"
                    >
                        <X size={16} />
                    </button>
                </div>
            </div>

            {/* Badge section */}
            <div className="agent-badges">
                <span className="badge">{getModelName()}</span>
            </div>

            {/* Tools Section */}
            {(toolNames.length > 0) ? (
                <div className="agent-tools">
                    <div className="tools-header">
                        <span className="tools-title">Tools</span>
                        <button
                            onClick={handleOpenConfig}
                            className="edit-tools-button"
                            type="button"
                        >
                            <Edit size={14} />
                        </button>
                    </div>
                    <div className="tools-list">
                        {toolNames.map((toolName, index) => (
                            <span key={`tool-${index.toString()}`} className="tool-badge">
                                {getToolIcon(toolName)}
                                <span className="tool-name">{toolName}</span>
                            </span>
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
// AgentNode.tsx
"use client";

import React, { memo } from "react";
import { Handle, Position } from "react-flow-renderer";
import { Router, Globe, Database, Link2, Wrench, Edit, X, Zap } from "lucide-react";
import { AgentType, AGENT_STYLES } from "./type";
import "./AgentNode.scss";

interface NodeProps {
    id: string;
    data: {
        id: string;
        shortId?: string;
        type: AgentType;
        name: string;
        prompt?: string;
        tools?: string[];
        onDelete: (id: string) => void;
        onConfigure: () => void;
    };
    selected: boolean;
}

const AgentNode = memo(({ id, data, selected }: NodeProps) => {
    const { type, name, tools = [], onDelete, onConfigure } = data;
    const styles = AGENT_STYLES[type] || { bgClass: "bg-gray-100", textClass: "text-gray-600" };

    // Get the appropriate icon based on agent type
    const getAgentIcon = (type: AgentType) => {
        switch (type) {
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

    // Get icon for tool
    const getToolIcon = (toolName: string) => {
        const toolIcons: { [key: string]: React.ReactNode } = {
            "Tool 1": <Zap size={16} className="text-orange-500" />,
            "Tool 2": <Database size={16} className="text-orange-500" />,
            "Tool 3": <Link2 size={16} className="text-orange-500" />
        };

        return toolIcons[toolName] || <Zap size={16} className="text-orange-500" />;
    };

    const handleDelete = (e: React.MouseEvent) => {
        e.stopPropagation();
        onDelete(id);
    };

    const handleOpenConfig = (e: React.MouseEvent) => {
        e.stopPropagation();
        onConfigure();
    };

    // Clean subtitle text
    const getSubtitle = (type: AgentType) => {
        if (type === "web_search") return "web search";
        return type.replace('_', ' ');
    };

    return (
        <div
            className={`agent-node ${selected ? "selected" : ""}`}
        >
            {/* Header with title and controls */}
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
                    >
                        <Edit size={16} />
                    </button>
                    <button
                        onClick={handleDelete}
                        className="control-button delete-button"
                    >
                        <X size={16} />
                    </button>
                </div>
            </div>

            {/* Badge section */}
            <div className="agent-badges">
                <span className="badge">Hosted</span>
                <span className="badge">ClaudeGPT-4</span>
                <span className="badge">Knowledge Base</span>
            </div>

            {/* Tools Section */}
            {(tools && tools.length > 0) && (
                <div className="agent-tools">
                    <div className="tools-header">
                        <span className="tools-title">Tools</span>
                        <button
                            onClick={handleOpenConfig}
                            className="edit-tools-button"
                        >
                            <Edit size={14} />
                        </button>
                    </div>
                    <div className="tools-list">
                        {tools.map((tool, index) => (
                            <span key={index} className="tool-badge">
                                {getToolIcon(tool)}
                                <span className="tool-name">{tool}</span>
                            </span>
                        ))}
                    </div>
                </div>
            )}

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
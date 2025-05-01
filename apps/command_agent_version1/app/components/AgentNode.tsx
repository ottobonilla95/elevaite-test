// AgentNode.tsx - Improved to match Figma design
"use client";

import React, { memo } from "react";
import { Handle, Position } from "react-flow-renderer";
import { Router, Globe, Database, Link2, Wrench, Edit, X, Zap } from "lucide-react";
import { AgentType, AGENT_STYLES } from "./type";

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
            className={`agent-node p-4 rounded-lg bg-white shadow-sm ${selected ? "ring-2 ring-blue-400" : "border border-gray-200"}`}
            style={{ width: 280 }}
        >
            {/* Header with title and controls */}
            <div className="flex justify-between items-start mb-2">
                <div className="flex items-start">
                    <div className="p-2 rounded-md bg-blue-100 mr-3">
                        {getAgentIcon(type)}
                    </div>
                    <div>
                        <p className="font-medium text-gray-900">{name}</p>
                        <p className="text-xs text-gray-500">{getSubtitle(type)}</p>
                    </div>
                </div>
                <div className="flex space-x-1">
                    <button
                        onClick={handleOpenConfig}
                        className="p-1 text-gray-400 hover:text-gray-600 rounded"
                    >
                        <Edit size={16} />
                    </button>
                    <button
                        onClick={handleDelete}
                        className="p-1 text-gray-400 hover:text-gray-600 rounded"
                    >
                        <X size={16} />
                    </button>
                </div>
            </div>

            {/* Badge section - exactly matching Figma design */}
            <div className="flex flex-wrap gap-1 mb-3">
                <span className="inline-block px-2 py-0.5 bg-gray-100 text-gray-600 text-xs rounded">
                    Hosted
                </span>
                <span className="inline-block px-2 py-0.5 bg-gray-100 text-gray-600 text-xs rounded">
                    ClaudeGPT-4
                </span>
                <span className="inline-block px-2 py-0.5 bg-gray-100 text-gray-600 text-xs rounded">
                    Arlo Knowledge Base
                </span>
            </div>

            {/* Tools Section - with Edit button aligned to right */}
            {(tools && tools.length > 0) && (
                <div>
                    <div className="flex justify-between items-center mb-2">
                        <span className="text-sm font-medium text-gray-700">Tools</span>
                        <button
                            onClick={handleOpenConfig}
                            className="p-1 text-gray-400 hover:text-gray-600 rounded"
                        >
                            <Edit size={14} />
                        </button>
                    </div>
                    <div className="flex flex-wrap gap-2">
                        {tools.map((tool, index) => (
                            <span
                                key={index}
                                className="inline-flex items-center px-2 py-1 bg-orange-50 text-orange-500 text-xs rounded"
                            >
                                {getToolIcon(tool)}
                                <span className="ml-1">{tool}</span>
                            </span>
                        ))}
                    </div>
                </div>
            )}

            {/* Input Handle - Blue dot at top */}
            <Handle
                type="target"
                position={Position.Top}
                style={{
                    background: "#3b82f6", // blue-500
                    width: 8,
                    height: 8,
                    top: -4,
                    border: "2px solid white"
                }}
                id={`${id}-target`}
            />

            {/* Output Handle - Blue dot at bottom */}
            <Handle
                type="source"
                position={Position.Bottom}
                style={{
                    background: "#3b82f6", // blue-500
                    width: 8,
                    height: 8,
                    bottom: -4,
                    border: "2px solid white"
                }}
                id={`${id}-source`}
            />
        </div>
    );
});

// Add display name to avoid React warnings
AgentNode.displayName = 'AgentNode';

export default AgentNode;
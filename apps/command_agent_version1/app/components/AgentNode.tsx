// AgentNode.tsx
"use client";

import React, { memo } from "react";
import { Handle, Position } from "react-flow-renderer";
import { Router, Globe, Database, Link2, Wrench, Settings, X, Sliders } from "lucide-react";
import { AgentType, AGENT_STYLES } from "./type";

interface NodeProps {
    id: string;
    data: {
        id: string;
        shortId?: string;
        type: AgentType;
        name: string;
        prompt?: string;
        onDelete: (id: string) => void;
        onConfigure: (id: string) => void;
    };
    selected: boolean;
}

const AgentNode = memo(({ id, data, selected }: NodeProps) => {
    const { type, name, shortId, onDelete, onConfigure } = data;
    const styles = AGENT_STYLES[type] || { bgClass: "bg-gray-100", textClass: "text-gray-600" };

    // Get the appropriate icon based on agent type
    const getAgentIcon = (type: AgentType) => {
        switch (type) {
            case "router":
                return <Router size={20} />;
            case "web_search":
                return <Globe size={20} />;
            case "api":
                return <Link2 size={20} />;
            case "data":
                return <Database size={20} />;
            case "troubleshooting":
                return <Wrench size={20} />;
            default:
                return <Router size={20} />;
        }
    };

    const handleDelete = (e: React.MouseEvent) => {
        e.stopPropagation();
        onDelete(id);
    };

    const handleOpenConfig = (e: React.MouseEvent) => {
        e.stopPropagation();
        onConfigure(id);
    };

    return (
        <div
            className={`agent-node p-3 rounded-lg shadow-md bg-white border ${selected ? "border-blue-500" : "border-gray-200"
                }`}
            style={{ width: 200 }}
        >
            {/* Header with controls */}
            <div className="flex justify-between items-center mb-2">
                <div className={`py-0.5 px-2 rounded-md text-xs font-medium ${styles.bgClass} ${styles.textClass}`}>
                    {type.charAt(0).toUpperCase() + type.slice(1)}
                </div>
                <div className="flex space-x-1">
                    <button
                        onClick={handleOpenConfig}
                        className="p-1 text-gray-400 hover:text-gray-600 rounded"
                    >
                        <Settings size={14} />
                    </button>
                    <button
                        onClick={handleDelete}
                        className="p-1 text-gray-400 hover:text-red-600 rounded"
                    >
                        <X size={14} />
                    </button>
                </div>
            </div>

            {/* Agent content */}
            <div className="flex flex-col items-center mt-2">
                <div className={`p-2 rounded-full ${styles.bgClass} mb-2`}>
                    {getAgentIcon(type)}
                </div>
                <div className="text-center">
                    <p className="font-medium text-sm">{name}</p>
                    {shortId && (
                        <p className="text-xs text-gray-500">ID: {shortId}</p>
                    )}
                </div>
            </div>

            {/* Configure Agent Button */}
            <div className="mt-3">
                <button
                    onClick={handleOpenConfig}
                    className="w-full flex items-center justify-center bg-blue-50 hover:bg-blue-100 text-blue-600 px-4 py-2 rounded-md text-sm font-medium"
                    title="Configure Agent"
                >
                    <Sliders className="w-4 h-4 mr-2" />
                    Configure Agent
                </button>
            </div>

            {/* Input Handle */}
            <Handle
                type="target"
                position={Position.Top}
                style={{
                    background: "#9ca3af",
                    width: 8,
                    height: 8,
                    top: -4,
                }}
                id={`${id}-target`}
            />

            {/* Output Handle */}
            <Handle
                type="source"
                position={Position.Bottom}
                style={{
                    background: "#9ca3af",
                    width: 8,
                    height: 8,
                    bottom: -4,
                }}
                id={`${id}-source`}
            />
        </div>
    );
});

AgentNode.displayName = "AgentNode";

export default AgentNode;
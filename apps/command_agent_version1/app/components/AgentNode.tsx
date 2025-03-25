"use client";

import React, { memo, useState } from "react";
import { Handle, Position } from "react-flow-renderer";
import {
    Router,
    Globe,
    Database,
    Link2,
    Wrench,
    Settings,
    X,
    GripHorizontal,
    MessageCircle
} from "lucide-react";
import AgentConfigModal from "./AgentConfigModel";

// Get icon based on agent type
const getAgentIcon = (type) => {
    switch (type) {
        case "router":
            return <Router className="w-5 h-5" />;
        case "web_search":
            return <Globe className="w-5 h-5" />;
        case "api":
            return <Link2 className="w-5 h-5" />;
        case "data":
            return <Database className="w-5 h-5" />;
        case "troubleshooting":
            return <Wrench className="w-5 h-5" />;
        default:
            return <Router className="w-5 h-5" />;
    }
};

// Get agent style based on type
const getAgentStyle = (type) => {
    switch (type) {
        case "router":
            return { bgClass: "bg-blue-100", textClass: "text-blue-600" };
        case "web_search":
            return { bgClass: "bg-emerald-100", textClass: "text-emerald-600" };
        case "api":
            return { bgClass: "bg-amber-100", textClass: "text-amber-600" };
        case "data":
            return { bgClass: "bg-purple-100", textClass: "text-purple-600" };
        case "troubleshooting":
            return { bgClass: "bg-red-100", textClass: "text-red-600" };
        default:
            return { bgClass: "bg-gray-100", textClass: "text-gray-600" };
    }
};

const AgentNode = (props) => {
    // Local state for config modal
    const [isConfigOpen, setIsConfigOpen] = useState(false);

    // Destructure all required props
    const { id, selected, data, updateNodeData } = props;
    const { type, name, shortId, prompt, onDelete } = data;

    const styles = getAgentStyle(type);
    const selectedClass = selected ? 'ring-2 ring-blue-500' : '';

    // Check if prompt exists and has content
    const hasPrompt = prompt && prompt.trim().length > 0;

    // Open config modal
    const handleOpenConfig = (e) => {
        e.stopPropagation();
        console.log("Opening config modal for node:", id);
        setIsConfigOpen(true);
    };

    // Close config modal
    const handleCloseConfig = () => {
        console.log("Closing config modal for node:", id);
        setIsConfigOpen(false);
    };

    // Save config changes
    const handleSaveConfig = (nodeId, newName, newPrompt) => {
        console.log("Saving config for node:", nodeId, newName, newPrompt);

        // If updateNodeData is available, use it
        if (typeof updateNodeData === 'function') {
            updateNodeData(nodeId, { name: newName, prompt: newPrompt });
        } else {
            console.error("updateNodeData function not provided to AgentNode");
        }
    };

    return (
        <>
            <div
                className={`relative rounded-lg shadow-md border p-3 bg-white min-w-[180px] ${selectedClass} cursor-pointer`}
            >
                {/* Drag handle */}
                <div
                    className="absolute top-0 left-0 right-0 h-6 flex items-center justify-center cursor-move opacity-50 hover:opacity-100"
                    onMouseDown={(e) => e.stopPropagation()}
                >
                    <GripHorizontal className="w-4 h-4 text-gray-500" />
                </div>

                {/* Add handles on all sides to allow connections from anywhere */}
                {/* Left handle (input) */}
                <Handle
                    type="target"
                    position={Position.Left}
                    style={{
                        left: -10,
                        width: 12,
                        height: 12,
                        backgroundColor: '#3b82f6',
                        border: '2px solid white'
                    }}
                    id="left"
                    isConnectable={true}
                />

                {/* Right handle (output) */}
                <Handle
                    type="source"
                    position={Position.Right}
                    style={{
                        right: -10,
                        width: 12,
                        height: 12,
                        backgroundColor: '#3b82f6',
                        border: '2px solid white'
                    }}
                    id="right"
                    isConnectable={true}
                />

                {/* Top handle (additional input) */}
                <Handle
                    type="target"
                    position={Position.Top}
                    style={{
                        top: -10,
                        width: 12,
                        height: 12,
                        backgroundColor: '#3b82f6',
                        border: '2px solid white'
                    }}
                    id="top"
                    isConnectable={true}
                />

                {/* Bottom handle (additional output) */}
                <Handle
                    type="source"
                    position={Position.Bottom}
                    style={{
                        bottom: -10,
                        width: 12,
                        height: 12,
                        backgroundColor: '#3b82f6',
                        border: '2px solid white'
                    }}
                    id="bottom"
                    isConnectable={true}
                />

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

                        {/* Prompt indicator */}
                        {hasPrompt && (
                            <div className="flex items-center justify-center mt-1" title="Agent has prompt configured">
                                <MessageCircle className="w-3.5 h-3.5 text-green-500 mr-1" />
                                <span className="text-xs text-green-500">Prompt</span>
                            </div>
                        )}
                    </div>
                </div>

                {/* Configuration button */}
                <button
                    onClick={handleOpenConfig}
                    className="absolute top-1 right-7 p-1 rounded-full hover:bg-gray-200 text-gray-600"
                    title="Configure Agent"
                >
                    <Settings className="w-3.5 h-3.5" />
                </button>

                {/* Delete button */}
                <button
                    onClick={(e) => {
                        e.stopPropagation();
                        if (typeof onDelete === 'function') {
                            console.log('Deleting node with ID:', id);
                            onDelete(id);
                        }
                    }}
                    className="absolute top-1 right-1 p-1 rounded-full hover:bg-gray-200 text-gray-600"
                    title="Delete Agent"
                >
                    <X className="w-3.5 h-3.5" />
                </button>
            </div>

            {/* Configuration Modal */}
            <AgentConfigModal
                isOpen={isConfigOpen}
                nodeData={isConfigOpen ? { id, type, name, shortId, prompt } : null}
                onClose={handleCloseConfig}
                onSave={handleSaveConfig}
            />
        </>
    );
};

// Use memo to prevent unnecessary re-renders
export default memo(AgentNode);
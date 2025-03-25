"use client";

import React from "react";
import { X } from "lucide-react";

// Define types
interface NodeData {
    id: string;
    shortId?: string;
    type: AgentType;
    name: string;
    prompt?: string;
}

type AgentType = "router" | "web_search" | "api" | "data" | "troubleshooting";

// Agent styles map
const AGENT_STYLES: Record<AgentType, { bgClass: string; textClass: string }> = {
    router: { bgClass: "bg-blue-100", textClass: "text-blue-600" },
    web_search: { bgClass: "bg-emerald-100", textClass: "text-emerald-600" },
    api: { bgClass: "bg-amber-100", textClass: "text-amber-600" },
    data: { bgClass: "bg-purple-100", textClass: "text-purple-600" },
    troubleshooting: { bgClass: "bg-red-100", textClass: "text-red-600" }
};

// Agent prompt descriptions
const AGENT_PROMPT_DESCRIPTIONS: Record<AgentType, string> = {
    router: 'Define how this router should distribute queries to connected agents.',
    web_search: 'Specify search parameters and filtering criteria.',
    api: 'Define API endpoints, parameters, and authentication details.',
    data: 'Describe data processing and analysis instructions.',
    troubleshooting: 'Configure problem-solving approach and diagnostics.'
};

interface AgentConfigModalProps {
    isOpen: boolean;
    nodeData: NodeData | null;
    onClose: () => void;
    onSave: (id: string, name: string, prompt: string) => void;
}

const AgentConfigModal: React.FC<AgentConfigModalProps> = ({
    isOpen,
    nodeData,
    onClose,
    onSave
}) => {
    // Local state for form values
    const [name, setName] = React.useState("");
    const [prompt, setPrompt] = React.useState("");

    // Update local state when node data changes
    React.useEffect(() => {
        if (nodeData) {
            setName(nodeData.name || "");
            setPrompt(nodeData.prompt || "");
        }
    }, [nodeData]);

    // Handle save
    const handleSave = () => {
        if (nodeData && nodeData.id) {
            onSave(nodeData.id, name, prompt);
            onClose();
        }
    };

    if (!isOpen || !nodeData) {
        return null;
    }

    // Calculate prompt character count
    const maxLength = 1000;
    const currentLength = prompt.length;

    // Convert type like "web_search" to "Web Search" for display
    const displayType = nodeData.type
        .split('_')
        .map(word => word.charAt(0).toUpperCase() + word.slice(1))
        .join(' ');

    return (
        <div
            className="fixed inset-0 bg-black bg-opacity-30 flex items-center justify-center z-50"
            onClick={onClose}
        >
            <div
                className="bg-white rounded-lg shadow-lg"
                style={{ width: "360px", maxWidth: "95vw" }}
                onClick={(e) => e.stopPropagation()}
            >
                {/* Header */}
                <div className="flex justify-between items-center px-4 py-3 border-b border-gray-200">
                    <h3 className="text-lg font-medium">
                        Configure {displayType} Agent
                    </h3>
                    <button
                        onClick={onClose}
                        className="text-gray-400 hover:text-gray-600"
                    >
                        <X size={18} />
                    </button>
                </div>

                {/* Body */}
                <div className="px-4 py-3" style={{ maxHeight: "70vh", overflowY: "auto" }}>
                    <div className="space-y-4">
                        {/* Agent Name */}
                        <div>
                            <label className="block text-sm font-medium mb-1">Agent Name</label>
                            <input
                                type="text"
                                value={name}
                                onChange={(e) => setName(e.target.value)}
                                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-1 focus:ring-blue-500"
                            />
                        </div>

                        {/* Agent Type */}
                        <div>
                            <label className="block text-sm font-medium mb-1">Agent Type</label>
                            <div className={`py-2 px-3 ${AGENT_STYLES[nodeData.type].bgClass} rounded-md text-sm ${AGENT_STYLES[nodeData.type].textClass}`}>
                                {nodeData.type}
                            </div>
                        </div>

                        {/* Agent Prompt */}
                        <div>
                            <div className="flex justify-between items-center mb-1">
                                <label className="block text-sm font-medium">Agent Prompt</label>
                                <span className="text-xs text-gray-500">
                                    {currentLength}/{maxLength} characters
                                </span>
                            </div>
                            <textarea
                                value={prompt}
                                onChange={(e) => setPrompt(e.target.value)}
                                placeholder={`Add instructions for this ${nodeData.type} agent...`}
                                className="w-full px-3 py-2 border border-gray-300 rounded-md h-28 focus:outline-none focus:ring-1 focus:ring-blue-500"
                                maxLength={maxLength}
                            />
                            <div className="text-xs text-gray-500 mt-1">
                                {AGENT_PROMPT_DESCRIPTIONS[nodeData.type]}
                            </div>
                        </div>

                        {/* Node ID */}
                        <div>
                            <label className="block text-sm font-medium mb-1">Node ID</label>
                            <div className="py-2 px-3 bg-gray-100 rounded-md text-xs font-mono text-gray-600 break-all">
                                {nodeData.id}
                            </div>
                        </div>
                    </div>
                </div>

                {/* Footer */}
                <div className="px-4 py-3 border-t border-gray-200 flex justify-end space-x-2">
                    <button
                        onClick={onClose}
                        className="px-4 py-2 bg-white border border-gray-300 rounded-md text-sm"
                    >
                        Cancel
                    </button>
                    <button
                        onClick={handleSave}
                        className="px-4 py-2 bg-blue-600 text-white rounded-md text-sm"
                    >
                        Save Changes
                    </button>
                </div>
            </div>
        </div>
    );
};

export default AgentConfigModal;
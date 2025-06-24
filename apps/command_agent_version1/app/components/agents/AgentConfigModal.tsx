"use client";

import React, { useState, useEffect } from "react";
import { X, Plus, Save, Check } from "lucide-react";
import { AgentType } from "../type";
import { AgentNodeData } from "../../lib/interfaces";

interface ModalProps {
    isOpen: boolean;
    nodeData: Omit<AgentNodeData, "onDelete" | "onConfigure"> | null;
    onClose: () => void;
    onSave: (id: string, name: string, prompt: string, description: string, tags: string[]) => void;
}

const AgentConfigModal: React.FC<ModalProps> = ({
    isOpen,
    nodeData,
    onClose,
    onSave
}) => {
    const [name, setName] = useState("");
    const [prompt, setPrompt] = useState("");
    const [description, setDescription] = useState(nodeData?.agent.description || "");
    const [tags, setTags] = useState<string[]>([]);
    const [activeTab, setActiveTab] = useState("prompt");
    const maxLength = 2000;

    // Available tag options
    const availableTags = [
        { value: "router", label: "Router" },
        { value: "data", label: "Data Extractor" },
        { value: "web_search", label: "Web Search" },
        { value: "api", label: "API" },
        { value: "troubleshooting", label: "Troubleshooting" },
        { value: "cx", label: "CX Application" },
        { value: "command", label: "Command Agent" },
        { value: "worker", label: "Worker Agent" }
    ];

    // Reset state when node data changes
    useEffect(() => {
        if (nodeData) {
            setName(nodeData.name || "");
            setPrompt(nodeData.prompt || "");
            setDescription(nodeData.description || "");
            // Initialize tags with the node's type as default if no tags exist
            setTags(nodeData.tags || [nodeData.type]);
        }
    }, [nodeData]);

    if (!isOpen || !nodeData) return null;

    // Toggle a tag in the selected tags array
    const toggleTag = (tagValue: string) => {
        if (tags.includes(tagValue)) {
            setTags(tags.filter(t => t !== tagValue));
        } else {
            setTags([...tags, tagValue]);
        }
    };

    const handleSave = () => {
        onSave(nodeData.id, name, prompt, description, tags);
    };

    const currentLength = prompt.length;

    // Function to prevent modal closing when clicking inside
    const handleModalClick = (e: React.MouseEvent) => {
        e.stopPropagation();
    };

    const placeholderText = (type: AgentType) => {
        switch (type) {
            case "router":
                return "Define how this router should distribute queries to connected agents...";
            case "data":
                return "Define how this data extractor should process and extract information...";
            case "web_search":
                return "Define how this web search agent should query the internet and process results...";
            case "api":
                return "Define how this API agent should interact with external services...";
            case "troubleshooting":
                return "Define how this troubleshooting agent should identify and resolve issues...";
            default:
                return "Define how this agent should process input...";
        }
    };

    return (
        <div
            className="fixed inset-0 bg-black bg-opacity-30 flex items-start justify-center z-50 pt-14"
            onClick={onClose}
        >
            <div
                className="bg-white rounded-lg shadow-lg w-[950px] max-w-[95vw] max-h-[calc(100vh-120px)] flex flex-col overflow-hidden"
                onClick={handleModalClick}
            >
                {/* Header */}
                <div className="flex justify-between items-center px-4 py-3 border-b border-gray-200">
                    <h3 className="text-lg font-medium">
                        Edit {nodeData.type.charAt(0).toUpperCase() + nodeData.type.slice(1)} Agent
                    </h3>
                    <button
                        onClick={onClose}
                        className="text-gray-400 hover:text-gray-600 transition-colors"
                    >
                        <X size={18} />
                    </button>
                </div>

                {/* Tabs */}
                <div className="border-b border-gray-200">
                    <div className="flex">
                        <button
                            className={`px-4 py-2 text-sm font-medium transition-colors duration-200 ${activeTab === "prompt"
                                ? "text-orange-500 border-b-2 border-orange-500"
                                : "text-gray-500 hover:text-gray-700"
                                }`}
                            onClick={() => setActiveTab("prompt")}
                        >
                            Prompt
                        </button>
                        <button
                            className={`px-4 py-2 text-sm font-medium transition-colors duration-200 ${activeTab === "parameters"
                                ? "text-orange-500 border-b-2 border-orange-500"
                                : "text-gray-500 hover:text-gray-700"
                                }`}
                            onClick={() => setActiveTab("parameters")}
                        >
                            Parameters
                        </button>
                        <button
                            className={`px-4 py-2 text-sm font-medium transition-colors duration-200 ${activeTab === "testing"
                                ? "text-orange-500 border-b-2 border-orange-500"
                                : "text-gray-500 hover:text-gray-700"
                                }`}
                            onClick={() => setActiveTab("testing")}
                        >
                            Testing
                        </button>
                    </div>
                </div>

                {/* Body */}
                <div className="p-4 overflow-y-auto flex-1">
                    {activeTab === "prompt" && (
                        <div className="space-y-4">
                            {/* Prompt Name and Parameters */}
                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <label className="block text-sm font-medium mb-1">Prompt Name</label>
                                    <input
                                        type="text"
                                        value={name}
                                        onChange={(e) => setName(e.target.value)}
                                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-1 focus:ring-orange-500 transition-shadow"
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium mb-1">Parameters</label>
                                    <div className="flex space-x-2">
                                        <div className="w-1/2">
                                            <label className="block text-xs text-gray-500 mb-1">Max Tokens</label>
                                            <input
                                                type="number"
                                                defaultValue={1000}
                                                className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-1 focus:ring-orange-500 transition-shadow"
                                            />
                                        </div>
                                        <div className="w-1/2">
                                            <label className="block text-xs text-gray-500 mb-1">Temp</label>
                                            <input
                                                type="number"
                                                defaultValue={0.7}
                                                step={0.1}
                                                min={0}
                                                max={1}
                                                className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-1 focus:ring-orange-500 transition-shadow"
                                            />
                                        </div>
                                    </div>
                                </div>
                            </div>

                            {/* Tags and Dataset */}
                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <label className="block text-sm font-medium mb-1">Tags</label>
                                    <div className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-1 focus:ring-orange-500 transition-shadow bg-white">
                                        <div className="flex flex-wrap mb-1">
                                            {/* Selected tags */}
                                            {tags.length > 0 && (
                                                <div className="flex flex-wrap gap-1 mb-1">
                                                    {tags.map(tag => {
                                                        const tagLabel = availableTags.find(t => t.value === tag)?.label || tag;
                                                        return (
                                                            <div key={tag} className="bg-orange-100 text-orange-800 text-xs px-2 py-1 rounded-full flex items-center">
                                                                {tagLabel}
                                                                <button
                                                                    className="ml-1 text-orange-600 hover:text-orange-800"
                                                                    onClick={() => toggleTag(tag)}
                                                                >
                                                                    <X size={12} />
                                                                </button>
                                                            </div>
                                                        );
                                                    })}
                                                </div>
                                            )}
                                        </div>

                                        {/* Tag options */}
                                        <div className="mt-2 border-t pt-2">
                                            <div className="text-xs text-gray-500 mb-1">Select tags:</div>
                                            <div className="grid grid-cols-2 gap-1">
                                                {availableTags.map(tag => (
                                                    <div
                                                        key={tag.value}
                                                        className={`
                                                            cursor-pointer text-sm px-2 py-1 rounded 
                                                            ${tags.includes(tag.value)
                                                                ? 'bg-orange-100 text-orange-800'
                                                                : 'hover:bg-gray-100 text-gray-700'
                                                            }
                                                        `}
                                                        onClick={() => toggleTag(tag.value)}
                                                    >
                                                        <div className="flex items-center">
                                                            {tags.includes(tag.value) && (
                                                                <Check size={14} className="mr-1 text-orange-500" />
                                                            )}
                                                            <span>{tag.label}</span>
                                                        </div>
                                                    </div>
                                                ))}
                                            </div>
                                        </div>
                                    </div>
                                </div>
                                <div>
                                    <label className="block text-sm font-medium mb-1">Dataset</label>
                                    <select
                                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-1 focus:ring-orange-500 transition-shadow"
                                        defaultValue="arlo"
                                    >
                                        <option value="arlo">Knowledge Base</option>
                                        <option value="mcp">Multi-Cloud Platform</option>
                                        <option value="docs">API Documentation</option>
                                        <option value="none">None</option>
                                    </select>
                                </div>
                            </div>

                            {/* Description and Model */}
                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <label className="block text-sm font-medium mb-1">Description</label>
                                    <input
                                        type="text"
                                        value={description}
                                        onChange={(e) => setDescription(e.target.value)}
                                        placeholder="Describe what this agent does"
                                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-1 focus:ring-orange-500 transition-shadow"
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium mb-1">Model</label>
                                    <select
                                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-1 focus:ring-orange-500 transition-shadow"
                                        defaultValue={nodeData.config?.model || "claude"}
                                    >
                                        <option value="claude">Claude 3</option>
                                        <option value="gpt4o">GPT-4o</option>
                                        <option value="GPT-4o-mini">GPT-4o-mini</option>
                                        <option value="gpt35">GPT-3.5</option>
                                        <option value="mixtral">Mixtral</option>
                                        <option value="llama3">Llama 3</option>
                                    </select>
                                </div>
                            </div>

                            {/* System Message */}
                            <div>
                                <div className="flex justify-between items-center mb-1">
                                    <label className="block text-sm font-medium">System Message</label>
                                    <span className="text-xs text-gray-500">
                                        {currentLength}/{maxLength} characters
                                    </span>
                                </div>
                                <textarea
                                    value={prompt}
                                    onChange={(e) => setPrompt(e.target.value)}
                                    placeholder={placeholderText(nodeData.type)}
                                    className="w-full px-3 py-2 border border-gray-300 rounded-md h-40 focus:outline-none focus:ring-1 focus:ring-orange-500 transition-shadow"
                                    maxLength={maxLength}
                                />
                            </div>
                        </div>
                    )}

                    {activeTab === "parameters" && (
                        <div className="space-y-4">
                            <div className="bg-orange-50 p-3 rounded-md text-orange-700 text-sm mb-4">
                                These parameters control how the LLM processes inputs and generates responses.
                            </div>

                            <div>
                                <label className="block text-sm font-medium mb-1">Temperature</label>
                                <input
                                    type="range"
                                    min="0"
                                    max="1"
                                    step="0.1"
                                    defaultValue="0.7"
                                    className="w-full"
                                />
                                <div className="flex justify-between text-xs text-gray-500 mt-1">
                                    <span>0 - Precise</span>
                                    <span>0.7</span>
                                    <span>1 - Creative</span>
                                </div>
                                <div className="text-xs text-gray-500 mt-1">
                                    Controls randomness in the output. Lower values are more deterministic.
                                </div>
                            </div>

                            <div>
                                <label className="block text-sm font-medium mb-1">Max Tokens</label>
                                <input
                                    type="number"
                                    defaultValue={1000}
                                    min={1}
                                    max={4096}
                                    className="w-full px-3 py-2 border border-gray-300 rounded-md transition-shadow"
                                />
                                <div className="text-xs text-gray-500 mt-1">
                                    Maximum number of tokens in the response. Higher values allow for longer outputs.
                                </div>
                            </div>

                            <div>
                                <label className="block text-sm font-medium mb-1">Top P</label>
                                <input
                                    type="range"
                                    min="0"
                                    max="1"
                                    step="0.05"
                                    defaultValue="0.95"
                                    className="w-full"
                                />
                                <div className="text-xs text-gray-500 mt-1">
                                    Controls diversity via nucleus sampling. Lower values make output more focused.
                                </div>
                            </div>

                            <div>
                                <label className="block text-sm font-medium mb-1">Frequency Penalty</label>
                                <input
                                    type="range"
                                    min="0"
                                    max="2"
                                    step="0.1"
                                    defaultValue="0"
                                    className="w-full"
                                />
                                <div className="text-xs text-gray-500 mt-1">
                                    Reduces repetition by penalizing tokens that have already appeared. Higher values reduce repetition.
                                </div>
                            </div>

                            <div>
                                <label className="block text-sm font-medium mb-1">Presence Penalty</label>
                                <input
                                    type="range"
                                    min="0"
                                    max="2"
                                    step="0.1"
                                    defaultValue="0"
                                    className="w-full"
                                />
                                <div className="text-xs text-gray-500 mt-1">
                                    Increases diversity by penalizing tokens that have appeared at all. Higher values encourage more diverse topics.
                                </div>
                            </div>
                        </div>
                    )}

                    {activeTab === "testing" && (
                        <div className="space-y-4">
                            <div className="bg-blue-50 p-3 rounded-md text-blue-800 text-sm mb-4">
                                Test your prompt with sample inputs to see how it performs. Results will be shown below.
                            </div>

                            {/* Testing Console */}
                            <div>
                                <label className="block text-sm font-medium mb-1">Testing Console</label>
                                <div className="border border-gray-300 rounded-md p-3 bg-gray-50">
                                    <div className="border-b border-gray-200 pb-2 mb-2">
                                        <div className="text-xs text-gray-500 mb-1">Input 1</div>
                                        <input
                                            type="text"
                                            placeholder="Add test input..."
                                            className="w-full px-2 py-1 bg-transparent border-0 focus:outline-none focus:ring-0 text-sm"
                                        />
                                    </div>
                                    <div className="flex justify-between">
                                        <button className="text-orange-500 hover:text-orange-700 transition-colors text-xs flex items-center">
                                            <Plus className="w-3.5 h-3.5 mr-1" />
                                            Add Input
                                        </button>
                                        <button className="bg-orange-500 hover:bg-orange-600 transition-colors text-white px-3 py-1 rounded text-xs">
                                            Run Test
                                        </button>
                                    </div>
                                </div>

                                {/* Test Results */}
                                <div className="mt-4">
                                    <label className="block text-sm font-medium mb-1">Results</label>
                                    <div className="border border-gray-300 rounded-md p-3 bg-white h-40 overflow-y-auto">
                                        <div className="text-gray-400 text-sm italic">
                                            Test results will appear here...
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    )}
                </div>

                {/* Footer */}
                <div className="px-4 py-3 border-t border-gray-200 flex justify-end space-x-2 mt-auto">
                    <button
                        onClick={onClose}
                        className="px-4 py-2 bg-white border border-gray-300 rounded-md text-sm hover:bg-gray-50 transition-colors"
                    >
                        Cancel
                    </button>
                    <button
                        onClick={handleSave}
                        className="px-4 py-2 bg-orange-500 hover:bg-orange-600 text-white rounded-md text-sm transition-colors flex items-center"
                    >
                        <Save size={16} className="mr-2" />
                        Save Changes
                    </button>
                </div>
            </div>
        </div>
    );
};

export default AgentConfigModal;
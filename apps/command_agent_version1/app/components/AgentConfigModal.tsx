// AgentConfigModal.tsx
"use client";

import React, { useState, useEffect } from "react";
import { X, Plus } from "lucide-react";
import { AgentType } from "./type";

interface ModalProps {
    isOpen: boolean;
    nodeData: {
        id: string;
        type: AgentType;
        name: string;
        shortId?: string;
        prompt?: string;
    } | null;
    onClose: () => void;
    onSave: (id: string, name: string, prompt: string) => void;
}

const AgentConfigModal: React.FC<ModalProps> = ({
    isOpen,
    nodeData,
    onClose,
    onSave
}) => {
    const [name, setName] = useState("");
    const [prompt, setPrompt] = useState("");
    const [activeTab, setActiveTab] = useState("prompt");
    const maxLength = 1000;

    // Reset state when node data changes
    useEffect(() => {
        if (nodeData) {
            setName(nodeData.name || "");
            setPrompt(nodeData.prompt || "");
        }
    }, [nodeData]);

    if (!isOpen || !nodeData) return null;

    const handleSave = () => {
        onSave(nodeData.id, name, prompt);
    };

    const currentLength = prompt.length;

    // Function to prevent modal closing when clicking inside
    const handleModalClick = (e: React.MouseEvent) => {
        e.stopPropagation();
    };

    return (
        <div
            className="fixed inset-0 bg-black bg-opacity-30 flex items-center justify-center z-50"
            onClick={onClose}
        >
            <div
                className="bg-white rounded-lg shadow-lg transform transition-transform duration-300 ease-in-out"
                style={{ width: "650px", maxWidth: "95vw" }}
                onClick={handleModalClick}
            >
                {/* Header */}
                <div className="flex justify-between items-center px-4 py-3 border-b border-gray-200">
                    <h3 className="text-lg font-medium">
                        Edit Prompt
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
                                ? "text-blue-600 border-b-2 border-blue-600"
                                : "text-gray-500 hover:text-gray-700"
                                }`}
                            onClick={() => setActiveTab("prompt")}
                        >
                            Prompt
                        </button>
                        <button
                            className={`px-4 py-2 text-sm font-medium transition-colors duration-200 ${activeTab === "parameters"
                                ? "text-blue-600 border-b-2 border-blue-600"
                                : "text-gray-500 hover:text-gray-700"
                                }`}
                            onClick={() => setActiveTab("parameters")}
                        >
                            Parameters
                        </button>
                    </div>
                </div>

                {/* Body */}
                <div className="p-4" style={{ maxHeight: "70vh", overflowY: "auto" }}>
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
                                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-1 focus:ring-blue-500 transition-shadow"
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
                                                className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-1 focus:ring-blue-500 transition-shadow"
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
                                                className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-1 focus:ring-blue-500 transition-shadow"
                                            />
                                        </div>
                                    </div>
                                </div>
                            </div>

                            {/* Type and Dataset */}
                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <label className="block text-sm font-medium mb-1">Type</label>
                                    <select
                                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-1 focus:ring-blue-500 transition-shadow"
                                        defaultValue={nodeData.type}
                                    >
                                        <option value="router">Router</option>
                                        <option value="data">Data Extractor</option>
                                        <option value="web_search">Web Search</option>
                                        <option value="api">API</option>
                                        <option value="troubleshooting">Troubleshooting</option>
                                    </select>
                                </div>
                                <div>
                                    <label className="block text-sm font-medium mb-1">Dataset</label>
                                    <select
                                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-1 focus:ring-blue-500 transition-shadow"
                                        defaultValue="arlo"
                                    >
                                        <option value="arlo">Arlo Knowledge Base</option>
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
                                        placeholder="Extracts information from invoices"
                                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-1 focus:ring-blue-500 transition-shadow"
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium mb-1">Model</label>
                                    <select
                                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-1 focus:ring-blue-500 transition-shadow"
                                        defaultValue="claude"
                                    >
                                        <option value="claude">Claude 3</option>
                                        <option value="gpt4">GPT-4</option>
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
                                    placeholder={`Define how this ${nodeData.type} should distribute queries to connected agents...`}
                                    className="w-full px-3 py-2 border border-gray-300 rounded-md h-40 focus:outline-none focus:ring-1 focus:ring-blue-500 transition-shadow"
                                    maxLength={maxLength}
                                />
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
                                        <button className="text-blue-500 hover:text-blue-700 transition-colors text-xs flex items-center">
                                            <Plus className="w-3.5 h-3.5 mr-1" />
                                            Add Input
                                        </button>
                                        <button className="bg-blue-500 hover:bg-blue-600 transition-colors text-white px-3 py-1 rounded text-xs">
                                            Run Test
                                        </button>
                                    </div>
                                </div>
                            </div>
                        </div>
                    )}

                    {activeTab === "parameters" && (
                        <div className="space-y-4">
                            <div className="bg-yellow-50 p-3 rounded-md text-yellow-800 text-sm mb-4">
                                These are the parameters for the prompt. They control how the model processes the input.
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
                            </div>

                            <div>
                                <label className="block text-sm font-medium mb-1">Max Tokens</label>
                                <input
                                    type="number"
                                    defaultValue={1000}
                                    className="w-full px-3 py-2 border border-gray-300 rounded-md transition-shadow"
                                />
                                <div className="text-xs text-gray-500 mt-1">
                                    Maximum number of tokens in the response
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
                                    Controls diversity via nucleus sampling
                                </div>
                            </div>
                        </div>
                    )}
                </div>

                {/* Footer */}
                <div className="px-4 py-3 border-t border-gray-200 flex justify-end space-x-2">
                    <button
                        onClick={onClose}
                        className="px-4 py-2 bg-white border border-gray-300 rounded-md text-sm hover:bg-gray-50 transition-colors"
                    >
                        Cancel
                    </button>
                    <button
                        onClick={handleSave}
                        className="px-4 py-2 bg-orange-500 hover:bg-orange-600 text-white rounded-md text-sm transition-colors"
                    >
                        Save
                    </button>
                </div>
            </div>
        </div>
    );
};

export default AgentConfigModal;
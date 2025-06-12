"use client";

import React from "react";
import { Edit, Save, X, Sliders } from "lucide-react";

type AgentType = "router" | "web_search" | "api" | "data" | "troubleshooting";

interface AgentPromptEditorProps {
    type: AgentType;
    name?: string;
    description?: string;
    prompt?: string;
    onOpenFullEditor: () => void;
    onClose?: () => void;
    onSave?: (data: { name: string; prompt: string }) => void;
}

const AgentPromptEditor: React.FC<AgentPromptEditorProps> = ({
    type,
    name = "",
    description = "",
    prompt = "",
    onOpenFullEditor,
    onClose,
    onSave
}) => {
    // Content-based UI that resembles the third image you shared
    return (
        <div className="flex flex-col h-full">
            {/* Header with close button */}
            <div className="flex justify-between items-center px-4 py-3 border-b border-gray-200">
                <h3 className="text-lg font-medium">Edit {type.charAt(0).toUpperCase() + type.slice(1)} Agent</h3>
                {onClose && (
                    <button
                        onClick={onClose}
                        className="text-gray-400 hover:text-gray-600 transition-colors"
                    >
                        <X size={18} />
                    </button>
                )}
            </div>

            {/* Main content area */}
            <div className="p-4 flex-1 overflow-y-auto">
                <div className="space-y-4">
                    {/* Basic information */}
                    <div>
                        <label className="block text-sm font-medium mb-1">Prompt Name</label>
                        <input
                            type="text"
                            defaultValue={name}
                            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-1 focus:ring-blue-500 transition-shadow"
                            placeholder="Enter agent name"
                        />
                    </div>

                    <div>
                        <label className="block text-sm font-medium mb-1">Type</label>
                        <select
                            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-1 focus:ring-blue-500 transition-shadow"
                            defaultValue={type}
                        >
                            <option value="router">Router</option>
                            <option value="data">Data Extractor</option>
                            <option value="web_search">Web Search</option>
                            <option value="api">API</option>
                            <option value="troubleshooting">Troubleshooting</option>
                        </select>
                    </div>

                    <div>
                        <label className="block text-sm font-medium mb-1">Description</label>
                        <input
                            type="text"
                            defaultValue={description}
                            placeholder="Describe what this agent does"
                            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-1 focus:ring-blue-500 transition-shadow"
                        />
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                        <div>
                            <label className="block text-sm font-medium mb-1">Dataset</label>
                            <select
                                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-1 focus:ring-blue-500 transition-shadow"
                                defaultValue="arlo"
                            >
                                <option value="arlo">Knowledge Base</option>
                                <option value="mcp">Multi-Cloud Platform</option>
                                <option value="docs">API Documentation</option>
                                <option value="none">None</option>
                            </select>
                        </div>
                        <div>
                            <label className="block text-sm font-medium mb-1">Model</label>
                            <select
                                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-1 focus:ring-blue-500 transition-shadow"
                                defaultValue="claude"
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

                    {/* Buttons for editing full prompt and configuration */}
                    <div className="flex flex-col space-y-2 mt-4">
                        <button
                            onClick={onOpenFullEditor}
                            className="flex items-center justify-center bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-md text-sm font-medium transition-colors"
                        >
                            <Edit className="w-4 h-4 mr-2" />
                            Edit Full Prompt
                        </button>

                        <button
                            className="flex items-center justify-center bg-gray-100 hover:bg-gray-200 text-gray-700 px-4 py-2 rounded-md text-sm font-medium transition-colors"
                        >
                            <Sliders className="w-4 h-4 mr-2" />
                            Advanced Parameters
                        </button>
                    </div>

                    {/* Preview of the prompt */}
                    <div>
                        <div className="flex justify-between items-center mb-1">
                            <label className="block text-sm font-medium">System Message Preview</label>
                            <span className="text-xs text-gray-500">
                                {prompt.length}/1000 characters
                            </span>
                        </div>
                        <div className="w-full px-3 py-2 border border-gray-300 rounded-md h-32 bg-gray-50 overflow-y-auto text-sm">
                            {prompt || `Define how this ${type} should process queries...`}
                        </div>
                    </div>
                </div>
            </div>

            {/* Footer with action buttons */}
            <div className="px-4 py-3 border-t border-gray-200 mt-auto flex justify-end space-x-2">
                {onClose && (
                    <button
                        onClick={onClose}
                        className="px-4 py-2 bg-white border border-gray-300 rounded-md text-sm hover:bg-gray-50 transition-colors"
                    >
                        Cancel
                    </button>
                )}
                {onSave && (
                    <button
                        onClick={() => onSave({ name, prompt })}
                        className="px-4 py-2 bg-orange-500 hover:bg-orange-600 text-white rounded-md text-sm transition-colors"
                    >
                        <Save className="w-4 h-4 mr-2 inline-block" />
                        Save
                    </button>
                )}
            </div>
        </div>
    );
};

export default AgentPromptEditor;
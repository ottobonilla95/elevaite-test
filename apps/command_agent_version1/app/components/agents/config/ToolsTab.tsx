"use client";

import React, { useEffect, useState } from "react";
import { ChevronUp, ChevronDown, Trash2, Plus, Search, X } from "lucide-react";
import { getToolIcon } from "../iconUtils";
import { useTools } from "../../../ui/contexts/ToolsContext";
import { usePrompts } from "../../../ui/contexts/PromptsContext";
import { type ToolsTabProps } from "./types";
import { PromptResponse } from "../../../lib/interfaces";
import { MockupTools } from "../../../lib/mockupComponents";

function ToolsTab({
    selectedFunctions,
    disabledFields,
    onEditPrompt,
    handleToolSelect,
    handlePromptSelect,
    selectedPromptId,
    agent,
    onPromptClick
}: ToolsTabProps): JSX.Element {
    const [toolsOpen, setToolsOpen] = useState(true);
    const [promptsOpen, setPromptsOpen] = useState(true);
    const [showSearch, setShowSearch] = useState(false);
    const [searchQuery, setSearchQuery] = useState("");
    const [showPromptSearch, setShowPromptSearch] = useState(false);
    const [promptSearchQuery, setPromptSearchQuery] = useState("");
    const [selectedPrompt, setSelectedPrompt] = useState<PromptResponse | null>(null);

    // Get tools from context
    const { tools: availableTools, isLoading: isLoadingTools } = useTools();

    // Get prompts from context
    const { agentPrompts: availablePrompts, isLoading: isLoadingPrompts, getPromptById } = usePrompts();

    useEffect(() => {
        setSelectedPrompt(agent.agent.system_prompt);
    }, [agent]);

    // Update selectedPrompt when selectedPromptId changes
    useEffect(() => {
        if (selectedPromptId) {
            const prompt = getPromptById(selectedPromptId);
            if (prompt) {
                setSelectedPrompt(prompt);
            }
        } else {
            // No prompt selected, clear the selected prompt
            setSelectedPrompt(null);
        }
    }, [selectedPromptId, getPromptById]);

    // Filter tools based on search query
    const filteredTools = availableTools.filter(tool =>
        tool.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        tool.description.toLowerCase().includes(searchQuery.toLowerCase())
    );

    // Get already selected tool names for filtering
    const selectedToolNames = selectedFunctions.map(func => func.function.name);

    // Filter out already selected tools
    const availableFilteredTools = filteredTools.filter(tool =>
        !selectedToolNames.includes(tool.name)
    );

    // Filter prompts based on search query
    const filteredPrompts = (availablePrompts || []).filter(prompt =>
        prompt.prompt_label.toLowerCase().includes(promptSearchQuery.toLowerCase()) ||
        prompt.prompt.toLowerCase().includes(promptSearchQuery.toLowerCase()) ||
        prompt.unique_label.toLowerCase().includes(promptSearchQuery.toLowerCase())
    );

    const handleAddTool = (toolName: string): void => {
        handleToolSelect(toolName);
        // Optionally close search after adding a tool
        // setShowSearch(false);
        // setSearchQuery("");
    };

    const handleAddPrompt = (promptId: string): void => {
        if (handlePromptSelect) {
            handlePromptSelect(promptId);
        }
        // Close search after adding a prompt
        setShowPromptSearch(false);
        setPromptSearchQuery("");
    };

    return (
        <div className="tools-tab">
            {/* Tools Section */}
            <button
                className="flex justify-between items-center w-full font-medium text-sm mt-4 mb-3"
                onClick={() => { setToolsOpen(!toolsOpen); }}
                type="button"
            >
                <h3 className="section-title">Tools</h3>
                {toolsOpen ? <ChevronUp size={18} /> : <ChevronDown size={18} />}
            </button>

            {toolsOpen ? <div>
                {/* Selected Tools */}
                {selectedFunctions.length > 0 && (
                    <div className="flex flex-wrap">
                        {selectedFunctions.map(func => (
                            <div key={func.function.name} className="flex flex-col gap-3">
                                <div className="flex justify-between">
                                    <div
                                        className="flex items-center gap-2 rounded-md text-xs bg-[#FF681F1F] text-[#FF681F] py-1 pr-[10px] pl-2"
                                    >
                                        {getToolIcon(func.function.name)}
                                        <span className="tool-name">{func.function.name}</span>

                                    </div>
                                    {!disabledFields ? <button
                                        className="remove-tool-button"
                                        onClick={() => { handleToolSelect(func.function.name); }}
                                        type="button"
                                    >
                                        <Trash2 size={16} />
                                    </button> : null}
                                </div>
                                <span className="text-xs text-gray-500">{func.function.description}</span>
                            </div>
                        ))}
                    </div>
                )}

                {/* Add Tools Button or Search Interface */}
                {!disabledFields && !showSearch && (
                    <button
                        className="flex items-center justify-start gap-2 w-full text-[#FF681F] text-xs"
                        onClick={() => { setShowSearch(true); }}
                        type="button"
                    >
                        <Plus size={16} />
                        Add Tools
                    </button>
                )}

                {/* Search Interface */}
                {!disabledFields && showSearch ? <div className="flex flex-col gap-3">
                    {/* Close Button */}
                    <button
                        onClick={() => {
                            setShowSearch(false);
                            setSearchQuery("");
                        }}
                        className="flex items-center gap-2 text-[#FF681F] text-xs justify-start hover:text-[#E55A1A]"
                        type="button"
                    >
                        <X size={16} />
                        Close
                    </button>

                    {/* Search Bar */}
                    <div className="flex items-center border border-gray-300 rounded-md px-3 py-2">
                        <Search size={16} className="text-gray-400 mr-2" />
                        <input
                            type="text"
                            placeholder="Search tools..."
                            value={searchQuery}
                            onChange={(e) => { setSearchQuery(e.target.value); }}
                            className="flex-1 outline-none text-sm"
                        />
                    </div>

                    {/* Loading State */}
                    {isLoadingTools ? <div className="text-center text-gray-500 text-sm py-4">
                        Loading tools...
                    </div> : null}

                    {/* Search Results */}
                    {!isLoadingTools && (
                        <div className="max-h-60 overflow-y-auto">
                            {availableFilteredTools.length > 0 ? (
                                <div className="flex flex-col gap-2">
                                    {availableFilteredTools.map(tool => (
                                        <button
                                            key={tool.name}
                                            onClick={() => { handleAddTool(tool.name); }}
                                            className="flex items-start gap-2 p-2 border border-gray-200 rounded-md hover:bg-gray-50 text-left"
                                            type="button"
                                        >
                                            <div className="flex items-center gap-2 flex-1">
                                                <div className="w-4 h-4 flex-shrink-0">
                                                    {getToolIcon(tool.name)}
                                                </div>
                                                <div className="flex flex-col">
                                                    <span className="text-sm font-medium">{tool.name}</span>
                                                    <span className="text-xs text-gray-600">{tool.description}</span>
                                                </div>
                                            </div>
                                            <Plus size={14} className="text-[#FF681F] mt-1 self-center" />
                                        </button>
                                    ))}
                                </div>
                            ) : (
                                <div className="text-center text-gray-500 text-sm py-4">
                                    {searchQuery ? "No tools found matching your search." : "No additional tools available."}
                                </div>
                            )}
                        </div>
                    )}
                </div> : null}
            </div> : null}

            {/* Prompt Section */}
            <button
                className="flex justify-between items-center w-full font-medium text-sm mt-4 mb-3"
                onClick={() => { setPromptsOpen(!promptsOpen); }}
                type="button"
            >
                <h3 className="section-title">Prompt</h3>
                {promptsOpen ? <ChevronUp size={18} /> : <ChevronDown size={18} />}
            </button>
            {promptsOpen ? <div className="flex flex-col gap-2">
                {selectedPrompt ? (
                    <button
                        onClick={() => onPromptClick?.(selectedPrompt)}
                        className="flex flex-col border rounded-[10px] px-4 py-3 hover:bg-gray-50 transition-colors text-left w-full"
                        type="button"
                    >
                        <div className="flex items-center justify-between gap-2">
							<div className="flex justify-between border-l-2 border-orange-500 pl-3">
								<span className="text-sm font-medium">{selectedPrompt.prompt_label}</span>
							</div>
							<svg width="4" height="18" viewBox="0 0 4 18" fill="none" xmlns="http://www.w3.org/2000/svg">
								<path d="M2 10C2.55228 10 3 9.55228 3 9C3 8.44772 2.55228 8 2 8C1.44772 8 1 8.44772 1 9C1 9.55228 1.44772 10 2 10Z" stroke="black" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
								<path d="M2 3C2.55228 3 3 2.55228 3 2C3 1.44772 2.55228 1 2 1C1.44772 1 1 1.44772 1 2C1 2.55228 1.44772 3 2 3Z" stroke="black" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
								<path d="M2 17C2.55228 17 3 16.5523 3 16C3 15.4477 2.55228 15 2 15C1.44772 15 1 15.4477 1 16C1 16.5523 1.44772 17 2 17Z" stroke="black" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
							</svg>
						</div>
                    </button>
                ) : (
                    "No prompt"
                )}

                {/* Add Prompt Button or Search Interface */}
                {!disabledFields && !showPromptSearch && (
                    <button
                        className="flex items-center justify-start gap-2 w-full text-[#FF681F] text-xs"
                        onClick={() => { setShowPromptSearch(true); }}
                        type="button"
                    >
                        <Plus size={16} />
                        Add Prompt
                    </button>
                )}

                {/* Prompt Search Interface */}
                {!disabledFields && showPromptSearch ? <div className="flex flex-col gap-3">
                    {/* Close Button */}
                    <button
                        onClick={() => {
                            setShowPromptSearch(false);
                            setPromptSearchQuery("");
                        }}
                        className="flex items-center gap-2 text-[#FF681F] text-xs justify-start hover:text-[#E55A1A]"
                        type="button"
                    >
                        <X size={16} />
                        Close
                    </button>

                    {/* Search Bar */}
                    <div className="flex items-center border border-gray-300 rounded-md px-3 py-2">
                        <Search size={16} className="text-gray-400 mr-2" />
                        <input
                            type="text"
                            placeholder="Search prompts..."
                            value={promptSearchQuery}
                            onChange={(e) => { setPromptSearchQuery(e.target.value); }}
                            className="flex-1 outline-none text-sm"
                        />
                    </div>

                    {/* Loading State */}
                    {isLoadingPrompts ? <div className="text-center text-gray-500 text-sm py-4">
                        Loading prompts...
                    </div> : null}

                    {/* Search Results */}
                    {!isLoadingPrompts && (
                        <div className="max-h-60 overflow-y-auto">
                            {filteredPrompts.length > 0 ? (
                                <div className="flex flex-col gap-2">
                                    {filteredPrompts.map(prompt => (
                                        <button
                                            key={prompt.pid}
                                            onClick={() => { handleAddPrompt(prompt.pid); }}
                                            className="flex items-start gap-2 p-2 border border-gray-200 rounded-md hover:bg-gray-50 text-left"
                                            type="button"
                                        >
                                            <div className="flex items-center gap-2 flex-1">
                                                <div className="w-4 h-4 flex-shrink-0">
                                                    <div className="w-4 h-4 bg-blue-100 rounded flex items-center justify-center">
                                                        <span className="text-blue-600 text-xs">P</span>
                                                    </div>
                                                </div>
                                                <div className="flex flex-col">
                                                    <span className="text-sm font-medium">{prompt.prompt_label}</span>
                                                    <span className="text-xs text-gray-600">{prompt.unique_label}</span>
                                                </div>
                                            </div>
                                            <Plus size={14} className="text-[#FF681F] mt-1 self-center" />
                                        </button>
                                    ))}
                                </div>
                            ) : (
                                <div className="text-center text-gray-500 text-sm py-4">
                                    {promptSearchQuery ? "No prompts found matching your search." : "No prompts available."}
                                </div>
                            )}
                        </div>
                    )}
                </div> : null}
            </div> : null}
        </div >
    );
}

export default ToolsTab;

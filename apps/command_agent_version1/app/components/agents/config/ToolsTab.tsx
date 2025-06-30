"use client";

import React, { useState } from "react";
import { ChevronUp, ChevronDown, Trash2, Plus, Search, X } from "lucide-react";
import { getToolIcon } from "../iconUtils";
import { useTools } from "../../../ui/contexts/ToolsContext";
import { usePrompts } from "../../../ui/contexts/PromptsContext";
import { type ToolsTabProps } from "./types";

function ToolsTab({
    selectedFunctions,
    disabledFields,
    onEditPrompt,
    handleToolSelect,
    handlePromptSelect,
    selectedPromptId,
    agent
}: ToolsTabProps): JSX.Element {
    const [toolsOpen, setToolsOpen] = useState(true);
    const [promptsOpen, setPromptsOpen] = useState(true);
    const [showSearch, setShowSearch] = useState(false);
    const [searchQuery, setSearchQuery] = useState("");
    const [showPromptSearch, setShowPromptSearch] = useState(false);
    const [promptSearchQuery, setPromptSearchQuery] = useState("");

    // Get tools from context
    const { tools: availableTools, isLoading: isLoadingTools } = useTools();

    // Get prompts from context
    const { agentPrompts: availablePrompts, isLoading: isLoadingPrompts, getPromptById } = usePrompts();

    // Get the current prompt to display (either selected or original)
    const currentPrompt = selectedPromptId ? getPromptById(selectedPromptId) : agent.agent.system_prompt;

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
                className="flex justify-between items-center w-full py-1 pr-[10px] pl-2"
                onClick={() => { setToolsOpen(!toolsOpen); }}
                type="button"
            >
                <h3 className="section-title">Tools</h3>
                {toolsOpen ? <ChevronUp size={18} /> : <ChevronDown size={18} />}
            </button>

            {toolsOpen ? <div className="flex flex-col gap-3 p-2">

                {/* Selected Tools */}
                {selectedFunctions.length > 0 && (
                    <div className="flex flex-wrap">
                        {selectedFunctions.map(func => (
                            <div key={func.function.name} className="flex flex-col gap-3 p-2">
                                <div className="flex justify-between">
                                    <div
                                        className="flex items-center gap-2 rounded-md bg-[#FF681F1F] text-[#FF681F] py-1 pr-[10px] pl-2"
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
                                <span className="text-xs text-[#212124]">{func.function.description}</span>
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
                className="flex justify-between items-center w-full py-1 pr-[10px] pl-2 border-t-[1px] border-gray-200"
                onClick={() => { setPromptsOpen(!promptsOpen); }}
                type="button"
            >
                <h3 className="section-title">Prompt</h3>
                {promptsOpen ? <ChevronUp size={18} /> : <ChevronDown size={18} />}
            </button>
            {promptsOpen ? <div className="flex flex-col gap-3 p-2">
                {currentPrompt ? <div className="flex flex-col border rounded-[10px] px-4 py-3">
                    <div className="flex justify-between border-l-2 border-orange-500 pl-3">
                        <span className="text-sm font-medium">{currentPrompt.prompt_label}</span>
                    </div>
                </div> : "No prompt"}

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
                {!disabledFields && showPromptSearch && (
                    <div className="flex flex-col gap-3">
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
                        {isLoadingPrompts && (
                            <div className="text-center text-gray-500 text-sm py-4">
                                Loading prompts...
                            </div>
                        )}

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
                    </div>
                )}
            </div> : null}
        </div >
    );
}

export default ToolsTab;

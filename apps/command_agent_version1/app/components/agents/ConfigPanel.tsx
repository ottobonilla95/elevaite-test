"use client";

import React, { useState, useEffect, useRef, useCallback } from "react";
import TabHeader, { type Tab } from "../TabHeader";
import { type AgentNodeData, type AgentConfigData, type AgentType, type ChatCompletionToolParam, type PromptResponse } from "../../lib/interfaces";
import { fetchToolSchemasAsArray } from "../../lib/toolActions";
import { usePrompts } from "../../ui/contexts/PromptsContext";
import { getAgentIcon } from "./iconUtils";
import { ConfigurationTab, ToolsTab, getAgentTypeDisplay, getModelProviders, getModels } from "./config";
import PromptDetailView from "./config/PromptDetailView";
import "./ConfigPanel.scss";







interface ConfigPanelProps {
    agent: AgentNodeData;
    agentName: string;
    agentType: AgentType | "custom";
    agentConfig?: AgentConfigData;
    description: string;
    onEditPrompt: () => void;
    onSave?: (configData: AgentConfigData) => void;
    onClose?: () => void;
    onNameChange?: (newName: string) => void;
    toggleSidebar?: () => void;
    sidebarOpen?: boolean;
    setSidebarOpen?: () => void;
    currentFunctions?: ChatCompletionToolParam[]; // Current agent functions
    onFunctionsChange?: (functions: ChatCompletionToolParam[]) => void; // Callback for function changes
}

function ConfigPanel({
    agent,
    agentName,
    agentType,
    description,
    onEditPrompt,
    onSave,
    toggleSidebar,
    sidebarOpen,
    currentFunctions = [],
    onFunctionsChange,
    agentConfig
}: ConfigPanelProps): JSX.Element {
    // State for editable fields
    const [deploymentType, setDeploymentType] = useState("Elevaite");
    const [modelProvider, setModelProvider] = useState("meta");
    const [model, setModel] = useState("Llama-3.1-8B-Instruct");
    const [outputFormat, setOutputFormat] = useState("JSON");
    const [activeTab, setActiveTab] = useState("config");

    // State for sidebar view mode
    const [sidebarView, setSidebarView] = useState<"config" | "prompt">("config");
    const [selectedPromptForView, setSelectedPromptForView] = useState<PromptResponse | null>(null);

    // State for selected tools (now as ChatCompletionToolParam array)
    const [selectedFunctions, setSelectedFunctions] = useState<ChatCompletionToolParam[]>(currentFunctions);

    // State for available tool schemas
    const [availableToolSchemas, setAvailableToolSchemas] = useState<ChatCompletionToolParam[]>([]);
    const [toolSchemasLoading, setToolSchemasLoading] = useState(false);
    const [toolSchemasError, setToolSchemasError] = useState<string | null>(null);

    // Note: We're now using tool schemas directly instead of the tools context

    // State for agent name editing
    const [editedName, setEditedName] = useState(agentName);
    const [disabledFields, setDisabledFields] = useState(true);

    // State for editable agent type and tags
    const [editedAgentType, setEditedAgentType] = useState<AgentType>(
        agent.agent.agent_type ?? (agentType === "custom" ? "router" : agentType)
    );
    const [editedDescription, setEditedDescription] = useState(
        agent.agent.description ?? description
    );
    const [editedTags, setEditedTags] = useState(agent.agent.system_prompt.tags?.join(", ") ?? "");
    const [selectedPromptId, setSelectedPromptId] = useState<string | null>(
        agent.agent.system_prompt?.pid ?? null
    );

    // Debug: Log the initial selectedPromptId
    useEffect(() => {
        console.log("Initial selectedPromptId:", selectedPromptId);
        console.log("Agent system prompt:", agent.agent.system_prompt);
    }, []);

    // Get prompts context
    const { getPromptById } = usePrompts();

    // Update local state when agentName prop changes
    useEffect(() => {
        setEditedName(agentName);
    }, [agentName]);

    // Update selected functions when currentFunctions prop changes
    useEffect(() => {
        setSelectedFunctions(currentFunctions);
    }, [currentFunctions]);

    // Load tool schemas on component mount
    useEffect(() => {
        const loadToolSchemas = async (): Promise<void> => {
            try {
                setToolSchemasLoading(true);
                setToolSchemasError(null);
                const schemas = await fetchToolSchemasAsArray();
                setAvailableToolSchemas(schemas);
            } catch (error) {
                // eslint-disable-next-line no-console -- TODO: Replace with proper error handling
                console.error("Failed to load tool schemas:", error);
                setToolSchemasError("Failed to load tool schemas");
            } finally {
                setToolSchemasLoading(false);
            }
        };

        void loadToolSchemas();
    }, []);
    // Define tabs for TabHeader component
    const sidebarTabs: Tab[] = [
        { id: "config", label: "Configuration" },
        { id: "tools", label: "Tools & Prompts" }
    ];

    // Update model provider when deployment type changes
    useEffect(() => {
        const providers = getModelProviders(deploymentType);
        setModelProvider(providers[0]);
    }, [deploymentType]);

    // Update model when model provider changes
    useEffect(() => {
        const availableModels = getModels(deploymentType, modelProvider);
        setModel(availableModels[0]);
    }, [modelProvider, deploymentType]);

    useEffect(() => {
        if (agentConfig) {
            setDeploymentType(agent.config?.deploymentType ?? "Elevaite");
            setModelProvider(agent.agent.system_prompt.ai_model_provider);
            setModel(agent.agent.system_prompt.ai_model_name);
            setOutputFormat(agent.agent.output_type.join(", "));
            setSelectedFunctions(agentConfig.selectedTools);
        }
    }, [agentConfig]);

    // Function to handle tool selection
    const handleToolSelect = (toolName: string): void => {
        // Find the tool schema for the selected tool
        const toolSchema = availableToolSchemas.find(schema => schema.function.name === toolName);
        if (!toolSchema) return;

        // Check if tool is already selected
        const isSelected = selectedFunctions.some(func => func.function.name === toolName);

        let updatedFunctions: ChatCompletionToolParam[];
        if (isSelected) {
            // Remove the tool
            updatedFunctions = selectedFunctions.filter(func => func.function.name !== toolName);
        } else {
            // Add the tool
            updatedFunctions = [...selectedFunctions, toolSchema];
        }

        setSelectedFunctions(updatedFunctions);

        // Notify parent component of the change
        if (onFunctionsChange) {
            onFunctionsChange(updatedFunctions);
        }
    };

    // Handle save button click
    const handleSave = useCallback((): void => {
        console.log("Current selectedPromptId in handleSave:", selectedPromptId)
        if (onSave) {
            console.log("Saving agent configuration:", {
                agentName: editedName,
                agentType: editedAgentType,
                description: editedDescription,
                tags: editedTags,
                selectedPromptId: selectedPromptId,
                deploymentType,
                modelProvider,
                model,
                outputFormat,
                selectedTools: selectedFunctions
            });
            onSave({
                agentName: editedName, // Include the potentially updated name
                agentType: editedAgentType,
                description: editedDescription,
                tags: editedTags,
                selectedPromptId, // Include the selected prompt
                deploymentType,
                modelProvider,
                model,
                outputFormat,
                selectedTools: selectedFunctions
            });
        }
    }, [selectedPromptId, editedName, editedAgentType, editedDescription, editedTags, deploymentType, modelProvider, model, outputFormat, selectedFunctions, onSave]);

    // Handle save as button click - creates a new agent
    const handleSaveAs = useCallback((): void => {
        if (onSave) {
            // Create a new agent with the current configuration
            onSave({
                agentName: editedName, // Use the edited name for the new agent
                agentType: editedAgentType,
                description: editedDescription,
                tags: editedTags,
                selectedPromptId, // Include the selected prompt for new agent
                deploymentType,
                modelProvider,
                model,
                outputFormat,
                selectedTools: selectedFunctions,
                isNewAgent: true // Flag to indicate this should create a new agent
            });
        }
    }, [selectedPromptId, editedName, editedAgentType, editedDescription, editedTags, deploymentType, modelProvider, model, outputFormat, selectedFunctions, onSave]);

    // Handle prompt selection
    const handlePromptSelect = (promptId: string): void => {
        console.log("handlePromptSelect called with promptId:", promptId);
        const selectedPrompt = getPromptById(promptId);
        console.log("Got one, ", selectedPrompt);
        if (selectedPrompt) {
            console.log("Setting selectedPromptId to:", promptId);
            setSelectedPromptId(promptId);
        } else {
            console.log("No prompt found for ID:", promptId);
        }
    };

    // Handle prompt click to view details
    const handlePromptClick = (prompt: PromptResponse): void => {
        setSelectedPromptForView(prompt);
        setSidebarView("prompt");
    };

    // Handle back to config view
    const handleBackToConfig = (): void => {
        setSidebarView("config");
        setSelectedPromptForView(null);
    };

    return (
        <div className="config-panel">
            {/* Header with close button and editable name */}
            <div className="config-panel-header">
                <div className="flex flex-1 items-center pr-4">
                    {!disabledFields ? (
                        <div className="flex flex-col gap-3 flex-1">
                            <div className="flex flex-col gap-1">
                                <label htmlFor="agent-name-input" className="text-sm font-medium" style={{ fontSize: '14px' }}>Agent Base</label>
                                <input
                                    id="agent-name-input"
                                    type="text"
                                    value={editedName}
                                    onChange={(e) => { setEditedName(e.target.value); }}
                                    className="border border-gray-300 rounded-md px-3 py-2"
                                    style={{ fontSize: '12px' }}
                                    placeholder="Enter agent name"
                                />
                            </div>
                            <div className="flex flex-col gap-1">
                                <label htmlFor="agent-description-input" className="text-sm font-medium" style={{ fontSize: '14px' }}>Description</label>
                                <input
                                    id="agent-description-input"
                                    type="text"
                                    value={editedDescription}
                                    onChange={(e) => { setEditedDescription(e.target.value); }}
                                    className="border border-gray-300 rounded-md px-3 py-2"
                                    style={{ fontSize: '12px' }}
                                    placeholder="Enter agent description"
                                />
                            </div>
                        </div>
                    ) : (
                        <div className="agent-name-display">
                            <div className="agent-icon flex-shrink-0">
                                {getAgentIcon(agentType)}
                            </div>
                            <div className="agent-title">
                                <p className="agent-name">{editedName}</p>
                                <p className="agent-description">{editedDescription}</p>
                            </div>
                            <button className="activate-fields" type="button" onClick={() => { setDisabledFields(!disabledFields); }}>
                                <svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
                                    <g opacity="0.8" clipPath="url(#clip0_255_10554)">
                                        <path d="M14 14H8.66664M1.66663 14.3334L5.36614 12.9105C5.60277 12.8195 5.72108 12.774 5.83177 12.7146C5.93009 12.6618 6.02383 12.6009 6.11199 12.5324C6.21124 12.4554 6.30088 12.3658 6.48015 12.1865L14 4.66671C14.7364 3.93033 14.7364 2.73642 14 2.00004C13.2636 1.26366 12.0697 1.26366 11.3333 2.00004L3.81348 9.51985C3.63421 9.69912 3.54457 9.78876 3.46755 9.88801C3.39914 9.97617 3.33823 10.0699 3.28545 10.1682C3.22603 10.2789 3.18053 10.3972 3.08951 10.6339L1.66663 14.3334ZM1.66663 14.3334L3.03871 10.766C3.13689 10.5107 3.18598 10.3831 3.27019 10.3246C3.34377 10.2735 3.43483 10.2542 3.52282 10.271C3.62351 10.2902 3.72021 10.3869 3.91361 10.5803L5.41967 12.0864C5.61307 12.2798 5.70977 12.3765 5.729 12.4772C5.74581 12.5652 5.72648 12.6562 5.67539 12.7298C5.61692 12.814 5.48928 12.8631 5.23401 12.9613L1.66663 14.3334Z" stroke={!disabledFields ? "#FF681F" : "#212124"} strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
                                    </g>
                                    <defs>
                                        <clipPath id="clip0_255_10554">
                                            <rect width="16" height="16" fill="white" />
                                        </clipPath>
                                    </defs>
                                </svg>
                            </button>
                        </div>
                    )}
                </div>

                <button type="button" onClick={toggleSidebar} className="flex flex-shrink-0 items-center">
                    {
                        sidebarOpen
                            ?
                            <svg width="14" height="12" viewBox="0 0 14 12" fill="none" xmlns="http://www.w3.org/2000/svg">
                                <path d="M1 11L6 6L1 1M8 11L13 6L8 1" stroke="#212124" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
                            </svg>
                            :
                            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                                <g opacity="0.8">
                                    <path d="M18 17L13 12L18 7M11 17L6 12L11 7" stroke="#212124" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
                                </g>
                            </svg>
                    }
                </button>
            </div>
            <div className="flex flex-col justify-between flex-1">
                <div>
                    {sidebarView === "config" ? (
                        <>
                            {/* Navigation Tabs */}
                            <TabHeader
                                tabs={sidebarTabs}
                                activeTab={activeTab}
                                onTabChange={setActiveTab}
                                innerClassName="sidebar-header-tabs-inner p-1 rounded-lg flex items-center w-full"
                            />

                            {/* Tab Content */}
                            {activeTab === "config" && (
                                <ConfigurationTab
                                    agent={agent}
                                    agentType={editedAgentType}
                                    deploymentType={deploymentType}
                                    setDeploymentType={setDeploymentType}
                                    modelProvider={modelProvider}
                                    setModelProvider={setModelProvider}
                                    model={model}
                                    setModel={setModel}
                                    outputFormat={outputFormat}
                                    setOutputFormat={setOutputFormat}
                                    disabledFields={disabledFields}
                                    setAgentType={setEditedAgentType}
                                    tags={editedTags}
                                    setTags={setEditedTags}
                                />
                            )}

                            {activeTab === "tools" && (
                                <ToolsTab
                                    selectedFunctions={selectedFunctions}
                                    handleToolSelect={handleToolSelect}
                                    handlePromptSelect={handlePromptSelect}
                                    selectedPromptId={selectedPromptId}
                                    disabledFields={disabledFields}
                                    onEditPrompt={onEditPrompt}
                                    agent={agent}
                                    onPromptClick={handlePromptClick}
                                />
                            )}
                        </>
                    ) : (
                        /* Prompt Detail View */
                        selectedPromptForView && (
                            <PromptDetailView
                                prompt={selectedPromptForView}
                                onBack={handleBackToConfig}
                                disabledFields={disabledFields}
                            />
                        )
                    )}
                </div>

                {/* Action Buttons - Only show when editing */}
                {!disabledFields && (
                    <div className="flex gap-3 justify-evenly">
                        {/* Cancel Button */}
                        <button
                            onClick={() => {
                                // Reset all edited values to original
                                setEditedName(agentName);
                                setEditedDescription(agent.agent.description ?? description);
                                setEditedAgentType(agent.agent.agent_type ?? (agentType === "custom" ? "router" : agentType));
                                setEditedTags(agent.agent.system_prompt.tags?.join(", ") ?? "");
                                setDisabledFields(true);
                            }}
                            className="grow px-4 py-2 border border-[#FF681F] text-[#FF681F] rounded-md hover:bg-[#FF681F]/5 transition-colors"
                            style={{ fontSize: '14px' }}
                            type="button"
                        >
                            Cancel
                        </button>

                        {/* Save Button */}
                        <button
                            onClick={() => {
                                handleSave();
                                setDisabledFields(true);
                            }}
                            className="grow px-4 py-2 border border-[#FF681F] text-[#FF681F] rounded-md hover:bg-[#FF681F]/5 transition-colors"
                            style={{ fontSize: '14px' }}
                            type="button"
                        >
                            Save
                        </button>

                        {/* Save As Button */}
                        <button
                            onClick={() => {
                                handleSaveAs();
                                setDisabledFields(true);
                            }}
                            className="grow px-4 py-2 bg-[#FF681F] text-white rounded-md hover:bg-[#E55A1A] transition-colors"
                            style={{ fontSize: '14px' }}
                            type="button"
                        >
                            Save As
                        </button>
                    </div>
                )}
            </div>
        </div>
    );
};

export default ConfigPanel;
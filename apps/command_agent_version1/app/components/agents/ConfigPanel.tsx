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
import { ChevronsLeft, ChevronsRight, PenLine } from "lucide-react";







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

    // Reset sidebar view when agent changes
    useEffect(() => {
        setSidebarView("config");
        setSelectedPromptForView(null);
    }, [agent]);

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
            {selectedPromptForView ? <PromptDetailView
                prompt={selectedPromptForView}
                onBack={handleBackToConfig}
                disabledFields={disabledFields}
                setDisabledFields={setDisabledFields}
            /> : <>
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
                            <div className="flex flex-1 items-center gap-3 justify-between">
                                <div className="agent-name-display">
                                    <div className="agent-icon flex-shrink-0">
                                        {getAgentIcon(agentType)}
                                    </div>
                                    <div className="agent-title">
                                        <p className="agent-name">{editedName}</p>
                                        <p className="agent-description">{editedDescription}</p>
                                    </div>
                                </div>
                                <button className="activate-fields" type="button" onClick={() => { setDisabledFields(!disabledFields); }}>
                                    <PenLine size={20} />
                                </button>
                            </div>
                        )}
                    </div>

                    <button type="button" onClick={toggleSidebar} className="flex flex-shrink-0 items-center">
                        {sidebarOpen ? <ChevronsRight /> : <ChevronsLeft />}
                    </button>
                </div>
                <div className="flex flex-col justify-between flex-1">
                    <div>
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
            </>}
        </div>
    );
};

export default ConfigPanel;
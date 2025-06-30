"use client";

import React, { useState, useEffect, useRef } from "react";
import {
    ChevronDown,
    ChevronUp,
    Edit,
    Save,
    X,
    Check,
    Trash2,
} from "lucide-react";
import TabHeader, { type Tab } from "../TabHeader";
import { AGENT_STYLES } from "../type";
import { type AgentNodeData, type AgentConfigData, type AgentType, type ChatCompletionToolParam } from "../../lib/interfaces";
import { fetchToolSchemasAsArray } from "../../lib/toolActions";
import { getAgentIcon, getToolIcon } from "./iconUtils";
import "./ConfigPanel.scss";
import Pill from "../ui/Pill";

// Tab Components
function ConfigurationTab({
    agentType,
    deploymentType,
    modelProvider,
    model,
    outputFormat,
    setDeploymentType,
    setModelProvider,
    setModel,
    setOutputFormat,
    disabledFields,
}: {
    agentType: AgentType,
    deploymentType: string,
    modelProvider: string,
    model: string,
    outputFormat: string,
    setDeploymentType: (type: string) => void,
    setModelProvider: (provider: string) => void,
    setModel: (model: string) => void,
    setOutputFormat: (format: string) => void,
    disabledFields: boolean,
}): JSX.Element {

    // Deployment type options
    const deploymentTypes = [
        "Elevaite",
        "Enterprise",
        "Cloud"
    ];

    // Current model providers based on selected deployment type
    const modelProviders = getModelProviders(deploymentType);

    // Current models based on selected deployment type and model provider
    const models = getModels(deploymentType, modelProvider);

    return (
        <div className="configuration-tab gap-3 p-2">

            {/* Agent Type Badge */}
            <div className="agent-type-container flex flex-col gap-1 justify-start">
                <span className="text-xs font-medium">Agent Type</span>
                <Pill
                    text="Task-Based Agent"
                    textColor="#0950C3"
                    backgroundColor="#EBF2FE"
                />
            </div>

            {/* Parameters Grid */}
            <span className="text-sm font-medium">Parameters</span>
            <div className="parameters-grid">
                <div className="parameter-item">
                    <label className="parameter-label">Model
                        {disabledFields ? <Pill
                            text={model}
                            textColor="#6C8271"
                            backgroundColor="#6C82711F"
                            className="flex-shrink"
                        /> :
                            <select
                                value={model}
                                onChange={(e) => { setModel(e.target.value); }}
                                className="parameter-select"
                                disabled={disabledFields}
                            >
                                {models.map((_model) => (
                                    <option key={_model} value={_model}>{_model}</option>
                                ))}
                            </select>}
                    </label>
                </div>
                <div className="parameter-item">
                    <label className="parameter-label">Model Charge Type
                        {disabledFields ? <Pill
                            text={deploymentType}
                            textColor="#6C8271"
                            backgroundColor="#6C82711F"
                            className="flex-shrink"
                        /> :
                            <select
                                value={deploymentType}
                                onChange={(e) => { setDeploymentType(e.target.value); }}
                                className="parameter-select"
                                disabled={disabledFields}
                            >
                                {deploymentTypes.map((type) => (
                                    <option key={type} value={type}>{type}</option>
                                ))}
                            </select>}
                    </label>
                </div>
                {/* <div className="parameter-item">
                    <label className="parameter-label">Model Provider:
                        <select
                            value={modelProvider}
                            onChange={(e) => { setModelProvider(e.target.value); }}
                            className="parameter-select payment-select"
                            disabled={disabledFields}
                        >
                            {modelProviders.map((provider) => (
                                <option key={provider} value={provider}>{provider}</option>
                            ))}
                        </select></label>
                </div> */}
                <div className="parameter-item">
                    <label className="parameter-label">Output Format
                        {disabledFields ? <Pill
                            text={outputFormat}
                            textColor="#6C8271"
                            backgroundColor="#6C82711F"
                            className="flex-shrink"
                        /> :
                            <select
                                value={outputFormat}
                                onChange={(e) => { setOutputFormat(e.target.value); }}
                                className="parameter-select"
                                disabled={disabledFields}
                            >
                                <option value="JSON">JSON</option>
                                <option value="Text">Text</option>
                                <option value="CSV">CSV</option>
                                <option value="HTML">HTML</option>
                                <option value="Markdown">Markdown</option>
                                <option value="YAML">YAML</option>
                            </select>}
                    </label>
                </div>
            </div>
        </div>
    );
}

function ToolsTab({
    selectedFunctions,
    disabledFields,
    onEditPrompt,
    handleToolSelect,
    agent
}: {
    selectedFunctions: ChatCompletionToolParam[];
    disabledFields: boolean;
    onEditPrompt: () => void;
    handleToolSelect: (toolName: string) => void;
    agent: AgentNodeData;
}): JSX.Element {
    const [toolsOpen, setToolsOpen] = useState(true);
    const [promptsOpen, setPromptsOpen] = useState(true);
    return (
        <div className="tools-tab">
            {/* Tools content will go here */}{/* Tools Section */}
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
                    <div className="selected-tools-list">
                        {selectedFunctions.map(func => (
                            <div key={func.function.name} className="flex flex-col gap-2">
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
            </div> : null}

            {/* Edit Prompt Button */}
            <button
                className="flex justify-between items-center w-full py-1 pr-[10px] pl-2 border-t-[1px] border-gray-200"
                onClick={() => { setPromptsOpen(!promptsOpen); }}
                type="button"
            >
                <h3 className="section-title">Prompt</h3>
                {promptsOpen ? <ChevronUp size={18} /> : <ChevronDown size={18} />}
            </button>
            {promptsOpen ? <div className="flex flex-col gap-3 p-2">
                {agent.agent.system_prompt ? <div className="flex flex-col border rounded-[10px] px-4 py-3">
                    <div className="flex justify-between border-l-2 border-orange-500 pl-3">
                        <span className="text-sm font-medium">{agent.agent.system_prompt.prompt_label}</span>
                        {/* <span className="text-sm font-medium">{agent.agent.system_prompt.}</span> */}
                    </div>

                </div> : "No prompt"}
            </div> : null}
        </div >
    );
}

// Get the agent type display name
const getAgentTypeDisplay = (type: AgentType): string => {
    switch (type) {
        case "router": return "Router";
        case "web_search": return "Web Search";
        case "Weather Search Agent": return "API";
        case "data": return "Data Extractor";
        case "troubleshooting": return "Troubleshooting";
        default: return type;
    }
};

// Get the style class for the agent type
const getStyleClass = (type: AgentType): string => {
    // eslint-disable-next-line @typescript-eslint/no-unnecessary-condition -- Better safe than sorry
    const styles = AGENT_STYLES[type] || { bgClass: "bg-gray-100", textClass: "text-gray-600" };
    return `${styles.bgClass} ${styles.textClass}`;
};

// Get model providers based on deployment type
const getModelProviders = (deployType: string): string[] => {
    switch (deployType) {
        case "Elevaite":
            return ["meta", "openbmb", "OpenAI"];
        case "Enterprise":
            return ["OpenAI", "Gemini", "Bedrock", "Azure"];
        case "Cloud":
            return ["OpenAI", "Gemini", "Bedrock", "Azure"];
        default:
            return ["meta"];
    }
};

// Get models based on deployment type and model provider
const getModels = (deployType: string, provider: string): string[] => {
    if (deployType === "Elevaite") {
        switch (provider) {
            case "meta":
                return ["Llama-3.1-8B-Instruct"];
            case "openbmb":
                return ["MiniCPM-V-2_6"];
            case "OpenAI":
                return ["GPT-4o", "GPT-4o mini", "GPT-3.5", "o3-mini"];
            default:
                return ["Llama-3.1-8B-Instruct"];
        }
    } else if (deployType === "Enterprise" || deployType === "Cloud") {
        switch (provider) {
            case "OpenAI":
                return ["GPT-4o", "GPT-4o mini", "GPT-3.5", "o3-mini"];
            case "Gemini":
                return ["2.5 Pro", "2.5 Flash", "2.0 Flash"];
            case "Bedrock":
                return ["Claude 3.5", "Claude 3.5 Sonnet", "Claude 3.5 Haiku", "Llama 3.1 8B Instruct"];
            case "Azure":
                return ["GPT-4o", "GPT-4o mini", "GPT-3.5"];
            default:
                return ["GPT-4o"];
        }
    }
    return ["GPT-4o"];
};

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
    onClose,
    onNameChange,
    toggleSidebar,
    sidebarOpen,
    currentFunctions = [],
    onFunctionsChange,
    agentConfig
}: ConfigPanelProps): JSX.Element {
    // State for collapsible sections
    const [parametersOpen, setParametersOpen] = useState(true);

    // State for editable fields
    const [deploymentType, setDeploymentType] = useState("Elevaite");
    const [modelProvider, setModelProvider] = useState("meta");
    const [model, setModel] = useState("Llama-3.1-8B-Instruct");
    const [outputFormat, setOutputFormat] = useState("JSON");
    const [activeTab, setActiveTab] = useState("config");

    // State for selected tools (now as ChatCompletionToolParam array)
    const [selectedFunctions, setSelectedFunctions] = useState<ChatCompletionToolParam[]>(currentFunctions);

    // State for available tool schemas
    const [availableToolSchemas, setAvailableToolSchemas] = useState<ChatCompletionToolParam[]>([]);
    const [toolSchemasLoading, setToolSchemasLoading] = useState(false);
    const [toolSchemasError, setToolSchemasError] = useState<string | null>(null);

    // Note: We're now using tool schemas directly instead of the tools context

    // State for agent name editing
    const [isEditingName, setIsEditingName] = useState(false);
    const [editedName, setEditedName] = useState(agentName);
    const nameInputRef = useRef<HTMLInputElement>(null);
    const [disabledFields, setDisabledFields] = useState(true);

    // Effect to focus input when editing starts
    useEffect(() => {
        if (isEditingName && nameInputRef.current) {
            nameInputRef.current.focus();
        }
    }, [isEditingName]);

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

    // Handle name editing
    const startEditingName = (): void => {
        setIsEditingName(true);
    };

    const saveEditedName = (): void => {
        if (editedName.trim() === '') {
            setEditedName(agentName); // Restore original name if empty
        } else if (onNameChange && editedName !== agentName) {
            onNameChange(editedName);
        }
        setIsEditingName(false);
    };

    // Handle save button click
    const handleSave = (): void => {
        if (onSave) {
            onSave({
                agentName: editedName, // Include the potentially updated name
                deploymentType,
                modelProvider,
                model,
                outputFormat,
                selectedTools: selectedFunctions
            });
        }
    };

    // Handle keydown event for name input
    const handleNameKeyDown = (e: React.KeyboardEvent<HTMLInputElement>): void => {
        if (e.key === 'Enter') {
            saveEditedName();
        } else if (e.key === 'Escape') {
            setEditedName(agentName); // Restore original name
            setIsEditingName(false);
        }
    };

    return (
        <div className="config-panel">
            {/* Header with close button and editable name */}
            <div className="config-panel-header">
                <div className="flex items-center">
                    {isEditingName ? (
                        <div className="agent-name-edit-container">
                            <input
                                ref={nameInputRef}
                                type="text"
                                value={editedName}
                                onChange={(e) => { setEditedName(e.target.value); }}
                                onBlur={saveEditedName}
                                onKeyDown={handleNameKeyDown}
                                className="agent-name-input"
                                placeholder="Enter agent name"
                            />
                            <button
                                onClick={saveEditedName}
                                className="save-name-button"
                                type="button"
                            >
                                <Check size={16} />
                            </button>
                        </div>
                    ) : (
                        <div className="agent-name-display">
                            <div className="agent-icon">
                                {getAgentIcon(agentType)}
                            </div>
                            <div className="agent-title">
                                <p className="agent-name">{editedName}</p>
                                <p className="agent-type">{agent.description}</p>
                            </div>
                            <button
                                onClick={startEditingName}
                                className="edit-name-button"
                                type="button"
                            >
                                <Edit size={16} />
                            </button>
                        </div>
                    )}
                    {onClose ? <button
                        onClick={onClose}
                        className="close-button"
                        type="button"
                    >
                        <X size={18} />
                    </button> : null}
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

                <button type="button" onClick={toggleSidebar}>
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

            {/* Agent Description */}
            <p className="agent-description">
                {description || `This ${getAgentTypeDisplay(agentType)} agent processes and routes queries.`}
            </p>
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
                    agentType={agentType}
                    deploymentType={deploymentType}
                    setDeploymentType={setDeploymentType}
                    modelProvider={modelProvider}
                    setModelProvider={setModelProvider}
                    model={model}
                    setModel={setModel}
                    outputFormat={outputFormat}
                    setOutputFormat={setOutputFormat}
                    disabledFields={disabledFields}
                />
            )}

            {activeTab === "tools" && (
                <ToolsTab
                    selectedFunctions={selectedFunctions}
                    handleToolSelect={handleToolSelect}
                    disabledFields={disabledFields}
                    onEditPrompt={onEditPrompt}
                    agent={agent}
                />
            )}

            {/* Save Button */}
            {onSave ? <button
                onClick={handleSave}
                className="save-button"
                type="button"
            >
                <Save className="button-icon" />
                Save Configuration
            </button> : null}
        </div>
    );
};

export default ConfigPanel;
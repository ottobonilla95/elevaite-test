"use client";

import React, { useState, useEffect, useRef } from "react";
import {
    ChevronDown,
    ChevronUp,
    Edit,
    Save,
    X,
    Zap,
    Database,
    Link2,
    Check,
    Search,
    Code,
    FileText,
    Calculator,
    Mail
} from "lucide-react";
import { AgentType, AGENT_STYLES } from "./type";
import { useTools } from "../ui/contexts/ToolsContext";
import "./ConfigPanel.scss";

interface ConfigPanelProps {
    agentName: string;
    agentType: AgentType | "custom";
    description: string;
    onEditPrompt: () => void;
    onSave?: (configData: any) => void;
    onClose?: () => void;
    onNameChange?: (newName: string) => void;
    toggleSidebar?: () => void;
    sidebarOpen?: boolean;
}

const ConfigPanel: React.FC<ConfigPanelProps> = ({
    agentName,
    agentType,
    description,
    onEditPrompt,
    onSave,
    onClose,
    onNameChange,
    toggleSidebar,
    sidebarOpen,
}) => {
    // State for collapsible sections
    const [parametersOpen, setParametersOpen] = useState(true);
    const [toolsOpen, setToolsOpen] = useState(true);

    // State for editable fields
    const [deploymentType, setDeploymentType] = useState("Elevaite");
    const [modelProvider, setModelProvider] = useState("meta");
    const [model, setModel] = useState("Llama-3.1-8B-Instruct");
    const [outputFormat, setOutputFormat] = useState("JSON");

    // State for selected tools
    const [selectedTools, setSelectedTools] = useState<string[]>([]);

    // Use tools context
    const { tools: availableTools, isLoading: toolsLoading, error: toolsError } = useTools();

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

    // Deployment type options
    const deploymentTypes = [
        "Elevaite",
        "Enterprise",
        "Cloud"
    ];

    // Get model providers based on deployment type
    const getModelProviders = (deployType: string) => {
        switch (deployType) {
            case "Elevaite":
                return ["meta", "openbmb"];
            case "Enterprise":
                return ["OpenAI", "Gemini", "Bedrock", "Azure"];
            case "Cloud":
                return ["OpenAI", "Gemini", "Bedrock", "Azure"];
            default:
                return ["meta"];
        }
    };

    // Get models based on deployment type and model provider
    const getModels = (deployType: string, provider: string) => {
        if (deployType === "Elevaite") {
            switch (provider) {
                case "meta":
                    return ["Llama-3.1-8B-Instruct"];
                case "openbmb":
                    return ["MiniCPM-V-2_6"];
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

    // Current model providers based on selected deployment type
    const modelProviders = getModelProviders(deploymentType);

    // Current models based on selected deployment type and model provider
    const models = getModels(deploymentType, modelProvider);

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



    // Function to handle tool selection
    const handleToolSelect = (value: string) => {
        // Toggle selection
        if (selectedTools.includes(value)) {
            setSelectedTools(selectedTools.filter(tool => tool !== value));

        } else {
            setSelectedTools([...selectedTools, value]);
        }
    };

    // Get tool icon based on tool info - dynamic mapping based on tool functionality
    const getToolIcon = (toolName: string) => {
        const name = toolName.toLowerCase();

        // Map icons based on keywords in tool names
        if (name.includes('web') || name.includes('search')) {
            return <Search size={16} className="text-orange-500" />;
        } else if (name.includes('database') || name.includes('data')) {
            return <Database size={16} className="text-orange-500" />;
        } else if (name.includes('api') || name.includes('http') || name.includes('link')) {
            return <Link2 size={16} className="text-orange-500" />;
        } else if (name.includes('code') || name.includes('execution')) {
            return <Code size={16} className="text-orange-500" />;
        } else if (name.includes('file') || name.includes('document')) {
            return <FileText size={16} className="text-orange-500" />;
        } else if (name.includes('math') || name.includes('calculate')) {
            return <Calculator size={16} className="text-orange-500" />;
        } else if (name.includes('mail') || name.includes('email')) {
            return <Mail size={16} className="text-orange-500" />;
        } else {
            // Default icon for unknown tools
            return <Zap size={16} className="text-orange-500" />;
        }
    };

    // Handle name editing
    const startEditingName = () => {
        setIsEditingName(true);
    };

    const saveEditedName = () => {
        if (editedName.trim() === '') {
            setEditedName(agentName); // Restore original name if empty
        } else if (onNameChange && editedName !== agentName) {
            onNameChange(editedName);
        }
        setIsEditingName(false);
    };

    // Handle save button click
    const handleSave = () => {
        if (onSave) {
            onSave({
                agentName: editedName, // Include the potentially updated name
                deploymentType,
                modelProvider,
                model,
                outputFormat,
                selectedTools
            });
        }
    };

    // Get the agent type display name
    const getAgentTypeDisplay = (type: AgentType) => {
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
    const getStyleClass = (type: AgentType) => {
        const styles = AGENT_STYLES[type] || { bgClass: "bg-gray-100", textClass: "text-gray-600" };
        return `${styles.bgClass} ${styles.textClass}`;
    };

    // Handle keydown event for name input
    const handleNameKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
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
                                onChange={(e) => setEditedName(e.target.value)}
                                onBlur={saveEditedName}
                                onKeyDown={handleNameKeyDown}
                                className="agent-name-input"
                                placeholder="Enter agent name"
                            />
                            <button
                                onClick={saveEditedName}
                                className="save-name-button"
                            >
                                <Check size={16} />
                            </button>
                        </div>
                    ) : (
                        <div className="agent-name-display">
                            <h2 className="config-panel-title">{editedName}</h2>
                            <button
                                onClick={startEditingName}
                                className="edit-name-button"
                            >
                                <Edit size={16} />
                            </button>
                        </div>
                    )}
                    {onClose && (
                        <button
                            onClick={onClose}
                            className="close-button"
                        >
                            <X size={18} />
                        </button>
                    )}
                    <button className="activate-fields" type="button" onClick={() => setDisabledFields(!disabledFields)}>
                        <svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
                            <g opacity="0.8" clipPath="url(#clip0_255_10554)">
                                <path d="M14 14H8.66664M1.66663 14.3334L5.36614 12.9105C5.60277 12.8195 5.72108 12.774 5.83177 12.7146C5.93009 12.6618 6.02383 12.6009 6.11199 12.5324C6.21124 12.4554 6.30088 12.3658 6.48015 12.1865L14 4.66671C14.7364 3.93033 14.7364 2.73642 14 2.00004C13.2636 1.26366 12.0697 1.26366 11.3333 2.00004L3.81348 9.51985C3.63421 9.69912 3.54457 9.78876 3.46755 9.88801C3.39914 9.97617 3.33823 10.0699 3.28545 10.1682C3.22603 10.2789 3.18053 10.3972 3.08951 10.6339L1.66663 14.3334ZM1.66663 14.3334L3.03871 10.766C3.13689 10.5107 3.18598 10.3831 3.27019 10.3246C3.34377 10.2735 3.43483 10.2542 3.52282 10.271C3.62351 10.2902 3.72021 10.3869 3.91361 10.5803L5.41967 12.0864C5.61307 12.2798 5.70977 12.3765 5.729 12.4772C5.74581 12.5652 5.72648 12.6562 5.67539 12.7298C5.61692 12.814 5.48928 12.8631 5.23401 12.9613L1.66663 14.3334Z" stroke={`${!disabledFields ? "#FF681F" : "#212124"}`} strokeWidth="1.5" stroke-linecap="round" stroke-linejoin="round" />
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
                                <path d="M1 11L6 6L1 1M8 11L13 6L8 1" stroke="#212124" strokeWidth="1.5" stroke-linecap="round" stroke-linejoin="round" />
                            </svg>
                            :
                            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                                <g opacity="0.8">
                                    <path d="M18 17L13 12L18 7M11 17L6 12L11 7" stroke="#212124" strokeWidth="1.5" stroke-linecap="round" stroke-linejoin="round" />
                                </g>
                            </svg>
                    }
                </button>
            </div>

            {/* Agent Type Badge */}
            <div className="agent-type-container">
                <span className={`agent-type-badge ${getStyleClass(agentType)}`}>
                    {getAgentTypeDisplay(agentType)}
                </span>
                <span className="agent-flavor-badge">
                    Task-Based Agent
                </span>
            </div>

            {/* Agent Description */}
            <p className="agent-description">
                {description || `This ${getAgentTypeDisplay(agentType)} agent processes and routes queries.`}
            </p>

            {/* Parameters Section */}
            <div className="panel-section">
                <div
                    className="section-header"
                    onClick={() => setParametersOpen(!parametersOpen)}
                >
                    <h3 className="section-title">Parameters</h3>
                    {parametersOpen ? <ChevronUp size={18} /> : <ChevronDown size={18} />}
                </div>

                {parametersOpen && (
                    <div className="section-content">
                        <div className="parameters-grid">
                            <div className="parameter-item">
                                <label className="parameter-label">Deployment Type:</label>
                                <select
                                    value={deploymentType}
                                    onChange={(e) => setDeploymentType(e.target.value)}
                                    className="parameter-select"
                                    disabled={disabledFields}
                                >
                                    {deploymentTypes.map((type) => (
                                        <option key={type} value={type}>{type}</option>
                                    ))}
                                </select>
                            </div>
                            <div className="parameter-item">
                                <label className="parameter-label">Model Provider:</label>
                                <select
                                    value={modelProvider}
                                    onChange={(e) => setModelProvider(e.target.value)}
                                    className="parameter-select payment-select"
                                    disabled={disabledFields}
                                >
                                    {modelProviders.map((provider) => (
                                        <option key={provider} value={provider}>{provider}</option>
                                    ))}
                                </select>
                            </div>
                            <div className="parameter-item">
                                <label className="parameter-label">Model:</label>
                                <select
                                    value={model}
                                    onChange={(e) => setModel(e.target.value)}
                                    className="parameter-select"
                                    disabled={disabledFields}
                                >
                                    {models.map((model) => (
                                        <option key={model} value={model}>{model}</option>
                                    ))}
                                </select>
                            </div>
                            <div className="parameter-item">
                                <label className="parameter-label">Output Format:</label>
                                <select
                                    value={outputFormat}
                                    onChange={(e) => setOutputFormat(e.target.value)}
                                    className="parameter-select"
                                    disabled={disabledFields}
                                >
                                    <option value="JSON">JSON</option>
                                    <option value="Text">Text</option>
                                    <option value="CSV">CSV</option>
                                    <option value="HTML">HTML</option>
                                    <option value="Markdown">Markdown</option>
                                    <option value="YAML">YAML</option>
                                </select>
                            </div>
                        </div>

                        {/* Edit Prompt Button */}
                        <button
                            onClick={onEditPrompt}
                            className="edit-prompt-button"
                            disabled={disabledFields}
                        >
                            <Edit className="button-icon" />
                            Edit Prompt
                        </button>
                    </div>
                )}
            </div>

            {/* Tools Section */}
            <div className="panel-section">
                <div
                    className="section-header"
                    onClick={() => setToolsOpen(!toolsOpen)}
                >
                    <h3 className="section-title">Tools</h3>
                    {toolsOpen ? <ChevronUp size={18} /> : <ChevronDown size={18} />}
                </div>

                {toolsOpen && (
                    <div className="section-content">
                        <p className="tools-description">Select tools to add to your agent:</p>

                        {toolsLoading ? (
                            <div className="text-center py-2">
                                <div className="text-sm text-gray-500">Loading tools...</div>
                            </div>
                        ) : toolsError ? (
                            <div className="text-center py-2">
                                <div className="text-sm text-red-500">{toolsError}</div>
                            </div>
                        ) : (
                            <>
                                {/* Tool Selection Dropdown */}
                                <div className="tool-selector">
                                    <select
                                        className="tool-select"
                                        onChange={(e) => handleToolSelect(e.target.value)}
                                        value=""
                                        disabled={disabledFields}
                                    >
                                        <option value="" disabled>Select tools to add...</option>
                                        {availableTools.map(tool => (
                                            <option key={tool.name} value={tool.name}>{tool.name}</option>
                                        ))}
                                    </select>
                                </div>
                            </>
                        )}

                        {/* Selected Tools */}
                        {selectedTools.length > 0 && (
                            <div className="selected-tools-container">
                                <h4 className="selected-tools-title">Selected Tools:</h4>
                                <div className="selected-tools-list">
                                    {selectedTools.map(tool => (
                                        <div
                                            key={tool}
                                            className="tool-badge"
                                        >
                                            {getToolIcon(tool)}
                                            <span className="tool-name">{tool}</span>
                                            <button
                                                className="remove-tool-button"
                                                onClick={() => setSelectedTools(
                                                    selectedTools.filter(t => t !== tool)
                                                )}
                                            >
                                                ×
                                            </button>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}
                    </div>
                )}
            </div>

            {/* Save Button */}
            {onSave && (
                <button
                    onClick={handleSave}
                    className="save-button"
                >
                    <Save className="button-icon" />
                    Save Configuration
                </button>
            )}
        </div>
    );
};

export default ConfigPanel;
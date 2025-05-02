// ConfigPanel.tsx
"use client";

import React, { useState } from "react";
import {
    ChevronDown,
    ChevronUp,
    Edit,
    Save,
    X,
    Zap,
    Database,
    Link2
} from "lucide-react";
import { AgentType, AGENT_STYLES } from "./type";
import "./ConfigPanel.scss";

interface ConfigPanelProps {
    agentName: string;
    agentType: AgentType;
    description: string;
    onEditPrompt: () => void;
    onSave?: (configData: any) => void;
    onClose?: () => void;
}

const ConfigPanel: React.FC<ConfigPanelProps> = ({
    agentName,
    agentType,
    description,
    onEditPrompt,
    onSave,
    onClose
}) => {
    // State for collapsible sections
    const [parametersOpen, setParametersOpen] = useState(true);
    const [toolsOpen, setToolsOpen] = useState(true);

    // State for editable fields
    const [model, setModel] = useState("GPT-4");
    const [modelChargeType, setModelChargeType] = useState("Hosted");
    const [dataset, setDataset] = useState("Knowledge Base");
    const [outputFormat, setOutputFormat] = useState("JSON");

    // State for selected tools
    const [selectedTools, setSelectedTools] = useState<string[]>(["Document Parser"]);

    // Available tools options
    const availableTools = [
        "Document Parser",
        "Regex Extractor",
        "MCP Integration",
        "Workflow Orchestrator",
        "Real-time Analytics",
        "Data Transformer",
        "Semantic Search",
        "Conversational Agent"
    ];

    // Function to handle tool selection
    const handleToolSelect = (value: string) => {
        // Toggle selection
        if (selectedTools.includes(value)) {
            setSelectedTools(selectedTools.filter(tool => tool !== value));
        } else {
            setSelectedTools([...selectedTools, value]);
        }
    };

    // Get tool icon based on name
    const getToolIcon = (toolName: string) => {
        const toolIcons: { [key: string]: React.ReactNode } = {
            "Document Parser": <Database size={16} className="text-orange-500" />,
            "Regex Extractor": <Zap size={16} className="text-orange-500" />,
            "MCP Integration": <Link2 size={16} className="text-orange-500" />,
            "Workflow Orchestrator": <Zap size={16} className="text-orange-500" />,
            "Real-time Analytics": <Database size={16} className="text-orange-500" />,
            "Data Transformer": <Link2 size={16} className="text-orange-500" />,
            "Semantic Search": <Zap size={16} className="text-orange-500" />,
            "Conversational Agent": <Database size={16} className="text-orange-500" />
        };

        return toolIcons[toolName] || <Zap size={16} className="text-orange-500" />;
    };

    // Handle save button click
    const handleSave = () => {
        if (onSave) {
            onSave({
                model,
                modelChargeType,
                dataset,
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
            case "api": return "API";
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

    return (
        <div className="config-panel">
            {/* Header with close button */}
            <div className="config-panel-header">
                <h2 className="config-panel-title">{agentName}</h2>
                {onClose && (
                    <button
                        onClick={onClose}
                        className="close-button"
                    >
                        <X size={18} />
                    </button>
                )}
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
                                <label className="parameter-label">Model:</label>
                                <select
                                    value={model}
                                    onChange={(e) => setModel(e.target.value)}
                                    className="parameter-select"
                                >
                                    <option value="GPT-4">GPT-4</option>
                                    <option value="GPT-3.5">GPT-3.5</option>
                                    <option value="Claude 3">Claude 3</option>
                                    <option value="Claude 3.5">Claude 3.5</option>
                                    <option value="Gemini Pro">Gemini Pro</option>
                                    <option value="Mixtral">Mixtral</option>
                                    <option value="Llama 3">Llama 3</option>
                                </select>
                            </div>
                            <div className="parameter-item">
                                <label className="parameter-label">Charge Type:</label>
                                <select
                                    value={modelChargeType}
                                    onChange={(e) => setModelChargeType(e.target.value)}
                                    className="parameter-select payment-select"
                                >
                                    <option value="Hosted">Hosted</option>
                                    <option value="Pay As You Go">Pay As You Go</option>
                                    <option value="Free Tier">Free Tier</option>
                                    <option value="Enterprise">Enterprise</option>
                                </select>
                            </div>
                            <div className="parameter-item">
                                <label className="parameter-label">Dataset:</label>
                                <select
                                    value={dataset}
                                    onChange={(e) => setDataset(e.target.value)}
                                    className="parameter-select"
                                >
                                    <option value="Knowledge Base">Knowledge Base</option>
                                    <option value="Company Docs">Company Docs</option>
                                    <option value="Support FAQ">Support FAQ</option>
                                    <option value="MCP">Multi-Cloud Platform</option>
                                    <option value="API Documentation">API Documentation</option>
                                    <option value="None">None</option>
                                </select>
                            </div>
                            <div className="parameter-item">
                                <label className="parameter-label">Output Format:</label>
                                <select
                                    value={outputFormat}
                                    onChange={(e) => setOutputFormat(e.target.value)}
                                    className="parameter-select"
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

                        {/* Tool Selection Dropdown */}
                        <div className="tool-selector">
                            <select
                                className="tool-select"
                                onChange={(e) => handleToolSelect(e.target.value)}
                                value=""
                            >
                                <option value="" disabled>Select tools to add...</option>
                                {availableTools.map(tool => (
                                    <option key={tool} value={tool}>{tool}</option>
                                ))}
                            </select>
                        </div>

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
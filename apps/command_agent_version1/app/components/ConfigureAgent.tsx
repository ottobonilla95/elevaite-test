// ConfigureAgent.tsx - With selectable tools
"use client";

import React, { useState } from "react";
import {
    ChevronDown,
    ChevronUp,
    FileText,
    Code,
    ListFilter,
    Edit,
    Save,
    X,
    MessageSquare,
    Database,
    GitBranch,
    Zap,
    ArrowUpDown,
    Search
} from "lucide-react";
import { AgentType, AGENT_STYLES } from "./type";
import { type CommonSelectOption } from "@repo/ui/components";

interface ConfigureAgentProps {
    agentName: string;
    agentType: AgentType;
    description: string;
    onEditPrompt: () => void;
    onSave?: (configData: any) => void;
    onClose?: () => void;
}

const ConfigureAgent: React.FC<ConfigureAgentProps> = ({
    agentName,
    agentType,
    description,
    onEditPrompt,
    onSave,
    onClose
}) => {
    const [parametersOpen, setParametersOpen] = useState(true);
    const [toolsOpen, setToolsOpen] = useState(true);

    // State for editable fields
    const [model, setModel] = useState("GPT-4");
    const [modelChargeType, setModelChargeType] = useState("Hosted");
    const [dataset, setDataset] = useState("Arlo Knowledge Base");
    const [outputFormat, setOutputFormat] = useState("JSON");

    // State for selected tools
    const [selectedTools, setSelectedTools] = useState<string[]>(["Document Parser"]);

    // Tool options for the select box
    const toolOptions: CommonSelectOption[] = [
        { value: "Document Parser", label: "Document Parser" },
        { value: "Regex Extractor", label: "Regex Extractor" },
        { value: "MCP Integration", label: "MCP Integration" },
        { value: "Workflow Orchestrator", label: "Workflow Orchestrator" },
        { value: "Real-time Analytics", label: "Real-time Analytics" },
        { value: "Data Transformer", label: "Data Transformer" },
        { value: "Semantic Search", label: "Semantic Search" },
        { value: "Conversational Agent", label: "Conversational Agent" },
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

    // Function to handle tool drag start
    const handleToolDragStart = (event: React.DragEvent<HTMLDivElement>, toolName: string, toolIcon: React.ReactNode) => {
        // Create tool data for dragging
        const toolData = {
            id: `tool-${Date.now()}`,
            type: "data", // Default type for tools
            name: toolName,
            isTool: true
        };

        // Set data transfer
        event.dataTransfer.setData("application/reactflow-tool", JSON.stringify(toolData));
        event.dataTransfer.effectAllowed = "move";

        // Add visual feedback for dragging
        const target = event.currentTarget;
        setTimeout(() => {
            target.style.opacity = "0.5";
            target.style.transform = "scale(0.95)";
        }, 0);

        // Reset visual style after drag ends
        const resetStyle = () => {
            target.style.opacity = "1";
            target.style.transform = "scale(1)";
            document.removeEventListener("dragend", resetStyle);
        };

        document.addEventListener("dragend", resetStyle);
    };

    // Get the style class for the agent type
    const getStyleClass = (type: AgentType) => {
        const styles = AGENT_STYLES[type] || { bgClass: "bg-gray-100", textClass: "text-gray-600" };
        return `${styles.bgClass} ${styles.textClass}`;
    };

    // Get the agent type display name
    const getAgentTypeDisplay = (type: AgentType) => {
        switch (type) {
            case "router": return "Router";
            case "web_search": return "Web Search";
            case "api": return "API Agent";
            case "data": return "Data Extractor";
            case "troubleshooting": return "Troubleshooting";
            default: return type;
        }
    };

    // Handle save button click
    const handleSave = () => {
        if (onSave) {
            onSave({
                model,
                modelChargeType,
                dataset,
                outputFormat
            });
        }
    };

    // Handle close button click
    const handleClose = () => {
        if (onClose) {
            onClose();
        }
    };

    return (
        <div className="configure-agent p-4">
            {/* Header with close button */}
            <div className="flex items-center justify-between mb-3">
                <h2 className="text-lg font-medium">{agentName}</h2>
                {onClose && (
                    <button
                        onClick={handleClose}
                        className="p-1 text-gray-400 hover:text-gray-600 rounded"
                    >
                        <X size={18} />
                    </button>
                )}
            </div>

            {/* Agent Type Badge */}
            <div className="flex items-center mb-3">
                <span className={`px-2 py-0.5 text-xs font-medium rounded-full ${getStyleClass(agentType)}`}>
                    {getAgentTypeDisplay(agentType)}
                </span>
                <span className="bg-blue-50 text-blue-700 text-xs font-medium px-2.5 py-1 rounded-full ml-2">
                    Task-Based Agent
                </span>
            </div>

            {/* Agent Description */}
            <p className="text-sm text-gray-700 mb-4">
                {description || `Routes queries to appropriate agents`}
            </p>

            {/* Parameters Section */}
            <div className="border border-gray-200 rounded-lg mb-4 overflow-hidden">
                <div
                    className="flex items-center justify-between p-3 bg-gray-50 cursor-pointer"
                    onClick={() => setParametersOpen(!parametersOpen)}
                >
                    <h3 className="font-medium">Parameters</h3>
                    {parametersOpen ? <ChevronUp size={18} /> : <ChevronDown size={18} />}
                </div>

                {parametersOpen && (
                    <div className="p-3 bg-white">
                        <div className="grid grid-cols-2 gap-4">
                            <div>
                                <label className="block text-xs text-gray-500 mb-1">Model:</label>
                                <select
                                    value={model}
                                    onChange={(e) => setModel(e.target.value)}
                                    className="w-full border border-gray-200 rounded-md px-3 py-1.5 text-sm"
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
                            <div>
                                <label className="block text-xs text-gray-500 mb-1">Model Charge Type:</label>
                                <select
                                    value={modelChargeType}
                                    onChange={(e) => setModelChargeType(e.target.value)}
                                    className="w-full bg-green-50 text-green-700 border border-green-200 rounded-md px-3 py-1.5 text-sm"
                                >
                                    <option value="Hosted">Hosted</option>
                                    <option value="Pay As You Go">Pay As You Go</option>
                                    <option value="Free Tier">Free Tier</option>
                                    <option value="Enterprise">Enterprise</option>
                                </select>
                            </div>
                            <div>
                                <label className="block text-xs text-gray-500 mb-1">Dataset:</label>
                                <select
                                    value={dataset}
                                    onChange={(e) => setDataset(e.target.value)}
                                    className="w-full border border-gray-200 rounded-md px-3 py-1.5 text-sm"
                                >
                                    <option value="Arlo Knowledge Base">Arlo Knowledge Base</option>
                                    <option value="Company Docs">Company Docs</option>
                                    <option value="Support FAQ">Support FAQ</option>
                                    <option value="MCP">Multi-Cloud Platform</option>
                                    <option value="API Documentation">API Documentation</option>
                                    <option value="None">None</option>
                                </select>
                            </div>
                            <div>
                                <label className="block text-xs text-gray-500 mb-1">Output Format:</label>
                                <select
                                    value={outputFormat}
                                    onChange={(e) => setOutputFormat(e.target.value)}
                                    className="w-full border border-gray-200 rounded-md px-3 py-1.5 text-sm"
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
                            className="mt-4 w-full flex items-center justify-center bg-blue-50 hover:bg-blue-100 text-blue-600 px-4 py-2 rounded-md text-sm font-medium transition-colors"
                        >
                            <Edit className="w-4 h-4 mr-2" />
                            Edit Prompt
                        </button>
                    </div>
                )}
            </div>

            {/* Tools Section */}
            <div className="border border-gray-200 rounded-lg mb-4">
                <div
                    className="flex items-center justify-between p-3 bg-gray-50 cursor-pointer"
                    onClick={() => setToolsOpen(!toolsOpen)}
                >
                    <h3 className="font-medium">Tools</h3>
                    {toolsOpen ? <ChevronUp size={18} /> : <ChevronDown size={18} />}
                </div>

                {toolsOpen && (
                    <div className="p-3 bg-white">
                        <p className="text-xs text-gray-500 mb-3">Select a tool and drag it to the canvas to add it to your workflow:</p>

                        {/* Tool Selection Dropdown */}
                        <div className="mb-4">
                            <select
                                className="w-full border border-gray-200 rounded-md px-3 py-2 text-sm"
                                onChange={(e) => handleToolSelect(e.target.value)}
                                value=""
                            >
                                <option value="" disabled>Select tools to add...</option>
                                {toolOptions.map(option => (
                                    <option key={option.value} value={option.value}>{option.label}</option>
                                ))}
                            </select>
                        </div>

                        {/* Selected Tools */}
                        {selectedTools.length > 0 && (
                            <div className="mb-4 p-3 border border-gray-200 rounded-md">
                                <h4 className="text-sm font-medium mb-2">Selected Tools (drag to canvas):</h4>
                                <div className="flex flex-wrap gap-2">
                                    {selectedTools.map(tool => (
                                        <div
                                            key={tool}
                                            className="px-2 py-1 bg-blue-100 text-blue-700 text-xs rounded-md flex items-center cursor-move"
                                            draggable
                                            onDragStart={(e) => handleToolDragStart(e, tool, null)}
                                        >
                                            <span>{tool}</span>
                                            <button
                                                className="ml-1 text-blue-500 hover:text-blue-700"
                                                onClick={(e) => {
                                                    e.stopPropagation();
                                                    setSelectedTools(selectedTools.filter(t => t !== tool));
                                                }}
                                            >
                                                ×
                                            </button>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}

                        <div className="space-y-3">
                            {/* Document Parser Tool */}
                            <div
                                className={`flex items-center p-2 bg-orange-50 rounded-md cursor-move transition duration-200 hover:shadow-md ${selectedTools.includes("Document Parser") ? "ring-2 ring-blue-500" : ""}`}
                                draggable
                                onDragStart={(e) => handleToolDragStart(e, "Document Parser", <FileText />)}
                                onClick={() => handleToolSelect("Document Parser")}
                            >
                                <div className="w-8 h-8 rounded-full bg-orange-100 flex items-center justify-center mr-3">
                                    <FileText className="w-4 h-4 text-orange-500" />
                                </div>
                                <div>
                                    <h4 className="font-medium text-sm text-orange-700">Document Parser</h4>
                                    <p className="text-xs text-orange-600">Parses PDF and scanned documents</p>
                                </div>
                            </div>

                            {/* Regex Extractor Tool */}
                            <div
                                className={`flex items-center p-2 bg-amber-50 rounded-md cursor-move transition duration-200 hover:shadow-md ${selectedTools.includes("Regex Extractor") ? "ring-2 ring-blue-500" : ""}`}
                                draggable
                                onDragStart={(e) => handleToolDragStart(e, "Regex Extractor", <Code />)}
                                onClick={() => handleToolSelect("Regex Extractor")}
                            >
                                <div className="w-8 h-8 rounded-full bg-amber-100 flex items-center justify-center mr-3">
                                    <Code className="w-4 h-4 text-amber-500" />
                                </div>
                                <div>
                                    <h4 className="font-medium text-sm text-amber-700">Regex Extractor</h4>
                                    <p className="text-xs text-amber-600">Used to find structured values like invoice #</p>
                                </div>
                            </div>

                            {/* MCP Integration Tool */}
                            <div
                                className={`flex items-center p-2 bg-blue-50 rounded-md cursor-move transition duration-200 hover:shadow-md ${selectedTools.includes("MCP Integration") ? "ring-2 ring-blue-500" : ""}`}
                                draggable
                                onDragStart={(e) => handleToolDragStart(e, "MCP Integration", <Database />)}
                                onClick={() => handleToolSelect("MCP Integration")}
                            >
                                <div className="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center mr-3">
                                    <Database className="w-4 h-4 text-blue-500" />
                                </div>
                                <div>
                                    <h4 className="font-medium text-sm text-blue-700">MCP Integration</h4>
                                    <p className="text-xs text-blue-600">Connects to Multi-Cloud Platform services</p>
                                </div>
                            </div>

                            {/* Workflow Orchestrator */}
                            <div
                                className={`flex items-center p-2 bg-green-50 rounded-md cursor-move transition duration-200 hover:shadow-md ${selectedTools.includes("Workflow Orchestrator") ? "ring-2 ring-blue-500" : ""}`}
                                draggable
                                onDragStart={(e) => handleToolDragStart(e, "Workflow Orchestrator", <GitBranch />)}
                                onClick={() => handleToolSelect("Workflow Orchestrator")}
                            >
                                <div className="w-8 h-8 rounded-full bg-green-100 flex items-center justify-center mr-3">
                                    <GitBranch className="w-4 h-4 text-green-500" />
                                </div>
                                <div>
                                    <h4 className="font-medium text-sm text-green-700">Workflow Orchestrator</h4>
                                    <p className="text-xs text-green-600">Manages complex multi-step processes</p>
                                </div>
                            </div>

                            {/* Real-time Analytics */}
                            <div
                                className={`flex items-center p-2 bg-pink-50 rounded-md cursor-move transition duration-200 hover:shadow-md ${selectedTools.includes("Real-time Analytics") ? "ring-2 ring-blue-500" : ""}`}
                                draggable
                                onDragStart={(e) => handleToolDragStart(e, "Real-time Analytics", <Zap />)}
                                onClick={() => handleToolSelect("Real-time Analytics")}
                            >
                                <div className="w-8 h-8 rounded-full bg-pink-100 flex items-center justify-center mr-3">
                                    <Zap className="w-4 h-4 text-pink-500" />
                                </div>
                                <div>
                                    <h4 className="font-medium text-sm text-pink-700">Real-time Analytics</h4>
                                    <p className="text-xs text-pink-600">Processes streaming data for insights</p>
                                </div>
                            </div>

                            {/* Data Transformer */}
                            <div
                                className={`flex items-center p-2 bg-indigo-50 rounded-md cursor-move transition duration-200 hover:shadow-md ${selectedTools.includes("Data Transformer") ? "ring-2 ring-blue-500" : ""}`}
                                draggable
                                onDragStart={(e) => handleToolDragStart(e, "Data Transformer", <ArrowUpDown />)}
                                onClick={() => handleToolSelect("Data Transformer")}
                            >
                                <div className="w-8 h-8 rounded-full bg-indigo-100 flex items-center justify-center mr-3">
                                    <ArrowUpDown className="w-4 h-4 text-indigo-500" />
                                </div>
                                <div>
                                    <h4 className="font-medium text-sm text-indigo-700">Data Transformer</h4>
                                    <p className="text-xs text-indigo-600">Converts between data formats</p>
                                </div>
                            </div>

                            {/* Semantic Search */}
                            <div
                                className={`flex items-center p-2 bg-teal-50 rounded-md cursor-move transition duration-200 hover:shadow-md ${selectedTools.includes("Semantic Search") ? "ring-2 ring-blue-500" : ""}`}
                                draggable
                                onDragStart={(e) => handleToolDragStart(e, "Semantic Search", <Search />)}
                                onClick={() => handleToolSelect("Semantic Search")}
                            >
                                <div className="w-8 h-8 rounded-full bg-teal-100 flex items-center justify-center mr-3">
                                    <Search className="w-4 h-4 text-teal-500" />
                                </div>
                                <div>
                                    <h4 className="font-medium text-sm text-teal-700">Semantic Search</h4>
                                    <p className="text-xs text-teal-600">Finds relevant information in knowledge bases</p>
                                </div>
                            </div>

                            {/* Conversational Agent */}
                            <div
                                className={`flex items-center p-2 bg-gray-50 rounded-md cursor-move transition duration-200 hover:shadow-md ${selectedTools.includes("Conversational Agent") ? "ring-2 ring-blue-500" : ""}`}
                                draggable
                                onDragStart={(e) => handleToolDragStart(e, "Conversational Agent", <MessageSquare />)}
                                onClick={() => handleToolSelect("Conversational Agent")}
                            >
                                <div className="w-8 h-8 rounded-full bg-gray-100 flex items-center justify-center mr-3">
                                    <MessageSquare className="w-4 h-4 text-gray-500" />
                                </div>
                                <div>
                                    <h4 className="font-medium text-sm text-gray-700">Conversational Agent</h4>
                                    <p className="text-xs text-gray-600">Handles natural language interactions</p>
                                </div>
                            </div>
                        </div>
                    </div>
                )}
            </div>

            {/* Save Button */}
            {onSave && (
                <button
                    onClick={handleSave}
                    className="w-full flex items-center justify-center bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-md text-sm font-medium"
                >
                    <Save className="w-4 h-4 mr-2" />
                    Save Configuration
                </button>
            )}
        </div>
    );
};

export default ConfigureAgent;
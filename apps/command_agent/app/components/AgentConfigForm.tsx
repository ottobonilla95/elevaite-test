"use client";

import React, { useState } from "react";
import {
    Code,
    Globe,
    MessageSquare,
    Search,
    Zap,
    BrainCircuit,
    MemoryStick,
    LayoutGrid,
    Thermometer,
    Settings,
    Database
} from "lucide-react";

const AgentConfigForm = () => {
    // State for agent name and type
    const [agentName, setAgentName] = useState("");
    const [agentType, setAgentType] = useState("transaction");
    const [businessDomain, setBusinessDomain] = useState("customer-service");

    // State for tool selection
    const [tools, setTools] = useState({
        api: false,
        web: false,
        rag: false,
    });

    // State for memory options
    const [memory, setMemory] = useState({
        shortTerm: true,
        longTerm: false,
    });

    // State for routing configuration
    const [routing, setRouting] = useState("simple");

    // State for temperature
    const [temperature, setTemperature] = useState(0.7);

    // State for prompt
    const [prompt, setPrompt] = useState("");

    // State for model selection
    const [model, setModel] = useState("gpt-4");

    const handleToolChange = (name: "api" | "web" | "rag") => {
        setTools(prev => ({ ...prev, [name]: !prev[name] }));
    };

    const handleMemoryChange = (name: "shortTerm" | "longTerm") => {
        setMemory(prev => ({ ...prev, [name]: !prev[name] }));
    };

    const handleTemperatureChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        setTemperature(parseFloat(e.target.value));
    };

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();

        // Prepare the configuration data
        const config = {
            agentName,
            agentType,
            businessDomain,
            tools,
            memory,
            routing,
            temperature,
            prompt,
            model,
        };

        console.log("Agent Configuration:", config);

        // Simple alert instead of toast
        alert("Configuration Saved: Your AI agent has been configured successfully.");
    };

    return (
        <form onSubmit={handleSubmit} className="w-full max-w-4xl mx-auto">
            {/* Agent Basic Info Card */}
            <div className="relative overflow-hidden bg-white dark:bg-gray-800 rounded-xl shadow-lg border border-gray-200 dark:border-gray-700 mb-6">
                <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-orange-500 to-orange-600"></div>
                <div className="p-6">
                    <div className="flex items-center gap-2 mb-2">
                        <div className="p-2 rounded-md bg-orange-500/10">
                            <Settings className="h-6 w-6 text-orange-500" />
                        </div>
                        <h2 className="text-xl font-semibold">Agent Details</h2>
                    </div>
                    <p className="text-sm text-gray-500 dark:text-gray-400 mb-4">
                        Define the core properties of your agent
                    </p>

                    <div className="space-y-4">
                        {/* Agent Name */}
                        <div>
                            <label htmlFor="agentName" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                                Agent Name
                            </label>
                            <input
                                type="text"
                                id="agentName"
                                value={agentName}
                                onChange={(e) => setAgentName(e.target.value)}
                                placeholder="Enter agent name"
                                className="w-full p-2 rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                            />
                        </div>

                        {/* Agent Type */}
                        <div>
                            <label htmlFor="agentType" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                                Agent Type
                            </label>
                            <select
                                id="agentType"
                                value={agentType}
                                onChange={(e) => setAgentType(e.target.value)}
                                className="w-full p-2 rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                            >
                                <option value="transaction">Transaction Command Agent</option>
                                <option value="analysis">Analysis Command Agent</option>
                                <option value="assistant">General Assistant</option>
                                <option value="specialist">Domain Specialist</option>
                            </select>
                        </div>

                        {/* Business Domain */}
                        <div>
                            <label htmlFor="businessDomain" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                                Business Domain
                            </label>
                            <select
                                id="businessDomain"
                                value={businessDomain}
                                onChange={(e) => setBusinessDomain(e.target.value)}
                                className="w-full p-2 rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                            >
                                <option value="customer-service">Customer Service</option>
                                <option value="sales">Sales</option>
                                <option value="marketing">Marketing</option>
                                <option value="hr">Human Resources</option>
                                <option value="finance">Finance</option>
                                <option value="it">IT Operations</option>
                            </select>
                        </div>
                    </div>
                </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
                {/* Model Selection Card */}
                <div className="relative overflow-hidden bg-white dark:bg-gray-800 rounded-xl shadow-lg border border-gray-200 dark:border-gray-700">
                    <div className="absolute top-0 right-0 w-32 h-32 bg-gradient-to-br from-orange-500/20 to-orange-600/20 rounded-bl-full z-0"></div>
                    <div className="relative z-10 p-6">
                        <div className="flex items-center gap-2 mb-2">
                            <div className="p-2 rounded-md bg-orange-500/10">
                                <BrainCircuit className="h-6 w-6 text-orange-500" />
                            </div>
                            <h2 className="text-xl font-semibold">Model Selection</h2>
                        </div>
                        <p className="text-sm text-gray-500 dark:text-gray-400 mb-4">
                            Choose the foundation model for your agent
                        </p>
                        <select
                            value={model}
                            onChange={(e) => setModel(e.target.value)}
                            className="w-full p-2 rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                        >
                            <option value="gpt-4">GPT-4 Turbo</option>
                            <option value="claude-3">Claude 3 Sonnet</option>
                            <option value="claude-3-haiku">Claude 3 Haiku</option>
                            <option value="llama-3">Llama 3</option>
                            <option value="gemini-1.5">Gemini 1.5 Pro</option>
                        </select>
                    </div>
                </div>

                {/* Temperature Card */}
                <div className="relative overflow-hidden bg-white dark:bg-gray-800 rounded-xl shadow-lg border border-gray-200 dark:border-gray-700">
                    <div className="absolute top-0 right-0 w-32 h-32 bg-gradient-to-br from-orange-500/20 to-orange-600/20 rounded-bl-full z-0"></div>
                    <div className="relative z-10 p-6">
                        <div className="flex items-center gap-2 mb-2">
                            <div className="p-2 rounded-md bg-orange-500/10">
                                <Thermometer className="h-6 w-6 text-orange-500" />
                            </div>
                            <h2 className="text-xl font-semibold">Temperature</h2>
                        </div>
                        <p className="text-sm text-gray-500 dark:text-gray-400 mb-4">
                            Adjust creativity vs precision balance
                        </p>
                        <div className="space-y-4">
                            <div className="flex items-center justify-between">
                                <span className="text-sm font-medium">Value: </span>
                                <span className="text-sm font-mono bg-orange-500/10 text-orange-700 dark:text-orange-400 px-2 py-1 rounded">
                                    {temperature.toFixed(2)}
                                </span>
                            </div>
                            <input
                                type="range"
                                min="0"
                                max="1"
                                step="0.01"
                                value={temperature}
                                onChange={handleTemperatureChange}
                                className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer dark:bg-gray-700"
                            />
                            <div className="flex justify-between text-sm text-gray-500 dark:text-gray-400">
                                <div className="flex items-center gap-1">
                                    <div className="h-2 w-2 rounded-full bg-green-500"></div>
                                    <span>Precise</span>
                                </div>
                                <div className="flex items-center gap-1">
                                    <span>Creative</span>
                                    <div className="h-2 w-2 rounded-full bg-orange-500"></div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            {/* Agent Prompt Card */}
            <div className="relative overflow-hidden bg-white dark:bg-gray-800 rounded-xl shadow-lg border border-gray-200 dark:border-gray-700 mb-6">
                <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-orange-500 to-orange-600"></div>
                <div className="p-6">
                    <div className="flex items-center gap-2 mb-2">
                        <div className="p-2 rounded-md bg-orange-500/10">
                            <MessageSquare className="h-6 w-6 text-orange-500" />
                        </div>
                        <h2 className="text-xl font-semibold">Agent Prompt</h2>
                    </div>
                    <p className="text-sm text-gray-500 dark:text-gray-400 mb-4">
                        Define the behavior and capabilities of your AI agent
                    </p>
                    <textarea
                        placeholder="Enter detailed instructions for your AI agent..."
                        value={prompt}
                        onChange={(e) => setPrompt(e.target.value)}
                        className="w-full min-h-[120px] p-3 border border-gray-300 dark:border-gray-600 rounded-md resize-y bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                    />
                </div>
            </div>

            {/* Tool Selection Card */}
            <div className="relative overflow-hidden bg-white dark:bg-gray-800 rounded-xl shadow-lg border border-gray-200 dark:border-gray-700 mb-6">
                <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-orange-500 to-orange-600"></div>
                <div className="p-6">
                    <div className="flex items-center gap-2 mb-2">
                        <div className="p-2 rounded-md bg-orange-500/10">
                            <LayoutGrid className="h-6 w-6 text-orange-500" />
                        </div>
                        <h2 className="text-xl font-semibold">Tool Selection</h2>
                    </div>
                    <p className="text-sm text-gray-500 dark:text-gray-400 mb-4">
                        Enable capabilities that your agent can leverage
                    </p>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        {/* API Access Card */}
                        <div
                            className={`p-4 rounded-lg cursor-pointer transition-all ${tools.api ? 'bg-orange-500/10 border-2 border-orange-500/50' : 'bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 hover:shadow-md'}`}
                            onClick={() => handleToolChange("api")}
                        >
                            <div className="flex items-center gap-4">
                                <input
                                    type="checkbox"
                                    id="api"
                                    checked={tools.api}
                                    onChange={() => handleToolChange("api")}
                                    className="h-4 w-4 text-orange-500 rounded focus:ring-orange-500 border-gray-300"
                                />
                                <div className="flex flex-col">
                                    <div className="flex items-center gap-2">
                                        <Code className="h-4 w-4 text-orange-600" />
                                        <label htmlFor="api" className="font-medium cursor-pointer">API Access</label>
                                    </div>
                                    <p className="text-xs text-gray-500 dark:text-gray-400 pt-1">Connect to enterprise systems</p>
                                </div>
                            </div>
                        </div>

                        {/* Web Browsing Card */}
                        <div
                            className={`p-4 rounded-lg cursor-pointer transition-all ${tools.web ? 'bg-orange-500/10 border-2 border-orange-500/50' : 'bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 hover:shadow-md'}`}
                            onClick={() => handleToolChange("web")}
                        >
                            <div className="flex items-center gap-4">
                                <input
                                    type="checkbox"
                                    id="web"
                                    checked={tools.web}
                                    onChange={() => handleToolChange("web")}
                                    className="h-4 w-4 text-orange-500 rounded focus:ring-orange-500 border-gray-300"
                                />
                                <div className="flex flex-col">
                                    <div className="flex items-center gap-2">
                                        <Globe className="h-4 w-4 text-orange-600" />
                                        <label htmlFor="web" className="font-medium cursor-pointer">Web Browsing</label>
                                    </div>
                                    <p className="text-xs text-gray-500 dark:text-gray-400 pt-1">Search and retrieve online information</p>
                                </div>
                            </div>
                        </div>

                        {/* RAG System Card */}
                        <div
                            className={`p-4 rounded-lg cursor-pointer transition-all ${tools.rag ? 'bg-orange-500/10 border-2 border-orange-500/50' : 'bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 hover:shadow-md'}`}
                            onClick={() => handleToolChange("rag")}
                        >
                            <div className="flex items-center gap-4">
                                <input
                                    type="checkbox"
                                    id="rag"
                                    checked={tools.rag}
                                    onChange={() => handleToolChange("rag")}
                                    className="h-4 w-4 text-orange-500 rounded focus:ring-orange-500 border-gray-300"
                                />
                                <div className="flex flex-col">
                                    <div className="flex items-center gap-2">
                                        <Database className="h-4 w-4 text-orange-600" />
                                        <label htmlFor="rag" className="font-medium cursor-pointer">RAG System</label>
                                    </div>
                                    <p className="text-xs text-gray-500 dark:text-gray-400 pt-1">Access proprietary knowledge base</p>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
                {/* Memory Options Card */}
                <div className="relative overflow-hidden bg-white dark:bg-gray-800 rounded-xl shadow-lg border border-gray-200 dark:border-gray-700">
                    <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-orange-500 to-orange-600"></div>
                    <div className="p-6">
                        <div className="flex items-center gap-2 mb-2">
                            <div className="p-2 rounded-md bg-orange-500/10">
                                <MemoryStick className="h-6 w-6 text-orange-500" />
                            </div>
                            <h2 className="text-xl font-semibold">Memory Options</h2>
                        </div>
                        <p className="text-sm text-gray-500 dark:text-gray-400 mb-4">
                            Configure how your agent remembers context
                        </p>
                        <div className="space-y-4">
                            <div className="flex items-center justify-between p-4 rounded-lg bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600">
                                <div className="flex flex-col gap-1">
                                    <label htmlFor="shortTerm" className="font-medium">Short-term Memory</label>
                                    <p className="text-xs text-gray-500 dark:text-gray-400">Retain context within conversations</p>
                                </div>
                                <div className="relative inline-flex items-center cursor-pointer">
                                    <input
                                        id="shortTerm"
                                        type="checkbox"
                                        className="sr-only peer"
                                        checked={memory.shortTerm}
                                        onChange={() => handleMemoryChange('shortTerm')}
                                    />
                                    <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-orange-300 dark:peer-focus:ring-orange-800 rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full rtl:peer-checked:after:-translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:start-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-orange-500"></div>
                                </div>
                            </div>

                            <div className="flex items-center justify-between p-4 rounded-lg bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600">
                                <div className="flex flex-col gap-1">
                                    <label htmlFor="longTerm" className="font-medium">Long-term Memory</label>
                                    <p className="text-xs text-gray-500 dark:text-gray-400">Remember context across sessions</p>
                                </div>
                                <div className="relative inline-flex items-center cursor-pointer">
                                    <input
                                        id="longTerm"
                                        type="checkbox"
                                        className="sr-only peer"
                                        checked={memory.longTerm}
                                        onChange={() => handleMemoryChange('longTerm')}
                                    />
                                    <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-orange-300 dark:peer-focus:ring-orange-800 rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full rtl:peer-checked:after:-translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:start-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-orange-500"></div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Routing Configuration Card */}
                <div className="relative overflow-hidden bg-white dark:bg-gray-800 rounded-xl shadow-lg border border-gray-200 dark:border-gray-700">
                    <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-orange-500 to-orange-600"></div>
                    <div className="p-6">
                        <div className="flex items-center gap-2 mb-2">
                            <div className="p-2 rounded-md bg-orange-500/10">
                                <LayoutGrid className="h-6 w-6 text-orange-500" />
                            </div>
                            <h2 className="text-xl font-semibold">Routing Configuration</h2>
                        </div>
                        <p className="text-sm text-gray-500 dark:text-gray-400 mb-4">
                            Define how your agent handles complex queries
                        </p>
                        <select
                            value={routing}
                            onChange={(e) => setRouting(e.target.value)}
                            className="w-full p-2 rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                        >
                            <option value="simple">Simple Routing</option>
                            <option value="agent-router">Agent Router</option>
                            <option value="multi-agent">Multi-Agent Routing</option>
                        </select>
                        <div className="mt-3 text-xs text-gray-500 dark:text-gray-400">
                            {routing === "simple" && "Routes all queries through a single decision path."}
                            {routing === "agent-router" && "Uses a dedicated router agent to direct queries to specialized agents."}
                            {routing === "multi-agent" && "Employs multiple agents working collaboratively to solve complex tasks."}
                        </div>
                    </div>
                </div>
            </div>

            {/* Submit Button Card */}
            <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg border border-gray-200 dark:border-gray-700 mb-6 overflow-hidden">
                <div className="p-6 flex justify-center">
                    <button
                        type="submit"
                        className="inline-flex items-center justify-center px-8 py-3 rounded-md text-white font-medium bg-gradient-to-r from-orange-500 to-orange-600 hover:from-orange-600 hover:to-orange-700 transition-colors focus:outline-none focus:ring-2 focus:ring-orange-500 focus:ring-offset-2"
                    >
                        <Zap className="mr-2 h-5 w-5" />
                        Configure Agent
                    </button>
                </div>
            </div>
        </form>
    );
};

export default AgentConfigForm;
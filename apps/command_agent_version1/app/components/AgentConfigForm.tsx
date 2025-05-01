// AgentConfigForm.tsx - Updated with new sidebar design and tools
"use client";

import React, { useState, useCallback, useRef, useEffect } from "react";
import { v4 as uuidv4 } from "uuid";
import { ReactFlowProvider, ReactFlowInstance } from "react-flow-renderer";
import "react-flow-renderer/dist/style.css";
import FlowCanvas from "./FlowCanvas";
import ConfigureAgent from "./ConfigureAgent";
import AgentConfigModal from "./AgentConfigModal";
import {
    Router,
    Globe,
    Database,
    Link2,
    Wrench,
    MessageSquare,
    Settings,
    Save,
    Send,
    Plus,
    ChevronDown,
    ChevronRight,
    Zap,
    Edit
} from "lucide-react";
import { AgentType, AGENT_STYLES, AGENT_TYPES, NodeData } from "./type";

// Define additional types needed
interface Node {
    id: string;
    type: string;
    position: {
        x: number;
        y: number;
    };
    data: NodeData;
}

interface Edge {
    id: string;
    source: string;
    target: string;
    type?: string;
    animated?: boolean;
    style?: any;
    markerEnd?: any;
    data?: any;
}

interface ChatMessage {
    id: number;
    text: string;
    sender: "user" | "bot";
}

interface WorkflowConfig {
    workflowId: string;
    workflowName: string;
    agents: Array<{
        id: string;
        uuid: string;
        type: AgentType;
        name: string;
        prompt?: string;
        tools?: string[];
        position: {
            x: number;
            y: number;
        };
    }>;
    connections: Array<{
        fromUuid: string;
        toUuid: string;
    }>;
}

// SidebarSection component
const SidebarSection: React.FC<{
    title: string;
    isOpen: boolean;
    onToggle: () => void;
    children?: React.ReactNode;
}> = ({ title, isOpen, onToggle, children }) => {
    return (
        <div className="sidebar-section mb-4">
            <div
                className="section-header flex items-center justify-between py-2 px-1 cursor-pointer"
                onClick={onToggle}
            >
                <h2 className="text-sm font-medium text-gray-800">{title}</h2>
                <div className="text-orange-500">
                    {isOpen ? <ChevronDown size={18} /> : <ChevronRight size={18} />}
                </div>
            </div>

            {isOpen && (
                <div className="section-content mt-2">
                    {children}
                </div>
            )}
        </div>
    );
};

// SidebarItem component
const SidebarItem: React.FC<{
    icon: React.ReactNode;
    label: string;
    subLabel?: string;
    onClick?: () => void;
    draggable?: boolean;
    onDragStart?: (e: React.DragEvent<HTMLDivElement>) => void;
}> = ({ icon, label, subLabel, onClick, draggable, onDragStart }) => {
    return (
        <div
            className="sidebar-item cursor-grab p-2 mb-2 rounded-md hover:bg-gray-100 transition-colors"
            onClick={onClick}
            draggable={draggable}
            onDragStart={onDragStart}
        >
            <div className="sidebar-item-content flex items-center">
                <div className="item-icon mr-3">
                    {icon}
                </div>
                <div className="item-details">
                    <h3 className="text-sm font-medium">{label}</h3>
                    {subLabel && (
                        <p className="text-xs text-gray-500">{subLabel}</p>
                    )}
                </div>
            </div>
        </div>
    );
};

const AgentConfigForm = () => {
    // First, let's handle the client-side initialization properly
    const [mounted, setMounted] = useState(false);

    // Use refs for values that need to be stable across renders but aren't part of the UI state
    const workflowIdRef = useRef("");
    const reactFlowWrapper = useRef<HTMLDivElement>(null);
    const reactFlowInstanceRef = useRef<ReactFlowInstance | null>(null);

    // State for flow management
    const [nodes, setNodes] = useState<Node[]>([]);
    const [edges, setEdges] = useState<Edge[]>([]);

    // State for selected node and configuration
    const [selectedNode, setSelectedNode] = useState<Node | null>(null);
    const [isPromptModalOpen, setIsPromptModalOpen] = useState(false);

    // State for UI
    const [workflowName, setWorkflowName] = useState("My Agent Workflow");
    const [isChatMode, setIsChatMode] = useState(false);
    const [chatInput, setChatInput] = useState("");
    const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);
    const [isLoading, setIsLoading] = useState(false);
    const [showConfigPanel, setShowConfigPanel] = useState(false);

    // State for sidebar sections
    const [sectionsState, setSectionsState] = useState({
        components: true,
        actions: false,
        tools: false
    });

    // State for workflow tabs
    const [activeTab, setActiveTab] = useState("actions");

    // Toggle section visibility
    const toggleSection = (section: keyof typeof sectionsState) => {
        setSectionsState({
            ...sectionsState,
            [section]: !sectionsState[section]
        });
    };

    // Store flow instance when it's ready
    const onInit = (instance: ReactFlowInstance) => {
        reactFlowInstanceRef.current = instance;
    };

    // Initialize client-side only data after mount
    useEffect(() => {
        // Generate IDs only after component has mounted on the client
        if (!workflowIdRef.current) {
            workflowIdRef.current = uuidv4();
        }
        setMounted(true);
    }, []);

    // Node operations
    const handleDeleteNode = useCallback((nodeId: string) => {
        console.log("Deleting node with ID:", nodeId);

        setNodes(prevNodes => {
            const updatedNodes = prevNodes.filter(node => node.id !== nodeId);
            console.log("Nodes after deletion:", updatedNodes.map(n => n.id));
            return updatedNodes;
        });

        // Also remove any connected edges
        setEdges(prevEdges => {
            const updatedEdges = prevEdges.filter(edge =>
                edge.source !== nodeId && edge.target !== nodeId
            );
            console.log("Edges after deletion:", updatedEdges);
            return updatedEdges;
        });

        // If we just deleted the selected node, clear the selection
        if (selectedNode && selectedNode.id === nodeId) {
            setSelectedNode(null);
            setShowConfigPanel(false);
        }
    }, [selectedNode]);

    // Handle dropping an agent onto the canvas - IMPROVED for proper positioning and tools
    const onDrop = useCallback(
        (event: React.DragEvent<HTMLDivElement>) => {
            event.preventDefault();

            console.log("Drop event triggered");

            if (!reactFlowWrapper.current || !reactFlowInstanceRef.current) {
                console.error("React Flow wrapper or instance not ready");
                return;
            }

            const reactFlowBounds = reactFlowWrapper.current.getBoundingClientRect();
            const agentDataJson = event.dataTransfer.getData("application/reactflow");

            console.log("Drop data:", agentDataJson); // Debug logging

            if (!agentDataJson) {
                console.error("No data received during drop");
                return;
            }

            try {
                const agentData = JSON.parse(agentDataJson);
                console.log("Parsed drop data:", agentData);

                // Get drop position in react-flow coordinates
                const position = reactFlowInstanceRef.current.project({
                    x: event.clientX - reactFlowBounds.left,
                    y: event.clientY - reactFlowBounds.top
                });

                // Create a new node with a unique ID
                const nodeId = uuidv4();
                const newNode = {
                    id: nodeId,
                    type: "agent",
                    position,
                    data: {
                        id: nodeId,
                        shortId: agentData.id,
                        type: agentData.type,
                        name: agentData.name,
                        prompt: "", // Initialize with empty prompt
                        tools: ["Tool 1", "Tool 2", "Tool 3"], // Default tools
                        onDelete: handleDeleteNode,
                        onConfigure: () => handleNodeSelect({
                            id: nodeId,
                            type: "agent",
                            position,
                            data: {
                                id: nodeId,
                                shortId: agentData.id,
                                type: agentData.type,
                                name: agentData.name,
                                prompt: "",
                                tools: ["Tool 1", "Tool 2", "Tool 3"]
                            }
                        })
                    },
                };

                console.log("Creating new node:", newNode);
                setNodes(prevNodes => [...prevNodes, newNode]);

                // Set the newly created node as selected after a small delay
                // to ensure the node is properly rendered
                setTimeout(() => {
                    handleNodeSelect(newNode);
                }, 50);

            } catch (error) {
                console.error("Error creating node:", error);
            }
        },
        [handleDeleteNode]
    );

    // Handle drag over
    const onDragOver = useCallback((event: React.DragEvent<HTMLDivElement>) => {
        event.preventDefault();
        event.dataTransfer.dropEffect = "move";
    }, []);

    // Handle drag start for agent types
    const handleDragStart = useCallback((event, agent) => {
        console.log("Drag started:", agent);

        // Ensure the agent has all required properties
        const dragData = {
            id: agent.id || `agent-${Date.now()}`,
            type: agent.type || 'custom',
            name: agent.name || 'Custom Agent',
            // Include any other properties needed for the node
        };

        // Set the data transfer
        event.dataTransfer.setData("application/reactflow", JSON.stringify(dragData));
        event.dataTransfer.effectAllowed = "move";

        // Add visual feedback for dragging
        if (event.target.classList) {
            event.target.classList.add('dragging');
            setTimeout(() => {
                event.target.classList.remove('dragging');
            }, 100);
        }
    }, []);

    // Get agent icon based on type
    const getAgentIcon = (type: AgentType) => {
        switch (type) {
            case "router":
                return <Router size={20} className="text-purple-600" />;
            case "web_search":
                return <Globe size={20} className="text-blue-600" />;
            case "api":
                return <Link2 size={20} className="text-green-600" />;
            case "data":
                return <Database size={20} className="text-yellow-600" />;
            case "troubleshooting":
                return <Wrench size={20} className="text-red-600" />;
            default:
                return <Router size={20} className="text-gray-600" />;
        }
    };

    // Get agent icon container class based on type
    const getAgentIconClass = (type: AgentType) => {
        switch (type) {
            case "router":
                return "bg-purple-100";
            case "web_search":
                return "bg-blue-100";
            case "api":
                return "bg-green-100";
            case "data":
                return "bg-yellow-100";
            case "troubleshooting":
                return "bg-red-100";
            default:
                return "bg-gray-100";
        }
    };

    // Handle node selection
    const handleNodeSelect = useCallback((node: Node | null) => {
        // Only set the node if a node is clicked (don't deselect when clicking canvas)
        if (node) {
            setSelectedNode(node);
            setShowConfigPanel(true);
        }
        // Don't deselect or hide panel when clicking on canvas
    }, []);

    // Handle opening the prompt modal
    const handleOpenPromptModal = useCallback(() => {
        if (selectedNode) {
            setIsPromptModalOpen(true);
        }
    }, [selectedNode]);

    // Handle closing the prompt modal
    const handleClosePromptModal = useCallback(() => {
        setIsPromptModalOpen(false);
    }, []);

    // Handle saving the prompt
    const handleSavePrompt = useCallback((id: string, name: string, prompt: string, description: string) => {
        // Update the node data with the new name and prompt
        setNodes(prevNodes => prevNodes.map(node =>
            node.id === id
                ? {
                    ...node,
                    data: {
                        ...node.data,
                        name,
                        prompt,
                        description
                    }
                }
                : node
        ));
        setIsPromptModalOpen(false);

        // Update selectedNode if it's the node we just edited
        if (selectedNode && selectedNode.id === id) {
            setSelectedNode(prev => prev ? {
                ...prev,
                data: {
                    ...prev.data,
                    name,
                    prompt,
                    description
                }
            } : null);
        }
    }, [selectedNode]);

    // Deploy workflow
    const handleDeployWorkflow = async () => {
        if (nodes.length === 0) {
            alert("Please add at least one agent to your workflow before deploying.");
            return;
        }

        // Check if there's a router agent
        const routerNode = nodes.find(node => node.data.type === 'router');
        if (!routerNode) {
            alert("Your workflow must include a Router Agent.");
            return;
        }

        setIsLoading(true);

        try {
            // Deploy the workflow - this is just a placeholder, replace with your actual API
            console.log("Deploying workflow:", { nodes, edges });

            // Simulate API call
            await new Promise(resolve => setTimeout(resolve, 1000));

            // Switch to chat mode
            setIsChatMode(true);
            setShowConfigPanel(false); // Hide the config panel in chat mode

            // Add a system message to the chat
            setChatMessages([{
                id: Date.now(),
                text: "Workflow deployed successfully. You can now ask questions.",
                sender: "bot"
            }]);
        } catch (error) {
            console.error("Error deploying workflow:", error);
            alert("Failed to deploy workflow: " + (error as Error).message);
        } finally {
            setIsLoading(false);
        }
    };

    // Send chat message
    const handleSendMessage = async () => {
        if (!chatInput.trim()) return;

        // Add user message to chat
        const userMessage = {
            id: Date.now(),
            text: chatInput,
            sender: "user" as const
        };

        setChatMessages(prevMessages => [...prevMessages, userMessage]);

        // Save and clear input
        const query = chatInput;
        setChatInput("");

        setIsLoading(true);

        try {
            // Simulate API call
            await new Promise(resolve => setTimeout(resolve, 1000));

            // Add bot response
            const botMessage = {
                id: Date.now() + 1,
                text: "This is a simulated response to your query: " + query,
                sender: "bot" as const
            };

            setChatMessages(prevMessages => [...prevMessages, botMessage]);
        } catch (error) {
            console.error("Error running workflow:", error);

            // Add error message to chat
            setChatMessages(prevMessages => [
                ...prevMessages,
                {
                    id: Date.now() + 1,
                    text: `Error: ${(error as Error).message || "Failed to process message"}`,
                    sender: "bot" as const
                }
            ]);
        } finally {
            setIsLoading(false);
        }
    };

    // Save workflow
    const handleSaveWorkflow = () => {
        if (nodes.length === 0) {
            alert("Please add at least one agent to your workflow before saving.");
            return;
        }

        const workflow: WorkflowConfig = {
            workflowId: workflowIdRef.current,
            workflowName,
            agents: nodes.map(node => ({
                id: node.data.shortId || "",
                uuid: node.id,
                type: node.data.type,
                name: node.data.name,
                prompt: node.data.prompt, // Include prompt in saved workflow
                tools: node.data.tools, // Include tools in saved workflow
                position: node.position
            })),
            connections: edges.map(edge => ({
                fromUuid: edge.source,
                toUuid: edge.target
            }))
        };

        console.log("Saving workflow:", workflow);
        alert(`Workflow "${workflowName}" saved with ID: ${workflowIdRef.current.substring(0, 8)}`);
    };

    // Create a new workflow
    const handleCreateNewWorkflow = () => {
        workflowIdRef.current = uuidv4();
        setWorkflowName("My Agent Workflow");
        setNodes([]);
        setEdges([]);
        setIsChatMode(false);
        setChatMessages([]);
        setSelectedNode(null);
        setShowConfigPanel(false);
    };

    // Get agent description based on the selected node
    const getAgentDescription = (node: Node) => {
        const agentType = node.data.type;
        const agentDef = AGENT_TYPES.find(a => a.type === agentType);
        return node.data.description || agentDef?.description || "";
    };

    // Handle saving the agent configuration with tools
    const handleSaveAgentConfig = (configData: any) => {
        if (!selectedNode) return;

        console.log("Saving agent configuration:", configData);

        // If tools are provided in the configuration data, update them
        const tools = configData.selectedTools || selectedNode.data.tools || [];

        // Update the node data with the new configuration
        setNodes(prevNodes => prevNodes.map(node =>
            node.id === selectedNode.id
                ? {
                    ...node,
                    data: {
                        ...node.data,
                        tools, // Update tools from configuration
                        config: configData  // Store configuration in the node data
                    }
                }
                : node
        ));

        // Update selectedNode if it's the node we just edited
        if (selectedNode) {
            setSelectedNode(prev => prev ? {
                ...prev,
                data: {
                    ...prev.data,
                    tools,
                    config: configData
                }
            } : null);
        }

        // Show confirmation and optionally close the panel
        alert(`Configuration saved for ${selectedNode.data.name}`);
    };

    // If not yet mounted, return a loading placeholder that matches server-side rendering
    if (!mounted) {
        return (
            <div className="designer-content" style={{ position: 'relative' }}>
                <div className="designer-sidebar bg-white border-r border-gray-200 w-64">
                    <div className="sidebar-header p-4 border-b border-gray-200">
                        <h2 className="text-lg font-semibold mb-2">Workflow</h2>
                        <div className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm bg-gray-50">
                            Loading...
                        </div>
                        <div className="mt-2 text-xs text-gray-500">
                            ID: Loading...
                        </div>
                    </div>
                    <div className="p-4">
                        <div className="text-center py-4 text-gray-500">
                            Loading agents...
                        </div>
                    </div>
                </div>
                <div className="flex-1 bg-gray-50"></div>
            </div>
        );
    }

    return (
        <ReactFlowProvider>
            <div className="designer-content" ref={reactFlowWrapper} style={{ position: 'relative', overflowY: 'auto', height: 'calc(100vh - 60px)' }}>
                {/* Sidebar for agents - New Design */}
                {!isChatMode && (
                    <div className="designer-sidebar bg-white border-r border-gray-200 w-64 h-full overflow-y-auto">
                        {/* Workflow Header */}
                        <div className="sidebar-header p-4 border-b border-gray-200">
                            <h2 className="text-lg font-semibold mb-1">{workflowName}</h2>
                            <p className="text-sm text-gray-500">Analyze and process invoice documents</p>
                        </div>

                        {/* Navigation Tabs */}
                        <div className="flex border-b border-gray-200">
                            <div
                                className={`flex-1 text-center py-2 font-medium text-sm cursor-pointer ${activeTab === "actions"
                                    ? "text-orange-500 border-b-2 border-orange-500"
                                    : "text-gray-500 hover:text-orange-500"
                                    }`}
                                onClick={() => setActiveTab("actions")}
                            >
                                Actions
                            </div>
                            <div
                                className={`flex-1 text-center py-2 font-medium text-sm cursor-pointer ${activeTab === "workflows"
                                    ? "text-orange-500 border-b-2 border-orange-500"
                                    : "text-gray-500 hover:text-orange-500"
                                    }`}
                                onClick={() => setActiveTab("workflows")}
                            >
                                Workflows
                            </div>
                        </div>

                        {/* Collapsible Sections */}
                        {activeTab === "actions" && (
                            <div className="p-4">
                                {/* Components Section */}
                                <SidebarSection
                                    title="Components"
                                    isOpen={sectionsState.components}
                                    onToggle={() => toggleSection('components')}
                                >
                                    {AGENT_TYPES.filter(agent =>
                                        ['router', 'web_search', 'api', 'data'].includes(agent.type)
                                    ).map((agent) => (
                                        <SidebarItem
                                            key={agent.id}
                                            icon={
                                                <div className={`w-8 h-8 rounded-md ${getAgentIconClass(agent.type as AgentType)} flex items-center justify-center`}>
                                                    {getAgentIcon(agent.type as AgentType)}
                                                </div>
                                            }
                                            label={agent.name}
                                            subLabel="Initiate workflows"
                                            draggable={true}
                                            onDragStart={(e) => handleDragStart(e, agent)}
                                        />
                                    ))}
                                </SidebarSection>

                                {/* Actions Section */}
                                <SidebarSection
                                    title="Actions"
                                    isOpen={sectionsState.actions}
                                    onToggle={() => toggleSection('actions')}
                                >


                                    {/* Notification Action */}
                                    <SidebarItem
                                        icon={
                                            <div className="w-8 h-8 rounded-md bg-purple-100 flex items-center justify-center">
                                                <MessageSquare size={20} className="text-purple-600" />
                                            </div>
                                        }
                                        label="Notification"
                                        subLabel="Initiate workflows"
                                        draggable={true}
                                        onDragStart={(e) => handleDragStart(e, {
                                            id: 'notification-' + Date.now(),
                                            type: 'notification',
                                            name: 'Notification'
                                        })}
                                    />

                                    {/* Conditional Action */}
                                    <SidebarItem
                                        icon={
                                            <div className="w-8 h-8 rounded-md bg-green-100 flex items-center justify-center">
                                                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-green-600">
                                                    <path d="m8 3 4 8 5-5 5 15H2L8 3z" />
                                                </svg>
                                            </div>
                                        }
                                        label="Conditional"
                                        subLabel="Initiate workflows"
                                        draggable={true}
                                        onDragStart={(e) => handleDragStart(e, {
                                            id: 'conditional-' + Date.now(),
                                            type: 'conditional',
                                            name: 'Conditional'
                                        })}
                                    />

                                    {/* Delay Action */}
                                    <SidebarItem
                                        icon={
                                            <div className="w-8 h-8 rounded-md bg-amber-100 flex items-center justify-center">
                                                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-amber-600">
                                                    <circle cx="12" cy="12" r="10" />
                                                    <polyline points="12 6 12 12 16 14" />
                                                </svg>
                                            </div>
                                        }
                                        label="Delay"
                                        subLabel="Initiate workflows"
                                        draggable={true}
                                        onDragStart={(e) => handleDragStart(e, {
                                            id: 'delay-' + Date.now(),
                                            type: 'delay',
                                            name: 'Delay'
                                        })}
                                    />
                                </SidebarSection>

                                {/* Tools Section */}
                                <SidebarSection
                                    title="Tools"
                                    isOpen={sectionsState.tools}
                                    onToggle={() => toggleSection('tools')}
                                >
                                    <SidebarItem
                                        icon={
                                            <div className="w-8 h-8 rounded-md bg-orange-100 flex items-center justify-center">
                                                <Zap size={20} className="text-orange-500" />
                                            </div>
                                        }
                                        label="API Connectors"
                                        subLabel="Initiate workflows"
                                        draggable={true}
                                        onDragStart={(e) => handleDragStart(e, {
                                            id: 'api-connector-' + Date.now(),
                                            type: 'api_connector',
                                            name: 'API Connector'
                                        })}
                                    />
                                </SidebarSection>
                            </div>
                        )}

                        {/* Workflows Content (Initially Hidden) */}
                        {activeTab === "workflows" && (
                            <div className="p-4">
                                <p className="text-center text-gray-500 py-8">No saved workflows yet.</p>
                            </div>
                        )}

                        {/* Deploy Workflow Button */}
                        <div className="p-4 mt-auto border-t border-gray-200">
                            <button
                                onClick={handleDeployWorkflow}
                                className="w-full px-4 py-2 bg-orange-500 text-white rounded-md text-sm font-medium hover:bg-orange-600 transition-colors"
                                disabled={isLoading}
                            >
                                {isLoading ? 'Deploying...' : 'Deploy Workflow'}
                            </button>
                        </div>
                    </div>
                )}

                {/* Chat interface sidebar */}
                {isChatMode && (
                    <div className="designer-sidebar bg-white border-r border-gray-200 w-64 h-full overflow-y-auto">
                        <div className="sidebar-header p-4 border-b border-gray-200">
                            <h2 className="text-lg font-semibold">{workflowName}</h2>
                            <div className="text-xs text-gray-500 mt-1">
                                ID: {workflowIdRef.current.substring(0, 8)}
                            </div>
                        </div>

                        <div className="flex border-b border-gray-200">
                            <div className="flex-1 text-center py-2 text-orange-500 border-b-2 border-orange-500 font-medium text-sm">
                                Actions
                            </div>
                            <div className="flex-1 text-center py-2 text-gray-500 font-medium text-sm">
                                Workflows
                            </div>
                        </div>

                        <div className="p-4">
                            <button
                                onClick={() => setIsChatMode(false)}
                                className="flex items-center w-full px-3 py-2 bg-gray-100 rounded-md text-sm font-medium hover:bg-gray-200 mb-3"
                                disabled={isLoading}
                            >
                                <Settings size={16} className="mr-2" />
                                Edit Workflow
                            </button>

                            <button
                                onClick={handleCreateNewWorkflow}
                                className="flex items-center w-full px-3 py-2 bg-blue-50 text-blue-600 rounded-md text-sm font-medium hover:bg-blue-100"
                                disabled={isLoading}
                            >
                                <Plus size={16} className="mr-2" />
                                New Workflow
                            </button>
                        </div>

                        <div className="p-4 mt-auto border-t border-gray-200">
                            <button
                                onClick={() => setIsChatMode(false)}
                                className="w-full px-4 py-2 bg-orange-500 text-white rounded-md text-sm font-medium hover:bg-orange-600 transition-colors"
                                disabled={isLoading}
                            >
                                {isLoading ? 'Loading...' : 'Return to Editor'}
                            </button>
                        </div>
                    </div>
                )}

                {/* Configuration sidebar - shown when a node is selected */}
                {!isChatMode && showConfigPanel && selectedNode && (
                    <div className="config-sidebar" style={{ position: 'absolute', right: 0, top: 0, width: '320px', height: '100%', backgroundColor: 'white', borderLeft: '1px solid #e5e7eb', overflowY: 'auto', zIndex: 10 }}>
                        <ConfigureAgent
                            agentName={selectedNode.data.name}
                            agentType={selectedNode.data.type}
                            description={getAgentDescription(selectedNode)}
                            onEditPrompt={handleOpenPromptModal}
                            onSave={handleSaveAgentConfig}
                            onClose={() => setShowConfigPanel(false)}
                        />
                    </div>
                )}

                {/* Main content area */}
                <div className="flex-1" style={{ position: 'relative', minHeight: '600px', overflow: 'hidden' }}>
                    {/* Flow canvas */}
                    {!isChatMode && (
                        <div style={{ width: '100%', height: '100%' }}>
                            <FlowCanvas
                                nodes={nodes}
                                edges={edges}
                                setNodes={setNodes}
                                setEdges={setEdges}
                                onDrop={onDrop}
                                onDragOver={onDragOver}
                                onNodeSelect={handleNodeSelect}
                                onInit={onInit}
                            />
                        </div>
                    )}

                    {/* Chat interface */}
                    {isChatMode && (
                        <div className="chat-container" style={{ height: '100%', display: 'flex', flexDirection: 'column', overflowY: 'auto' }}>
                            <div className="chat-messages" style={{ flex: 1, overflowY: 'auto', padding: '1rem' }}>
                                {chatMessages.length === 0 ? (
                                    <div className="h-full flex items-center justify-center">
                                        <div className="text-center">
                                            <div className="bg-orange-100 text-orange-500 rounded-full p-4 inline-flex mb-4">
                                                <MessageSquare size={24} />
                                            </div>
                                            <h3 className="text-lg font-medium">Start a conversation</h3>
                                            <p className="text-gray-500 mt-2 max-w-md">
                                                Ask a question to begin using your deployed agent flow.
                                            </p>
                                        </div>
                                    </div>
                                ) : (
                                    <div className="space-y-4">
                                        {chatMessages.map((message) => (
                                            <div
                                                key={message.id}
                                                className={`message ${message.sender === "user" ? "ml-auto bg-orange-500 text-white" : "bg-gray-100"} p-3 rounded-lg max-w-[75%]`}
                                            >
                                                {message.text}
                                            </div>
                                        ))}
                                    </div>
                                )}
                            </div>
                            <div className="chat-input" style={{ display: 'flex', padding: '1rem', borderTop: '1px solid #e5e7eb' }}>
                                <input
                                    type="text"
                                    value={chatInput}
                                    onChange={(e) => setChatInput(e.target.value)}
                                    onKeyDown={(e) => e.key === 'Enter' && !isLoading && handleSendMessage()}
                                    placeholder="Type a message..."
                                    className="flex-1 px-4 py-2 border border-gray-300 rounded-l-md focus:outline-none focus:ring-2 focus:ring-orange-500"
                                    disabled={isLoading}
                                />
                                <button
                                    onClick={handleSendMessage}
                                    className="px-4 py-2 bg-orange-500 text-white rounded-r-md hover:bg-orange-600 disabled:bg-orange-400"
                                    disabled={isLoading}
                                >
                                    {isLoading ? '...' : <Send size={18} />}
                                </button>
                            </div>
                        </div>
                    )}
                </div>

                {/* Prompt editing modal */}
                {selectedNode && (
                    <AgentConfigModal
                        isOpen={isPromptModalOpen}
                        nodeData={selectedNode ? {
                            id: selectedNode.id,
                            type: selectedNode.data.type,
                            name: selectedNode.data.name,
                            shortId: selectedNode.data.shortId,
                            prompt: selectedNode.data.prompt,
                            description: selectedNode.data.description
                        } : null}
                        onClose={handleClosePromptModal}
                        onSave={handleSavePrompt}
                    />
                )}
            </div>
        </ReactFlowProvider>
    );
};

export default AgentConfigForm;
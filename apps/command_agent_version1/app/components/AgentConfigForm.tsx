"use client";

import React, { useState, useCallback, useRef, useEffect } from "react";
import { v4 as uuidv4 } from "uuid";
import { ReactFlowProvider } from "react-flow-renderer";
import "react-flow-renderer/dist/style.css";
import FlowCanvas from "./FlowCanvas";
import {
    Router,
    Globe,
    Database,
    Link2,
    Wrench,
    MessageSquare,
    Settings,
    X,
    Save,
    Send,
    Plus
} from "lucide-react";
import { WorkflowAPI } from "../api/workflowApi";
// Define proper types
interface NodeData {
    id: string;
    shortId?: string;
    type: AgentType;
    name: string;
    onDelete: (id: string) => void;
    onConfigure: (id: string) => void;
}

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
}

interface ChatMessage {
    id: number;
    text: string;
    sender: "user" | "bot";
}

type AgentType = "router" | "web_search" | "api" | "data" | "troubleshooting";

interface AgentTypeDefinition {
    id: string;
    type: AgentType;
    name: string;
    description?: string;
}

interface WorkflowConfig {
    workflowId: string;
    workflowName: string;
    agents: Array<{
        id: string;
        uuid: string;
        type: AgentType;
        name: string;
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

// Agent types definitions
const AGENT_TYPES: AgentTypeDefinition[] = [
    {
        id: "router-1",
        type: "router",
        name: "Router Agent",
        description: "Routes queries to appropriate agents"
    },
    {
        id: "search-1",
        type: "web_search",
        name: "Web Search Agent",
        description: "Searches the web for information"
    },
    {
        id: "api-1",
        type: "api",
        name: "API Agent",
        description: "Connects to external APIs"
    },
    {
        id: "data-1",
        type: "data",
        name: "Data Agent",
        description: "Processes and analyzes data"
    }
];

// Agent styles map
const AGENT_STYLES: Record<AgentType, { bgClass: string; textClass: string }> = {
    router: { bgClass: "bg-blue-100", textClass: "text-blue-600" },
    web_search: { bgClass: "bg-emerald-100", textClass: "text-emerald-600" },
    api: { bgClass: "bg-amber-100", textClass: "text-amber-600" },
    data: { bgClass: "bg-purple-100", textClass: "text-purple-600" },
    troubleshooting: { bgClass: "bg-red-100", textClass: "text-red-600" }
};

const AgentConfigForm = () => {
    // First, let's handle the client-side initialization properly
    const [mounted, setMounted] = useState(false);

    // Use refs for values that need to be stable across renders but aren't part of the UI state
    const workflowIdRef = useRef("");

    // State for flow management
    const [nodes, setNodes] = useState<Node[]>([]);
    const [edges, setEdges] = useState<Edge[]>([]);

    // State for UI
    const [selectedNode, setSelectedNode] = useState<Node | null>(null);
    const [workflowName, setWorkflowName] = useState("My Agent Workflow");
    const [isConfiguring, setIsConfiguring] = useState(false);
    const [isChatMode, setIsChatMode] = useState(false);
    const [chatInput, setChatInput] = useState("");
    const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);
    const [isLoading, setIsLoading] = useState(false); // Add loading state

    const reactFlowWrapper = useRef<HTMLDivElement>(null);

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
            // Log current nodes for debugging
            console.log("Current nodes:", prevNodes.map(n => ({ id: n.id, name: n.data.name })));

            // Check if the node exists before deletion
            const nodeExists = prevNodes.some(node => node.id === nodeId);
            if (!nodeExists) {
                console.error("Node not found for deletion:", nodeId);
                return prevNodes; // Return unchanged if node doesn't exist
            }

            // Remove the node
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

        // Clear selection if needed
        if (selectedNode && selectedNode.id === nodeId) {
            setSelectedNode(null);
            setIsConfiguring(false);
        }
    }, [selectedNode]);

    const handleConfigureNode = useCallback((nodeId: string) => {
        console.log("Configuring node with ID:", nodeId);
        const node = nodes.find(n => n.id === nodeId);
        if (node) {
            setSelectedNode(node);
            setIsConfiguring(true);
        } else {
            console.error("Node not found for configuration:", nodeId);
        }
    }, [nodes]);

    const handleCloseConfig = () => {
        setIsConfiguring(false);
        setSelectedNode(null);
    };

    // Handle dropping an agent onto the canvas
    const onDrop = useCallback(
        (event: React.DragEvent<HTMLDivElement>) => {
            event.preventDefault();

            if (reactFlowWrapper.current) {
                const reactFlowBounds = reactFlowWrapper.current.getBoundingClientRect();
                const agentDataJson = event.dataTransfer.getData("application/reactflow");

                if (agentDataJson) {
                    try {
                        const agentData = JSON.parse(agentDataJson) as AgentTypeDefinition;

                        // Generate a position relative to the drop point
                        const position = {
                            x: event.clientX - reactFlowBounds.left - 100,
                            y: event.clientY - reactFlowBounds.top - 40,
                        };

                        // Create a new node with a unique ID
                        const nodeId = uuidv4();
                        const newNode: Node = {
                            id: nodeId,
                            type: "agent",
                            position,
                            data: {
                                id: nodeId,
                                shortId: agentData.id,
                                type: agentData.type,
                                name: agentData.name,
                                onDelete: handleDeleteNode,
                                onConfigure: handleConfigureNode
                            },
                        };

                        console.log("Creating new node:", newNode);
                        setNodes(prevNodes => [...prevNodes, newNode]);
                    } catch (error) {
                        console.error("Error creating node:", error);
                    }
                }
            }
        },
        [handleDeleteNode, handleConfigureNode]
    );

    // Handle drag over
    const onDragOver = useCallback((event: React.DragEvent<HTMLDivElement>) => {
        event.preventDefault();
        event.dataTransfer.dropEffect = "move";
    }, []);

    // Handle drag start for agent types
    const handleDragStart = (event: React.DragEvent<HTMLDivElement>, agent: AgentTypeDefinition) => {
        event.dataTransfer.setData("application/reactflow", JSON.stringify(agent));
        event.dataTransfer.effectAllowed = "move";
    };

    // Deploy workflow - Updated to use API
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
            // Deploy the workflow
            const response = await WorkflowAPI.deployWorkflow(nodes, edges);
            console.log("Workflow deployed:", response);

            // Switch to chat mode
            setIsChatMode(true);

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

    // Send chat message - Updated to use API
    const handleSendMessage = async () => {
        if (!chatInput.trim()) return;

        // Find router node
        const routerNode = nodes.find(node => node.data.type === 'router');

        if (!routerNode) {
            alert("No router agent found in the workflow!");
            return;
        }

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
            // Send message to backend
            const response = await WorkflowAPI.runWorkflow(routerNode.id, query);

            // Add response to chat
            const botMessage = {
                id: Date.now() + 1,
                text: response.response || "No response received from workflow",
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
    };

    // Render agent icon based on type
    const renderAgentIcon = (type: AgentType) => {
        switch (type) {
            case "router":
                return <Router size={16} />;
            case "web_search":
                return <Globe size={16} />;
            case "api":
                return <Link2 size={16} />;
            case "data":
                return <Database size={16} />;
            case "troubleshooting":
                return <Wrench size={16} />;
            default:
                return <Router size={16} />;
        }
    };

    // Get CSS class for agent type
    const getAgentColorClass = (type: AgentType) => {
        switch (type) {
            case "router":
                return "bg-blue-100 text-blue-600";
            case "web_search":
                return "bg-emerald-100 text-emerald-600";
            case "api":
                return "bg-amber-100 text-amber-600";
            case "data":
                return "bg-purple-100 text-purple-600";
            case "troubleshooting":
                return "bg-red-100 text-red-600";
            default:
                return "bg-gray-100 text-gray-600";
        }
    };

    // If not yet mounted, return a loading placeholder that matches server-side rendering
    if (!mounted) {
        return (
            <div className="designer-content" style={{ position: 'relative' }}>
                <div className="designer-sidebar">
                    <div className="sidebar-header">
                        <h2 className="text-lg font-semibold mb-2">Workflow</h2>
                        <div className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm bg-gray-50">
                            Loading...
                        </div>
                        <div className="mt-2 text-xs text-gray-500">
                            ID: Loading...
                        </div>
                    </div>
                    <div className="sidebar-items">
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
            <div className="designer-content" ref={reactFlowWrapper} style={{ position: 'relative', overflowY: 'auto' }}>
                {/* Sidebar for agents */}
                {!isChatMode && (
                    <div className="designer-sidebar" style={{ overflowY: 'auto', maxHeight: '100%' }}>
                        <div className="sidebar-header">
                            <h2 className="text-lg font-semibold mb-2">Workflow</h2>
                            <input
                                type="text"
                                value={workflowName}
                                onChange={(e) => setWorkflowName(e.target.value)}
                                className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
                                placeholder="Workflow Name"
                            />
                            <div className="mt-2 text-xs text-gray-500">
                                ID: {workflowIdRef.current.substring(0, 8)}
                            </div>
                        </div>

                        <h3 className="font-medium text-sm mb-3 px-3 pt-3">Available Agents</h3>
                        <div className="sidebar-items">
                            {AGENT_TYPES.map((agent) => (
                                <div
                                    key={agent.id}
                                    className="sidebar-item"
                                    draggable
                                    onDragStart={(e) => handleDragStart(e, agent)}
                                >
                                    <div className="sidebar-item-content">
                                        <div className={`item-icon ${getAgentColorClass(agent.type)}`}>
                                            {renderAgentIcon(agent.type)}
                                        </div>
                                        <div className="item-details">
                                            <h3>{agent.name}</h3>
                                            <p>ID: {agent.id}</p>
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>

                        <div className="pt-4 border-t border-gray-200 mt-4 px-4 pb-4 space-y-2">
                            <button
                                onClick={handleSaveWorkflow}
                                className="flex items-center justify-center w-full px-4 py-2 bg-white border border-gray-300 rounded-md text-sm font-medium hover:bg-gray-50"
                                disabled={isLoading}
                            >
                                <Save size={16} className="mr-2" />
                                Save Workflow
                            </button>
                            <button
                                onClick={handleDeployWorkflow}
                                className="flex items-center justify-center w-full px-4 py-2 bg-blue-600 text-white rounded-md text-sm font-medium hover:bg-blue-700"
                                disabled={isLoading}
                            >
                                {isLoading ? 'Deploying...' : 'Deploy Workflow'}
                            </button>
                        </div>
                    </div>
                )}

                {/* Chat interface sidebar */}
                {isChatMode && (
                    <div className="designer-sidebar" style={{ overflowY: 'auto', maxHeight: '100%' }}>
                        <div className="sidebar-header">
                            <h2 className="text-lg font-semibold">{workflowName}</h2>
                            <div className="text-xs text-gray-500 mt-1">
                                ID: {workflowIdRef.current.substring(0, 8)}
                            </div>
                        </div>

                        <div className="sidebar-items">
                            <button
                                onClick={() => setIsChatMode(false)}
                                className="flex items-center w-full px-3 py-2 bg-gray-100 rounded-md text-sm font-medium hover:bg-gray-200"
                                disabled={isLoading}
                            >
                                <Settings size={16} className="mr-2" />
                                Edit Workflow
                            </button>

                            <button
                                onClick={handleCreateNewWorkflow}
                                className="flex items-center w-full px-3 py-2 mt-2 bg-blue-50 text-blue-600 rounded-md text-sm font-medium hover:bg-blue-100"
                                disabled={isLoading}
                            >
                                <Plus size={16} className="mr-2" />
                                New Workflow
                            </button>
                        </div>
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
                                            <div className="bg-blue-100 text-blue-600 rounded-full p-4 inline-flex mb-4">
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
                                                className={`message ${message.sender} ${message.sender === "user" ? "ml-auto bg-blue-500 text-white p-3 rounded-lg max-w-[75%]" : "bg-gray-100 p-3 rounded-lg max-w-[75%]"}`}
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
                                    className="flex-1 px-4 py-2 border border-gray-300 rounded-l-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                                    disabled={isLoading}
                                />
                                <button
                                    onClick={handleSendMessage}
                                    className="px-4 py-2 bg-blue-600 text-white rounded-r-md hover:bg-blue-700 disabled:bg-blue-400"
                                    disabled={isLoading}
                                >
                                    {isLoading ? '...' : <Send size={18} />}
                                </button>
                            </div>
                        </div>
                    )}
                </div>

                {/* Configuration modal */}
                {isConfiguring && selectedNode && (
                    <div className="config-modal" style={{ position: 'fixed', inset: 0, backgroundColor: 'rgba(0, 0, 0, 0.5)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 50 }}>
                        <div className="modal-content" style={{ backgroundColor: 'white', borderRadius: '8px', padding: '1.5rem', width: '24rem', maxWidth: '90%' }}>
                            <div className="flex justify-between items-center mb-4">
                                <h3 className="text-lg font-medium">Configure {selectedNode.data.name}</h3>
                                <button
                                    onClick={handleCloseConfig}
                                    className="text-gray-500 hover:text-gray-700"
                                >
                                    <X size={18} />
                                </button>
                            </div>

                            <div className="space-y-4">
                                <div>
                                    <label className="block text-sm font-medium mb-1">Agent Name</label>
                                    <input
                                        type="text"
                                        value={selectedNode.data.name}
                                        onChange={(e) => {
                                            const newName = e.target.value;
                                            setNodes((prevNodes) =>
                                                prevNodes.map((n) =>
                                                    n.id === selectedNode.id
                                                        ? { ...n, data: { ...n.data, name: newName } }
                                                        : n
                                                )
                                            );
                                        }}
                                        className="w-full px-3 py-2 border border-gray-300 rounded-md"
                                    />
                                </div>

                                <div>
                                    <label className="block text-sm font-medium mb-1">Agent Type</label>
                                    <div className="py-2 px-3 bg-gray-100 rounded-md text-sm">{selectedNode.data.type}</div>
                                </div>

                                <div>
                                    <label className="block text-sm font-medium mb-1">Node ID</label>
                                    <div className="py-2 px-3 bg-gray-100 rounded-md text-sm font-mono text-gray-600 break-all">{selectedNode.id}</div>
                                </div>

                                <button
                                    onClick={handleCloseConfig}
                                    className="w-full px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
                                >
                                    Apply Configuration
                                </button>
                            </div>
                        </div>
                    </div>
                )}
            </div>
        </ReactFlowProvider>
    );
};

export default AgentConfigForm;
// AgentConfigForm.tsx - Modified to improve connections and dragging
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
    Plus
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

    // Handle dropping an agent onto the canvas - IMPROVED for proper positioning
    const onDrop = useCallback(
        (event: React.DragEvent<HTMLDivElement>) => {
            event.preventDefault();

            if (reactFlowWrapper.current && reactFlowInstanceRef.current) {
                const reactFlowBounds = reactFlowWrapper.current.getBoundingClientRect();
                const agentDataJson = event.dataTransfer.getData("application/reactflow");

                if (agentDataJson) {
                    try {
                        const agentData = JSON.parse(agentDataJson) as any;

                        // Get drop position in react-flow coordinates
                        const position = reactFlowInstanceRef.current.project({
                            x: event.clientX - reactFlowBounds.left,
                            y: event.clientY - reactFlowBounds.top
                        });

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
                                prompt: "", // Initialize with empty prompt
                                onDelete: handleDeleteNode,
                                onConfigure: () => handleNodeSelect(newNode)
                            },
                        };

                        console.log("Creating new node:", newNode);
                        setNodes(prevNodes => [...prevNodes, newNode]);

                        // Set the newly created node as selected
                        handleNodeSelect(newNode);
                    } catch (error) {
                        console.error("Error creating node:", error);
                    }
                }
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
    const handleDragStart = (event: React.DragEvent<HTMLDivElement>, agent: any) => {
        event.dataTransfer.setData("application/reactflow", JSON.stringify(agent));
        event.dataTransfer.effectAllowed = "move";
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
    const handleSavePrompt = useCallback((id: string, name: string, prompt: string) => {
        // Update the node data with the new name and prompt
        setNodes(prevNodes => prevNodes.map(node =>
            node.id === id
                ? {
                    ...node,
                    data: {
                        ...node.data,
                        name,
                        prompt
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
                    prompt
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
        return agentDef?.description || "";
    };

    // Handle saving the agent configuration
    const handleSaveAgentConfig = (configData: any) => {
        if (!selectedNode) return;

        console.log("Saving agent configuration:", configData);

        // Update the node data with the new configuration
        setNodes(prevNodes => prevNodes.map(node =>
            node.id === selectedNode.id
                ? {
                    ...node,
                    data: {
                        ...node.data,
                        config: configData  // Store configuration in the node data
                    }
                }
                : node
        ));

        // Show confirmation and optionally close the panel
        alert(`Configuration saved for ${selectedNode.data.name}`);
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
            <div className="designer-content" ref={reactFlowWrapper} style={{ position: 'relative', overflowY: 'auto', height: 'calc(100vh - 60px)' }}>
                {/* Sidebar for agents */}
                {!isChatMode && (
                    <div className="designer-sidebar" style={{ overflowY: 'auto', maxHeight: '100%', width: '250px' }}>
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
                                        <div className={`item-icon ${AGENT_STYLES[agent.type].bgClass} ${AGENT_STYLES[agent.type].textClass}`}>
                                            {/* Use appropriate icon based on agent type */}
                                            {agent.type === "router" && <Router size={16} />}
                                            {agent.type === "web_search" && <Globe size={16} />}
                                            {agent.type === "api" && <Link2 size={16} />}
                                            {agent.type === "data" && <Database size={16} />}
                                            {agent.type === "troubleshooting" && <Wrench size={16} />}
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
                    <div className="designer-sidebar" style={{ overflowY: 'auto', maxHeight: '100%', width: '250px' }}>
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

                {/* Prompt editing modal */}
                {selectedNode && (
                    <AgentConfigModal
                        isOpen={isPromptModalOpen}
                        nodeData={selectedNode ? {
                            id: selectedNode.id,
                            type: selectedNode.data.type,
                            name: selectedNode.data.name,
                            shortId: selectedNode.data.shortId,
                            prompt: selectedNode.data.prompt
                        } : null}
                        onClose={handleClosePromptModal}
                        onSave={handleSavePrompt}
                    />
                )}
            </div>

            {/* Add default CSS for sidebar items */}
            <style jsx>{`
                .designer-sidebar {
                    background-color: white;
                    border-right: 1px solid #e5e7eb;
                    padding: 1rem;
                }

                .sidebar-header {
                    padding-bottom: 1rem;
                    border-bottom: 1px solid #e5e7eb;
                    margin-bottom: 1rem;
                }

                .sidebar-items {
                    padding: 0.5rem 0;
                }

                .sidebar-item {
                    cursor: pointer;
                    padding: 0.5rem;
                    margin-bottom: 0.5rem;
                    border-radius: 0.375rem;
                    transition: background-color 0.2s;
                }

                .sidebar-item:hover {
                    background-color: #f3f4f6;
                }

                .sidebar-item-content {
                    display: flex;
                    align-items: center;
                }

                .item-icon {
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    width: 2rem;
                    height: 2rem;
                    border-radius: 0.375rem;
                    margin-right: 0.75rem;
                }

                .item-details h3 {
                    font-size: 0.875rem;
                    font-weight: 500;
                    line-height: 1.25rem;
                }

                .item-details p {
                    font-size: 0.75rem;
                    color: #6b7280;
                }

                .chat-container {
                    display: flex;
                    flex-direction: column;
                    height: 100%;
                }

                .message {
                    word-break: break-word;
                }

                .message.user {
                    align-self: flex-end;
                }

                .message.bot {
                    align-self: flex-start;
                }
            `}</style>
        </ReactFlowProvider>
    );
};

export default AgentConfigForm;
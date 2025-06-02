"use client";

import React, { useState, useCallback, useRef, useEffect } from "react";
import { v4 as uuidv4 } from "uuid";
import { ReactFlowProvider, ReactFlowInstance } from "reactflow";

// Import components
import DesignerSidebar from "./DesignerSidebar";
import DesignerCanvas from "./DesignerCanvas";
import ConfigPanel from "./ConfigPanel";
import AgentConfigModal from "./AgentConfigModal";
import ChatInterface from "./ChatInterface";
import ChatSidebar from "./ChatSidebar";

// Import types
import { AgentType, AGENT_TYPES, NodeData } from "./type";

// Import styles
import "./AgentConfigForm.scss";
import { WorkflowAPI } from "../api/workflowApi.ts";
import HeaderBottom from "./HeaderBottom.tsx";

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
        tags?: string[];
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

const AgentConfigForm: React.FC = () => {
    // First, let's handle the client-side initialization properly
    const [mounted, setMounted] = useState(false);

    // Use refs for values that need to be stable across renders
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
    const [activeTab, setActiveTab] = useState("actions");
    const [sidebarOpen, setSidebarOpen] = useState(true);

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
    const handleDeleteNode = useCallback(
        (nodeId: string) => {
            setNodes((prevNodes) => prevNodes.filter((node) => node.id !== nodeId));

            // Also remove any connected edges
            setEdges((prevEdges) =>
                prevEdges.filter(
                    (edge) => edge.source !== nodeId && edge.target !== nodeId
                )
            );

            // If we just deleted the selected node, clear the selection
            if (selectedNode && selectedNode.id === nodeId) {
                setSelectedNode(null);
                setShowConfigPanel(false);
            }
        },
        [selectedNode]
    );

    // Handle dropping an agent onto the canvas
    const onDrop = useCallback(
        (event: React.DragEvent<HTMLDivElement>) => {
            event.preventDefault();

            if (!reactFlowWrapper.current || !reactFlowInstanceRef.current) {
                console.error("React Flow wrapper or instance not ready");
                return;
            }

            const reactFlowBounds = reactFlowWrapper.current.getBoundingClientRect();
            const agentDataJson = event.dataTransfer.getData("application/reactflow");

            if (!agentDataJson) {
                console.error("No data received during drop");
                return;
            }

            try {
                const agentData = JSON.parse(agentDataJson);

                // Get drop position in react-flow coordinates
                const position = reactFlowInstanceRef.current.project({
                    x: event.clientX - reactFlowBounds.left,
                    y: event.clientY - reactFlowBounds.top,
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
                        tags: [agentData.type], // Initialize tags with the type
                        onDelete: handleDeleteNode,
                        onConfigure: () =>
                            handleNodeSelect({
                                id: nodeId,
                                type: "agent",
                                position,
                                data: {
                                    id: nodeId,
                                    shortId: agentData.id,
                                    type: agentData.type,
                                    name: agentData.name,
                                    prompt: "",
                                    tools: ["Tool 1", "Tool 2", "Tool 3"],
                                    tags: [agentData.type],
                                    onDelete: handleDeleteNode,
                                    onConfigure: () => { }, // This will be overwritten
                                },
                            }),
                    },
                };

                setNodes((prevNodes) => [...prevNodes, newNode]);

                // Set the newly created node as selected after a small delay
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
    const handleDragStart = useCallback(
        (event: React.DragEvent<HTMLDivElement>, agent: any) => {
            // Ensure the agent has all required properties
            const dragData = {
                id: agent.id || `agent-${Date.now()}`,
                type: agent.type || "custom",
                name: agent.name || "Custom Agent",
            };

            // Set the data transfer
            event.dataTransfer.setData(
                "application/reactflow",
                JSON.stringify(dragData)
            );
            event.dataTransfer.effectAllowed = "move";

            // Add visual feedback for dragging
            if (event.currentTarget.classList) {
                const element = event.currentTarget;
                element.classList.add("dragging");
                setTimeout(() => {
                    if (element) {
                        element.classList.remove("dragging");
                    }
                }, 100);
            }
        },
        []
    );

    // Handle node selection
    const handleNodeSelect = useCallback((node: Node) => {
        setSelectedNode(node);
        setShowConfigPanel(true);
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
    const handleSavePrompt = useCallback(
        (
            id: string,
            name: string,
            prompt: string,
            description: string,
            tags: string[] = []
        ) => {
            // Update the node data with the new name, prompt, description and tags
            setNodes((prevNodes) =>
                prevNodes.map((node) =>
                    node.id === id
                        ? {
                            ...node,
                            data: {
                                ...node.data,
                                name,
                                prompt,
                                description,
                                tags,
                            },
                        }
                        : node
                )
            );
            setIsPromptModalOpen(false);

            // Update selectedNode if it's the node we just edited
            if (selectedNode && selectedNode.id === id) {
                setSelectedNode((prev) =>
                    prev
                        ? {
                            ...prev,
                            data: {
                                ...prev.data,
                                name,
                                prompt,
                                description,
                                tags,
                            },
                        }
                        : null
                );
            }
        },
        [selectedNode]
    );

    // Handle agent name change
    const handleAgentNameChange = useCallback(
        (nodeId: string, newName: string) => {
            if (newName.trim() === "") return; // Don't allow empty names

            // Update the node data with the new name
            setNodes((prevNodes) =>
                prevNodes.map((node) =>
                    node.id === nodeId
                        ? {
                            ...node,
                            data: {
                                ...node.data,
                                name: newName,
                                // Make sure onDelete and onConfigure are maintained
                                onDelete: node.data.onDelete,
                                onConfigure: node.data.onConfigure,
                            },
                        }
                        : node
                )
            );

            // Also update selectedNode if it's the node we just edited
            if (selectedNode && selectedNode.id === nodeId) {
                setSelectedNode((prev) =>
                    prev
                        ? {
                            ...prev,
                            data: {
                                ...prev.data,
                                name: newName,
                            },
                        }
                        : null
                );
            }

            // Show a brief notification to confirm the name change (optional)
            const notification = document.createElement("div");
            notification.textContent = `Agent renamed to "${newName}"`;
            notification.style.position = "fixed";
            notification.style.bottom = "20px";
            notification.style.right = "20px";
            notification.style.backgroundColor = "#f97316";
            notification.style.color = "white";
            notification.style.padding = "10px 15px";
            notification.style.borderRadius = "4px";
            notification.style.zIndex = "9999";
            notification.style.opacity = "0";
            notification.style.transition = "opacity 0.3s ease";

            document.body.appendChild(notification);

            // Fade in
            setTimeout(() => {
                notification.style.opacity = "1";
            }, 100);

            // Remove after 3 seconds
            setTimeout(() => {
                notification.style.opacity = "0";
                setTimeout(() => {
                    document.body.removeChild(notification);
                }, 300);
            }, 3000);
        },
        [selectedNode, setNodes]
    );

    // Deploy workflow
    const handleDeployWorkflow = async () => {
        console.log("Deploy button clicked");
        console.log("Current nodes:", nodes);

        // Check for nodes
        if (nodes.length === 0) {
            alert("Please add at least one agent to your workflow before deploying.");
            return;
        }

        // Log router check
        const routerNode = nodes.find(
            (node) =>
                node.data.tags?.includes("router") || node.data.type === "router"
        );
        console.log("Router node found:", routerNode);

        if (!routerNode) {
            alert("Your workflow must include a Router Agent.");
            return;
        }

        setIsLoading(true);

        try {
            // Deploy the workflow - this is just a placeholder, replace with your actual API
            console.log("Deploying workflow:", { nodes, edges });
            const response = await WorkflowAPI.deployWorkflow(nodes, edges);
            console.log("Workflow deployed:", response);

            // Simulate API call
            await new Promise(resolve => setTimeout(resolve, 1000));

            // Switch to chat mode
            setIsChatMode(true);
            setShowConfigPanel(false);
            setChatMessages([
                {
                    id: Date.now(),
                    text: "Workflow deployed successfully. You can now ask questions.",
                    sender: "bot",
                },
            ]);
        } catch (error) {
            console.error("Error:", error);
            alert("Error: " + (error as Error).message);
        }
    };
    // Save workflow using modern API
    const handleSaveWorkflow = async () => {
        if (nodes.length === 0) {
            alert("Please add at least one agent to your workflow before saving.");
            return;
        }

        try {
            setIsLoading(true);

            // Import the createWorkflow function
            const { createWorkflow } = await import("../lib/actions");

            // Convert current nodes and edges to the modern workflow format
            const agentsConfig = nodes.map((node) => ({
                agent_type: node.data.type,
                agent_id: node.data.shortId || node.id,
                position: {
                    x: node.position.x,
                    y: node.position.y,
                },
                config: {
                    name: node.data.name,
                    prompt: node.data.prompt,
                    description: node.data.description,
                    tags: node.data.tags,
                },
            }));

            const connectionsConfig = edges.map((edge) => ({
                source_agent_id: edge.source,
                target_agent_id: edge.target,
                connection_type: "default",
                priority: 0,
            }));

            const workflowRequest = {
                name: workflowName,
                description: `Workflow with ${nodes.length} agents and ${edges.length} connections`,
                version: "1.0.0",
                configuration: {
                    agents: agentsConfig,
                    connections: connectionsConfig,
                },
                created_by: "user", // TODO: We might want to get this from auth context
                is_active: true,
                tags: ["frontend-created"],
            };

            console.log("Creating workflow with modern API:", workflowRequest);

            const result = await createWorkflow(workflowRequest);

            // Update the workflow ID if we got one back
            if (result.workflow_id) {
                workflowIdRef.current = result.workflow_id;
            }

            alert(
                `Workflow "${workflowName}" saved successfully! ID: ${result.workflow_id}`
            );
        } catch (error) {
            console.error("Error saving workflow:", error);
            alert("Error saving workflow. Please try again.");
        } finally {
            setIsLoading(false);
        }
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

    // Load a workflow from saved workflows
    const handleLoadWorkflow = (workflowDetails: any) => {
        try {
            // Set workflow metadata
            workflowIdRef.current = workflowDetails.workflow_id;
            setWorkflowName(workflowDetails.name);

            // Convert workflow agents to nodes
            const loadedNodes: Node[] = [];
            console.log("Workflow agents:", workflowDetails.workflow_agents);
            if (workflowDetails.workflow_agents) {
                workflowDetails.workflow_agents.forEach((workflowAgent: any) => {
                    const agent = workflowAgent.agent;
                    const nodeId = workflowAgent.node_id || workflowAgent.agent_id;

                    const newNode: Node = {
                        id: nodeId,
                        type: "agent",
                        position: {
                            x: workflowAgent.position_x || 100,
                            y: workflowAgent.position_y || 100,
                        },
                        data: {
                            id: nodeId,
                            shortId: agent.deployment_code || agent.agent_id,
                            type: agent.agent_type || "custom",
                            name: agent.name,
                            prompt: agent.system_prompt?.prompt || "",
                            tools: ["Tool 1", "Tool 2", "Tool 3"], // Default tools
                            tags: [agent.agent_type || "custom"],
                            onDelete: handleDeleteNode,
                            onConfigure: () => handleNodeSelect(newNode),
                        },
                    };

                    loadedNodes.push(newNode);
                });
            }

            // Convert workflow connections to edges
            const loadedEdges: Edge[] = [];
            if (workflowDetails.workflow_connections) {
                workflowDetails.workflow_connections.forEach(
                    (connection: any, index: number) => {
                        const newEdge: Edge = {
                            id: `edge-${index}`,
                            source: `node-${connection.source_agent_id}`,
                            target: `node-${connection.target_agent_id}`,
                            type: "default",
                            animated: true,
                        };

                        loadedEdges.push(newEdge);
                    }
                );
            }

            // Update state
            setNodes(loadedNodes);
            setEdges(loadedEdges);
            setIsChatMode(false);
            setChatMessages([]);
            setSelectedNode(null);
            setShowConfigPanel(false);

            console.log(`Loaded workflow: ${workflowDetails.name}`, {
                nodes: loadedNodes,
                edges: loadedEdges,
            });
        } catch (error) {
            console.error("Error loading workflow:", error);
            alert("Error loading workflow. Please try again.");
        }
    };

    // Handle saving the agent configuration with tools
    const handleSaveAgentConfig = (configData: any) => {
        if (!selectedNode) return;

        console.log("Saving agent configuration:", configData);

        // If tools are provided in the configuration data, update them
        const tools = configData.selectedTools || selectedNode.data.tools || [];

        // The name might have been updated through the inline editor
        const agentName = configData.agentName || selectedNode.data.name;

        // Update the node data with the new configuration
        setNodes((prevNodes) =>
            prevNodes.map((node) =>
                node.id === selectedNode.id
                    ? {
                        ...node,
                        data: {
                            ...node.data,
                            name: agentName, // Use the potentially updated name
                            tools, // Update tools from configuration
                            config: configData, // Store configuration in the node data
                        },
                    }
                    : node
            )
        );

        // Update selectedNode if it's the node we just edited
        if (selectedNode) {
            setSelectedNode((prev) =>
                prev
                    ? {
                        ...prev,
                        data: {
                            ...prev.data,
                            name: agentName,
                            tools,
                            config: configData,
                        },
                    }
                    : null
            );
        }

        // Show confirmation
        alert(`Configuration saved for ${agentName}`);
    };

    // If not yet mounted, return a loading placeholder
    if (!mounted) {
        return (
            <div className="agent-config-form loading">
                <div className="loading-message">Loading...</div>
            </div>
        );
    }

    return (
        <>
            <HeaderBottom
                workflowName={workflowName}
                isLoading={isLoading}
                handleDeployWorkflow={handleDeployWorkflow}
            />
            <ReactFlowProvider>
                <div className="agent-config-form" ref={reactFlowWrapper}>
                    {/* Designer Mode */}
                    {!isChatMode ? (
                        <>
                            {/* Designer Sidebar */}
                            <DesignerSidebar
                                workflowName={workflowName}
                                handleDragStart={handleDragStart}
                                handleDeployWorkflow={handleDeployWorkflow}
                                handleSaveWorkflow={handleSaveWorkflow}
                                isLoading={isLoading}
                                activeTab={activeTab}
                                setActiveTab={setActiveTab}
                                onCreateNewWorkflow={handleCreateNewWorkflow}
                                onLoadWorkflow={handleLoadWorkflow}
                            />

                            {/* Main Canvas */}
                            <div className="designer-content">
                                <DesignerCanvas
                                    nodes={nodes}
                                    edges={edges}
                                    setNodes={setNodes}
                                    setEdges={setEdges}
                                    onDrop={onDrop}
                                    onDragOver={onDragOver}
                                    onNodeSelect={handleNodeSelect}
                                    onInit={onInit}
                                />

                                {/* Configuration Panel - shown when a node is selected */}
                                {showConfigPanel && selectedNode && (
                                    <div className={`config-panel-container${!sidebarOpen ? ' shrinked' : ''}`}>
                                        <ConfigPanel
                                            agentName={selectedNode.data.name}
                                            agentType={selectedNode.data.type}
                                            description={selectedNode.data.description || ""}
                                            onEditPrompt={handleOpenPromptModal}
                                            onSave={handleSaveAgentConfig}
                                            onClose={() => setShowConfigPanel(false)}
                                            onNameChange={(newName) => handleAgentNameChange(selectedNode.id, newName)}
                                            toggleSidebar={() => setSidebarOpen(!sidebarOpen)}
                                            sidebarOpen={sidebarOpen}
                                        />
                                    </div>
                                )}
                            </div>

                            {/* Agent Configuration Modal */}
                            {selectedNode && (
                                <AgentConfigModal
                                    isOpen={isPromptModalOpen}
                                    nodeData={selectedNode ? {
                                        id: selectedNode.id,
                                        type: selectedNode.data.type,
                                        name: selectedNode.data.name,
                                        shortId: selectedNode.data.shortId,
                                        prompt: selectedNode.data.prompt,
                                        description: selectedNode.data.description,
                                        tags: selectedNode.data.tags
                                    } : null}
                                    onClose={handleClosePromptModal}
                                    onSave={handleSavePrompt}
                                />
                            )}
                        </>
                    ) : (
                        /* Chat Mode */
                        <>
                            {/* Chat Sidebar */}
                            <ChatSidebar
                                workflowName={workflowName}
                                workflowId={workflowIdRef.current}
                                onExitChat={() => setIsChatMode(false)}
                                onCreateNewWorkflow={handleCreateNewWorkflow}
                                isLoading={isLoading}
                            />

                            {/* Chat Interface */}
                            <div className="chat-content">
                                <ChatInterface
                                    onExitChat={() => setIsChatMode(false)}
                                    onCreateNewWorkflow={handleCreateNewWorkflow}
                                    workflowName={workflowName}
                                    workflowId={workflowIdRef.current}
                                />
                            </div>
                        </>
                    )}
                </div>
            </ReactFlowProvider>
        </>
    );
};

export default AgentConfigForm;

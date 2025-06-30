"use client";

import React, { useState, useCallback, useRef, useEffect } from "react";
// eslint-disable-next-line import/named -- Seems to be a problem with eslint
import { v4 as uuidv4 } from "uuid";
import { ReactFlowProvider, type ReactFlowInstance } from "react-flow-renderer";
import { type AgentConfigData, type AgentNodeData, type AgentResponse, type Edge, type Node, SavedWorkflow, type WorkflowAgent, type WorkflowCreateRequest, type WorkflowResponse } from "../lib/interfaces";
import { createWorkflow, deployWorkflowModern } from "../lib/actions";
import { isAgentResponse } from "../lib/discriminators";
import DesignerSidebar from "./agents/DesignerSidebar";
import DesignerCanvas from "./agents/DesignerCanvas";
import ConfigPanel from "./agents/ConfigPanel";
import AgentConfigModal from "./agents/AgentConfigModal";
import ChatSidebar from "./agents/ChatSidebar";
import ChatInterface from "./agents/ChatInterface";
// Import styles
import "./AgentConfigForm.scss";
import HeaderBottom from "./agents/HeaderBottom.tsx";

interface ChatMessage {
  id: number;
  text: string;
  sender: "user" | "bot";
}

function AgentConfigForm(): JSX.Element {
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
  const handleDeleteNode = useCallback((nodeId: string) => {
    setNodes(prevNodes => prevNodes.filter(node => node.id !== nodeId));

    // Also remove any connected edges
    setEdges(prevEdges => prevEdges.filter(edge =>
      edge.source !== nodeId && edge.target !== nodeId
    ));

    // If we just deleted the selected node, clear the selection
    if (selectedNode && selectedNode.id === nodeId) {
      setSelectedNode(null);
      setShowConfigPanel(false);
    }
  }, [selectedNode]);

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
        const agentData = JSON.parse(agentDataJson) as unknown;
        console.log("Dropped agent data:", agentData);
        if (!agentData || !isAgentResponse(agentData)) {
          throw new Error("Invalid agent data");
        }

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
            id: agentData.agent_id,
            shortId: agentData.id.toString(),
            type: agentData.agent_type ?? "custom",
            name: agentData.name,
            prompt: "", // Initialize with empty prompt
            tools: agentData.functions, // ChatCompletionToolParam array
            tags: [agentData.agent_type ?? "custom"], // Initialize tags with the type
            onDelete: handleDeleteNode,
            onConfigure: () => {
              handleNodeSelect({
                id: nodeId,
                type: "agent",
                position,
                data: {
                  id: agentData.agent_id,
                  shortId: agentData.id.toString(),
                  type: agentData.agent_type ?? "custom",
                  name: agentData.name,
                  prompt: agentData.system_prompt.prompt || "",
                  tools: agentData.functions, // ChatCompletionToolParam array
                  tags: [agentData.agent_type ?? "custom"],
                  onDelete: handleDeleteNode,
                  // eslint-disable-next-line @typescript-eslint/no-empty-function -- Will be overwritten
                  onConfigure: () => { }, // This will be overwritten
                  agent: agentData,
                  config: {
                    model: agentData.system_prompt.ai_model_name,
                    agentName: agentData.name,
                    deploymentType: "",
                    modelProvider: agentData.system_prompt.ai_model_provider,
                    outputFormat: "",
                    selectedTools: agentData.functions
                  }
                }
              });
            },
            agent: agentData,
            config: {
              model: agentData.system_prompt.ai_model_name,
              agentName: agentData.name,
              deploymentType: "",
              modelProvider: agentData.system_prompt.ai_model_provider,
              outputFormat: "",
              selectedTools: agentData.functions
            }
          },
        };

        setNodes(prevNodes => [...prevNodes, newNode]);

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
  const handleDragStart = useCallback((event: React.DragEvent<HTMLButtonElement>, agent: AgentResponse) => {
    // Ensure the agent has all required properties
    const dragData = agent;
    console.log("Dragging agent:", dragData);

    // Set the data transfer
    event.dataTransfer.setData("application/reactflow", JSON.stringify(dragData));
    event.dataTransfer.effectAllowed = "move";

    // Add visual feedback for dragging
    if (event.currentTarget.classList) {
      const element = event.currentTarget;
      element.classList.add('dragging');
      setTimeout(() => {
        if (element) {
          element.classList.remove('dragging');
        }
      }, 100);
    }
  }, []);

  // Handle node selection
  const handleNodeSelect = useCallback((node: Node | null) => {
    setSelectedNode(node);
    setShowConfigPanel(node !== null);
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
  const handleSavePrompt = useCallback((id: string, name: string, prompt: string, description: string, tags: string[] = []) => {
    // Update the node data with the new name, prompt, description and tags
    setNodes(prevNodes => prevNodes.map(node =>
      node.id === id
        ? {
          ...node,
          data: {
            ...node.data,
            name,
            prompt,
            description,
            tags
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
          description,
          tags
        }
      } : null);
    }
  }, [selectedNode]);

  // Handle agent name change
  const handleAgentNameChange = useCallback((nodeId: string, newName: string) => {
    if (newName.trim() === '') return; // Don't allow empty names

    // Update the node data with the new name
    setNodes(prevNodes => prevNodes.map(node =>
      node.id === nodeId
        ? {
          ...node,
          data: {
            ...node.data,
            name: newName,
            // Make sure onDelete and onConfigure are maintained
            onDelete: node.data.onDelete,
            onConfigure: node.data.onConfigure
          }
        }
        : node
    ));

    // Also update selectedNode if it's the node we just edited
    if (selectedNode && selectedNode.id === nodeId) {
      setSelectedNode(prev => prev ? {
        ...prev,
        data: {
          ...prev.data,
          name: newName
        }
      } : null);
    }

    // Show a brief notification to confirm the name change (optional)
    const notification = document.createElement('div');
    notification.textContent = `Agent renamed to "${newName}"`;
    notification.style.position = 'fixed';
    notification.style.bottom = '20px';
    notification.style.right = '20px';
    notification.style.backgroundColor = '#f97316';
    notification.style.color = 'white';
    notification.style.padding = '10px 15px';
    notification.style.borderRadius = '4px';
    notification.style.zIndex = '9999';
    notification.style.opacity = '0';
    notification.style.transition = 'opacity 0.3s ease';

    document.body.appendChild(notification);

    // Fade in
    setTimeout(() => {
      notification.style.opacity = '1';
    }, 100);

    // Remove after 3 seconds
    setTimeout(() => {
      notification.style.opacity = '0';
      setTimeout(() => {
        document.body.removeChild(notification);
      }, 300);
    }, 3000);
  }, [selectedNode, setNodes]);

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
    const routerNode = nodes.find(node =>
      node.data.tags?.includes('router') ?? node.data.type === 'router'
    );
    console.log("Router node found:", routerNode);

    if (!routerNode) {
      alert("Your workflow must include a Router Agent.");
      return;
    }

    // If we get here, just try to switch to chat mode directly
    try {
      const res = await deployWorkflowModern(workflowIdRef.current, {
        deployment_name: "test-deployment",
        environment: "production",
        deployed_by: "test-user",
        runtime_config: {}
      });
      setIsChatMode(true);
      setShowConfigPanel(false);
      setChatMessages([{
        id: Date.now(),
        text: "Workflow deployed successfully. You can now ask questions.",
        sender: "bot"
      }]);
    } catch (error) {
      console.error("Error:", error);
      alert(`Error: ${(error as Error).message}`);
    }
  };
  // Save workflow
  const handleSaveWorkflow = () => {
    if (nodes.length === 0) {
      alert("Please add at least one agent to your workflow before saving.");
      return;
    }

    const workflow: WorkflowCreateRequest = {
      // workflowId: workflowIdRef.current,
      name: workflowName,
      configuration: {
        agents: nodes.map(node => ({
          agent_id: node.data.agent.agent_id,
          agent_type: node.data.agent.agent_type as string,
          prompt: node.data.prompt, // Include prompt in saved workflow
          tools: node.data.tools, // Include tools in saved workflow
          tags: node.data.tags, // Include tags in saved workflow
          position: node.position
        })),

        connections: edges.map(edge => ({
          source_agent_id: edge.source,
          target_agent_id: edge.target
        }))
      }
    };

    console.log("Saving workflow:", workflow);
    createWorkflow(workflow);
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

  // Load an existing workflow
  const handleLoadWorkflow = (workflowDetails: WorkflowResponse) => {
    try {
      // Set workflow metadata
      workflowIdRef.current = workflowDetails.workflow_id;
      setWorkflowName(workflowDetails.name);

      // Convert workflow agents to nodes
      const loadedNodes: Node[] = [];
      console.log("Workflow agents:", workflowDetails.workflow_agents);
      if (workflowDetails.workflow_agents) {
        workflowDetails.workflow_agents.forEach((workflowAgent: WorkflowAgent) => {
          const agent = workflowAgent.agent;
          const nodeId = workflowAgent.node_id || workflowAgent.agent_id;
          console.log("Dropped agent data:", agent);

          const newNode: Node = {
            id: nodeId,
            type: "agent",
            position: {
              x: workflowAgent.position_x ?? 100,
              y: workflowAgent.position_y ?? 100,
            },
            data: {
              id: nodeId,
              shortId: agent.deployment_code ?? agent.agent_id,
              type: agent.agent_type ?? "custom",
              name: agent.name,
              prompt: agent.system_prompt.prompt || "",
              tools: agent.functions ?? [], // Keep as ChatCompletionToolParam array
              tags: [agent.agent_type ?? "custom"],
              config: { model: agent.system_prompt.ai_model_name, agentName: agent.name, deploymentType: "", modelProvider: agent.system_prompt.ai_model_provider, outputFormat: "", selectedTools: agent.functions },
              onDelete: handleDeleteNode,
              onConfigure: () => { handleNodeSelect(newNode); },
              agent
            },
          };

          loadedNodes.push(newNode);
        });
      }

      // Convert workflow connections to edges
      const loadedEdges: Edge[] = [];
      if (workflowDetails.workflow_connections) {
        workflowDetails.workflow_connections.forEach(
          (connection, index: number) => {
            const newEdge: Edge = {
              id: `edge-${index.toString()}`,
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
  const handleSaveAgentConfig = (configData: AgentConfigData) => {
    if (!selectedNode) return;

    console.log("Saving agent configuration:", configData);

    // If tools are provided in the configuration data, update them
    const tools = configData.selectedTools || selectedNode.data.tools || [];

    // The name might have been updated through the inline editor
    const agentName = configData.agentName || selectedNode.data.name;

    // Update the node data with the new configuration
    setNodes(prevNodes => prevNodes.map(node =>
      node.id === selectedNode.id
        ? {
          ...node,
          data: {
            ...node.data,
            name: agentName, // Use the potentially updated name
            tools, // Update tools from configuration
            config: configData  // Store configuration in the node data
          }
        }
        : node
    ));

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
                handleCreateNewWorkflow={handleCreateNewWorkflow}
                handleLoadWorkflow={handleLoadWorkflow}
                isLoading={isLoading}
                activeTab={activeTab}
                setActiveTab={setActiveTab}
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
                {showConfigPanel && selectedNode ? <div className={`config-panel-container${!sidebarOpen ? ' shrinked' : ''}`}>
                  <ConfigPanel
                    agent={selectedNode.data}
                    agentConfig={selectedNode.data.config}
                    agentName={selectedNode.data.name}
                    agentType={selectedNode.data.type}
                    description={selectedNode.data.description ?? ""}
                    onEditPrompt={handleOpenPromptModal}
                    onSave={handleSaveAgentConfig}
                    onClose={() => { setShowConfigPanel(false); }}
                    onNameChange={(newName) => { handleAgentNameChange(selectedNode.id, newName); }}
                    toggleSidebar={() => { setSidebarOpen(!sidebarOpen); }}
                    sidebarOpen={sidebarOpen}
                    currentFunctions={selectedNode.data.tools ?? []}
                    onFunctionsChange={(functions) => {
                      // Update the node's tools when functions change
                      setNodes(nodes => nodes.map(node =>
                        node.id === selectedNode.id
                          ? { ...node, data: { ...node.data, tools: functions } }
                          : node
                      ));
                    }}
                  />
                </div> : null}
              </div>

              {/* Agent Configuration Modal */}
              {selectedNode ? <AgentConfigModal
                isOpen={isPromptModalOpen}
                nodeData={selectedNode ? {
                  id: selectedNode.id,
                  type: selectedNode.data.type,
                  name: selectedNode.data.name,
                  shortId: selectedNode.data.shortId,
                  prompt: selectedNode.data.prompt,
                  description: selectedNode.data.description,
                  tags: selectedNode.data.tags,
                  agent: selectedNode.data.agent
                } : null}
                onClose={handleClosePromptModal}
                onSave={handleSavePrompt}
              /> : null}
            </>
          ) : (
            /* Chat Mode */
            <>
              {/* Chat Sidebar */}
              <ChatSidebar
                workflowName={workflowName}
                workflowId={workflowIdRef.current}
                onExitChat={() => { setIsChatMode(false); }}
                onCreateNewWorkflow={handleCreateNewWorkflow}
                isLoading={isLoading}
              />

              {/* Chat Interface */}
              <div className="chat-content">
                <ChatInterface
                  onExitChat={() => { setIsChatMode(false); }}
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

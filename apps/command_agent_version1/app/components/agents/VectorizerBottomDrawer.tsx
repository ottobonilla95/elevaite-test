"use client";

import React, { useCallback, useState } from "react";
import ReactFlow, {
  Background,
  Controls,
  MiniMap,
  Handle,
  Position,
  type Node,
  type Edge,
  type Connection,
  addEdge,
  type NodeChange,
  type EdgeChange,
  ReactFlowProvider,
} from "react-flow-renderer";
import { X, ChevronDown, ChevronUp } from "lucide-react";
import "./VectorizerBottomDrawer.scss";

export type VectorizationStepType =
  | "load"
  | "parse"
  | "chunk"
  | "embed"
  | "store"
  | "query";

export interface VectorizationStepData {
  id: string;
  type: VectorizationStepType;
  name: string;
  description: string;
  config?: Record<string, unknown>;
  onDelete: (id: string) => void;
}

const getStepIcon = (stepType: VectorizationStepType): string => {
  switch (stepType) {
    case "load":
      return "📁";
    case "parse":
      return "📄";
    case "chunk":
      return "✂️";
    case "embed":
      return "🔢";
    case "store":
      return "💾";
    case "query":
      return "🔍";
    default:
      return "⚙️";
  }
};

function VectorizationStepNode({
  id,
  data,
}: {
  id: string;
  data: VectorizationStepData;
}): JSX.Element {
  const { type, name, onDelete } = data;

  return (
    <div className="vectorization-step-node border-2 rounded-lg p-3 min-w-[160px] relative">
      {/* Input Handle */}
      <Handle
        type="target"
        position={Position.Left}
        className="w-3 h-3 bg-brand-primary border-2 border-white"
        id={`${id}-input`}
      />

      {/* Horizontal layout like main canvas agents */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="text-lg">{getStepIcon(type)}</span>
          <span className="font-medium text-sm">{name}</span>
        </div>

        {/* Delete button */}
        <button
          onClick={(e) => {
            e.stopPropagation();
            onDelete(id);
          }}
          className="text-gray-400 hover:text-red-500 transition-colors"
          type="button"
        >
          <X size={14} />
        </button>
      </div>

      {/* Output Handle */}
      <Handle
        type="source"
        position={Position.Right}
        className="w-3 h-3 bg-brand-primary border-2 border-white"
        id={`${id}-output`}
      />
    </div>
  );
}

const nodeTypes = {
  vectorizationStep: VectorizationStepNode,
};

interface VectorizerBottomDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  agentName: string;
  onMinimizedChange?: (minimized: boolean) => void;
  nodes: Node<VectorizationStepData>[];
  edges: Edge[];
  setNodes: React.Dispatch<React.SetStateAction<Node<VectorizationStepData>[]>>;
  setEdges: React.Dispatch<React.SetStateAction<Edge[]>>;
}

export default function VectorizerBottomDrawer({
  isOpen,
  onClose,
  agentName,
  onMinimizedChange,
  nodes,
  edges,
  setNodes,
  setEdges,
}: VectorizerBottomDrawerProps): JSX.Element | null {
  const [isMinimized, setIsMinimized] = useState(false);

  const availableSteps: {
    type: VectorizationStepType;
    name: string;
    description: string;
  }[] = [
    {
      type: "load",
      name: "Load Data",
      description: "Load documents from various sources",
    },
    {
      type: "parse",
      name: "Parse",
      description: "Extract text from documents",
    },
    {
      type: "chunk",
      name: "Chunk",
      description: "Split text into manageable chunks",
    },
    { type: "embed", name: "Embed", description: "Generate vector embeddings" },
    { type: "store", name: "Store", description: "Save vectors to database" },
    {
      type: "query",
      name: "Query",
      description: "Search and retrieve vectors",
    },
  ];

  const onNodesChange = useCallback((changes: NodeChange[]) => {
    setNodes((nds) => {
      const newNodes = [...nds];
      changes.forEach((change) => {
        if (
          change.type === "position" &&
          "position" in change &&
          change.position
        ) {
          const nodeIndex = newNodes.findIndex((n) => n.id === change.id);
          if (nodeIndex !== -1) {
            newNodes[nodeIndex] = {
              ...newNodes[nodeIndex],
              position: change.position,
            };
          }
        } else if (change.type === "remove" && "id" in change) {
          return newNodes.filter((n) => n.id !== change.id);
        }
      });
      return newNodes;
    });
  }, []);

  const onEdgesChange = useCallback((changes: EdgeChange[]) => {
    setEdges((eds) => {
      let newEdges = [...eds];
      changes.forEach((change) => {
        if (change.type === "remove" && "id" in change) {
          newEdges = newEdges.filter((e) => e.id !== change.id);
        }
      });
      return newEdges;
    });
  }, []);

  const onConnect = useCallback((params: Connection) => {
    const newEdge = {
      ...params,
      id: `e-${params.source ?? "unknown"}-${params.target ?? "unknown"}-${Date.now().toString()}`,
      type: "smoothstep",
      animated: true,
      style: { stroke: "#FF681F", strokeWidth: 2 },
    };
    setEdges((eds) => addEdge(newEdge, eds));
  }, []);

  const handleDeleteStep = useCallback((nodeId: string) => {
    setNodes((nds) => nds.filter((node) => node.id !== nodeId));
    setEdges((eds) =>
      eds.filter((edge) => edge.source !== nodeId && edge.target !== nodeId)
    );
  }, []);

  const onDrop = useCallback(
    (event: React.DragEvent) => {
      event.preventDefault();

      const reactFlowBounds = event.currentTarget.getBoundingClientRect();
      const data = event.dataTransfer.getData("application/reactflow");

      if (!data) return;

      try {
        const stepData = JSON.parse(data) as {
          type: VectorizationStepType;
          name: string;
          description: string;
        };
        const position = {
          x: event.clientX - reactFlowBounds.left,
          y: event.clientY - reactFlowBounds.top,
        };

        const nodeId = `${stepData.type}-${Date.now().toString()}`;
        const newNode: Node<VectorizationStepData> = {
          id: nodeId,
          type: "vectorizationStep",
          position,
          data: {
            id: nodeId,
            type: stepData.type,
            name: stepData.name,
            description: stepData.description,
            onDelete: handleDeleteStep,
          },
        };

        setNodes((nds) => [...nds, newNode]);
      } catch {
        // Ignore invalid drop data
      }
    },
    [handleDeleteStep]
  );

  const onDragOver = useCallback((event: React.DragEvent) => {
    event.preventDefault();
    event.dataTransfer.dropEffect = "move";
  }, []);

  if (!isOpen) return null;

  return (
    <div
      className={`vectorizer-bottom-drawer ${isMinimized ? "minimized" : ""}`}
    >
      {/* Drawer Header */}
      <div className="drawer-header">
        <div className="flex items-center gap-3">
          <span className="text-lg">🔢</span>
          <h3 className="font-semibold text-gray-800">
            Vectorizer: {agentName}
          </h3>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => {
              const newMinimized = !isMinimized;
              setIsMinimized(newMinimized);
              onMinimizedChange?.(newMinimized);
            }}
            className="p-1 hover:bg-gray-100 rounded transition-colors"
            type="button"
          >
            {isMinimized ? <ChevronUp size={20} /> : <ChevronDown size={20} />}
          </button>
          <button
            onClick={onClose}
            className="p-1 hover:bg-gray-100 rounded transition-colors"
            type="button"
          >
            <X size={20} />
          </button>
        </div>
      </div>

      {/* Drawer Content */}
      {!isMinimized && (
        <div className="drawer-content">
          {/* Steps Sidebar */}
          <div className="steps-sidebar">
            <h4 className="text-sm font-medium text-gray-700 mb-3">
              Vectorization Steps
            </h4>
            <div className="steps-list">
              {availableSteps.map((step) => (
                <div
                  key={step.type}
                  draggable
                  onDragStart={(e) => {
                    e.dataTransfer.setData(
                      "application/reactflow",
                      JSON.stringify({
                        type: step.type,
                        name: step.name,
                        description: step.description,
                      })
                    );
                    e.dataTransfer.effectAllowed = "move";
                  }}
                  className="step-button"
                >
                  <span className="step-icon">{getStepIcon(step.type)}</span>
                  <div className="step-info">
                    <span className="step-name">{step.name}</span>
                    <span className="step-description">{step.description}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Vectorization Canvas */}
          <div className="vectorization-canvas">
            <ReactFlowProvider>
              <ReactFlow
                nodes={nodes}
                edges={edges}
                onNodesChange={onNodesChange}
                onEdgesChange={onEdgesChange}
                onConnect={onConnect}
                onDrop={onDrop}
                onDragOver={onDragOver}
                nodeTypes={nodeTypes}
                fitView
                attributionPosition="bottom-right"
                deleteKeyCode={["Backspace", "Delete"]}
                multiSelectionKeyCode={["Meta", "Ctrl"]}
                zoomOnScroll
                zoomOnPinch
                panOnScroll={false}
                panOnDrag
                selectNodesOnDrag
                nodesDraggable
                nodesConnectable
                elementsSelectable
                snapToGrid
                snapGrid={[15, 15]}
                onNodeClick={() => undefined} // Disable node clicking
                onNodeDoubleClick={() => undefined} // Disable double clicking
              >
                <Background color="#aaa" gap={16} />
                <Controls />
                <MiniMap />
              </ReactFlow>
            </ReactFlowProvider>
          </div>
        </div>
      )}
    </div>
  );
}

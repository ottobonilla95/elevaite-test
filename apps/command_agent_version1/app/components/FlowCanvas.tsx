// FlowCanvas.tsx - Improved with delete option for edge labels
"use client";

import React, { useCallback, useState, useEffect } from "react";
import ReactFlow, {
  Controls,
  Background,
  MiniMap,
  addEdge,
  MarkerType,
  Node,
  Edge,
  Connection,
  OnConnectStartParams,
  NodeChange,
  EdgeChange,
  ConnectionLineType,
  BackgroundVariant,
  ReactFlowInstance,
} from "reactflow";
import { X } from "lucide-react";
import AgentNode from "./AgentNode";

// Custom edge component with improved UI and delete option
const CustomEdge = ({
  id,
  sourceX,
  sourceY,
  targetX,
  targetY,
  data,
  style = {},
  markerEnd,
  source,
  target,
  sourcePosition,
  targetPosition,
}) => {
  // Create a curved path between source and target
  const edgePath = `M ${sourceX} ${sourceY} C ${sourceX} ${sourceY + 50} ${targetX} ${targetY - 50} ${targetX} ${targetY}`;

  // Calculate the center point of the edge for label positioning
  const centerX = (sourceX + targetX) / 2;
  const centerY = (sourceY + targetY) / 2;

  // Default to "Action" if not specified
  const actionType = data?.actionType || "Action";

  // Set color based on action type
  let bgColor = "#4CAF50"; // Default green for "Action"
  if (actionType === "Conditional") {
    bgColor = "#FF9800"; // Orange for "Conditional"
  } else if (actionType === "Notification") {
    bgColor = "#9C27B0"; // Purple for "Notification"
  } else if (actionType === "Delay") {
    bgColor = "#FF5722"; // Deep Orange for "Delay"
  }

  // Function to remove label (will be passed to edge click handler)
  const removeLabel = (event) => {
    event.stopPropagation();
    const customEvent = new CustomEvent("remove-edge-label", {
      detail: { id },
    });
    document.dispatchEvent(customEvent);
  };

  return (
    <>
      <path
        id={id}
        className="react-flow__edge-path"
        d={edgePath}
        strokeWidth={2}
        markerEnd={markerEnd}
        style={style}
      />
      <foreignObject
        width={110}
        height={28}
        x={centerX - 55}
        y={centerY - 14}
        className="edgebutton-foreignobject"
        requiredExtensions="http://www.w3.org/1999/xhtml"
      >
        <div
          style={{
            background: bgColor,
            color: "white",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            padding: "4px 8px",
            borderRadius: "4px",
            fontSize: "12px",
            fontWeight: 500,
            width: "fit-content",
            height: "100%",
            boxShadow: "0 2px 4px rgba(0,0,0,0.1)",
          }}
          className="nodrag nopan"
        >
          <span style={{ marginRight: "6px" }}>
            {actionType === "Action" ? "+ Action" : actionType}
          </span>
          <button
            onClick={removeLabel}
            style={{
              background: "rgba(255,255,255,0.2)",
              border: "none",
              borderRadius: "2px",
              width: "16px",
              height: "16px",
              padding: 0,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              cursor: "pointer",
              color: "white",
            }}
          >
            <X size={12} />
          </button>
        </div>
      </foreignObject>
    </>
  );
};

// Define node and edge types outside the component
const nodeTypes = {
  agent: AgentNode,
};

const edgeTypes = {
  custom: CustomEdge,
};

interface FlowCanvasProps {
  nodes: Node[];
  edges: Edge[];
  setNodes: React.Dispatch<React.SetStateAction<Node[]>>;
  setEdges: React.Dispatch<React.SetStateAction<Edge[]>>;
  onDrop: (event: React.DragEvent<HTMLDivElement>) => void;
  onDragOver: (event: React.DragEvent<HTMLDivElement>) => void;
  onNodeSelect: (node: Node | null) => void;
  onInit?: (instance: ReactFlowInstance) => void;
}

const FlowCanvas: React.FC<FlowCanvasProps> = ({
  nodes,
  edges,
  setNodes,
  setEdges,
  onDrop,
  onDragOver,
  onNodeSelect,
  onInit,
}) => {
  // State for tracking active connections and selections
  const [reactFlowInstance, setReactFlowInstance] =
    useState<ReactFlowInstance | null>(null);

  // Pass reactFlow instance to parent when ready
  useEffect(() => {
    if (reactFlowInstance && onInit) {
      onInit(reactFlowInstance);
    }
  }, [reactFlowInstance, onInit]);

  // Add event listener for edge label removal
  useEffect(() => {
    const handleRemoveEdgeLabel = (event) => {
      const { id } = event.detail;

      // Remove the action type data but keep the edge
      setEdges((prevEdges) =>
        prevEdges.map((edge) => {
          if (edge.id === id) {
            // Remove the action type by setting it to null
            return {
              ...edge,
              data: null,
            };
          }
          return edge;
        })
      );
    };

    document.addEventListener("remove-edge-label", handleRemoveEdgeLabel);

    return () => {
      document.removeEventListener("remove-edge-label", handleRemoveEdgeLabel);
    };
  }, [setEdges]);

  // Default edge options for better looking connections
  const defaultEdgeOptions = {
    animated: true,
    style: { stroke: "#3b82f6", strokeWidth: 2 },
    type: "custom", // Use custom edge type by default
    markerEnd: {
      type: MarkerType.ArrowClosed,
      color: "#3b82f6",
      width: 20,
      height: 20,
    },
    data: {
      actionType: "Action", // Default action type
    },
  };

  // Helper function for snap-to-grid
  const snapToGrid = (position, gridSize = 15) => {
    return {
      x: Math.round(position.x / gridSize) * gridSize,
      y: Math.round(position.y / gridSize) * gridSize,
    };
  };

  // Handle node changes (position, selection, etc.)
  const onNodesChange = useCallback(
    (changes: NodeChange[]) => {
      // Apply changes to nodes
      setNodes((nds) => {
        return changes.reduce(
          (acc, change) => {
            if (
              change.type === "position" &&
              "position" in change &&
              change.position
            ) {
              // Apply grid snapping to position changes
              const node = acc.find((n) => n.id === change.id);
              if (node) {
                node.position = snapToGrid(change.position);
              }
            } else if (change.type === "select" && "selected" in change) {
              // Apply selection changes
              const node = acc.find((n) => n.id === change.id);
              if (node) {
                node.selected = change.selected;
              }
            } else if (change.type === "remove" && "id" in change) {
              // Remove nodes
              return acc.filter((n) => n.id !== change.id);
            }
            return acc;
          },
          [...nds]
        );
      });
    },
    [setNodes]
  );

  // Handle edge changes
  const onEdgesChange = useCallback(
    (changes: EdgeChange[]) => {
      setEdges((eds) => {
        return changes.reduce(
          (acc, change) => {
            if (change.type === "remove" && "id" in change) {
              // Remove edges
              return acc.filter((e) => e.id !== change.id);
            }
            return acc;
          },
          [...eds]
        );
      });
    },
    [setEdges]
  );

  // Handle connecting nodes
  const onConnect = useCallback(
    (params: Connection) => {
      console.log("Creating connection:", params);

      // Create new connection with the action type
      const newEdge = {
        ...params,
        id: `e-${params.source}-${params.target}-${Date.now()}`,
        type: "custom", // Use custom edge
        animated: true,
        style: { stroke: "#3b82f6", strokeWidth: 2 },
        markerEnd: {
          type: MarkerType.ArrowClosed,
          color: "#3b82f6",
          width: 20,
          height: 20,
        },
        data: {
          actionType: "Action", // Default action type
        },
      };

      // Add the new edge
      setEdges((eds) => addEdge(newEdge, eds));
    },
    [setEdges]
  );

  // Handle clicking on a node
  const onNodeClick = useCallback(
    (event, node) => {
      event.stopPropagation(); // Prevent event bubbling
      if (onNodeSelect) {
        onNodeSelect(node);
      }
    },
    [onNodeSelect]
  );

  // Handle clicking on an edge to change action type
  const onEdgeClick = useCallback(
    (event, edge) => {
      // If the edge doesn't have a label, don't do anything
      if (!edge.data) return;

      // Cycle through action types
      const actionTypes = ["Action", "Conditional", "Notification", "Delay"];
      const currentType = edge.data?.actionType || "Action";
      const currentIndex = actionTypes.indexOf(currentType);
      const nextIndex = (currentIndex + 1) % actionTypes.length;
      const nextType = actionTypes[nextIndex];

      // Update the edge data
      setEdges((eds) =>
        eds.map((e) => {
          if (e.id === edge.id) {
            return {
              ...e,
              data: {
                ...e.data,
                actionType: nextType,
              },
            };
          }
          return e;
        })
      );
    },
    [setEdges]
  );

  // Handle flow initialization
  const onLoad = useCallback((instance) => {
    setReactFlowInstance(instance);
  }, []);

  return (
    <div
      className="reactflow-wrapper"
      style={{ width: "100%", height: "100%" }}
    >
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onConnect={onConnect}
        onNodeClick={onNodeClick}
        onEdgeClick={onEdgeClick}
        nodeTypes={nodeTypes}
        edgeTypes={edgeTypes}
        onInit={onLoad}
        fitView
        attributionPosition="bottom-right"
        onDrop={onDrop}
        onDragOver={onDragOver}
        defaultEdgeOptions={defaultEdgeOptions}
        connectionLineType={ConnectionLineType.SmoothStep}
        connectionLineStyle={{ stroke: "#3b82f6", strokeWidth: 2 }}
        snapToGrid={true}
        snapGrid={[15, 15]}
        nodesDraggable={true}
        nodesConnectable={true}
        elementsSelectable={true}
      >
        <Controls />
        <Background
          color="#aaa"
          gap={16}
          variant={BackgroundVariant.Dots}
          size={1}
        />
        <MiniMap
          nodeStrokeColor={(node) => {
            if (node.selected) return "#f97316";
            return "#555";
          }}
          nodeColor={(node) => {
            if (node.selected) return "#f97316";
            return "#fff";
          }}
          nodeBorderRadius={3}
        />
      </ReactFlow>
    </div>
  );
};

export default FlowCanvas;

// FlowCanvas.tsx - Enhanced for better connection handling
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
    NodePositionChange,
    NodeSelectionChange,
    EdgeChange,
    ConnectionLineType,
    BackgroundVariant,
    ReactFlowInstance
} from "react-flow-renderer";
import AgentNode from "./AgentNode";

// Node types
const nodeTypes = {
    agent: AgentNode,
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
    onInit
}) => {
    // State for connection line tracking
    const [connectionNodeId, setConnectionNodeId] = useState<string | null>(null);
    const [reactFlowInstance, setReactFlowInstance] = useState<ReactFlowInstance | null>(null);

    // Pass reactFlow instance to parent when ready
    useEffect(() => {
        if (reactFlowInstance && onInit) {
            onInit(reactFlowInstance);
        }
    }, [reactFlowInstance, onInit]);

    // Default edge options for better looking connections
    const defaultEdgeOptions = {
        animated: true,
        style: { stroke: '#3b82f6', strokeWidth: 2 },
        type: 'smoothstep', // Use smoothstep for cleaner connections
        markerEnd: {
            type: MarkerType.ArrowClosed,
            color: '#3b82f6',
            width: 20,
            height: 20,
        },
    };

    // Helper function for snap-to-grid
    const snapToGrid = (position: { x: number; y: number }, gridSize: number = 15) => {
        return {
            x: Math.round(position.x / gridSize) * gridSize,
            y: Math.round(position.y / gridSize) * gridSize,
        };
    };

    // Handle node changes with improved position tracking
    const onNodesChange = useCallback(
        (changes: NodeChange[]) => {
            // Process position changes with improved handling
            const positionChanges = changes.filter(change =>
                change.type === 'position' && 'position' in change
            ) as NodePositionChange[];

            const selectChanges = changes.filter(change =>
                change.type === 'select' && 'selected' in change
            ) as NodeSelectionChange[];

            // Apply position changes with grid snapping
            if (positionChanges.length > 0) {
                setNodes(nds =>
                    nds.map(node => {
                        const posChange = positionChanges.find(
                            c => c.id === node.id
                        );

                        if (posChange && posChange.position) {
                            return {
                                ...node,
                                position: snapToGrid(posChange.position),
                                style: {
                                    ...node.style,
                                    // Add subtle shadow for dragged nodes
                                    boxShadow: '0 4px 8px rgba(0, 0, 0, 0.1)'
                                }
                            };
                        }
                        return node;
                    })
                );
            }

            // Apply selection changes
            if (selectChanges.length > 0) {
                setNodes(nds =>
                    nds.map(node => {
                        const selectChange = selectChanges.find(
                            c => c.id === node.id
                        );

                        if (selectChange) {
                            return {
                                ...node,
                                selected: selectChange.selected,
                                // Highlight selected nodes
                                style: {
                                    ...node.style,
                                    boxShadow: selectChange.selected ? '0 0 10px #3b82f6' : undefined
                                }
                            };
                        }
                        return node;
                    })
                );
            }

            // Handle other changes
            const otherChanges = changes.filter(change =>
                change.type !== 'position' && change.type !== 'select'
            ) as EdgeChange[];

            if (otherChanges.length > 0) {
                // Let ReactFlow handle other types of changes
                setNodes(nds => {
                    const newNodes = [...nds];
                    for (const change of otherChanges) {
                        if (change.type === 'remove' && 'id' in change) {
                            const index = newNodes.findIndex(n => n.id === change.id);
                            if (index !== -1) {
                                newNodes.splice(index, 1);
                            }
                        }
                    }
                    return newNodes;
                });
            }
        },
        [setNodes]
    );

    // Handle edge changes
    const onEdgesChange = useCallback(
        (changes: EdgeChange[]) => {
            setEdges((eds) => {
                // Filter out removed edges
                return eds.filter((edge) => {
                    for (const change of changes) {
                        if (change.type === 'remove' && 'id' in change && change.id === edge.id) {
                            return false;
                        }
                    }
                    return true;
                });
            });
        },
        [setEdges]
    );

    // Handle connecting nodes with better edge styling
    const onConnect = useCallback(
        (params: Connection) => {
            // Check if connection already exists to prevent duplicates
            const connectionExists = edges.some(
                edge => edge.source === params.source && edge.target === params.target
            );

            if (connectionExists) {
                console.log("Connection already exists");
                return;
            }

            // Create new connection with standard styling
            const newEdge = {
                ...params,
                id: `e-${params.source}-${params.target}-${Date.now()}`,
                type: 'smoothstep', // Use smoothstep for cleaner connections
                animated: true,
                style: { stroke: '#3b82f6', strokeWidth: 2 },
                markerEnd: {
                    type: MarkerType.ArrowClosed,
                    color: '#3b82f6',
                    width: 20,
                    height: 20,
                }
            };

            // Add the new edge
            setEdges(eds => addEdge(newEdge, eds));

            // After connection, select the target node
            setTimeout(() => {
                const targetNode = nodes.find(node => node.id === params.target);
                if (targetNode && onNodeSelect) {
                    onNodeSelect(targetNode);
                }
            }, 50);
        },
        [edges, nodes, setEdges, onNodeSelect]
    );

    // Handle clicking on a node
    const onNodeClick = useCallback(
        (event: React.MouseEvent, node: Node) => {
            event.stopPropagation(); // Prevent event bubbling
            if (onNodeSelect) {
                onNodeSelect(node);
            }
        },
        [onNodeSelect]
    );

    // Handle clicking on the background (don't deselect)
    const onPaneClick = useCallback(() => {
        // We do nothing here to prevent deselection
        // The actual deselection will be handled by the close button
    }, []);

    // Handle connection start
    const onConnectStart = useCallback(
        (event: React.MouseEvent, params: OnConnectStartParams) => {
            setConnectionNodeId(params.nodeId || null);
        },
        []
    );

    // Handle connection end
    const onConnectEnd = useCallback(
        (event: MouseEvent) => {
            setConnectionNodeId(null);
        },
        []
    );

    // Handle flow initialization
    const onLoad = (instance: ReactFlowInstance) => {
        setReactFlowInstance(instance);
    };

    return (
        <div className="reactflow-wrapper" style={{ width: '100%', height: '100%' }}>
            <ReactFlow
                nodes={nodes}
                edges={edges}
                onNodesChange={onNodesChange}
                onEdgesChange={onEdgesChange}
                onConnect={onConnect}
                onConnectStart={onConnectStart}
                onConnectEnd={onConnectEnd}
                onNodeClick={onNodeClick}
                onPaneClick={onPaneClick}
                nodeTypes={nodeTypes}
                //onLoad={onLoad}
                onInit={onLoad}
                fitView
                attributionPosition="bottom-right"
                onDrop={onDrop}
                onDragOver={onDragOver}
                defaultEdgeOptions={defaultEdgeOptions}
                connectionLineType={ConnectionLineType.SmoothStep}
                connectionLineStyle={{ stroke: '#3b82f6', strokeWidth: 2 }}
                snapToGrid={true}
                snapGrid={[15, 15]}
                nodesDraggable={true}
                nodesConnectable={true}
                elementsSelectable={true}
                selectNodesOnDrag={false}
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
                        if (node.selected) return '#3b82f6';
                        return '#555';
                    }}
                    nodeColor={(node) => {
                        if (node.selected) return '#3b82f6';
                        return '#fff';
                    }}
                    nodeBorderRadius={3}
                />
            </ReactFlow>
        </div>
    );
};

export default FlowCanvas;








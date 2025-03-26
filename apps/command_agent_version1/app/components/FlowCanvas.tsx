// FlowCanvas.tsx - Position fix
"use client";

import React, { useCallback, useRef, useEffect, useState, useMemo } from "react";
import ReactFlow, {
    Controls,
    Background,
    useNodesState,
    useEdgesState,
    addEdge,
    MarkerType,
    Node,
    Edge,
    Connection,
    ReactFlowInstance,
    applyNodeChanges
} from "react-flow-renderer";
import AgentNode from "./AgentNode";

interface FlowCanvasProps {
    nodes: Node[];
    edges: Edge[];
    setNodes: React.Dispatch<React.SetStateAction<Node[]>>;
    setEdges: React.Dispatch<React.SetStateAction<Edge[]>>;
    onDrop: (event: React.DragEvent<HTMLDivElement>) => void;
    onDragOver: (event: React.DragEvent<HTMLDivElement>) => void;
}

// Define nodeTypes outside the component to prevent error
const createNodeTypes = (updateNodeData) => ({
    agent: (props) => <AgentNode {...props} updateNodeData={updateNodeData} />
});

const FlowCanvas: React.FC<FlowCanvasProps> = ({
    nodes: externalNodes,
    edges: externalEdges,
    setNodes: setExternalNodes,
    setEdges: setExternalEdges,
    onDrop,
    onDragOver
}) => {
    // Track if component is mounted
    const [mounted, setMounted] = useState(false);

    // Track if we're currently dragging to prevent sync issues
    const isDraggingRef = useRef(false);

    // Track if external nodes have changed
    const externalNodesRef = useRef(externalNodes);

    // ReactFlow instance
    const reactFlowInstance = useRef<ReactFlowInstance | null>(null);

    // Internal ReactFlow state
    const [nodes, setNodes, onNodesChange] = useNodesState<Node[]>([]);
    const [edges, setEdges, onEdgesChange] = useEdgesState<Edge[]>([]);

    // Function to update node data - will be passed to AgentNode component
    const updateNodeData = useCallback((nodeId: string, newData: { name?: string, prompt?: string }) => {
        console.log("Updating node data:", nodeId, newData);

        // Update the node in our internal state
        setNodes(prevNodes =>
            prevNodes.map(node =>
                node.id === nodeId
                    ? {
                        ...node,
                        data: {
                            ...node.data,
                            ...(newData.name && { name: newData.name }),
                            ...(newData.prompt !== undefined && { prompt: newData.prompt })
                        }
                    }
                    : node
            )
        );

        // Also update external nodes state
        setExternalNodes(prevNodes =>
            prevNodes.map(node =>
                node.id === nodeId
                    ? {
                        ...node,
                        data: {
                            ...node.data,
                            ...(newData.name && { name: newData.name }),
                            ...(newData.prompt !== undefined && { prompt: newData.prompt })
                        }
                    }
                    : node
            )
        );
    }, [setExternalNodes]);

    // Memoize node types to prevent unnecessary re-renders
    const nodeTypes = useMemo(() => createNodeTypes(updateNodeData), [updateNodeData]);

    // Default edge options
    const defaultEdgeOptions = useMemo(() => ({
        type: 'default',
        animated: true,
        style: { stroke: '#3b82f6', strokeWidth: 2 },
        markerEnd: {
            type: MarkerType.ArrowClosed,
            color: '#3b82f6',
        },
    }), []);

    // Initial setup after mount
    useEffect(() => {
        setMounted(true);
    }, []);

    // Update ref when external nodes change
    useEffect(() => {
        externalNodesRef.current = externalNodes;
    }, [externalNodes]);

    // Sync external nodes to internal state, but only when not dragging
    useEffect(() => {
        if (mounted && externalNodes && !isDraggingRef.current) {
            console.log("Syncing external nodes to internal state:", externalNodes);
            setNodes(externalNodes);
        }
    }, [externalNodes, mounted, setNodes]);

    // Sync external edges to internal state
    useEffect(() => {
        if (mounted && externalEdges) {
            setEdges(externalEdges);
        }
    }, [externalEdges, mounted, setEdges]);

    // Handle node changes (position, etc)
    const handleNodesChange = useCallback((changes) => {
        // Check if we're starting to drag
        const dragStart = changes.some(change =>
            change.type === 'position' && change.dragging === true
        );

        // Check if we're ending a drag
        const dragEnd = changes.some(change =>
            change.type === 'position' && change.dragging === false && isDraggingRef.current
        );

        // Update dragging state
        if (dragStart) {
            isDraggingRef.current = true;
        }

        // Apply changes to the internal state
        onNodesChange(changes);

        // If drag ended, update external state
        if (dragEnd) {
            requestAnimationFrame(() => {
                isDraggingRef.current = false;
                setExternalNodes(nodes);
            });
        }

        // For non-position changes, also update external state
        const hasNonPositionChanges = changes.some(change => change.type !== 'position');
        if (hasNonPositionChanges && !isDraggingRef.current) {
            setExternalNodes(nodes);
        }
    }, [nodes, onNodesChange, setExternalNodes]);

    // Handle edge changes
    const handleEdgesChange = useCallback((changes) => {
        // Apply changes to internal state
        onEdgesChange(changes);

        // Sync back to parent only when necessary
        const hasEdgeRemoval = changes.some(change => change.type === 'remove');
        if (hasEdgeRemoval) {
            // Use requestAnimationFrame to batch updates
            requestAnimationFrame(() => {
                setExternalEdges(edges);
            });
        }
    }, [edges, onEdgesChange, setExternalEdges]);

    // Handle connections between nodes
    const handleConnect = useCallback(
        (connection: Connection) => {
            if (!connection.source || !connection.target) {
                return;
            }

            const newEdge = {
                id: `e-${connection.source}-${connection.target}-${Date.now()}`,
                source: connection.source,
                target: connection.target,
                ...defaultEdgeOptions
            };

            // Update internal state
            const updatedEdges = addEdge(newEdge, edges);
            setEdges(updatedEdges);

            // Sync to parent
            setExternalEdges(updatedEdges);
        },
        [defaultEdgeOptions, edges, setEdges, setExternalEdges]
    );

    // When flow instance is ready
    const onInit = useCallback((instance: ReactFlowInstance) => {
        console.log("ReactFlow initialized");
        reactFlowInstance.current = instance;

        // Fit the view to make sure all nodes are visible
        setTimeout(() => {
            if (instance && instance.fitView) {
                instance.fitView({ padding: 0.2 });
            }
        }, 200);
    }, []);

    // Handle node drag stop specifically
    const onNodeDragStop = useCallback((event, node) => {
        // Update external nodes with the new position
        setExternalNodes(current =>
            current.map(n => n.id === node.id ? { ...n, position: node.position } : n)
        );
    }, [setExternalNodes]);

    // If not yet mounted, return a placeholder
    if (!mounted) {
        return <div className="w-full h-full bg-gray-50" />;
    }

    return (
        <div style={{ width: '100%', height: '100%', position: 'relative' }}>
            <ReactFlow
                nodes={nodes}
                edges={edges}
                onNodesChange={handleNodesChange}
                onEdgesChange={handleEdgesChange}
                onConnect={handleConnect}
                onInit={onInit}
                onNodeDragStop={onNodeDragStop}
                nodeTypes={nodeTypes}
                defaultEdgeOptions={defaultEdgeOptions}
                connectionLineStyle={{ stroke: '#3b82f6', strokeWidth: 2, strokeDasharray: '5,5' }}
                fitView
                fitViewOptions={{ padding: 0.2 }}
                minZoom={0.1}
                maxZoom={1.5}
                defaultZoom={0.8}
                onDrop={onDrop}
                onDragOver={onDragOver}
                proOptions={{ hideAttribution: true }}
                className="grid-pattern"
                connectionMode="loose"
                nodesDraggable={true}
                elementsSelectable={true}
                snapToGrid={false}
            >
                <Background color="#888" gap={20} />
                <Controls showInteractive={false} />
            </ReactFlow>
        </div>
    );
};

export default FlowCanvas;
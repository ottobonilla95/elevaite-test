"use client";

import React, { useCallback, useState, useEffect } from "react";
import ReactFlow, {
	Controls,
	MiniMap,
	addEdge,
	MarkerType,
	type Connection,
	type NodeChange,
	type EdgeChange,
	ConnectionLineType,
	type ReactFlowInstance
} from "react-flow-renderer";
import { type Edge, type Node } from "../../lib/interfaces";
import CustomEdge from "./CustomEdge";
import AgentNode from "./AgentNode";
import "./DesignerCanvas.scss";

// Define node and edge types
const nodeTypes = {
	agent: AgentNode,
};

const edgeTypes = {
	custom: CustomEdge,
};

interface DesignerCanvasProps {
	nodes: Node[];
	edges: Edge[];
	setNodes: React.Dispatch<React.SetStateAction<Node[]>>;
	setEdges: React.Dispatch<React.SetStateAction<Edge[]>>;
	onDrop: (event: React.DragEvent<HTMLDivElement>) => void;
	onDragOver: (event: React.DragEvent<HTMLDivElement>) => void;
	onNodeSelect: (node: Node | null) => void;
	onInit?: (instance: ReactFlowInstance) => void;
}

function DesignerCanvas({
	nodes,
	edges,
	setNodes,
	setEdges,
	onDrop,
	onDragOver,
	onNodeSelect,
	onInit
}: DesignerCanvasProps): JSX.Element {
	// State for tracking active connections
	const [reactFlowInstance, setReactFlowInstance] = useState<ReactFlowInstance | null>(null);

	// Pass reactFlow instance to parent when ready
	useEffect(() => {
		if (reactFlowInstance && onInit) {
			onInit(reactFlowInstance);
		}
	}, [reactFlowInstance, onInit]);

	interface RemoveEdgeLabelDetail {
		id: string;
		removeConnectionOnly?: boolean;
	}

	// Add event listener for edge label removal
	useEffect(() => {
		const handleRemoveEdgeLabel = (event: CustomEvent<RemoveEdgeLabelDetail>): void => {
			const { id } = event.detail;

			// Update the edges array - keep the connection but remove the data/label
			setEdges(prevEdges =>
				prevEdges.map(edge => {
					if (edge.id === id) {
						// Keep the edge but remove the data that contains the label info
						return {
							...edge,
							data: undefined // This removes the label while keeping the connection
						};
					}
					return edge;
				})
			);
		};

		// Add event listener
		document.addEventListener('remove-edge-label', handleRemoveEdgeLabel as EventListener);

		// Clean up on unmount
		return () => {
			document.removeEventListener('remove-edge-label', handleRemoveEdgeLabel as EventListener);
		};
	}, [setEdges]);

	// Default edge options
	const defaultEdgeOptions = {
		animated: true,
		style: { stroke: '#3b82f6', strokeWidth: 2 },
		type: 'custom', // Use custom edge type by default
		markerEnd: {
			type: MarkerType.ArrowClosed,
			color: '#3b82f6',
			width: 20,
			height: 20,
		},
		data: {
			actionType: "Action" // Default action type
		}
	};

	// Helper function for snap-to-grid
	const snapToGrid = (position: { x: number; y: number }, gridSize = 15): { x: number; y: number } => {
		return {
			x: Math.round(position.x / gridSize) * gridSize,
			y: Math.round(position.y / gridSize) * gridSize,
		};
	};

	// Handle node changes (position, selection, etc.)
	const onNodesChange = useCallback(
		(changes: NodeChange[]) => {
			// Apply changes to nodes
			setNodes(nds => {
				const newNodes = [...nds];
				changes.forEach(change => {
					if (change.type === 'position' && 'position' in change && change.position) {
						// Apply grid snapping to position changes
						const nodeIndex = newNodes.findIndex(n => n.id === change.id);
						if (nodeIndex !== -1) {
							newNodes[nodeIndex] = {
								...newNodes[nodeIndex],
								position: snapToGrid(change.position)
							};
						}
					} else if (change.type === 'select' && 'selected' in change) {
						// Apply selection changes
						const nodeIndex = newNodes.findIndex(n => n.id === change.id);
						if (nodeIndex !== -1) {
							newNodes[nodeIndex] = {
								...newNodes[nodeIndex],
								selected: change.selected
							};
						}
					} else if (change.type === 'remove' && 'id' in change) {
						// Remove nodes
						const nodeIndex = newNodes.findIndex(n => n.id === change.id);
						if (nodeIndex !== -1) {
							newNodes.splice(nodeIndex, 1);
						}
					}
				});
				return newNodes;
			});
		},
		[setNodes]
	);

	// Debug: Monitor edge data changes
	useEffect(() => {
		console.log("Current edges with data:", edges.map(edge => ({
			id: edge.id,
			source: edge.source,
			target: edge.target,
			actionType: edge.data?.actionType,
			type: edge.type,
			fullData: edge.data
		})));
	}, [edges]);

	// Handle edge changes
	const onEdgesChange = useCallback(
		(changes: EdgeChange[]) => {
			setEdges(eds => {
				const newEdges = [...eds];
				changes.forEach(change => {
					if (change.type === 'remove' && 'id' in change) {
						// Remove edges
						const edgeIndex = newEdges.findIndex(e => e.id === change.id);
						if (edgeIndex !== -1) {
							newEdges.splice(edgeIndex, 1);
						}
					}
				});
				return newEdges;
			});
		},
		[setEdges]
	);

	// Handle connecting nodes
	const onConnect = useCallback(
		(params: Connection) => {
			// Create new connection with the action type
			const newEdge = {
				...params,
				id: `e-${params.source}-${params.target}-${Date.now()}`,
				type: 'custom', // Use custom edge
				animated: true,
				style: { stroke: '#3b82f6', strokeWidth: 2 },
				markerEnd: {
					type: MarkerType.ArrowClosed,
					color: '#3b82f6',
					width: 20,
					height: 20,
				},
				data: {
					actionType: "Action" // Default action type
				}
			};

			// Add the new edge
			setEdges(eds => addEdge(newEdge, eds));
		},
		[setEdges]
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

	// Handle right-clicking on an edge for context menu
	const onEdgeContextMenu = useCallback(
		(event: React.MouseEvent, edge: Edge): void => {
			event.preventDefault();

			// If edge has no label, show "Add Label" option
			if (!edge.data?.actionType) {
				// You could implement a context menu here
				// For now, just add the label directly
				setEdges(eds =>
					eds.map(e => {
						if (e.id === edge.id) {
							return {
								...e,
								data: {
									...e.data,
									actionType: "Action"
								}
							};
						}
						return e;
					})
				);
			}
		},
		[setEdges]
	);

	// Handle clicking on an edge to change action type or add label
	const onEdgeClick = useCallback(
		(_event: React.MouseEvent, edge: Edge): void => {
			// If the edge doesn't have data or actionType, add a label
			if (!edge.data?.actionType) {
				setEdges(eds =>
					eds.map(e => {
						if (e.id === edge.id) {
							return {
								...e,
								data: {
									...e.data,
									actionType: "Action" // Default to "Action" when adding a label
								}
							};
						}
						return e;
					})
				);
				return;
			}

			// Cycle through action types for labeled edges
			const actionTypes = ["Action", "Conditional", "Notification", "Delay"] as const;
			const currentType = edge.data.actionType;

			// Handle "None" case by starting from "Action"
			if (currentType === "None") {
				setEdges(eds =>
					eds.map(e => {
						if (e.id === edge.id) {
							return {
								...e,
								data: {
									...e.data,
									actionType: "Action"
								}
							};
						}
						return e;
					})
				);
				return;
			}

			const currentIndex = actionTypes.indexOf(currentType);
			const nextIndex = (currentIndex + 1) % actionTypes.length;
			const nextType = actionTypes[nextIndex];

			// Update the edge data
			setEdges(eds =>
				eds.map(e => {
					if (e.id === edge.id) {
						return {
							...e,
							data: {
								...e.data,
								actionType: nextType
							}
						};
					}
					return e;
				})
			);
		},
		[setEdges]
	);

	// Handle flow initialization
	const onLoad = useCallback((instance: ReactFlowInstance) => {
		setReactFlowInstance(instance);
	}, []);

	return (
		<div className="designer-canvas">
			<ReactFlow
				nodes={nodes}
				edges={edges}
				onNodesChange={onNodesChange}
				onEdgesChange={onEdgesChange}
				onConnect={onConnect}
				onNodeClick={onNodeClick}
				onEdgeClick={onEdgeClick}
				onEdgeContextMenu={onEdgeContextMenu}
				nodeTypes={nodeTypes}
				edgeTypes={edgeTypes}
				onInit={onLoad}
				fitView
				attributionPosition="bottom-right"
				onDrop={onDrop}
				onDragOver={onDragOver}
				defaultEdgeOptions={defaultEdgeOptions}
				connectionLineType={ConnectionLineType.SmoothStep}
				connectionLineStyle={{ stroke: '#3b82f6', strokeWidth: 2 }}
				snapToGrid
				snapGrid={[15, 15]}
				nodesDraggable
				nodesConnectable
				elementsSelectable
			>
				<Controls />
				{/*  <Background
                    color="#aaa"
                    gap={16}
                    variant={BackgroundVariant.Dots}
                    size={1}
                /> */}
				<MiniMap
					nodeStrokeColor={(node) => {
						if (node.selected) return '#f97316';
						return '#555';
					}}
					nodeColor={(node) => {
						if (node.selected) return '#f97316';
						return '#fff';
					}}
					nodeBorderRadius={3}
				/>
			</ReactFlow>
		</div>
	);
};

export default DesignerCanvas;
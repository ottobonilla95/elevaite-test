"use client";
import {
	addEdge, applyEdgeChanges, applyNodeChanges,
	type Connection, type Edge, type EdgeChange, type Node, type NodeChange, type OnConnect,
	type OnEdgesChange, type OnNodesChange, type ReactFlowInstance, type XYPosition,
} from "@xyflow/react";
import { createContext, useCallback, useContext, useMemo, useRef, useState } from "react";
import { v4 as uuidv4 } from "uuid";
import { type ExecutionResults, type ExecutionStatus } from "../actions/executions";
import { executeWorkflow, saveWorkflow, updateWorkflow } from "../actions/workflows";
import { canvasToWorkflowConfig } from "../api/mappers/canvasToWorkflow";
import { CanvasNodeType } from "../enums";
import { useCanvasHistory } from "../hooks/useCanvasHistory";
import { useExecutionPolling } from "../hooks/useExecutionPolling";
import { type SidePanelOption, type SidePanelPayload } from "../interfaces";
import { OutputTextKeys } from "../model/innerEnums";
import { OutputNodeId } from "../model/uiEnums";
import { type ExecutionResultsResponse, type WorkflowConfig } from "../model/workflowSteps";
import { setItemDetail } from "../utilities/config";




// STRUCTURE

export interface CanvasContextStructure {
	setReactFlowInstance: (instance: ReactFlowInstance | null) => void;
	nodes: Node[];
	edges: Edge[];
	selectedNodeId: string | null;
	viewport: {
		x: number;
		y: number;
		zoom: number;
	};
	handleNodeChange: OnNodesChange;
	handleEdgesChange: OnEdgesChange;
	handleConnection: OnConnect;
	setSelectedNodeId: (nodeId: string | null) => void;
	setViewport: (next: { x: number; y: number; zoom: number }) => void;
	resetCanvas: (nextNodes?: Node[], nextEdges?: Edge[]) => void;
	addNodeAtPosition: (payload: SidePanelPayload, position?: XYPosition) => void;
	updateNodeData: (nodeId: string, updater: (data: SidePanelPayload) => SidePanelPayload) => void;
	nodeViewState: "simple" | "expanded" | "mixed";
	nodeViewChange: (nodeId?: string, intent?: "min" | "max") => void;
	deleteNodeById: (nodeId: string) => void;

	// Workflow tracking
	workflowId: string | null;
	workflowName: string;
	setWorkflowId: (id: string | null) => void;
	setWorkflowName: (name: string) => void;

	// Execution
	executionId: string | null;
	executionStatus: ExecutionStatus | null;
	runPreview: () => Promise<void>;

	// History
	undo: () => void;
	redo: () => void;
	canUndo: boolean;
	canRedo: boolean;
}

export const CanvasContext = createContext<CanvasContextStructure>({
	setReactFlowInstance: () => { /** */ },
	nodes: [],
	edges: [],
	selectedNodeId: null,
	viewport: { x: 0, y: 0, zoom: 1 },
	handleNodeChange: () => { /** */ },
	handleEdgesChange: () => { /** */ },
	handleConnection: () => { /** */ },
	setSelectedNodeId: () => { /** */ },
	setViewport: () => { /** */ },
	resetCanvas: () => { /** */ },
	addNodeAtPosition: () => { /** */ },
	updateNodeData: () => { /** */ },
	nodeViewState: "mixed",
	nodeViewChange: () => { /** */ },
	deleteNodeById: () => { /** */ },

	// Workflow tracking
	workflowId: null,
	workflowName: "Untitled Workflow",
	setWorkflowId: () => { /** */ },
	setWorkflowName: () => { /** */ },

	// Execution
	executionId: null,
	executionStatus: null,
	runPreview: async () => { /** */ },

	// History
	undo: () => { /** */ },
	redo: () => { /** */ },
	canUndo: false,
	canRedo: false,
});






// PROVIDER

interface CanvasContextProviderProps {
	children: React.ReactNode;
}

export function CanvasContextProvider(props: CanvasContextProviderProps): React.ReactElement<any> {
	const TRACK_NODE_MOVEMENT = false;
	const TRACK_NODE_SELECTION = false;
	const TRACK_NODE_VIEW_CHANGES = false;
	const reactFlowInstanceRef = useRef<ReactFlowInstance | null>(null);
	const { snapshot, commit, undo, redo, canUndo, canRedo } = useCanvasHistory();
	const nodes = snapshot.nodes;
	const edges = snapshot.edges;
	const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
	const [viewport, setViewport] = useState<{ x: number; y: number; zoom: number }>({ x: 0, y: 0, zoom: 1 });
	const nodeViewState: "simple" | "expanded" | "mixed" = useMemo(() => getNodeViewState(nodes), [nodes]);

	const [workflowId, setWorkflowId] = useState<string | null>(null);
	const [workflowName, setWorkflowName] = useState<string>("Untitled Workflow");
	const [workflowExecutionId, setWorkflowExecutionId] = useState<string | null>(null);

	// Apply execution results to output nodes
	const applyExecutionResults = useCallback((status: ExecutionResults) => {
		const stepResults = status.step_results;
		console.log("📊 applyExecutionResults called");
		console.log("📊 step_results:", stepResults);
		console.log("📊 step_results keys:", stepResults ? Object.keys(stepResults) : "none");
		if (!stepResults) return;

		commit((prev) => {
			// Build a map of target node id -> source node id from edges
			const incomingEdges = new Map<string, string>();
			for (const edge of prev.edges) {
				incomingEdges.set(edge.target, edge.source);
			}
			console.log("📊 edges (raw):", prev.edges.map(e => ({ id: e.id, source: e.source, target: e.target })));
			console.log("📊 incomingEdges map:", Object.fromEntries(incomingEdges));
			console.log("📊 all node IDs:", prev.nodes.map(n => n.id));

			return {
				...prev,
				nodes: prev.nodes.map((node) => {
					const payload = node.data as SidePanelPayload;
					// Only update output nodes
					const isOutputNode = Object.values(OutputNodeId).includes(payload.id as OutputNodeId);
					console.log("📊 node:", node.id, "payload.id:", payload.id, "isOutputNode:", isOutputNode);
					if (!isOutputNode) {
						return node;
					}

					// Get the output step's own result (output step now stores its own data)
					const outputStepResult = stepResults[node.id];
					console.log("📊 output node:", node.id, "outputStepResult:", outputStepResult);
					if (!outputStepResult) return node;

					// Output step structure: { step_id, label, format, data: {...}, success }
					// The "data" field contains the immediate dependency's output
					const outputData = outputStepResult.output_data;
					const dependencyData = outputData?.data;
					console.log("📊 outputData:", outputData, "dependencyData:", dependencyData);
					if (dependencyData === undefined) return node;

					// Extract text from the dependency's output
					let outputText: string;
					if (typeof dependencyData === "string") {
						outputText = dependencyData;
					} else if (typeof dependencyData === "object" && dependencyData !== null) {
						const obj = dependencyData as Record<string, unknown>;
						// Agent outputs use "response", other steps may use "result", "output", or "text"
						const extracted = obj.response ?? obj.result ?? obj.output ?? obj.text;
						console.log("📊 extracted from obj:", extracted);
						outputText = typeof extracted === "string" ? extracted : JSON.stringify(dependencyData, null, 2);
					} else {
						outputText = String(dependencyData);
					}
					console.log("📊 final outputText:", outputText);

					return {
						...node,
						data: setItemDetail(payload as SidePanelOption, OutputTextKeys.TEXT, outputText) as SidePanelPayload,
					};
				}),
			};
		});
	}, [commit]);

	// Execution polling - clears executionId when terminal status is reached
	const clearExecutionId = useCallback(() => { setWorkflowExecutionId(null); }, []);
	const handleExecutionTerminal = useCallback((status: ExecutionResults) => {
		// eslint-disable-next-line no-console -- WIP debugging
		console.log("🏁 Execution terminal:", status.status, status);
		applyExecutionResults(status);
	}, [applyExecutionResults]);
	const { executionStatus } = useExecutionPolling(workflowExecutionId, clearExecutionId, {
		intervalMs: 200,
		onTerminal: handleExecutionTerminal,
	});


	// Fetch workflows on mount
	// useEffect(() => {
	// 	async function fetchWorkflows() {
	// 		try {
	// 			const workflows = await listWorkflows();
	// 			console.log("📡 Workflows from backend:", workflows);
	// 		} catch (error) {
	// 			console.error("❌ Error fetching workflows:", error);
	// 		}
	// 	}

	// 	fetchWorkflows();
	// }, []);


	// Callback handlers
	const callbackHandleNodeChange: OnNodesChange = useCallback(handleNodeChange, [commit]);
	const callbackHandleEdgesChange: OnEdgesChange = useCallback(handleEdgesChange, [commit]);
	const callbackHandleConnection: OnConnect = useCallback(handleConnection, [commit]);

	// Callback functions

	function handleNodeChange(changes: NodeChange[]): void {
		const relevantChanges = filterNodeChangesForHistory(changes);
		if (relevantChanges.length === 0) return;

		const { hasMovement, hasSelection, hasOther } = classifyNodeChanges(relevantChanges);

		// Decide if this should be a history step
		const addToHistory =
			hasOther ||
			// eslint-disable-next-line @typescript-eslint/no-unnecessary-condition -- this is a flag
			(TRACK_NODE_MOVEMENT && hasMovement) ||
			// eslint-disable-next-line @typescript-eslint/no-unnecessary-condition -- this is a flag
			(TRACK_NODE_SELECTION && hasSelection);

		commit(
			(prev) => {
				const updatedNodes = applyNodeChanges(relevantChanges, prev.nodes);

				// Update selectedNodeId when selection changes
				if (hasSelection) {
					const selected = updatedNodes.find(n => n.selected);
					setSelectedNodeId(selected?.id ?? null);
				}

				return { ...prev, nodes: updatedNodes };
			},
			{ addToHistory },
		);
	}


	function handleEdgesChange(changes: EdgeChange[]): void {
		commit((prev) => ({ ...prev, edges: applyEdgeChanges(changes, prev.edges) }));
	}

	function handleConnection(connection: Connection): void {
		console.log("handleConnection called with:", connection);
		console.log("selected Node", selectedNodeId);
		commit((prev) => ({ ...prev, edges: addEdge(connection, prev.edges) }));
	}


	// Other Functions

	function setReactFlowInstance(instance: ReactFlowInstance | null): void {
		reactFlowInstanceRef.current = instance;
	}


	function resetCanvas(resetNodes?: Node[], resetEdges?: Edge[]): void {
		commit(() => ({
			nodes: resetNodes ?? [],
			edges: resetEdges ?? [],
		}));

		setSelectedNodeId(null);
		// setViewport({ x: 0, y: 0, zoom: 1 });
	}


	function addNodeAtPosition(payload: SidePanelPayload, position?: XYPosition): void {
		let flowPosition: XYPosition = { x: 0, y: 0 };

		if (reactFlowInstanceRef.current) {
			let clientPosition: XYPosition;

			if (position) {
				clientPosition = position;
			} else {
				const canvasElement = document.querySelector(".main-canvas-container");

				if (canvasElement) {
					const rect = canvasElement.getBoundingClientRect();
					clientPosition = {
						x: rect.left + rect.width / 2,
						y: rect.top + rect.height / 2,
					};
				} else {
					clientPosition = { x: 0, y: 0 };
				}
			}

			flowPosition = reactFlowInstanceRef.current.screenToFlowPosition(clientPosition);
		}

		// Small jitter to avoid perfect stacking on new items
		if (!position) {
			const jitterRange = 40; // pixels
			const offsetX: number = (Math.random() - 0.5) * jitterRange;
			const offsetY: number = (Math.random() - 0.5) * jitterRange;

			flowPosition = {
				x: flowPosition.x + offsetX,
				y: flowPosition.y + offsetY,
			};
		}

		const newNode: Node = {
			id: `node_${uuidv4()}`,
			type: CanvasNodeType.COMMAND,
			position: flowPosition,
			data: {
				...payload,
				nodeDetails: {
					...(payload.nodeDetails ?? {}),
					isExpanded: true,
				},
			},
		};

		commit((prev) => ({ ...prev, nodes: [...prev.nodes, newNode] }));
	}



	function nodeViewChange(nodeId?: string, intent?: "min" | "max"): void {
		commit((prev) => {
			const target = intent !== undefined ? intent === "max" : undefined;

			const updatedNodes = prev.nodes.map((node) => {
				const payload = node.data as SidePanelPayload;
				const currentExpanded = Boolean(payload.nodeDetails?.isExpanded);
				let nextExpanded = currentExpanded;

				if (nodeId && node.id === nodeId) {
					if (target !== undefined) {
						nextExpanded = target;
					} else {
						nextExpanded = !currentExpanded;
					}
				} else if (!nodeId && target !== undefined) {
					nextExpanded = target;
				} else {
					return node;
				}

				if (nextExpanded === currentExpanded) return node;

				return {
					...node,
					data: {
						...payload,
						nodeDetails: {
							...(payload.nodeDetails ?? {}),
							isExpanded: nextExpanded,
						},
					},
				};
			});

			return {
				...prev,
				nodes: updatedNodes,
			};
		}, { addToHistory: TRACK_NODE_VIEW_CHANGES });
	}


	function getNodeViewState(currentNodes: Node[]): "simple" | "expanded" | "mixed" {
		if (currentNodes.length === 0) return "mixed";

		let allSimple = true;
		let allExpanded = true;

		for (const node of currentNodes) {
			const payload = node.data as SidePanelPayload;
			const isExpanded = Boolean(payload.nodeDetails?.isExpanded);

			if (isExpanded) { allSimple = false; }
			else { allExpanded = false; }
		}

		if (allSimple) return "simple";
		if (allExpanded) return "expanded";
		return "mixed";
	}

	function updateNodeData(nodeId: string, updater: (data: SidePanelPayload) => SidePanelPayload): void {
		commit((prev) => ({
			...prev,
			nodes: prev.nodes.map((node) => {
				if (node.id !== nodeId) return node;
				return {
					...node,
					data: updater(node.data as SidePanelPayload),
				};
			}),
		}));
	}

	function deleteNodeById(nodeId: string): void {
		if (selectedNodeId === nodeId) { setSelectedNodeId(null); }
		commit((prev) => {
			const filteredNodes = prev.nodes.filter((node) => node.id !== nodeId);
			const filteredEdges = prev.edges.filter(
				(edge) => edge.source !== nodeId && edge.target !== nodeId,
			);

			return {
				nodes: filteredNodes,
				edges: filteredEdges,
			};
		});
	}


	function filterNodeChangesForHistory(changes: NodeChange[]): NodeChange[] {
		return changes.filter((change) => change.type !== "add" && change.type !== "remove");
	}

	function classifyNodeChanges(changes: NodeChange[]): { hasMovement: boolean; hasSelection: boolean; hasOther: boolean; } {
		let hasMovement = false;
		let hasSelection = false;
		let hasOther = false;

		for (const change of changes) {
			if (change.type === "position" || change.type === "dimensions") {
				hasMovement = true;
			} else if (change.type === "select") {
				hasSelection = true;
			} else {
				hasOther = true;
			}
		}

		return { hasMovement, hasSelection, hasOther };
	}


	async function runPreview(): Promise<void> {
		console.log("🚀 Starting workflow preview...");

		try {
			// Convert canvas to workflow config
			const workflowConfig = canvasToWorkflowConfig(nodes, edges, {
				workflowId: workflowId ?? undefined,
				workflowName,
			});
			console.log("📋 Workflow config:", workflowConfig);

			let savedWorkflow: WorkflowConfig;

			// Save or update the workflow
			if (workflowId) {
				console.log("📝 Updating existing workflow:", workflowId);
				savedWorkflow = await updateWorkflow(workflowId, workflowConfig);
			} else {
				console.log("✨ Creating new workflow");
				savedWorkflow = await saveWorkflow(workflowConfig);
				// Store the new workflow ID in context
				if (savedWorkflow.id) {
					setWorkflowId(savedWorkflow.id);
				}
			}
			console.log("💾 Saved workflow:", savedWorkflow);

			// Execute the workflow
			const targetId = savedWorkflow.id ?? workflowId;
			if (!targetId) {
				throw new Error("No workflow ID available for execution");
			}

			// eslint-disable-next-line no-console -- WIP debugging
			console.log("▶️ Executing workflow:", targetId);
			const execution: ExecutionResultsResponse = await executeWorkflow(targetId, {});
			// eslint-disable-next-line no-console -- WIP debugging
			console.log("✅ Execution started:", execution);

			// Store the execution ID
			setWorkflowExecutionId(execution.id);

		} catch (error) {
			console.error("❌ Preview failed:", error);
		}
	}


	return (
		<CanvasContext.Provider
			value={{
				setReactFlowInstance,
				nodes,
				edges,
				selectedNodeId,
				viewport,
				handleNodeChange: callbackHandleNodeChange,
				handleEdgesChange: callbackHandleEdgesChange,
				handleConnection: callbackHandleConnection,
				setSelectedNodeId,
				setViewport,
				resetCanvas,
				addNodeAtPosition,
				updateNodeData,
				nodeViewState,
				nodeViewChange,
				deleteNodeById,
				workflowId,
				workflowName,
				setWorkflowId,
				setWorkflowName,
				executionId: workflowExecutionId,
				executionStatus,
				runPreview,
				undo,
				redo,
				canUndo,
				canRedo,
			}}
		>
			{props.children}
		</CanvasContext.Provider>
	);
}


export function useCanvas(): CanvasContextStructure {
	return useContext(CanvasContext);
}

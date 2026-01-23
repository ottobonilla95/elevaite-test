"use client";
import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { type BuiltInVariable, getBuiltInVariables } from "../actions/steps";
import { type ItemDetails, type ItemDetailsValue, type SidePanelPayload } from "../interfaces";
import { setItemDetails } from "../utilities/config";
import { useCanvas } from "./CanvasContext";




// STRUCTURE

export interface ConfigPanelContextStructure {
	// Node selection
	selectedNode: SidePanelPayload | null;
	setSelectedNode: (nodeId: string | null) => void;
	clearSelectedNode: () => void;
	
	// Panel visibility
	isConfigPanelOpen: boolean;
	openConfigPanel: (focus?: string) => void;
	closeConfigPanel: () => void;
	
	// Focus anchor
	focusAnchor: string | undefined;
	clearFocusAnchor: () => void;
	
	// Draft state management
	draft: ItemDetails;
	updateDraft: (key: string, value: ItemDetailsValue) => void;
	updateDraftMultiple: (updates: ItemDetails) => void;
	isDirty: boolean;
	saveChanges: () => void;
	discardChanges: () => void;

	// Label editing (for new nodes)
	draftLabel: string | null;
	setDraftLabel: (label: string) => void;
	isLabelEditable: boolean;

	// BuiltIn variables
	builtInVariables: BuiltInVariable[];
	builtInVariablesLoading: boolean;
}

export const ConfigPanelContext = createContext<ConfigPanelContextStructure>({
	selectedNode: null,
	setSelectedNode: () => { /** */ },
	clearSelectedNode: () => { /** */ },
	isConfigPanelOpen: false,
	openConfigPanel: () => { /** */ },
	closeConfigPanel: () => { /** */ },
	// Focus anchor
	focusAnchor: undefined,
	clearFocusAnchor: () => { /** */ },
	// Draft defaults
	draft: {},
	updateDraft: () => { /** */ },
	updateDraftMultiple: () => { /** */ },
	isDirty: false,
	saveChanges: () => { /** */ },
	discardChanges: () => { /** */ },
	// Label editing defaults
	draftLabel: null,
	setDraftLabel: () => { /** */ },
	isLabelEditable: false,
	// BuiltIn variables defaults
	builtInVariables: [],
	builtInVariablesLoading: false,
});









// PROVIDER

interface ConfigPanelContextProviderProps {
	children: React.ReactNode;
}

export function ConfigPanelContextProvider(props: ConfigPanelContextProviderProps): React.ReactElement<any> {
	const { children } = props;
	const canvasContext = useCanvas();
    const [isConfigPanelOpen, setIsConfigPanelOpen] = useState(false);
    const [focusAnchor, setFocusAnchor] = useState<string|undefined>();
	const [selectedNode, setSelectedNode] = useState<SidePanelPayload | null>(null);
	const [selectedNodeCanvasId, setSelectedNodeCanvasId] = useState<string | null>(null);
	const [draft, setDraft] = useState<ItemDetails>({});
	const [draftLabel, setDraftLabel] = useState<string | null>(null);
	const [builtInVariables, setBuiltInVariables] = useState<BuiltInVariable[]>([]);
	const [builtInVariablesLoading, setBuiltInVariablesLoading] = useState(false);
	
	const canvasSelectedNode = useMemo<SidePanelPayload | null>(() => {
		if (!canvasContext.selectedNodeId) return null;
		const node = canvasContext.nodes.find((n) => n.id === canvasContext.selectedNodeId);
		return (node?.data as SidePanelPayload | undefined) ?? null;
	}, [canvasContext.nodes, canvasContext.selectedNodeId]);

	
	useEffect(() => {
		void fetchBuiltInVariables();
	}, []);

	useEffect(() => {
		if (canvasSelectedNode) {
			setSelectedNode(canvasSelectedNode);
			setSelectedNodeCanvasId(canvasContext.selectedNodeId);
			setDraft({});
			setDraftLabel(null);
		}
	}, [canvasSelectedNode, canvasContext.selectedNodeId]);

	useEffect(() => {
		if (!isConfigPanelOpen || !selectedNodeCanvasId) return;
		const exists = canvasContext.nodes.some(n => n.id === selectedNodeCanvasId);
		if (!exists) {
			closeConfigPanel();
			setSelectedNode(null);
			setSelectedNodeCanvasId(null);
			setDraft({});
			setDraftLabel(null);
		}
	}, [canvasContext.nodes, isConfigPanelOpen, selectedNodeCanvasId]);



	const handleSetSelectedNode = useCallback((nodeId: string | null) => {
		canvasContext.setSelectedNodeId(nodeId);
	}, [canvasContext]);

    function handleClearSelectedNode(): void {
        setSelectedNode(null);
		setSelectedNodeCanvasId(null);
        canvasContext.setSelectedNodeId(null);
		setDraft({});
		setDraftLabel(null);
    }

    function openConfigPanel(focus?: string): void {
        setIsConfigPanelOpen(true);
        setFocusAnchor(focus);
    }

    function closeConfigPanel(): void {
        setIsConfigPanelOpen(false);
        setFocusAnchor(undefined);
    }

	function clearFocusAnchor(): void {
		setFocusAnchor(undefined);
	}

	// Draft management functions
	const updateDraft = useCallback((key: string, value: ItemDetailsValue): void => {
		setDraft(prev => ({ ...prev, [key]: value }));
	}, []);

	const updateDraftMultiple = useCallback((updates: ItemDetails): void => {
		setDraft(prev => ({ ...prev, ...updates }));
	}, []);

	// Check if this node allows label editing (new items)
	const isLabelEditable = useMemo(() => {
		return Boolean(selectedNode?.nodeDetails?.isNewItem);
	}, [selectedNode]);

	const isDirty = useMemo(() => {
		const hasDraftChanges = Object.keys(draft).length > 0;
		const hasLabelChange = draftLabel !== null;
		return hasDraftChanges || hasLabelChange;
	}, [draft, draftLabel]);

	const saveChanges = useCallback((): void => {
		if (!selectedNodeCanvasId || !isDirty) return;
		
		canvasContext.updateNodeData(selectedNodeCanvasId, (data) => {
			let updatedData = setItemDetails(data, draft);
			// Also update label if it was changed
			if (draftLabel !== null) {
				updatedData = { ...updatedData, label: draftLabel };
			}
			return updatedData;
		});
		setDraft({});
		setDraftLabel(null);
		closeConfigPanel();
	}, [selectedNodeCanvasId, isDirty, draft, draftLabel, canvasContext]);

	const discardChanges = useCallback((): void => {
		setDraft({});
		setDraftLabel(null);
		closeConfigPanel();
	}, []);


	async function fetchBuiltInVariables(): Promise<void> {
		setBuiltInVariablesLoading(true);
		try {
			const response = await getBuiltInVariables();
			setBuiltInVariables(response.variables);
		} catch (error) {
			// eslint-disable-next-line no-console -- Error logging for debugging
			console.error("Error fetching builtIn variables:", error);
		} finally {
			setBuiltInVariablesLoading(false);
		}
	}


	return (
		<ConfigPanelContext.Provider
            value={{
                selectedNode,
		        setSelectedNode: handleSetSelectedNode,
		        clearSelectedNode: handleClearSelectedNode,
				isConfigPanelOpen,
				openConfigPanel,
                closeConfigPanel,
				focusAnchor,
				clearFocusAnchor,
				draft,
				updateDraft,
				updateDraftMultiple,
				isDirty,
				saveChanges,
				discardChanges,
				draftLabel,
				setDraftLabel,
				isLabelEditable,
				builtInVariables,
				builtInVariablesLoading,
            }}
        >
			{children}
		</ConfigPanelContext.Provider>
	);
}

export function useConfigPanel(): ConfigPanelContextStructure {
	return useContext(ConfigPanelContext);
}
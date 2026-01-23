import { type Node, type Edge } from "@xyflow/react";
import { useCallback, useState } from "react";


const DEFAULT_MAX_HISTORY_SIZE = 50;

interface CanvasHistorySnapshot {
	nodes: Node[];
	edges: Edge[];
}

interface CanvasHistoryOptions {
	maxHistorySize?: number;
}

interface CommitOptions {
	addToHistory?: boolean;
}

interface CanvasHistoryApi {
	snapshot: CanvasHistorySnapshot;
	commit: (
		updater: (prev: CanvasHistorySnapshot) => CanvasHistorySnapshot,
		options?: CommitOptions,
	) => void;
	undo: () => void;
	redo: () => void;
	canUndo: boolean;
	canRedo: boolean;
	clearHistory: () => void;
}

interface HistoryState {
	past: CanvasHistorySnapshot[];
	present: CanvasHistorySnapshot;
	future: CanvasHistorySnapshot[];
}


export function useCanvasHistory(initialNodes: Node[] = [], initialEdges: Edge[] = [], options?: CanvasHistoryOptions): CanvasHistoryApi {
	const maxHistorySize = options?.maxHistorySize ?? DEFAULT_MAX_HISTORY_SIZE;
	const [history, setHistory] = useState<HistoryState>(() => ({
		past: [],
		present: { nodes: initialNodes, edges: initialEdges },
		future: [],
	}));


	const commit = useCallback(
		(updater: (prev: CanvasHistorySnapshot) => CanvasHistorySnapshot, commitOptions?: CommitOptions) => {
			const addToHistory = commitOptions?.addToHistory ?? true;

			setHistory((prevHistory) => {
				const { past, present, future } = prevHistory;
				const next = updater(present);
				
				if (!addToHistory) { return { past, present: next, future }; }

				const updatedPast = [...past, present];
				const trimmedPast = updatedPast.length > maxHistorySize
						? updatedPast.slice(updatedPast.length - maxHistorySize)
						: updatedPast;

				return {
					past: trimmedPast,
					present: next,
					future: [], // new edit clears redo stack
				};
			});
		}, [maxHistorySize],
	);

	const undo = useCallback(() => {
		setHistory((prevHistory) => {
			const { past, present, future } = prevHistory;

			if (past.length === 0) { return prevHistory; }

			const previous = past[past.length - 1];
			const newPast = past.slice(0, past.length - 1);

			return {
				past: newPast,
				present: previous,
				future: [present, ...future],
			};
		});
	}, []);

	const redo = useCallback(() => {
		setHistory((prevHistory) => {
			const { past, present, future } = prevHistory;

			if (future.length === 0) { return prevHistory; }

			const [next, ...rest] = future;

			const updatedPast = [...past, present];
			const trimmedPast =
				updatedPast.length > maxHistorySize
				? updatedPast.slice(updatedPast.length - maxHistorySize)
				: updatedPast;

			return {
				past: trimmedPast,
				present: next,
				future: rest,
			};
		});
	}, [maxHistorySize]);

	
	const clearHistory = useCallback(() => {
		setHistory((prevHistory) => ({ past: [], present: prevHistory.present, future: [] }));
	}, []);


	const { past, present, future } = history;
	const canUndo = past.length > 0;
	const canRedo = future.length > 0;

	return {
		snapshot: present,
		commit,
		undo,
		redo,
		canUndo,
		canRedo,
		clearHistory,
	};
}

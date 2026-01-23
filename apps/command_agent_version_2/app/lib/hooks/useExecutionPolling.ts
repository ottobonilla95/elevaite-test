"use client";
import { useEffect, useRef, useState } from "react";
import { type ExecutionResults, getExecutionStatus, type ExecutionStatus, getExecutionResults } from "../actions/executions";

export interface UseExecutionPollingOptions {
	/** Polling interval in milliseconds. Default: 200 */
	intervalMs?: number;
	/** Status values that indicate execution is complete (stop polling). Default: ["completed", "failed", "error", "cancelled"] */
	terminalStatuses?: string[];
	/** Callback when a terminal status is reached */
	onTerminal?: (status: ExecutionResults) => void;
}

export interface UseExecutionPollingResult {
	/** The latest execution status from polling, or null if not polling */
	executionStatus: ExecutionStatus | null;
	/** Whether polling is currently active */
	isPolling: boolean;
	/** Any error that occurred during polling */
	pollingError: Error | null;
}

const DEFAULT_TERMINAL_STATUSES = ["completed", "failed", "error", "cancelled"];

/**
 * Hook that polls execution status while an execution ID is active.
 * Returns the latest status so consumers can react to step-level changes.
 */
export function useExecutionPolling(
	executionId: string | null,
	onClear: () => void,
	options: UseExecutionPollingOptions = {},
): UseExecutionPollingResult {
	const {
		intervalMs = 500,
		terminalStatuses = DEFAULT_TERMINAL_STATUSES,
		onTerminal,
	} = options;

	const [executionStatus, setExecutionStatus] = useState<ExecutionStatus | null>(null);
	const [pollingError, setPollingError] = useState<Error | null>(null);
	const [isPolling, setIsPolling] = useState(false);
	const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
	// Track the previous executionId to detect when a NEW execution starts
	const prevExecutionIdRef = useRef<string | null>(null);

	useEffect(() => {
		// Only clear status when a NEW execution starts (different ID), not when execution ends
		// This preserves the final step statuses after completion
		if (executionId && executionId !== prevExecutionIdRef.current) {
			setExecutionStatus(null);
			setPollingError(null);
		}
		prevExecutionIdRef.current = executionId;

		if (!executionId) {
			setIsPolling(false);
			return;
		}

		setIsPolling(true);

		const currentExecutionId = executionId;

		async function poll(): Promise<void> {
			try {
				const status = await getExecutionStatus(currentExecutionId);
				setExecutionStatus(status);
				setPollingError(null);

				// Check if we've reached a terminal status
				if (terminalStatuses.includes(status.status)) {
					// Stop polling
					if (intervalRef.current) {
						clearInterval(intervalRef.current);
						intervalRef.current = null;
					}
					setIsPolling(false);
					const result = await getExecutionResults(currentExecutionId);
					onTerminal?.(result);
					onClear();
				}
			} catch (error) {
				setPollingError(error instanceof Error ? error : new Error(String(error)));
				// Don't stop polling on error - backend might be temporarily unavailable
				console.error("❌ Polling error:", error);
			}
		}

		// Initial poll
		void poll();

		// Set up interval
		intervalRef.current = setInterval(() => {
			void poll();
		}, intervalMs);

		// Cleanup on unmount or executionId change
		return () => {
			if (intervalRef.current) {
				clearInterval(intervalRef.current);
				intervalRef.current = null;
			}
		};
	}, [executionId, intervalMs, terminalStatuses, onTerminal, onClear]);

	return {
		executionStatus,
		isPolling,
		pollingError,
	};
}

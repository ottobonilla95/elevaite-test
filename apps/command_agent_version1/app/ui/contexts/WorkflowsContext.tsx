"use client";

import React, { createContext, useContext, useEffect, useState, useCallback } from "react";
import { getWorkflows, getWorkflowDetails, createWorkflow, updateWorkflow, deleteWorkflow, deployWorkflowModern, getChatDetails } from "../../lib/actions";
import type { SavedWorkflow, WorkflowResponse, WorkflowCreateRequest, WorkflowDeployment, WorkflowDeploymentRequest, WorkflowExecuteResponseObject } from "../../lib/interfaces";

interface WorkflowsContextType {
	// State
	workflows: SavedWorkflow[];
	isLoading: boolean;
	error: string | null;
	lastUpdated: Date | null;

	// Actions
	refreshWorkflows: () => Promise<void>;
	createWorkflowAndRefresh: (workflowData: WorkflowCreateRequest) => Promise<WorkflowResponse>;
	updateWorkflowAndRefresh: (workflowId: string, workflowData: WorkflowCreateRequest) => Promise<WorkflowResponse>;
	deleteWorkflowAndRefresh: (workflowId: string) => Promise<void>;
	deployWorkflowAndRefresh: (workflowId: string, deploymentData: WorkflowDeploymentRequest) => Promise<WorkflowDeployment>;
	getWorkflowById: (workflowId: string) => SavedWorkflow | undefined;
	getWorkflowDetails: (workflowId: string) => Promise<WorkflowResponse>;
	executeWorkflowToGetChatDetails: (workflowId: string) => Promise<WorkflowExecuteResponseObject | null>;

	// Filters
	filteredWorkflows: SavedWorkflow[];
	setSearchQuery: (query: string) => void;
	setStatusFilter: (status: "all" | "active" | "deployed" | "inactive") => void;
	setSortBy: (sortBy: "name" | "created_at" | "updated_at" | "agent_count") => void;
	setSortOrder: (order: "asc" | "desc") => void;

	expandChat: boolean;
	setExpandChat: (expand: boolean) => void;
	setWorkflows: (workflows: SavedWorkflow[]) => void;
}

const WorkflowsContext = createContext<WorkflowsContextType | undefined>(undefined);

interface WorkflowsProviderProps {
	children: React.ReactNode;
	autoRefreshInterval?: number; // Optional auto-refresh in milliseconds
}

// Transform workflow data helper function
function transformWorkflowData(workflows: WorkflowResponse[]): SavedWorkflow[] {
	return workflows.map(workflow => ({
		workflow_id: workflow.workflow_id,
		name: workflow.name,
		description: workflow.description,
		created_at: workflow.created_at,
		created_by: workflow.created_by,
		is_active: workflow.is_active,
		is_deployed: workflow.is_deployed,
		deployed_at: workflow.deployed_at,
		is_editable: workflow.is_editable,
		version: workflow.version,
		tags: workflow.tags,
		agent_count: workflow.workflow_agents?.length || 0,
		connection_count: workflow.workflow_connections?.length || 0,
	}));
}

export function WorkflowsProvider({
	children,
	autoRefreshInterval = 60000 // 60 seconds default
}: WorkflowsProviderProps): JSX.Element {
	// Core state
	const [workflows, setWorkflows] = useState<SavedWorkflow[]>([]);
	const [isLoading, setIsLoading] = useState(false);
	const [error, setError] = useState<string | null>(null);
	const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

	// Filter state
	const [searchQuery, setSearchQuery] = useState("");
	const [statusFilter, setStatusFilter] = useState<"all" | "active" | "deployed" | "inactive">("all");
	const [sortBy, setSortBy] = useState<"name" | "created_at" | "updated_at" | "agent_count">("created_at");
	const [sortOrder, setSortOrder] = useState<"asc" | "desc">("desc");

	const [expandChat, setExpandChat] = useState(false);

	// Get chat details
	async function executeWorkflowToGetChatDetails(workflowId: string): Promise<WorkflowExecuteResponseObject | null> {
		setIsLoading(true);
		try {
		  const result = await getChatDetails(workflowId);
		  return result;
		} catch (error) {
		  console.error("Going to the previous page failed:", error);
		  return null;
		} finally {
		  setIsLoading(false);
		}
	  }

	// Fetch workflows function
	const refreshWorkflows = useCallback(async () => {
		setIsLoading(true);
		setError(null);

		try {
			const fetchedWorkflows = await getWorkflows();
			const transformedWorkflows = transformWorkflowData(fetchedWorkflows);
			setWorkflows(transformedWorkflows);
			setLastUpdated(new Date());
		} catch (err) {
			const errorMessage = err instanceof Error ? err.message : "Failed to fetch workflows";
			setError(errorMessage);
			console.error("Error fetching workflows:", err);
		} finally {
			setIsLoading(false);
		}
	}, []);

	// Create workflow and refresh
	const createWorkflowAndRefresh = useCallback(async (workflowData: WorkflowCreateRequest): Promise<WorkflowResponse> => {
		try {
			const newWorkflow = await createWorkflow(workflowData);
			// Optimistically update the local state
			const newSavedWorkflow: SavedWorkflow = {
				workflow_id: newWorkflow.workflow_id,
				name: newWorkflow.name,
				description: newWorkflow.description,
				created_at: newWorkflow.created_at,
				created_by: newWorkflow.created_by,
				is_active: newWorkflow.is_active,
				is_deployed: newWorkflow.is_deployed,
				deployed_at: newWorkflow.deployed_at,
				is_editable: newWorkflow.is_editable,
				version: newWorkflow.version,
				tags: newWorkflow.tags,
				agent_count: newWorkflow.workflow_agents?.length || 0,
				connection_count: newWorkflow.workflow_connections?.length || 0,
			};
			setWorkflows(prev => [newSavedWorkflow, ...prev]);
			setLastUpdated(new Date());
			return newWorkflow;
		} catch (err) {
			// If creation fails, refresh to ensure consistency
			await refreshWorkflows();
			throw err;
		}
	}, [refreshWorkflows]);

	// Update workflow and refresh
	const updateWorkflowAndRefresh = useCallback(async (workflowId: string, workflowData: WorkflowCreateRequest): Promise<WorkflowResponse> => {
		try {
			const updatedWorkflow = await updateWorkflow(workflowId, workflowData);
			// Optimistically update the local state
			const updatedSavedWorkflow: SavedWorkflow = {
				workflow_id: updatedWorkflow.workflow_id,
				name: updatedWorkflow.name,
				description: updatedWorkflow.description,
				created_at: updatedWorkflow.created_at,
				created_by: updatedWorkflow.created_by,
				is_active: updatedWorkflow.is_active,
				is_deployed: updatedWorkflow.is_deployed,
				deployed_at: updatedWorkflow.deployed_at,
				is_editable: updatedWorkflow.is_editable,
				version: updatedWorkflow.version,
				tags: updatedWorkflow.tags,
				agent_count: updatedWorkflow.workflow_agents?.length || 0,
				connection_count: updatedWorkflow.workflow_connections?.length || 0,
			};
			setWorkflows(prev => prev.map(workflow =>
				workflow.workflow_id === workflowId ? updatedSavedWorkflow : workflow
			));
			setLastUpdated(new Date());
			return updatedWorkflow;
		} catch (err) {
			// If update fails, refresh to ensure consistency
			await refreshWorkflows();
			throw err;
		}
	}, [refreshWorkflows]);

	// Delete workflow and refresh
	const deleteWorkflowAndRefresh = useCallback(async (workflowId: string): Promise<void> => {
		try {
			await deleteWorkflow(workflowId);
			// Optimistically update the local state
			setWorkflows(prev => prev.filter(workflow => workflow.workflow_id !== workflowId));
			setLastUpdated(new Date());
		} catch (err) {
			// If deletion fails, refresh to ensure consistency
			await refreshWorkflows();
			throw err;
		}
	}, [refreshWorkflows]);

	// Deploy workflow and refresh
	const deployWorkflowAndRefresh = useCallback(async (workflowId: string, deploymentData: WorkflowDeploymentRequest): Promise<WorkflowDeployment> => {
		try {
			const deployment = await deployWorkflowModern(workflowId, deploymentData);
			// Update the workflow's deployment status
			setWorkflows(prev => prev.map(workflow =>
				workflow.workflow_id === workflowId
					? { ...workflow, is_deployed: true, deployed_at: deployment.deployed_at }
					: workflow
			));
			setLastUpdated(new Date());
			return deployment;
		} catch (err) {
			// If deployment fails, refresh to ensure consistency
			await refreshWorkflows();
			throw err;
		}
	}, [refreshWorkflows]);

	// Utility functions
	const getWorkflowById = useCallback((workflowId: string): SavedWorkflow | undefined => {
		return workflows.find(workflow => workflow.workflow_id === workflowId);
	}, [workflows]);

	// Get workflow details (full data)
	const getWorkflowDetailsById = useCallback(async (workflowId: string): Promise<WorkflowResponse> => {
		return await getWorkflowDetails(workflowId);
	}, []);

	// Filtered workflows based on current filters
	const filteredWorkflows = React.useMemo(() => {
		let filtered = workflows;

		// Apply search filter
		if (searchQuery.trim()) {
			const lowercaseQuery = searchQuery.toLowerCase();
			filtered = filtered.filter(workflow =>
				workflow.name.toLowerCase().includes(lowercaseQuery) ||
				(workflow.description?.toLowerCase().includes(lowercaseQuery) ?? false) ||
				(workflow.created_by?.toLowerCase().includes(lowercaseQuery) ?? false)
			);
		}

		// Apply status filter
		if (statusFilter !== "all") {
			switch (statusFilter) {
				case "active":
					filtered = filtered.filter(workflow => workflow.is_active);
					break;
				case "deployed":
					filtered = filtered.filter(workflow => workflow.is_deployed);
					break;
				case "inactive":
					filtered = filtered.filter(workflow => !workflow.is_active);
					break;
			}
		}

		// Apply sorting
		filtered.sort((a, b) => {
			let aValue: string | number;
			let bValue: string | number;

			switch (sortBy) {
				case "name":
					aValue = a.name.toLowerCase();
					bValue = b.name.toLowerCase();
					break;
				case "created_at":
					aValue = new Date(a.created_at).getTime();
					bValue = new Date(b.created_at).getTime();
					break;
				case "updated_at":
					aValue = new Date(a.created_at).getTime(); // Using created_at as fallback
					bValue = new Date(b.created_at).getTime();
					break;
				case "agent_count":
					aValue = a.agent_count ?? 0;
					bValue = b.agent_count ?? 0;
					break;
				default:
					return 0;
			}

			if (sortOrder === "asc") {
				return aValue < bValue ? -1 : aValue > bValue ? 1 : 0;
			}
			return aValue > bValue ? -1 : aValue < bValue ? 1 : 0;

		});

		return filtered;
	}, [workflows, searchQuery, statusFilter, sortBy, sortOrder]);

	// Initial load
	useEffect(() => {
		void refreshWorkflows();
	}, [refreshWorkflows]);

	// Auto-refresh interval
	useEffect(() => {
		if (!autoRefreshInterval) return;

		const interval = setInterval(() => {
			void refreshWorkflows();
		}, autoRefreshInterval);

		return () => clearInterval(interval);
	}, [refreshWorkflows, autoRefreshInterval]);

	const contextValue: WorkflowsContextType = {
		// State
		workflows,
		isLoading,
		error,
		lastUpdated,
		expandChat,

		// Actions
		refreshWorkflows,
		createWorkflowAndRefresh,
		updateWorkflowAndRefresh,
		deleteWorkflowAndRefresh,
		deployWorkflowAndRefresh,
		getWorkflowById,
		getWorkflowDetails: getWorkflowDetailsById,
		executeWorkflowToGetChatDetails,

		// Filters
		filteredWorkflows,
		setSearchQuery,
		setStatusFilter,
		setSortBy,
		setSortOrder,
		setExpandChat,
		setWorkflows
	};

	return (
		<WorkflowsContext.Provider value={contextValue}>
			{children}
		</WorkflowsContext.Provider>
	);
}

export function useWorkflows(): WorkflowsContextType {
	const context = useContext(WorkflowsContext);
	if (context === undefined) {
		throw new Error("useWorkflows must be used within a WorkflowsProvider");
	}
	return context;
}

export default WorkflowsContext;

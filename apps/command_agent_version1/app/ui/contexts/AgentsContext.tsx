"use client";

import React, { createContext, useContext, useEffect, useState, useCallback, useMemo } from "react";
import { fetchAllAgents, createAgent, updateAgent } from "../../lib/actions";
import type { AgentResponse, AgentCreate, AgentUpdate } from "../../lib/interfaces";

interface AgentsContextType {
	// State
	agents: AgentResponse[];
	isLoading: boolean;
	error: string | null;
	lastUpdated: Date | null;

	// Actions
	refreshAgents: () => Promise<void>;
	createAgentAndRefresh: (agentData: AgentCreate) => Promise<AgentResponse>;
	updateAgentAndRefresh: (agentId: string, agentData: AgentUpdate) => Promise<AgentResponse>;
	getAgentById: (agentId: string) => AgentResponse | undefined;
	getAgentsByType: (agentType: string) => AgentResponse[];
	searchAgents: (query: string) => AgentResponse[];
	getDeployedAgents: () => AgentResponse[];
	getActiveAgents: () => AgentResponse[];
	getAgentCount: () => number;

	// Filters
	filteredAgents: AgentResponse[];
	setSearchQuery: (query: string) => void;
	setTypeFilter: (types: string[]) => void;
	setDeployedFilter: (deployed?: boolean) => void;
}

const AgentsContext = createContext<AgentsContextType | undefined>(undefined);

interface AgentsProviderProps {
	children: React.ReactNode;
	autoRefreshInterval?: number; // Optional auto-refresh in milliseconds
}

export function AgentsProvider({
	children,
	autoRefreshInterval = 30000 // 30 seconds default
}: AgentsProviderProps): JSX.Element {
	// Core state
	const [agents, setAgents] = useState<AgentResponse[]>([]);
	const [isLoading, setIsLoading] = useState(false);
	const [error, setError] = useState<string | null>(null);
	const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

	// Filter state
	const [searchQuery, setSearchQuery] = useState("");
	const [typeFilter, setTypeFilter] = useState<string[]>([]);
	const [deployedFilter, setDeployedFilter] = useState<boolean | undefined>(undefined);

	// Fetch agents function
	const refreshAgents = useCallback(async () => {
		setIsLoading(true);
		setError(null);

		try {
			const fetchedAgents = await fetchAllAgents(0, 100, deployedFilter);
			setAgents(fetchedAgents);
			setLastUpdated(new Date());
		} catch (err) {
			const errorMessage = err instanceof Error ? err.message : "Failed to fetch agents";
			setError(errorMessage);
			console.error("Error fetching agents:", err);
		} finally {
			setIsLoading(false);
		}
	}, [deployedFilter]);

	// Create agent and refresh
	const createAgentAndRefresh = useCallback(async (agentData: AgentCreate): Promise<AgentResponse> => {
		try {
			const newAgent = await createAgent(agentData);
			// Optimistically update the local state
			setAgents(prev => [...prev, newAgent]);
			setLastUpdated(new Date());
			return newAgent;
		} catch (err) {
			// If creation fails, refresh to ensure consistency
			await refreshAgents();
			throw err;
		}
	}, [refreshAgents]);

	// Update agent and refresh
	const updateAgentAndRefresh = useCallback(async (agentId: string, agentData: AgentUpdate): Promise<AgentResponse> => {
		try {
			const updatedAgent = await updateAgent(agentId, agentData);
			// Optimistically update the local state
			setAgents(prev => prev.map(agent =>
				agent.agent_id === agentId ? updatedAgent : agent
			));
			setLastUpdated(new Date());
			return updatedAgent;
		} catch (err) {
			// If update fails, refresh to ensure consistency
			await refreshAgents();
			throw err;
		}
	}, [refreshAgents]);

	// Utility functions
	const getAgentById = useCallback((agentId: string): AgentResponse | undefined => {
		return agents.find(agent => agent.agent_id === agentId);
	}, [agents]);

	const getAgentsByType = useCallback((agentType: string): AgentResponse[] => {
		return agents.filter(agent => agent.agent_type === agentType);
	}, [agents]);

	const searchAgents = useCallback((query: string): AgentResponse[] => {
		const lowercaseQuery = query.toLowerCase();
		return agents.filter(agent =>
			agent.name.toLowerCase().includes(lowercaseQuery) ||
			(agent.description?.toLowerCase().includes(lowercaseQuery) ?? false) ||
			(agent.agent_type?.toLowerCase().includes(lowercaseQuery) ?? false)
		);
	}, [agents]);

	const getDeployedAgents = useCallback((): AgentResponse[] => {
		return agents.filter(agent => agent.deployed);
	}, [agents]);

	const getActiveAgents = useCallback((): AgentResponse[] => {
		return agents.filter(agent => agent.status === "active");
	}, [agents]);

	const getAgentCount = useCallback((): number => {
		return agents.length;
	}, [agents]);

	// Filtered agents based on current filters
	const filteredAgents = useMemo(() => {
		let filtered = agents;

		// Apply search filter
		if (searchQuery.trim()) {
			filtered = searchAgents(searchQuery);
		}

		// Apply type filter
		if (typeFilter.length > 0) {
			filtered = filtered.filter(agent => agent.agent_type && typeFilter.includes(agent.agent_type));
		}

		return filtered;
	}, [agents, searchQuery, typeFilter, searchAgents]);

	// Initial load
	useEffect(() => {
		void refreshAgents();
	}, [refreshAgents]);

	// Auto-refresh interval
	useEffect(() => {
		if (!autoRefreshInterval) return;

		const interval = setInterval(() => {
			void refreshAgents();
		}, autoRefreshInterval);

		return () => clearInterval(interval);
	}, [refreshAgents, autoRefreshInterval]);

	const contextValue: AgentsContextType = {
		// State
		agents,
		isLoading,
		error,
		lastUpdated,

		// Actions
		refreshAgents,
		createAgentAndRefresh,
		updateAgentAndRefresh,
		getAgentById,
		getAgentsByType,
		searchAgents,
		getDeployedAgents,
		getActiveAgents,
		getAgentCount,

		// Filters
		filteredAgents,
		setSearchQuery,
		setTypeFilter,
		setDeployedFilter,
	};

	return (
		<AgentsContext.Provider value={contextValue}>
			{children}
		</AgentsContext.Provider>
	);
}

export function useAgents(): AgentsContextType {
	const context = useContext(AgentsContext);
	if (context === undefined) {
		throw new Error("useAgents must be used within an AgentsProvider");
	}
	return context;
}

export default AgentsContext;

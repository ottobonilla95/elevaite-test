// DesignerSidebar.tsx
"use client";

import React, { useEffect, useState } from "react";
import {
	Router,
	Globe,
	Database,
	Link2,
	Wrench,
	Search,
	Eye,
	X,
	ChevronsLeft,
	ChevronsRight
} from "lucide-react";
import { CommonModal } from "@repo/ui/components";
import { type AgentResponse, type SavedWorkflow, type AgentType } from "../../lib/interfaces";
import { fetchAllAgents } from "../../lib/actions";
import { isValidAgentType } from "../../lib/discriminators";
import { RouterAgentIcon } from "../icons";
import TabHeader, { type Tab } from "../TabHeader";
import WorkflowsTab from "./WorkflowsTab";
import "./DesignerSidebar.scss";



// SidebarItem component for draggable items
interface SidebarItemProps {
	icon: React.ReactNode;
	label: string;
	subLabel?: string;
	onClick?: () => void;
	draggable?: boolean;
	onDragStart?: (e: React.DragEvent<HTMLButtonElement>) => void;
}

function SidebarItem({ icon, label, subLabel, onClick, draggable, onDragStart }: SidebarItemProps): JSX.Element {
	return (
		<button
			className="sidebar-item cursor-grab p-2 mb-2 rounded-md hover:bg-gray-100 transition-colors w-full"
			onClick={onClick}
			draggable={draggable}
			onDragStart={onDragStart}
			type="button"
		>
			<div className="sidebar-item-content flex w-full">
				<div className="item-icon mr-3">
					{icon}
				</div>
				<div className="item-details w-full flex justify-start flex-col">
					<h3 className="text-sm font-medium flex flex-1">{label}</h3>
					{subLabel ? <p className="text-xs text-gray-500 flex flex-1">{subLabel}</p> : null}
				</div>
			</div>
		</button>
	);
}

interface DesignerSidebarProps {
	handleDragStart: (event: React.DragEvent<HTMLElement>, agent: AgentResponse) => void;
	handleCreateNewWorkflow: () => void;
	handleLoadWorkflow: (workflow: SavedWorkflow) => void;
	handleCreateNewAgent: () => void;
	isLoading: boolean;
	activeTab: string;
	setActiveTab: (tab: string) => void;
}

function DesignerSidebar({
	handleDragStart,
	handleCreateNewWorkflow,
	handleLoadWorkflow,
	handleCreateNewAgent,
	isLoading: _isLoading,
	activeTab,
	setActiveTab
}: DesignerSidebarProps): JSX.Element {
	// State for agents and search
	const [agents, setAgents] = useState<AgentResponse[]>([]);
	const [searchQuery, setSearchQuery] = useState("");
	const [showAllAgentsModal, setShowAllAgentsModal] = useState(false);

	// Define tabs for TabHeader component
	const sidebarTabs: Tab[] = [
		{ id: "actions", label: "Actions" },
		{ id: "workflows", label: "Workflows" }
	];

	useEffect(() => {
		const fetchAgents = async (): Promise<void> => {
			try {
				const _agents = await fetchAllAgents();
				setAgents(_agents);
			} catch (error) {
				console.error("Error fetching agents:", error);
			}
		};
		void fetchAgents();
	}, []);

	// Filter agents based on search query
	const filteredAgents = agents.filter((agent): agent is AgentResponse & { agent_type: AgentType } =>
		isValidAgentType(agent.agent_type) &&
		['router', 'web_search', 'api', 'data', 'toshiba'].includes(agent.agent_type) &&
		(agent.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
			(agent.description?.toLowerCase().includes(searchQuery.toLowerCase()) ?? false))
	);

	// Get limited agents for sidebar display (first 5)
	const displayedAgents = filteredAgents.slice(0, 5);

	const [sidebarOpen, setSidebarOpen] = useState(true);

	// Get agent icon based on type
	const getAgentIcon = (type: AgentType): JSX.Element => {
		switch (type) {
			case "router":
				return <RouterAgentIcon />;
			case "web_search":
				return <Globe size={20} className="text-[#FF681F]" />;
			case "api":
				return <Link2 size={20} className="text-[#FF681F]" />;
			case "data":
				return <Database size={20} className="text-[#FF681F]" />;
			case "troubleshooting":
				return <Wrench size={20} className="text-[#FF681F]" />;
			default:
				return <Router size={20} className="text-[#FF681F]" />;
		}
	};

	return (
		<div className={`designer-sidebar bg-white${!sidebarOpen ? ' shrinked' : ''}`}>
			{/* Workflow Header */}
			{/* <div className="sidebar-header p-4 border-b border-gray-200">
                <h2 className="text-lg font-semibold mb-1">{workflowName}</h2>
                <p className="text-sm text-gray-500">{workflowDescription}</p>
            </div> */}

			{/* Navigation Tabs */}
			<div className="sidebar-header-tabs bg-white flex items-center justify-between">
				<TabHeader
					tabs={sidebarTabs}
					activeTab={activeTab}
					onTabChange={setActiveTab}
					innerClassName="sidebar-header-tabs-inner p-1 rounded-lg flex items-center w-full"
				/>
				<button type="button" onClick={() => { setSidebarOpen(!sidebarOpen); }}>
					{sidebarOpen ? <ChevronsLeft size={24} /> : <ChevronsRight size={24} />}
				</button>
			</div>

			{/* Agents Section */}
			{activeTab === "actions" && (
				<div className="actions-tab flex flex-grow flex-col">
					{/* Agents Header */}
					<div className="mx-2">
						<h2 className="font-medium text-black py-4">Agents</h2>

						{/* Search Bar */}
						<div className="flex items-center border border-gray-300 rounded-md px-3 py-2 mb-3">
							<Search size={16} className="text-gray-400 mr-2" />
							<input
								type="text"
								placeholder="Search agents..."
								value={searchQuery}
								onChange={(e) => { setSearchQuery(e.target.value); }}
								className="flex-1 outline-none text-sm"
							/>
						</div>

						{/* See All Button */}
						{filteredAgents.length > 5 && (
							<button
								type="button"
								onClick={() => { setShowAllAgentsModal(true); }}
								className="flex items-center justify-start gap-2 w-full text-[#FF681F] text-xs mt-3 px-1 pb-3 "
							>
								See All ({filteredAgents.length} agents)
							</button>
						)}

						{/* Agents List */}
						<div className="section-content">
							{displayedAgents.map((agent) => (
								<SidebarItem
									key={agent.agent_id}
									icon={
										<div className="w-8 h-8 rounded-md flex items-center justify-center">
											{getAgentIcon(agent.agent_type)}
										</div>
									}
									label={agent.name}
									subLabel={agent.description ?? "Initiate workflows"}
									draggable
									onDragStart={(e) => { handleDragStart(e, agent); }}
								/>
							))}
						</div>
					</div>

					{/* Footer Buttons */}
					<div className="designer-sidebar-controls-container pt-3 mt-auto space-y-2">
						{/* Create New Agent Button */}
						<button
							type="button"
							onClick={handleCreateNewAgent}
							className="w-full bg-blue-500 text-white rounded-md text-sm font-medium hover:bg-blue-600 transition-colors flex items-center justify-center"
						>
							Create new Agent
						</button>
					</div>
				</div>
			)}

			{/* Workflows Content */}
			{activeTab === "workflows" && (
				<WorkflowsTab
					onCreateNewWorkflow={handleCreateNewWorkflow}
					onLoadWorkflow={handleLoadWorkflow}
				/>
			)}

			{/* All Agents Modal */}
			{showAllAgentsModal ? <CommonModal onClose={() => { setShowAllAgentsModal(false); }}>
				<div className="p-6 max-w-4xl max-h-[80vh] overflow-hidden flex flex-col bg-white rounded-xl border border-[#6C8271]">
					<div className="flex items-center justify-between mb-4 gap-10">
						<h2 className="text-xl font-semibold">All Agents</h2>

						{/* Search Bar in Modal */}
						<div className="flex items-center gap-4">
							<div className="flex items-center border border-gray-300 rounded-md px-3 py-2">
								<Search size={16} className="text-gray-400 mr-2" />
								<input
									type="text"
									placeholder="Search agents..."
									value={searchQuery}
									onChange={(e) => { setSearchQuery(e.target.value); }}
									className="flex-1 outline-none text-sm"
								/>
							</div>
							<button
								type="button"
								onClick={() => { setShowAllAgentsModal(false); }}
								className="text-gray-500 hover:text-gray-700"
							>
								<X size={24} />
							</button>
						</div>
					</div>

					{/* Agents Grid */}
					<div className="flex-1 overflow-y-auto">
						<div className="grid grid-cols-1 gap-4">
							{filteredAgents.map((agent) => (
								<div
									key={agent.agent_id}
									className="border border-gray-200 rounded-lg p-4 hover:bg-gray-50 cursor-grab"
									draggable
									onDragStart={(e) => { handleDragStart(e, agent); }}
								>
									<div className="flex items-start gap-3">
										<div className="w-10 h-10 rounded-md bg-[#F8FAFC] border border-[#E2E8ED] text-[#FE854B] flex items-center justify-center flex-shrink-0">
											{getAgentIcon(agent.agent_type)}
										</div>
										<div className="flex-1 min-w-0">
											<h3 className="font-medium text-sm truncate">{agent.name}</h3>
											<p className="text-xs text-gray-600 mt-1 line-clamp-2">
												{agent.description ?? "Initiate workflows"}
											</p>
										</div>
									</div>
								</div>
							))}
						</div>
						{filteredAgents.length === 0 && (
							<div className="text-center text-gray-500 py-8">
								No agents found matching your search.
							</div>
						)}
					</div>
				</div>
			</CommonModal> : null}
		</div>
	);
}

export default DesignerSidebar;



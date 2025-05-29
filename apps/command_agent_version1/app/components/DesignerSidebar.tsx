// DesignerSidebar.tsx
"use client";

import React, { useEffect, useState } from "react";
import {
    ChevronDown,
    ChevronRight,
    Router,
    Globe,
    Database,
    Link2,
    Wrench,
    MessageSquare,
    Zap,
    Save,
    ChevronsLeft,
    ChevronsRight
} from "lucide-react";
import { AgentType, AGENT_TYPES } from "./type";
import "./DesignerSidebar.scss";
import { AgentResponse } from "../lib/interfaces";
import { fetchAllAgents } from "../lib/actions";

// SidebarSection component for collapsible sections
const SidebarSection: React.FC<{
    title: string;
    isOpen: boolean;
    onToggle: () => void;
    children?: React.ReactNode;
}> = ({ title, isOpen, onToggle, children }) => {
    return (
        <div className="sidebar-section mx-2">
            <div
                className="section-header flex items-center justify-between py-4 cursor-pointer"
                onClick={onToggle}
            >
                <h2 className="font-medium text-black">{title}</h2>
                <div className="text-black">
                    {
                        isOpen ?
                            <svg width="10" height="6" viewBox="0 0 10 6" fill="none" xmlns="http://www.w3.org/2000/svg">
                                <path d="M1 1L5 5L9 1" stroke="#212124" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" />
                            </svg>
                            :
                            <svg width="10" height="6" viewBox="0 0 10 6" fill="none" xmlns="http://www.w3.org/2000/svg">
                                <path d="M1 5L5 1L9 5" stroke="#212124" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" />
                            </svg>
                    }
                </div>
            </div>

            {isOpen && (
                <div className="section-content mt-3">
                    {children}
                </div>
            )}
        </div>
    );
};

// SidebarItem component for draggable items
const SidebarItem: React.FC<{
    icon: React.ReactNode;
    label: string;
    subLabel?: string;
    onClick?: () => void;
    draggable?: boolean;
    onDragStart?: (e: React.DragEvent<HTMLDivElement>) => void;
}> = ({ icon, label, subLabel, onClick, draggable, onDragStart }) => {
    return (
        <div
            className="sidebar-item cursor-grab p-2 mb-2 rounded-md hover:bg-gray-100 transition-colors"
            onClick={onClick}
            draggable={draggable}
            onDragStart={onDragStart}
        >
            <div className="sidebar-item-content flex items-center">
                <div className="item-icon mr-3">
                    {icon}
                </div>
                <div className="item-details">
                    <h3 className="text-sm font-medium">{label}</h3>
                    {subLabel && (
                        <p className="text-xs text-gray-500">{subLabel}</p>
                    )}
                </div>
            </div>
        </div>
    );
};

interface DesignerSidebarProps {
    workflowName: string;
    workflowDescription?: string;
    handleDragStart: (event: React.DragEvent<HTMLDivElement>, agent: any) => void;
    handleDeployWorkflow: () => void;
    handleSaveWorkflow: () => void; // Added save workflow function
    isLoading: boolean;
    activeTab: string;
    setActiveTab: (tab: string) => void;
}

const DesignerSidebar: React.FC<DesignerSidebarProps> = ({
    workflowName,
    workflowDescription = "Analyze and process agent workflows",
    handleDragStart,
    handleDeployWorkflow,
    handleSaveWorkflow, // Added save workflow function
    isLoading,
    activeTab,
    setActiveTab
}) => {
    // State for section visibility
    const [sectionsState, setSectionsState] = useState({
        components: true,
        actions: false,
        tools: false
    });

    const [agents, setAgents] = useState<AgentResponse[]>([]);

    useEffect(() => {
        const fetchAgents = async () => {
            try {
                const agents = await fetchAllAgents();
                setAgents(agents);
                console.log("Got agents");
                console.log(agents);
            } catch (error) {
                console.error("Error fetching agents:", error);
            }
        };

        fetchAgents();
    }, []);

    // Toggle section visibility
    const toggleSection = (section: keyof typeof sectionsState) => {
        setSectionsState({
            ...sectionsState,
            [section]: !sectionsState[section]
        });
    };

    const [sidebarOpen, setSidebarOpen] = useState(true);

    // Get agent icon based on type
    const getAgentIcon = (type: AgentType) => {
        switch (type) {
            case "router":
                return <svg width="22" height="22" viewBox="0 0 22 22" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M1.25879 15.3295V6.67058C1.25879 3.68174 3.68174 1.25879 6.67058 1.25879H15.3295C18.3183 1.25879 20.7412 3.68174 20.7412 6.67058V15.3295C20.7412 18.3183 18.3183 20.7412 15.3295 20.7412H6.67058C3.68174 20.7412 1.25879 18.3183 1.25879 15.3295Z" stroke="#FE854B" stroke-width="1.62354" />
                    <path d="M15.8706 13.7061C15.8706 13.7061 14.2471 15.8708 11 15.8708C7.75293 15.8708 6.12939 13.7061 6.12939 13.7061" stroke="#FE854B" stroke-width="1.62354" stroke-linecap="round" stroke-linejoin="round" />
                    <path d="M7.21159 8.83529C6.91271 8.83529 6.67041 8.59299 6.67041 8.29411C6.67041 7.99523 6.91271 7.75293 7.21159 7.75293C7.51047 7.75293 7.75277 7.99523 7.75277 8.29411C7.75277 8.59299 7.51047 8.83529 7.21159 8.83529Z" fill="#FE854B" stroke="#FE854B" stroke-width="1.62354" stroke-linecap="round" stroke-linejoin="round" />
                    <path d="M14.7882 8.83529C14.4894 8.83529 14.2471 8.59299 14.2471 8.29411C14.2471 7.99523 14.4894 7.75293 14.7882 7.75293C15.0871 7.75293 15.3294 7.99523 15.3294 8.29411C15.3294 8.59299 15.0871 8.83529 14.7882 8.83529Z" fill="#FE854B" stroke="#FE854B" stroke-width="1.62354" stroke-linecap="round" stroke-linejoin="round" />
                </svg>;
            case "web_search":
                return <Globe size={20} className="text-blue-600" />;
            case "api":
                return <Link2 size={20} className="text-green-600" />;
            case "data":
                return <Database size={20} className="text-yellow-600" />;
            case "troubleshooting":
                return <Wrench size={20} className="text-red-600" />;
            default:
                return <Router size={20} className="text-gray-600" />;
        }
    };

    // Get agent icon container class based on type
    const getAgentIconClass = (type: AgentType) => {
        switch (type) {
            case "router":
                return "bg-purple-100";
            case "web_search":
                return "bg-blue-100";
            case "api":
                return "bg-green-100";
            case "data":
                return "bg-yellow-100";
            case "troubleshooting":
                return "bg-red-100";
            default:
                return "bg-gray-100";
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
                <div className="sidebar-header-tabs-inner p-1 rounded-lg flex items-center">
                    <div
                        className={`flex-1 text-center py-1 px-4 rounded-4 text-xs cursor-pointer ${activeTab === "actions"
                            ? "active font-medium bg-white text-orange-500"
                            : "text-gray-500 hover:text-orange-500"
                            }`}
                        onClick={() => setActiveTab("actions")}
                    >
                        Actions
                    </div>
                    <div
                        className={`flex-1 text-center py-1 px-4 rounded-4 text-xs cursor-pointer ${activeTab === "workflows"
                            ? "active font-medium bg-white text-orange-500"
                            : "text-gray-500 hover:text-orange-500"
                            }`}
                        onClick={() => setActiveTab("workflows")}
                    >
                        Workflows
                    </div>
                </div>

                <button type="button" onClick={() => setSidebarOpen(!sidebarOpen)}>
                    {
                        sidebarOpen
                            ?
                            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                                <g opacity="0.8">
                                    <path d="M18 17L13 12L18 7M11 17L6 12L11 7" stroke="#212124" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" />
                                </g>
                            </svg>
                            :
                            <svg width="14" height="12" viewBox="0 0 14 12" fill="none" xmlns="http://www.w3.org/2000/svg">
                                <path d="M1 11L6 6L1 1M8 11L13 6L8 1" stroke="#212124" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" />
                            </svg>
                    }
                </button>
            </div>

            {/* Collapsible Sections */}
            {activeTab === "actions" && (
                <div>
                    {/* Components Section */}
                    <SidebarSection
                        title="Components"
                        isOpen={sectionsState.components}
                        onToggle={() => toggleSection('components')}
                    >
                        {agents.filter(agent =>
                            ['router', 'web_search', 'api', 'data'].includes(agent.agent_type)
                        ).map((agent) => (
                            <SidebarItem
                                key={agent.id}
                                icon={
                                    <div className={`w-8 h-8 rounded-md ${getAgentIconClass(agent.agent_type as AgentType)} flex items-center justify-center`}>
                                        {getAgentIcon(agent.agent_type as AgentType)}
                                    </div>
                                }
                                label={agent.name}
                                subLabel={agent.description || "Initiate workflows"}
                                draggable={true}
                                onDragStart={(e) => handleDragStart(e, agent)}
                            />
                        ))}
                    </SidebarSection>

                    {/* Actions Section */}
                    <SidebarSection
                        title="Actions"
                        isOpen={sectionsState.actions}
                        onToggle={() => toggleSection('actions')}
                    >
                        {/* Notification Action */}
                        <SidebarItem
                            icon={
                                <div className="w-8 h-8 rounded-md bg-purple-100 flex items-center justify-center">
                                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                                        <g opacity="0.8">
                                            <path d="M10.5004 11.9998H5.00043M4.91577 12.2913L2.58085 19.266C2.39742 19.8139 2.3057 20.0879 2.37152 20.2566C2.42868 20.4031 2.55144 20.5142 2.70292 20.5565C2.87736 20.6052 3.14083 20.4866 3.66776 20.2495L20.3792 12.7293C20.8936 12.4979 21.1507 12.3822 21.2302 12.2214C21.2993 12.0817 21.2993 11.9179 21.2302 11.7782C21.1507 11.6174 20.8936 11.5017 20.3792 11.2703L3.66193 3.74751C3.13659 3.51111 2.87392 3.39291 2.69966 3.4414C2.54832 3.48351 2.42556 3.59429 2.36821 3.74054C2.30216 3.90893 2.3929 4.18231 2.57437 4.72906L4.91642 11.7853C4.94759 11.8792 4.96317 11.9262 4.96933 11.9742C4.97479 12.0168 4.97473 12.0599 4.96916 12.1025C4.96289 12.1506 4.94718 12.1975 4.91577 12.2913Z" stroke="#FF681F" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" />
                                        </g>
                                    </svg>
                                </div>
                            }
                            label="Notification"
                            subLabel="Send notifications"
                            draggable={true}
                            onDragStart={(e) => handleDragStart(e, {
                                id: 'notification-' + Date.now(),
                                type: 'notification',
                                name: 'Notification'
                            })}
                        />

                        {/* Conditional Action */}
                        <SidebarItem
                            icon={
                                <div className="w-8 h-8 rounded-md bg-green-100 flex items-center justify-center">
                                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                                        <g opacity="0.8">
                                            <path d="M21 12L9 12M21 6L9 6M21 18L9 18M5 12C5 12.5523 4.55228 13 4 13C3.44772 13 3 12.5523 3 12C3 11.4477 3.44772 11 4 11C4.55228 11 5 11.4477 5 12ZM5 6C5 6.55228 4.55228 7 4 7C3.44772 7 3 6.55228 3 6C3 5.44772 3.44772 5 4 5C4.55228 5 5 5.44772 5 6ZM5 18C5 18.5523 4.55228 19 4 19C3.44772 19 3 18.5523 3 18C3 17.4477 3.44772 17 4 17C4.55228 17 5 17.4477 5 18Z" stroke="#FF681F" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" />
                                        </g>
                                    </svg>
                                </div>
                            }
                            label="Conditional"
                            subLabel="Add conditional logic"
                            draggable={true}
                            onDragStart={(e) => handleDragStart(e, {
                                id: 'conditional-' + Date.now(),
                                type: 'conditional',
                                name: 'Conditional'
                            })}
                        />

                        {/* Delay Action */}
                        <SidebarItem
                            icon={
                                <div className="w-8 h-8 rounded-md bg-amber-100 flex items-center justify-center">
                                    <svg width="20" height="22" viewBox="0 0 20 22" fill="none" xmlns="http://www.w3.org/2000/svg">
                                        <path d="M10 8.5V12.5L12.5 14M10 4C5.30558 4 1.5 7.80558 1.5 12.5C1.5 17.1944 5.30558 21 10 21C14.6944 21 18.5 17.1944 18.5 12.5C18.5 7.80558 14.6944 4 10 4ZM10 4V1M8 1H12M18.329 4.59204L16.829 3.09204L17.579 3.84204M1.67102 4.59204L3.17102 3.09204L2.42102 3.84204" stroke="#FF681F" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" />
                                    </svg>
                                </div>
                            }
                            label="Delay"
                            subLabel="Add time delays"
                            draggable={true}
                            onDragStart={(e) => handleDragStart(e, {
                                id: 'delay-' + Date.now(),
                                type: 'delay',
                                name: 'Delay'
                            })}
                        />

                        {/* Troubleshooting Agent */}
                        {/* {AGENT_TYPES.filter(agent => agent.type === 'troubleshooting').map((agent) => (
                            <SidebarItem
                                key={agent.id}
                                icon={
                                    <div className={`w-8 h-8 rounded-md ${getAgentIconClass(agent.type as AgentType)} flex items-center justify-center`}>
                                        {getAgentIcon(agent.type as AgentType)}
                                    </div>
                                }
                                label={agent.name}
                                subLabel={agent.description || "Troubleshoot issues"}
                                draggable={true}
                                onDragStart={(e) => handleDragStart(e, agent)}
                            />
                        ))} */}
                    </SidebarSection>

                    {/* Tools Section */}
                    <SidebarSection
                        title="Tools"
                        isOpen={sectionsState.tools}
                        onToggle={() => toggleSection('tools')}
                    >
                        <SidebarItem
                            icon={
                                <div className="w-8 h-8 rounded-md bg-orange-100 flex items-center justify-center">
                                    <Zap size={20} className="text-orange-500" />
                                </div>
                            }
                            label="API Connectors"
                            subLabel="Connect to external APIs"
                            draggable={true}
                            onDragStart={(e) => handleDragStart(e, {
                                id: 'api-connector-' + Date.now(),
                                type: 'api_connector',
                                name: 'API Connector'
                            })}
                        />
                    </SidebarSection>
                </div>
            )}

            {/* Workflows Content (Initially Hidden) */}
            {activeTab === "workflows" && (
                <div className="p-4">
                    <p className="text-center text-gray-500 py-8">No saved workflows yet.</p>
                </div>
            )}

            {/* Footer Buttons */}
            <div className="designer-sidebar-controls-container pt-3 mt-auto space-y-2">
                {/* Save Workflow Button */}
                <button
                    onClick={() => (alert("Templates"))}
                    className="w-full bg-blue-500 text-white rounded-md text-sm font-medium hover:bg-blue-600 transition-colors flex items-center justify-center"
                >
                    Templates
                </button>

                {/* Deploy Workflow Button */}
                <button
                    onClick={() => (alert("Help"))}
                    className="w-full bg-orange-500 text-white rounded-md text-sm font-medium hover:bg-orange-600 transition-colors"
                >
                    Help & Support
                </button>
            </div>
        </div>
    );
};

export default DesignerSidebar;
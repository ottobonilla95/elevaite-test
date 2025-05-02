// DesignerSidebar.tsx
"use client";

import React, { useState } from "react";
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
    Save
} from "lucide-react";
import { AgentType, AGENT_TYPES } from "./type";
import "./DesignerSidebar.scss";

// SidebarSection component for collapsible sections
const SidebarSection: React.FC<{
    title: string;
    isOpen: boolean;
    onToggle: () => void;
    children?: React.ReactNode;
}> = ({ title, isOpen, onToggle, children }) => {
    return (
        <div className="sidebar-section mb-4">
            <div
                className="section-header flex items-center justify-between py-2 px-1 cursor-pointer"
                onClick={onToggle}
            >
                <h2 className="text-sm font-medium text-gray-800">{title}</h2>
                <div className="text-orange-500">
                    {isOpen ? <ChevronDown size={18} /> : <ChevronRight size={18} />}
                </div>
            </div>

            {isOpen && (
                <div className="section-content mt-2">
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

    // Toggle section visibility
    const toggleSection = (section: keyof typeof sectionsState) => {
        setSectionsState({
            ...sectionsState,
            [section]: !sectionsState[section]
        });
    };

    // Get agent icon based on type
    const getAgentIcon = (type: AgentType) => {
        switch (type) {
            case "router":
                return <Router size={20} className="text-purple-600" />;
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
        <div className="designer-sidebar bg-white border-r border-gray-200 w-64 h-full overflow-y-auto">
            {/* Workflow Header */}
            <div className="sidebar-header p-4 border-b border-gray-200">
                <h2 className="text-lg font-semibold mb-1">{workflowName}</h2>
                <p className="text-sm text-gray-500">{workflowDescription}</p>
            </div>

            {/* Navigation Tabs */}
            <div className="flex border-b border-gray-200">
                <div
                    className={`flex-1 text-center py-2 font-medium text-sm cursor-pointer ${activeTab === "actions"
                        ? "text-orange-500 border-b-2 border-orange-500"
                        : "text-gray-500 hover:text-orange-500"
                        }`}
                    onClick={() => setActiveTab("actions")}
                >
                    Actions
                </div>
                <div
                    className={`flex-1 text-center py-2 font-medium text-sm cursor-pointer ${activeTab === "workflows"
                        ? "text-orange-500 border-b-2 border-orange-500"
                        : "text-gray-500 hover:text-orange-500"
                        }`}
                    onClick={() => setActiveTab("workflows")}
                >
                    Workflows
                </div>
            </div>

            {/* Collapsible Sections */}
            {activeTab === "actions" && (
                <div className="p-4">
                    {/* Components Section */}
                    <SidebarSection
                        title="Components"
                        isOpen={sectionsState.components}
                        onToggle={() => toggleSection('components')}
                    >
                        {AGENT_TYPES.filter(agent =>
                            ['router', 'web_search', 'api', 'data'].includes(agent.type)
                        ).map((agent) => (
                            <SidebarItem
                                key={agent.id}
                                icon={
                                    <div className={`w-8 h-8 rounded-md ${getAgentIconClass(agent.type as AgentType)} flex items-center justify-center`}>
                                        {getAgentIcon(agent.type as AgentType)}
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
                                    <MessageSquare size={20} className="text-purple-600" />
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
                                    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-green-600">
                                        <path d="m8 3 4 8 5-5 5 15H2L8 3z" />
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
                                    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-amber-600">
                                        <circle cx="12" cy="12" r="10" />
                                        <polyline points="12 6 12 12 16 14" />
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
            <div className="p-4 mt-auto border-t border-gray-200 space-y-2">
                {/* Save Workflow Button */}
                <button
                    onClick={handleSaveWorkflow}
                    className="w-full px-4 py-2 bg-blue-500 text-white rounded-md text-sm font-medium hover:bg-blue-600 transition-colors flex items-center justify-center"
                    disabled={isLoading}
                >
                    <Save size={16} className="mr-2" />
                    {isLoading ? 'Saving...' : 'Save Workflow'}
                </button>

                {/* Deploy Workflow Button */}
                <button
                    onClick={handleDeployWorkflow}
                    className="w-full px-4 py-2 bg-orange-500 text-white rounded-md text-sm font-medium hover:bg-orange-600 transition-colors"
                    disabled={isLoading}
                >
                    {isLoading ? 'Deploying...' : 'Deploy Workflow'}
                </button>
            </div>
        </div>
    );
};

export default DesignerSidebar;
// UpdatedSidebar.tsx
import React, { useState } from "react";
import { ChevronDown, ChevronRight } from "lucide-react";

// Define types for sidebar sections and items
interface SidebarItemProps {
    icon: React.ReactNode;
    label: string;
    subLabel?: string;
    onClick?: () => void;
}

interface SidebarSectionProps {
    title: string;
    isOpen: boolean;
    onToggle: () => void;
    children?: React.ReactNode;
}

// SidebarItem component
const SidebarItem: React.FC<SidebarItemProps> = ({ icon, label, subLabel, onClick }) => {
    return (
        <div
            className="sidebar-item cursor-pointer p-2 mb-2 rounded-md hover:bg-gray-100"
            onClick={onClick}
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

// SidebarSection component with toggle
const SidebarSection: React.FC<SidebarSectionProps> = ({
    title,
    isOpen,
    onToggle,
    children
}) => {
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

// Main sidebar component
const UpdatedSidebar: React.FC<{
    workflowName: string;
    workflowId: string;
    agentTypes: any[];
    handleDragStart: (event: React.DragEvent<HTMLDivElement>, agent: any) => void;
    handleSaveWorkflow: () => void;
    handleDeployWorkflow: () => void;
    isLoading: boolean;
}> = ({
    workflowName,
    workflowId,
    agentTypes,
    handleDragStart,
    handleSaveWorkflow,
    handleDeployWorkflow,
    isLoading
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

        return (
            <div className="designer-sidebar bg-white border-r border-gray-200 w-64 h-full overflow-y-auto">
                {/* Workflow Header */}
                <div className="sidebar-header p-4 border-b border-gray-200">
                    <h2 className="text-lg font-semibold mb-1">{workflowName}</h2>
                    <p className="text-sm text-gray-500">Analyze and process invoice documents</p>
                </div>

                {/* Navigation Tabs */}
                <div className="flex border-b border-gray-200">
                    <div className="flex-1 text-center py-2 text-orange-500 border-b-2 border-orange-500 font-medium text-sm">
                        Actions
                    </div>
                    <div className="flex-1 text-center py-2 text-gray-500 font-medium text-sm">
                        Workflows
                    </div>
                </div>

                {/* Collapsible Sections */}
                <div className="p-4">
                    {/* Components Section */}
                    <SidebarSection
                        title="Components"
                        isOpen={sectionsState.components}
                        onToggle={() => toggleSection('components')}
                    >
                        {agentTypes.filter(agent => ['router', 'web_search', 'api', 'data'].includes(agent.type)).map((agent) => (
                            <div
                                key={agent.id}
                                draggable
                                onDragStart={(e) => handleDragStart(e, agent)}
                            >
                                <SidebarItem
                                    icon={getAgentIcon(agent.type)}
                                    label={agent.name}
                                    subLabel={`Initiate workflows`}
                                />
                            </div>
                        ))}
                    </SidebarSection>

                    {/* Actions Section */}
                    <SidebarSection
                        title="Actions"
                        isOpen={sectionsState.actions}
                        onToggle={() => toggleSection('actions')}
                    >
                        {agentTypes.filter(agent => agent.type === 'troubleshooting').map((agent) => (
                            <div
                                key={agent.id}
                                draggable
                                onDragStart={(e) => handleDragStart(e, agent)}
                            >
                                <SidebarItem
                                    icon={getAgentIcon(agent.type)}
                                    label={agent.name}
                                    subLabel={`Initiate workflows`}
                                />
                            </div>
                        ))}
                    </SidebarSection>

                    {/* Tools Section */}
                    <SidebarSection
                        title="Tools"
                        isOpen={sectionsState.tools}
                        onToggle={() => toggleSection('tools')}
                    >
                        {/* You can add tool items here */}
                    </SidebarSection>
                </div>

                {/* Footer Buttons */}
                <div className="p-4 mt-auto">
                    <button
                        className="w-full mb-2 py-2 px-4 rounded-md border border-orange-500 text-orange-500 text-center text-sm font-medium"
                    >
                        Templates
                    </button>
                    <button
                        className="w-full py-2 px-4 rounded-md border border-orange-500 text-orange-500 text-center text-sm font-medium"
                    >
                        Help & Support
                    </button>
                </div>
            </div>
        );
    };

// Helper function to get the appropriate icon based on agent type
const getAgentIcon = (type: string) => {
    // You can reuse your existing getAgentIcon function here
    // or import the icons from Lucide React
    return <div className={`w-6 h-6 flex items-center justify-center rounded-md ${getAgentIconClass(type)}`}></div>;
};

// Helper function to get icon class based on agent type
const getAgentIconClass = (type: string) => {
    switch (type) {
        case 'router':
            return 'bg-purple-100 text-purple-600';
        case 'web_search':
            return 'bg-blue-100 text-blue-600';
        case 'api':
            return 'bg-green-100 text-green-600';
        case 'data':
            return 'bg-yellow-100 text-yellow-600';
        case 'troubleshooting':
            return 'bg-red-100 text-red-600';
        default:
            return 'bg-gray-100 text-gray-600';
    }
};

export default UpdatedSidebar;
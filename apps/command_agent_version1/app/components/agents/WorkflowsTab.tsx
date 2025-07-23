"use client";

import React, { useState } from "react";
import {
    Trash2,
    FileText,
    RefreshCw
} from "lucide-react";
import { useWorkflows } from "../../ui/contexts/WorkflowsContext";
import { type SavedWorkflow } from "../../lib/interfaces"

import "./WorkflowsTab.scss";

// Transform function moved to WorkflowsContext

interface WorkflowsTabProps {
    onCreateNewWorkflow: () => void;
    onLoadWorkflow: (workflow: SavedWorkflow) => void;
}

function WorkflowsTab({
    onCreateNewWorkflow,
    onLoadWorkflow
}: WorkflowsTabProps): JSX.Element {
    // Use workflows context
    const {
        workflows: allWorkflows,
        isLoading,
        deleteWorkflowAndRefresh,
        getWorkflowDetails
    } = useWorkflows();

    // State for template toggle
    const [showMyTemplates, setShowMyTemplates] = useState(true);

    // Filter workflows based on toggle state
    const savedWorkflows = showMyTemplates
        ? allWorkflows // Show all workflows when toggle is on
        : allWorkflows.filter(workflow => !workflow.is_editable); // Show only non-editable (system templates) when toggle is off

    // No longer need local loading function - handled by context

    const formatDate = (dateString: string) => {
        const date = new Date(dateString);
        return date.toLocaleDateString("en-US", {
            month: "short",
            day: "numeric",
            year: "numeric",
        });
    }

    /*For testing*/
    /* useEffect(() => {
      setWorkflows(mockupWorkflows);
    }, []); */
    /*For testing*/

    const handleDeleteWorkflow = async (workflowId: string): Promise<void> => {
        if (!window.confirm("Are you sure you want to delete this workflow?")) {
            return;
        }

        try {
            await deleteWorkflowAndRefresh(workflowId);
            // TODO: Replace with proper toast notification
            window.alert("Workflow deleted successfully.");
        } catch (deleteError) {
            // eslint-disable-next-line no-console -- Error logging is acceptable
            console.error('Error deleting workflow:', deleteError);
            // TODO: Replace with proper toast notification
            window.alert("Failed to delete workflow. Please try again.");
        }
    };

    const handleLoadWorkflow = async (workflow: SavedWorkflow): Promise<void> => {
        try {
            // Get full workflow details including agents and connections
            const workflowDetails = await getWorkflowDetails(workflow.workflow_id);

            // eslint-disable-next-line no-console -- Debug logging is acceptable
            console.log("Workflow details:", workflowDetails);

            // Call the parent component's load function with the full details
            onLoadWorkflow(workflowDetails);
        } catch (loadError) {
            // eslint-disable-next-line no-console -- Error logging is acceptable
            console.error('Error loading workflow:', loadError);
            // TODO: Replace with proper toast notification
            window.alert("Failed to load workflow. Please try again.");
        }
    };

    return (
        <div className="workflows-tab p-2 w-full">
            {/* Header */}
            <div className="flex flex-col gap-4 justify-between items-center my-3">
                {/* Template Toggle */}
                <div className="flex w-full items-center justify-end gap-3">
                    <label className="flex self-end gap-3 cursor-pointer">
                        <span className="text-sm text-gray-500">My Templates</span>
                        <div className="relative">
                            <input
                                type="checkbox"
                                checked={showMyTemplates}
                                onChange={(e) => { setShowMyTemplates(e.target.checked); }}
                                className="sr-only"
                            />
                            <div className={`transition-colors duration-200 ease-in-out ${showMyTemplates ? 'bg-orange-500' : 'bg-gray-300'
                                } flex items-center `} style={{ width: '40px', height: '20px', borderRadius: '12px' }}>
                                <div className={`bg-white rounded-full shadow-md transform transition-transform duration-200 ease-in-out ${showMyTemplates ? 'translate-x-6' : 'translate-x-1'
                                    } flex items-center justify-center`} style={{ width: '13.75px', height: '13.75px' }} />
                            </div>
                        </div>
                    </label>
                </div>
            </div>

            {/* Error Message */}
            {/*  {error ? (
                <div className="mb-4 p-3 bg-red-100 border border-red-300 text-red-700 rounded-md">
                    {error}
                </div>
            ) : null} */}

            {/* Workflows List */}
            <div className="space-y-3 w-full">
                {isLoading && savedWorkflows.length === 0 ? (
                    <div className="text-center py-12">
                        <RefreshCw size={48} className="mx-auto text-gray-300 mb-4 animate-spin" />
                        <p className="text-gray-500">Loading workflows...</p>
                    </div>
                ) : savedWorkflows.length === 0 ? (
                    <div className="text-center py-12">
                        <FileText size={48} className="mx-auto text-gray-300 mb-4" />
                        <p className="text-gray-500 mb-4">No saved workflows yet.</p>
                        <button
                            onClick={onCreateNewWorkflow}
                            className="px-4 py-2 bg-orange-500 text-white rounded-md text-sm font-medium hover:bg-orange-600 transition-colors"
                            type="button"
                        >
                            Create Your First Workflow
                        </button>
                    </div>
                ) : (
                    savedWorkflows.map((workflow) => (
                        <div
                            key={workflow.workflow_id}
                            data-test1={`workflow-item-${workflow.workflow_id}`}
                            className="workflow-item border border-gray-200 rounded-xl py-3 px-4 hover:border-orange-300 transition-colors cursor-pointer"
                            onClick={() => void handleLoadWorkflow(workflow)}
                            onKeyDown={(e) => {
                                if (e.key === 'Enter' || e.key === ' ') {
                                    e.preventDefault();
                                    void handleLoadWorkflow(workflow);
                                }
                            }}
                            role="button"
                            tabIndex={0}
                            aria-label={`Load workflow: ${workflow.name}`}
                        >

                            <div className="flex items-center justify-between">
                                <div className="text-sm font-bold">
                                    {workflow.name}
                                </div>
                                <div className="flex items-center gap-2">
                                    <button>
                                        <svg width="16" height="17" viewBox="0 0 16 17" fill="none" xmlns="http://www.w3.org/2000/svg">
                                            <g opacity="0.8">
                                                <path d="M13.9999 14.5H8.66652M1.6665 14.8333L5.36602 13.4104C5.60264 13.3194 5.72096 13.2739 5.83165 13.2145C5.92997 13.1617 6.0237 13.1008 6.11186 13.0324C6.21112 12.9554 6.30075 12.8657 6.48002 12.6865L13.9999 5.16665C14.7362 4.43027 14.7362 3.23636 13.9999 2.49998C13.2635 1.7636 12.0696 1.7636 11.3332 2.49998L3.81336 10.0198C3.63409 10.1991 3.54445 10.2887 3.46743 10.388C3.39902 10.4761 3.3381 10.5698 3.28533 10.6682C3.22591 10.7789 3.1804 10.8972 3.08939 11.1338L1.6665 14.8333ZM1.6665 14.8333L3.03858 11.266C3.13677 11.0107 3.18586 10.883 3.27006 10.8246C3.34365 10.7735 3.43471 10.7542 3.5227 10.771C3.62339 10.7902 3.72009 10.8869 3.91349 11.0803L5.41955 12.5863C5.61295 12.7797 5.70965 12.8764 5.72888 12.9771C5.74568 13.0651 5.72636 13.1562 5.67527 13.2298C5.6168 13.314 5.48916 13.3631 5.23388 13.4613L1.6665 14.8333Z" stroke="#212124" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
                                            </g>
                                        </svg>
                                    </button>
                                    {/* Only show delete button for editable workflows */}
                                    {workflow.is_editable ? <button
                                        onClick={(e) => {
                                            e.stopPropagation();
                                            void handleDeleteWorkflow(workflow.workflow_id);
                                        }}
                                        className="flex items-center justify-center"
                                        disabled={isLoading}
                                        type="button"
                                    >
                                        <Trash2 size={16} className="mr-1" />
                                    </button> : null}
                                </div>
                            </div>

                            {workflow.created_at && workflow.is_active && (
                                <div className="flex items-center justify-between gap-2 my-2">
                                    <div className="text-[#31C493] rounded-lg py-1 px-2" style={{ fontSize: '10px', border: '1px solid #31C493' }}>Active</div>
                                    <div className="italic opacity-50 text-xs"><strong>Updated</strong>: {formatDate(workflow.created_at)}</div>
                                </div>
                            )}

                            <div className="my-2 text-xs">
                                {workflow.description}
                            </div>

                            {/* Tags Section */}
                            <div className="workflow-tags-section flex gap-2 flex-wrap">
                                {!workflow.is_editable && (
                                    <span className="px-2 py-1 bg-purple-100 text-purple-700 text-xs rounded-full whitespace-nowrap">
                                        System Template
                                    </span>
                                )}
                                {workflow.tags && workflow.tags.length > 0 ? (
                                    workflow.tags.map((tag: string) => (
                                        <span
                                            key={tag}
                                            className="tag-blue"
                                        >
                                            {tag}
                                        </span>
                                    ))
                                ) : null}
                            </div>

                            {/* Meta Information */}
                            {/* <div className="workflow-meta-section mb-4">
                                <div className="flex flex-wrap items-center gap-3 text-xs text-gray-500">
                                    <div className="flex items-center gap-1">
                                        <User size={12} />
                                        {workflow.created_by ?? "Unknown"}
                                    </div>
                                    <div className="flex items-center gap-1">
                                        <Calendar size={12} />
                                        {formatDate(workflow.created_at)}
                                    </div>
                                    <div className="flex items-center gap-1">
                                        <Settings size={12} />
                                        {workflow.agent_count ?? 0} agents, {workflow.connection_count ?? 0} connections
                                    </div>
                                    {workflow.deployed_at ? (
                                        <div className="flex items-center gap-1">
                                            <Play size={12} />
                                            Deployed: {formatDate(workflow.deployed_at)}
                                        </div>
                                    ) : null}
                                </div>
                            </div> */}

                            {/* Action Buttons Section */}
                            <div className="workflow-actions-section">
                                <div className="flex gap-2" />
                            </div>
                        </div>
                    ))
                )}
            </div>


        </div>
    );
}

export default WorkflowsTab;

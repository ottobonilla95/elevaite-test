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
        error,
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



    const handleDeleteWorkflow = async (workflowId: string) => {
        if (!confirm("Are you sure you want to delete this workflow?")) {
            return;
        }

        try {
            await deleteWorkflowAndRefresh(workflowId);
            alert("Workflow deleted successfully.");
        } catch (error) {
            console.error('Error deleting workflow:', error);
            alert("Failed to delete workflow. Please try again.");
        }
    };

    const handleLoadWorkflow = async (workflow: SavedWorkflow) => {
        try {
            // Get full workflow details including agents and connections
            const workflowDetails = await getWorkflowDetails(workflow.workflow_id);

            console.log("Workflow details:", workflowDetails);

            // Call the parent component's load function with the full details
            onLoadWorkflow(workflowDetails);
        } catch (error) {
            console.error('Error loading workflow:', error);
            alert("Failed to load workflow. Please try again.");
        }
    };



    return (
        <div className="workflows-tab p-4 w-full">
            {/* Header */}
            <div className="flex flex-col gap-4 justify-between items-center mb-6">
                <div>
                    <h3 className="text-lg font-semibold text-gray-800">Saved Workflows</h3>
                    <p className="text-sm text-gray-500">Manage and deploy your agent workflows</p>
                </div>

                {/* Template Toggle */}
                <div className="flex w-full items-center justify-end gap-3">
                    <label className="flex self-end gap-3 cursor-pointer">
                        <span className="text-sm text-gray-700">My Templates</span>
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
            {error ? (
                <div className="mb-4 p-3 bg-red-100 border border-red-300 text-red-700 rounded-md">
                    {error}
                </div>
            ) : null}

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
                            className="workflow-item border border-gray-200 rounded-lg p-4 hover:border-orange-300 transition-colors flex w-full cursor-pointer"
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
                            {/* Title Section */}
                            <div className="flex justify-between items-center pb-3">
                                <div className="workflow-title-section mb-3 flex justify-start items-start flex-col">
                                    <h4 className="text-sm font-medium text-gray-800 leading-tight">{workflow.name}</h4>
                                    <p className="text-xs text-gray-600 mt-1">{workflow.description ?? "No description"}</p>
                                </div>
                                {/* Only show delete button for editable workflows */}
                                {workflow.is_editable ? <button
                                    onClick={(e) => {
                                        e.stopPropagation();
                                        void handleDeleteWorkflow(workflow.workflow_id);
                                    }}
                                    className="px-2 py-2 flex items-center justify-center hover:border"
                                    disabled={isLoading}
                                    type="button"
                                >
                                    <Trash2 size={16} className="mr-1" />
                                </button> : null}
                            </div>

                            {/* Tags Section */}
                            <div className="workflow-tags-section mb-3">
                                <div className="flex gap-2 flex-wrap">
                                    {!workflow.is_editable && (
                                        <span className="px-2 py-1 bg-purple-100 text-purple-700 text-xs rounded-full whitespace-nowrap">
                                            System Template
                                        </span>
                                    )}
                                    {workflow.tags && workflow.tags.length > 0 ? (
                                        workflow.tags.map((tag: string) => (
                                            <span
                                                key={tag}
                                                className="px-2 py-1 bg-blue-100 text-blue-700 text-xs rounded-full whitespace-nowrap"
                                            >
                                                {tag}
                                            </span>
                                        ))
                                    ) : null}
                                </div>
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


        </div >
    );
}

export default WorkflowsTab;

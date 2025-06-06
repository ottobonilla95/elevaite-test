"use client";

import React, { useState, useEffect } from "react";
import {
    Play,
    Trash2,
    Plus,
    FileText,
    Calendar,
    User,
    Settings,
    Download,
    RefreshCw
} from "lucide-react";
import { getWorkflows, getWorkflowDetails, deleteWorkflow } from "../lib/actions";
import { SavedWorkflow } from "../lib/interfaces"

import "./WorkflowsTab.scss";

// Transform workflow data to match our interface
function transformWorkflowData(workflows: any[]): SavedWorkflow[] {
    return workflows.map((workflow: any) => ({
        workflow_id: workflow.workflow_id,
        name: workflow.name,
        description: workflow.description,
        created_at: workflow.created_at,
        created_by: workflow.created_by,
        is_active: workflow.is_active,
        is_deployed: workflow.is_deployed,
        deployed_at: workflow.deployed_at,
        version: workflow.version,
        agent_count: workflow.workflow_agents?.length || 0,
        connection_count: workflow.workflow_connections?.length || 0
    }));
}

interface WorkflowsTabProps {
    onCreateNewWorkflow: () => void;
    onLoadWorkflow: (workflow: SavedWorkflow) => void;
}

const WorkflowsTab: React.FC<WorkflowsTabProps> = ({
    onCreateNewWorkflow,
    onLoadWorkflow
}) => {
    const [savedWorkflows, setSavedWorkflows] = useState<SavedWorkflow[]>([]);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    // Load workflows from API
    const loadWorkflows = async () => {
        setIsLoading(true);
        setError(null);
        try {
            const workflows = await getWorkflows();
            const transformedWorkflows = transformWorkflowData(workflows);
            setSavedWorkflows(transformedWorkflows);
        } catch (error) {
            console.error('Error loading workflows:', error);
            setError('Failed to load workflows. Please try again.');
            // Fallback to empty array
            setSavedWorkflows([]);
        } finally {
            setIsLoading(false);
        }
    };

    // Load workflows on component mount
    useEffect(() => {
        loadWorkflows();
    }, []);



    const handleDeleteWorkflow = async (workflowId: string) => {
        if (!confirm("Are you sure you want to delete this workflow?")) {
            return;
        }

        setIsLoading(true);
        try {
            await deleteWorkflow(workflowId);
            setSavedWorkflows(prev => prev.filter(w => w.workflow_id !== workflowId));
            alert("Workflow deleted successfully.");
        } catch (error) {
            console.error('Error deleting workflow:', error);
            alert("Failed to delete workflow. Please try again.");
        } finally {
            setIsLoading(false);
        }
    };

    const handleLoadWorkflow = async (workflow: SavedWorkflow) => {
        setIsLoading(true);
        try {
            // Get full workflow details including agents and connections
            const workflowDetails = await getWorkflowDetails(workflow.workflow_id);

            console.log("Workflow details:", workflowDetails);

            // Call the parent component's load function with the full details
            onLoadWorkflow(workflowDetails);

            // alert(`Loaded workflow: ${workflow.name}`);
        } catch (error) {
            console.error('Error loading workflow:', error);
            alert("Failed to load workflow. Please try again.");
        } finally {
            setIsLoading(false);
        }
    };

    const formatDate = (dateString: string) => {
        return new Date(dateString).toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    };

    return (
        <div className="workflows-tab p-4 w-full">
            {/* Header */}
            <div className="flex flex-col gap-2 justify-between items-center mb-6">
                <div>
                    <h3 className="text-lg font-semibold text-gray-800">Saved Workflows</h3>
                    <p className="text-sm text-gray-500">Manage and deploy your agent workflows</p>
                </div>
                <div className="flex gap-2">
                    <button
                        onClick={loadWorkflows}
                        className="px-3 py-2 bg-gray-500 text-white rounded-md text-sm font-medium hover:bg-gray-600 transition-colors flex items-center"
                        disabled={isLoading}
                    >
                        <RefreshCw size={16} className={`mr-2 ${isLoading ? 'animate-spin' : ''}`} />
                        Refresh
                    </button>
                    <button
                        onClick={onCreateNewWorkflow}
                        className="px-3 py-2 bg-green-500 text-white rounded-md text-sm font-medium hover:bg-green-600 transition-colors flex items-center"
                    >
                        <Plus size={16} className="mr-2" />
                        New Workflow
                    </button>
                </div>
            </div>

            {/* Error Message */}
            {error && (
                <div className="mb-4 p-3 bg-red-100 border border-red-300 text-red-700 rounded-md">
                    {error}
                </div>
            )}

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
                        >
                            Create Your First Workflow
                        </button>
                    </div>
                ) : (
                    savedWorkflows.map((workflow) => (
                        <div
                            key={workflow.workflow_id}
                            className="border border-gray-200 rounded-lg p-4 hover:border-orange-300 transition-colors flex flex-wrap w-full"
                        >
                            <div className="flex justify-between items-start flex-wrap w-full">
                                <div className="flex flex-col w-full">
                                    <div className="flex items-center gap-2 mb-2 w-full">
                                        <h4 className="font-medium text-gray-800 text-balance w-full">{workflow.name}</h4>
                                        {workflow.is_deployed && (
                                            <span className="px-2 py-1 bg-green-100 text-green-700 text-xs rounded-full">
                                                Deployed
                                            </span>
                                        )}
                                        {workflow.is_active && (
                                            <span className="px-2 py-1 bg-blue-100 text-blue-700 text-xs rounded-full">
                                                Active
                                            </span>
                                        )}
                                    </div>
                                    <p className="text-sm text-gray-600 mb-2">{workflow.description || "No description"}</p>

                                    <div className="flex flex-wrap items-center gap-2 mb-2 text-xs text-gray-500">
                                        <div className="flex items-center gap-1">
                                            <User size={12} />
                                            {workflow.created_by || "Unknown"}
                                        </div>
                                        <div className="flex items-center gap-1">
                                            <Calendar size={12} />
                                            {formatDate(workflow.created_at)}
                                        </div>
                                        <div className="flex items-center gap-1">
                                            <Settings size={12} />
                                            {workflow.agent_count || 0} agents, {workflow.connection_count || 0} connections
                                        </div>
                                        {workflow.deployed_at && (
                                            <div className="flex items-center gap-1">
                                                <Play size={12} />
                                                Deployed: {formatDate(workflow.deployed_at)}
                                            </div>
                                        )}
                                    </div>
                                </div>

                                <div className="flex gap-2 ml-4">
                                    <button
                                        onClick={() => handleLoadWorkflow(workflow)}
                                        className="px-3 py-1 bg-blue-500 text-white rounded text-xs hover:bg-blue-600 transition-colors flex items-center"
                                        disabled={isLoading}
                                    >
                                        <Download size={12} className="mr-1" />
                                        Load
                                    </button>
                                    <button
                                        onClick={() => handleDeleteWorkflow(workflow.workflow_id)}
                                        className="px-3 py-1 bg-red-500 text-white rounded text-xs hover:bg-red-600 transition-colors flex items-center"
                                        disabled={isLoading}
                                    >
                                        <Trash2 size={12} className="mr-1" />
                                        Delete
                                    </button>
                                </div>
                            </div>
                        </div>
                    ))
                )}
            </div>


        </div>
    );
};

export default WorkflowsTab;

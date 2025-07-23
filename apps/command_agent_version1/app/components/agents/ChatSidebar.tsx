"use client";

import React, { useState, useEffect } from "react";
import { Settings, Plus, List, ArrowLeft } from "lucide-react";
import "./ChatSidebar.scss";

interface WorkflowItem {
    id: string;
    name: string;
    timestamp: string;
}

interface ChatSidebarProps {
    workflowName: string;
    workflowId: string;
    onExitChat: () => void;
    onCreateNewWorkflow: () => void;
    onSwitchWorkflow?: (workflowId: string) => void;
    isLoading: boolean;
}

function ChatSidebar({
    workflowName,
    workflowId,
    onExitChat,
    onCreateNewWorkflow,
    onSwitchWorkflow,
    isLoading
}: ChatSidebarProps): JSX.Element {
    const [activeTab, setActiveTab] = useState<"Actions" | "Workflows">("Actions");
    const [savedWorkflows, setSavedWorkflows] = useState<WorkflowItem[]>([]);

    // Simulate fetching saved workflows
    useEffect(() => {
        // This would be replaced with an actual API call
        const mockSavedWorkflows: WorkflowItem[] = [
            {
                id: workflowId,
                name: workflowName,
                timestamp: "Just now"
            },
            {
                id: "3f9d8a21",
                name: "Customer Support Flow",
                timestamp: "Yesterday"
            },
            {
                id: "7a2b5c88",
                name: "Data Processing Pipeline",
                timestamp: "2 days ago"
            }
        ];

        setSavedWorkflows(mockSavedWorkflows);
    }, [workflowId, workflowName]);

    // Handle workflow selection
    const handleWorkflowSelect = (selectedId: string) => {
        if (onSwitchWorkflow && !isLoading) {
            onSwitchWorkflow(selectedId);
        }
    };

    return (
        <div className="chat-sidebar">
            <div className="chat-sidebar-header">
                <h2 className="workflow-title">{workflowName}</h2>
                <div className="workflow-id">
                    ID: {workflowId.substring(0, 8)}
                </div>
            </div>

            <div className="chat-sidebar-tabs">
                <div
                    className={`chat-sidebar-tab ${activeTab === "Actions" ? "active" : ""}`}
                    onClick={() => { setActiveTab("Actions"); }}
                >
                    Actions
                </div>
                <div
                    className={`chat-sidebar-tab ${activeTab === "Workflows" ? "active" : ""}`}
                    onClick={() => { setActiveTab("Workflows"); }}
                >
                    Workflows
                </div>
            </div>

            <div className="chat-sidebar-content">
                {activeTab === "Actions" ? (
                    <>
                        <button
                            onClick={onExitChat}
                            className="sidebar-button edit-button"
                            disabled={isLoading}
                        >
                            <Settings size={16} className="button-icon" />
                            Edit Workflow
                        </button>

                        <button
                            onClick={onCreateNewWorkflow}
                            className="sidebar-button new-button"
                            disabled={isLoading}
                        >
                            <Plus size={16} className="button-icon" />
                            New Workflow
                        </button>
                    </>
                ) : (
                    <div className="saved-workflows">
                        {savedWorkflows.length === 0 ? (
                            <div className="no-workflows">
                                <p>No saved workflows</p>
                            </div>
                        ) : (
                            savedWorkflows.map(workflow => (
                                <div
                                    key={workflow.id}
                                    className={`workflow-item ${workflow.id === workflowId ? "active" : ""}`}
                                    onClick={() => { handleWorkflowSelect(workflow.id); }}
                                >
                                    <div className="workflow-item-content">
                                        <List size={16} className="workflow-icon" />
                                        <div className="workflow-details">
                                            <div className="workflow-name">{workflow.name}</div>
                                            <div className="workflow-time">{workflow.timestamp}</div>
                                        </div>
                                    </div>
                                </div>
                            ))
                        )}
                    </div>
                )}
            </div>

            <div className="chat-sidebar-footer">
                <button
                    onClick={onExitChat}
                    className="return-button"
                    disabled={isLoading}
                >
                    {isLoading ? 'Loading...' : (
                        <>
                            <ArrowLeft size={16} className="return-icon" />
                            Return to Editor
                        </>
                    )}
                </button>
            </div>
        </div>
    );
};

export default ChatSidebar;
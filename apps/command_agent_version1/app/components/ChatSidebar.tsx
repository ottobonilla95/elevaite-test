// ChatSidebar.tsx
"use client";

import React from "react";
import { Settings, Plus } from "lucide-react";
import "./ChatSidebar.scss";

interface ChatSidebarProps {
    workflowName: string;
    workflowId: string;
    onExitChat: () => void;
    onCreateNewWorkflow: () => void;
    isLoading: boolean;
}

const ChatSidebar: React.FC<ChatSidebarProps> = ({
    workflowName,
    workflowId,
    onExitChat,
    onCreateNewWorkflow,
    isLoading
}) => {
    return (
        <div className="chat-sidebar">
            <div className="chat-sidebar-header">
                <h2 className="workflow-title">{workflowName}</h2>
                <div className="workflow-id">
                    ID: {workflowId.substring(0, 8)}
                </div>
            </div>

            <div className="chat-sidebar-tabs">
                <div className="chat-sidebar-tab active">
                    Actions
                </div>
                <div className="chat-sidebar-tab">
                    Workflows
                </div>
            </div>

            <div className="chat-sidebar-content">
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
            </div>

            <div className="chat-sidebar-footer">
                <button
                    onClick={onExitChat}
                    className="return-button"
                    disabled={isLoading}
                >
                    {isLoading ? 'Loading...' : 'Return to Editor'}
                </button>
            </div>
        </div>
    );
};

export default ChatSidebar;
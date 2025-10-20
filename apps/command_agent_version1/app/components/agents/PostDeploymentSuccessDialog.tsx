"use client";

import React, { useState } from "react";
import { CommonDialog } from '@repo/ui/components';
import { CheckCircle, Copy, Calendar, User, Wrench, ExternalLink, Check } from "lucide-react";
import type { WorkflowDeployment, WorkflowResponse } from "../../lib/interfaces/workflows";
import type { ChatCompletionToolParam } from "../../lib/interfaces/common";
import "./PostDeploymentSuccessDialog.scss";

interface PostDeploymentSuccessDialogProps {
    isOpen: boolean;
    onClose: () => void;
    deployment: WorkflowDeployment;
    workflow: WorkflowResponse;
    inferenceUrl: string;
    tools?: ChatCompletionToolParam[];
}

function PostDeploymentSuccessDialog({
    isOpen,
    onClose,
    deployment,
    workflow,
    inferenceUrl,
    tools = []
}: PostDeploymentSuccessDialogProps): JSX.Element | null {

    const [copiedUrl, setCopiedUrl] = useState(false);

    if (!isOpen) return null;

    const handleCopyUrl = async (): Promise<void> => {
        try {
            await navigator.clipboard.writeText(inferenceUrl);
            setCopiedUrl(true);
            setTimeout(() => { setCopiedUrl(false); }, 2000);
        } catch (error) {
            console.error("Failed to copy URL:", error);
        }
    };

    const formatDate = (dateString: string): string => {
        return new Date(dateString).toLocaleString();
    };

    const handleContinue = (): void => {
        onClose();
    };

    return (
        <CommonDialog
            className="deployment-success-dialog"
            title="Deployment Successful!"
            onConfirm={handleContinue}
            onCancel={onClose}
            confirmLabel="Continue"
            cancelLabel=""
            icon={<CheckCircle size={24} className="text-green-500" />}
        >
            <div className="post-deployment-dialog-content">
                {/* Success Message */}
                <div className="success-message">
                    <p className="success-text">
                        Your workflow <strong>&quot;{workflow.name}&quot;</strong> has been successfully deployed
                        and is now available for chat interactions.
                    </p>
                </div>

                {/* Deployment Details */}
                <div className="deployment-details">
                    <h4 className="section-title">Deployment Information</h4>
                    <div className="detail-grid">
                        <div className="detail-item">
                            <Calendar size={16} className="detail-icon" />
                            <div className="detail-content">
                                <span className="detail-label">Deployed At</span>
                                <span className="detail-value">{formatDate(deployment.deployed_at)}</span>
                            </div>
                        </div>

                        {deployment.deployed_by ? <div className="detail-item">
                            <User size={16} className="detail-icon" />
                            <div className="detail-content">
                                <span className="detail-label">Deployed By</span>
                                <span className="detail-value">{deployment.deployed_by}</span>
                            </div>
                        </div> : null}

                        <div className="detail-item">
                            <ExternalLink size={16} className="detail-icon" />
                            <div className="detail-content">
                                <span className="detail-label">Environment</span>
                                <span className="detail-value">{deployment.environment}</span>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Workflow Information */}
                <div className="workflow-info">
                    <h4 className="section-title">Workflow Details</h4>
                    <div className="workflow-summary">
                        <div className="summary-item">
                            <span className="summary-label">Agents:</span>
                            <span className="summary-value">{workflow.workflow_agents.length || 0}</span>
                        </div>
                        <div className="summary-item">
                            <span className="summary-label">Connections:</span>
                            <span className="summary-value">{workflow.workflow_connections.length || 0}</span>
                        </div>
                        <div className="summary-item">
                            <span className="summary-label">Version:</span>
                            <span className="summary-value">{workflow.version}</span>
                        </div>
                    </div>

                    {workflow.description ? <div className="workflow-description">
                        <span className="description-label">Description:</span>
                        <p className="description-text">{workflow.description}</p>
                    </div> : null}
                </div>

                {/* Tools Information */}
                {tools.length > 0 && (
                    <div className="tools-info">
                        <h4 className="section-title">
                            <Wrench size={16} className="section-icon" />
                            Available Tools ({tools.length})
                        </h4>
                        <div className="tools-list">
                            {tools.slice(0, 6).map((tool, index) => (
                                <div key={index} className="tool-item">
                                    <span className="tool-name">{tool.function.name}</span>
                                    {tool.function.description ? <span className="tool-description">{tool.function.description}</span> : null}
                                </div>
                            ))}
                            {tools.length > 6 && (
                                <div className="tool-item more-tools">
                                    <span className="tool-name">+{tools.length - 6} more tools</span>
                                </div>
                            )}
                        </div>
                    </div>
                )}

                {/* Inference URL */}
                <div className="inference-url-section">
                    <h4 className="section-title">Inference Endpoint</h4>
                    <div className="url-container">
                        <div className="url-display">
                            <code className="url-text">{inferenceUrl}</code>
                        </div>
                        <button
                            onClick={handleCopyUrl}
                            className={`copy-button ${copiedUrl ? 'copied' : ''}`}
                            type="button"
                        >
                            {copiedUrl ? (
                                <>
                                    <Check size={16} />
                                    Copied!
                                </>
                            ) : (
                                <>
                                    <Copy size={16} />
                                    Copy URL
                                </>
                            )}
                        </button>
                    </div>
                    <p className="url-note">
                        Use this endpoint to send queries to your deployed workflow via API calls.
                    </p>
                </div>
            </div>
        </CommonDialog>
    );
}

export default PostDeploymentSuccessDialog;

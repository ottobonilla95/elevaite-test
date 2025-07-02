"use client";

import React from "react";
import { CommonDialog } from '@repo/ui/components';
import { AlertTriangle, RefreshCw, Plus } from "lucide-react";
import "./PreDeploymentDialog.scss";

interface PreDeploymentDialogProps {
    isOpen: boolean;
    onClose: () => void;
    onUpdateExisting: () => void;
    onCreateNew: () => void;
    workflowName: string;
    isExistingWorkflow: boolean;
    hasChanges: boolean;
}

function PreDeploymentDialog({
    isOpen,
    onClose,
    onUpdateExisting,
    onCreateNew,
    workflowName,
    isExistingWorkflow,
    hasChanges
}: PreDeploymentDialogProps): JSX.Element | null {
    
    if (!isOpen) return null;

    // For new workflows, skip this dialog
    if (!isExistingWorkflow) {
        return null;
    }

    const handleUpdateExisting = (): void => {
        onUpdateExisting();
        onClose();
    };

    const handleCreateNew = (): void => {
        onCreateNew();
        onClose();
    };

    return (
        <CommonDialog
            title="Workflow Deployment Options"
            onConfirm={handleUpdateExisting}
            onCancel={onClose}
            confirmLabel="Update Existing"
            cancelLabel="Cancel"
            icon={<AlertTriangle size={24} className="text-orange-500" />}
        >
            <div className="pre-deployment-dialog-content">
                <div className="workflow-info">
                    <h3 className="workflow-name">"{workflowName}"</h3>
                    <p className="workflow-status">
                        {hasChanges 
                            ? "This workflow has been modified since it was last saved."
                            : "This workflow already exists in your workspace."
                        }
                    </p>
                </div>

                <div className="deployment-options">
                    <div className="option-card">
                        <div className="option-header">
                            <RefreshCw size={20} className="text-blue-500" />
                            <h4>Update Existing Workflow</h4>
                        </div>
                        <p className="option-description">
                            {hasChanges 
                                ? "Save your changes and deploy the updated workflow. This will replace the current version."
                                : "Deploy the existing workflow as-is. No changes will be made to the workflow configuration."
                            }
                        </p>
                        <button
                            onClick={handleUpdateExisting}
                            className="btn btn-primary option-button"
                            type="button"
                        >
                            <RefreshCw size={16} />
                            Update & Deploy
                        </button>
                    </div>

                    <div className="option-card">
                        <div className="option-header">
                            <Plus size={20} className="text-green-500" />
                            <h4>Create New Workflow</h4>
                        </div>
                        <p className="option-description">
                            Create a new workflow with a different name. The original workflow will remain unchanged.
                        </p>
                        <button
                            onClick={handleCreateNew}
                            className="btn btn-outline option-button"
                            type="button"
                        >
                            <Plus size={16} />
                            Create New
                        </button>
                    </div>
                </div>

                <div className="dialog-note">
                    <p className="note-text">
                        💡 <strong>Tip:</strong> If you're experimenting with changes, creating a new workflow 
                        allows you to keep both versions for comparison.
                    </p>
                </div>
            </div>
        </CommonDialog>
    );
}

export default PreDeploymentDialog;

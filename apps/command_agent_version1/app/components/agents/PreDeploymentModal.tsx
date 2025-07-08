"use client";

import React from "react";
import { CommonModal } from '@repo/ui/components';
import { X } from "lucide-react";
import "./PreDeploymentModal.scss";

interface PreDeploymentModalProps {
    isOpen: boolean;
    onClose: () => void;
    onUpdateExisting: () => void;
    onCreateNew: () => void;
    workflowName: string;
    isExistingWorkflow: boolean;
    hasChanges: boolean;
}

function PreDeploymentModal({
    isOpen,
    onClose,
    onUpdateExisting,
    onCreateNew,
    workflowName: _workflowName,
    isExistingWorkflow,
    hasChanges: _hasChanges
}: PreDeploymentModalProps): JSX.Element | null {

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
        <CommonModal onClose={onClose} className="pre-deployment-modal">
            <div className="pre-deployment-dialog-content bg-white rounded-xl border border-[#E3E8EF]">
                {/* Header */}
                <div className="modal-header">
                    <h2 className="modal-title">Save Before Deploying</h2>
                    <button
                        onClick={onClose}
                        className="close-button"
                        type="button"
                    >
                        <X size={20} />
                    </button>
                </div>

                {/* Content */}
                <div className="modal-body flex justify-start">
                    <div className="deployment-message">
                        You&apos;re about to deploy changes to this workflow. Would you like to update the original version or save it as a new one?
                    </div>
                </div>

                {/* Footer */}
                <div className="modal-footer">
                    <div className="deployment-actions">
                        <button
                            onClick={handleCreateNew}
                            className="btn btn-outline"
                            type="button"
                        >
                            Save As
                        </button>
                        <button
                            onClick={handleUpdateExisting}
                            className="btn btn-primary"
                            type="button"
                        >
                            Save
                        </button>
                    </div>
                </div>
            </div>
        </CommonModal>
    );
}

export default PreDeploymentModal;

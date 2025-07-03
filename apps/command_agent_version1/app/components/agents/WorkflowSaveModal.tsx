"use client";

import React, { useState, useEffect } from "react";
import { CommonModal } from '@repo/ui/components';
import { Save, Rocket, X } from "lucide-react";
import "./WorkflowSaveModal.scss";

interface WorkflowSaveModalProps {
    isOpen: boolean;
    onClose: () => void;
    onSave: (name: string, description: string) => void;
    onDeploy: (name: string, description: string) => void;
    initialName?: string;
    initialDescription?: string;
    isLoading?: boolean;
    mode?: "save" | "deploy" | "both";
}

function WorkflowSaveModal({
    isOpen,
    onClose,
    onSave,
    onDeploy,
    initialName = "",
    initialDescription = "",
    isLoading = false,
    mode = "both"
}: WorkflowSaveModalProps): JSX.Element | null {
    const [name, setName] = useState(initialName);
    const [description, setDescription] = useState(initialDescription);
    const [errors, setErrors] = useState<{ name?: string; description?: string }>({});

    // Reset form when modal opens/closes
    useEffect(() => {
        if (isOpen) {
            setName(initialName);
            setDescription(initialDescription);
            setErrors({});
        }
    }, [initialName, initialDescription]);

    // Validation
    const validateForm = (): boolean => {
        const newErrors: { name?: string; description?: string } = {};

        if (!name.trim()) {
            newErrors.name = "Workflow name is required";
        } else if (name.trim().length < 3) {
            newErrors.name = "Workflow name must be at least 3 characters";
        } else if (name.trim().length > 50) {
            newErrors.name = "Workflow name must be less than 50 characters";
        }

        if (description.trim().length > 200) {
            newErrors.description = "Description must be less than 200 characters";
        }

        setErrors(newErrors);
        return Object.keys(newErrors).length === 0;
    };

    const handleSave = (): void => {
        if (!validateForm()) return;
        console.log("AND THE NAME IS: ", name.trim());
        onSave(name.trim(), description.trim());
    };

    const handleDeploy = (): void => {
        if (!validateForm()) return;
        onDeploy(name.trim(), description.trim());
    };

    const handleKeyDown = (e: React.KeyboardEvent): void => {
        if (e.key === "Escape") {
            onClose();
        } else if (e.key === "Enter" && e.ctrlKey) {
            // Ctrl+Enter to save
            handleSave();
        }
    };

    if (!isOpen) return null;

    return (
        <CommonModal onClose={onClose} className="workflow-save-modal">
            <div className="workflow-save-modal-content" onKeyDown={handleKeyDown}>
                {/* Header */}
                <div className="modal-header">
                    <div className="header-content">
                        <h2 className="modal-title">
                            {mode === "save" ? "Save Workflow" : mode === "deploy" ? "Deploy Workflow" : "Save & Deploy Workflow"}
                        </h2>
                        <p className="modal-subtitle">
                            {mode === "save"
                                ? "Save your workflow for later use"
                                : mode === "deploy"
                                    ? "Deploy your workflow to make it available for chat"
                                    : "Save your workflow and optionally deploy it"
                            }
                        </p>
                    </div>
                    <button
                        onClick={onClose}
                        className="close-button"
                        type="button"
                        disabled={isLoading}
                    >
                        <X size={20} />
                    </button>
                </div>

                {/* Form */}
                <div className="modal-body">
                    <div className="form-group">
                        <label htmlFor="workflow-name" className="form-label">
                            Workflow Name <span className="required">*</span>
                        </label>
                        <input
                            id="workflow-name"
                            type="text"
                            value={name}
                            onChange={(e) => { setName(e.target.value) }}
                            placeholder="Enter workflow name..."
                            className={`form-input ${errors.name ? 'error' : ''}`}
                            disabled={isLoading}
                            maxLength={50}
                        />
                        {errors.name ? <span className="error-message">{errors.name}</span> : null}
                        <div className="character-count">
                            {name.length}/50
                        </div>
                    </div>

                    <div className="form-group">
                        <label htmlFor="workflow-description" className="form-label">
                            Description <span className="optional">(optional)</span>
                        </label>
                        <textarea
                            id="workflow-description"
                            value={description}
                            onChange={(e) => setDescription(e.target.value)}
                            placeholder="Describe what this workflow does..."
                            className={`form-textarea ${errors.description ? 'error' : ''}`}
                            disabled={isLoading}
                            rows={3}
                            maxLength={200}
                        />
                        {errors.description && <span className="error-message">{errors.description}</span>}
                        <div className="character-count">
                            {description.length}/200
                        </div>
                    </div>
                </div>

                {/* Footer */}
                <div className="modal-footer">
                    <button
                        onClick={onClose}
                        className="btn btn-secondary"
                        type="button"
                        disabled={isLoading}
                    >
                        Cancel
                    </button>

                    <div className="action-buttons">
                        {(mode === "save" || mode === "both") && (
                            <button
                                onClick={handleSave}
                                className="btn btn-outline"
                                type="button"
                                disabled={isLoading || !name.trim()}
                            >
                                <Save size={16} />
                                {isLoading ? "Saving..." : "Save"}
                            </button>
                        )}

                        {(mode === "deploy" || mode === "both") && (
                            <button
                                onClick={handleDeploy}
                                className="btn btn-primary"
                                type="button"
                                disabled={isLoading || !name.trim()}
                            >
                                <Rocket size={16} />
                                {isLoading ? "Deploying..." : "Deploy"}
                            </button>
                        )}
                    </div>
                </div>
            </div>
        </CommonModal>
    );
}

export default WorkflowSaveModal;

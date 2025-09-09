"use client";

import React, { useState, useEffect } from "react";
import { CommonModal } from '@repo/ui/components';
import { Save, X } from "lucide-react";
import "./WorkflowEditModal.scss";

interface WorkflowEditModalProps {
    isOpen: boolean;
    onClose: () => void;
    onSave: (name: string, description: string, tags: string[]) => void;
    initialName?: string;
    initialDescription?: string;
    initialTags?: string[];
    isLoading?: boolean;
}

function WorkflowEditModal({
    isOpen,
    onClose,
    onSave,
    initialName = "",
    initialDescription = "",
    initialTags = [],
    isLoading = false
}: WorkflowEditModalProps): JSX.Element | null {
    const [name, setName] = useState(initialName);
    const [description, setDescription] = useState(initialDescription);
    const [tagsInput, setTagsInput] = useState("");
    const [errors, setErrors] = useState<{ name?: string; description?: string }>({});

    // Reset form when modal opens/closes
    useEffect(() => {
        if (isOpen) {
            setName(initialName);
            setDescription(initialDescription);
            setTagsInput(initialTags.join(", "));
            setErrors({});
        }
    }, [isOpen, initialName, initialDescription, initialTags]);

    // Handle Escape key to close modal
    useEffect(() => {
        if (!isOpen) return;

        const handleKeyDown = (e: KeyboardEvent): void => {
            if (e.key === "Escape") {
                onClose();
            }
        };

        window.addEventListener("keydown", handleKeyDown);
        return () => {
            window.removeEventListener("keydown", handleKeyDown);
        };
    }, [isOpen, onClose]);

    if (!isOpen) return null;

    const validateForm = (): boolean => {
        const newErrors: { name?: string; description?: string } = {};

        if (!name.trim()) {
            newErrors.name = "Workflow name is required";
        }

        setErrors(newErrors);
        return Object.keys(newErrors).length === 0;
    };

    const handleSave = (e?: React.FormEvent): void => {
        if (e) {
            e.preventDefault();
        }

        if (validateForm()) {
            // Parse comma-separated tags
            const parsedTags = tagsInput
                .split(",")
                .map(tag => tag.trim())
                .filter(tag => tag.length > 0);

            console.log("Saving workflow:", { name: name.trim(), description: description.trim(), tags: parsedTags });
            onSave(name.trim(), description.trim(), parsedTags);
        }
    };

    const handleTagsChange = (e: React.ChangeEvent<HTMLInputElement>): void => {
        setTagsInput(e.target.value);
    };

    return (
        <CommonModal onClose={onClose} className="workflow-edit-modal">
            <div className="workflow-edit-modal-content">
                {/* Header */}
                <div className="modal-header">
                    <div className="header-content">
                        <h2 className="modal-title">Edit Workflow Details</h2>
                        <p className="modal-subtitle">
                            Update the name, description, and tags for this workflow
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
                <form onSubmit={handleSave}>
                    <div className="modal-body">
                        {/* Workflow Name */}
                        <div className="form-group">
                            <label htmlFor="workflow-name" className="form-label">
                                Workflow Name *
                            </label>
                            <input
                                id="workflow-name"
                                type="text"
                                value={name}
                                onChange={(e) => { setName(e.target.value); }}
                                className={`form-input ${errors.name ? 'error' : ''}`}
                                placeholder="Enter workflow name"
                                disabled={isLoading}
                            />
                            {errors.name ? <span className="error-message">{errors.name}</span> : null}
                        </div>

                        {/* Workflow Description */}
                        <div className="form-group">
                            <label htmlFor="workflow-description" className="form-label">
                                Description
                            </label>
                            <textarea
                                id="workflow-description"
                                value={description}
                                onChange={(e) => { setDescription(e.target.value); }}
                                className={`form-textarea ${errors.description ? 'error' : ''}`}
                                placeholder="Enter workflow description (optional)"
                                rows={3}
                                disabled={isLoading}
                            />
                            {errors.description ? <span className="error-message">{errors.description}</span> : null}
                        </div>

                        {/* Tags */}
                        <div className="form-group">
                            <label htmlFor="workflow-tags" className="form-label">
                                Tags
                            </label>
                            <input
                                id="workflow-tags"
                                type="text"
                                value={tagsInput}
                                onChange={handleTagsChange}
                                className="form-input"
                                placeholder="Enter tags separated by commas (e.g., automation, data-processing, customer-service)"
                                disabled={isLoading}
                            />
                            <p className="text-xs text-gray-500 mt-1">
                                Separate multiple tags with commas
                            </p>
                        </div>
                    </div>
                </form>

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

                    <button
                        onClick={handleSave}
                        className="btn btn-primary"
                        type="button"
                        disabled={isLoading || !name.trim()}
                    >
                        <Save size={16} />
                        {isLoading ? "Saving..." : "Save Changes"}
                    </button>
                </div>
            </div>
        </CommonModal>
    );
}

export default WorkflowEditModal;

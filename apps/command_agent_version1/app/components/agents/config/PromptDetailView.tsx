"use client";

import React, { useState, useEffect } from "react";
import { ArrowLeft, PenLine } from "lucide-react";
import { type PromptResponse, type PromptUpdate, type PromptCreate } from "../../../lib/interfaces";
import { usePrompts } from "../../../ui/contexts/PromptsContext";

interface PromptDetailViewProps {
    prompt: PromptResponse;
    onBack: () => void;
    disabledFields: boolean;
    setDisabledFields: (disabled: boolean) => void;
}

function PromptDetailView({ prompt, onBack, disabledFields }: PromptDetailViewProps): JSX.Element {
    // State for editing
    const [isEditing, setIsEditing] = useState(false);
    const [editedPrompt, setEditedPrompt] = useState<PromptResponse>(prompt);
    const [hasChanges, setHasChanges] = useState(false);

    // Prompts context for save operations
    const { updateExistingPrompt, createNewPrompt } = usePrompts();

    // Update local state when prompt prop changes
    useEffect(() => {
        setEditedPrompt(prompt);
        setHasChanges(false);
        setIsEditing(false);
    }, [prompt]);

    // Check for changes
    useEffect(() => {
        const hasChanged =
            editedPrompt.prompt_label !== prompt.prompt_label ||
            editedPrompt.prompt !== prompt.prompt ||
            editedPrompt.unique_label !== prompt.unique_label ||
            editedPrompt.ai_model_provider !== prompt.ai_model_provider ||
            editedPrompt.ai_model_name !== prompt.ai_model_name ||
            JSON.stringify(editedPrompt.tags) !== JSON.stringify(prompt.tags) ||
            JSON.stringify(editedPrompt.hyper_parameters) !== JSON.stringify(prompt.hyper_parameters) ||
            JSON.stringify(editedPrompt.variables) !== JSON.stringify(prompt.variables);

        setHasChanges(hasChanged);
    }, [editedPrompt, prompt]);

    // Handle field changes
    // eslint-disable-next-line @typescript-eslint/no-explicit-any -- yy
    const handleFieldChange = (field: keyof PromptResponse, value: any): void => {
        setEditedPrompt(prev => ({
            ...prev,
            // eslint-disable-next-line @typescript-eslint/no-unsafe-assignment -- yy w/e
            [field]: value
        }));
    };

    // Handle tags change
    const handleTagsChange = (tagsString: string): void => {
        const tags = tagsString.split(',').map(tag => tag.trim()).filter(tag => tag.length > 0);
        handleFieldChange('tags', tags.length > 0 ? tags : null);
    };

    // Handle save (update existing)
    const handleSave = async (): Promise<void> => {
        try {
            const updateData: PromptUpdate = {
                prompt_label: editedPrompt.prompt_label,
                prompt: editedPrompt.prompt,
                unique_label: editedPrompt.unique_label,
                ai_model_provider: editedPrompt.ai_model_provider,
                ai_model_name: editedPrompt.ai_model_name,
                tags: editedPrompt.tags,
                hyper_parameters: editedPrompt.hyper_parameters,
                variables: editedPrompt.variables
            };

            await updateExistingPrompt(prompt.pid, updateData);
            setIsEditing(false);
            setHasChanges(false);
        } catch (error) {
            console.error("Failed to save prompt:", error);
        }
    };

    // Handle save as new
    const handleSaveAsNew = async (): Promise<void> => {
        try {
            const createData: PromptCreate = {
                prompt_label: editedPrompt.prompt_label,
                prompt: editedPrompt.prompt,
                unique_label: editedPrompt.unique_label,
                app_name: editedPrompt.app_name,
                version: editedPrompt.version,
                ai_model_provider: editedPrompt.ai_model_provider,
                ai_model_name: editedPrompt.ai_model_name,
                tags: editedPrompt.tags,
                hyper_parameters: editedPrompt.hyper_parameters,
                variables: editedPrompt.variables
            };

            await createNewPrompt(createData);
            setIsEditing(false);
            setHasChanges(false);
        } catch (error) {
            console.error("Failed to create new prompt:", error);
        }
    };

    // Handle cancel
    const handleCancel = (): void => {
        setEditedPrompt(prompt);
        setIsEditing(false);
        setHasChanges(false);
    };

    return (
        <div className="prompt-detail-view flex flex-col h-full">
            {/* Header */}
            <div className="flex items-center justify-between p-4 border-b border-gray-200">
                <div className="flex items-center gap-3">
                    <button
                        onClick={onBack}
                        className="flex items-center gap-2 text-gray-600 hover:text-gray-800"
                        type="button"
                    >
                        <ArrowLeft size={16} />
                        Back
                    </button>
                    <div className="h-4 w-px bg-gray-300" />
                    <h2 className="text-lg font-medium">Prompt Details</h2>
                </div>

                {!disabledFields && (
                    <button
                        onClick={() => { setIsEditing(!isEditing); }}
                        className="px-3 py-1 text-sm border border-[#FF681F] text-[#FF681F] rounded-md hover:bg-[#FF681F] hover:text-white transition-colors"
                        type="button"
                    >
                        {isEditing ? "Cancel Edit" : "Edit"}
                    </button>
                )}
            </div>

            {/* Content */}
            <div className="flex-1 overflow-y-auto p-4 space-y-6">
                {/* Basic Information */}
                <div className="space-y-4">
                    <h3 className="text-sm font-medium text-gray-900">Basic Information</h3>

                    {/* Prompt Label */}
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                            Prompt Label
                            {isEditing ? (
                                <input
                                    type="text"
                                    value={editedPrompt.prompt_label}
                                    onChange={(e) => { handleFieldChange('prompt_label', e.target.value); }}
                                    className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-[#FF681F] focus:border-transparent"
                                />
                            ) : (
                                <div className="px-3 py-2 bg-gray-50 rounded-md text-sm">
                                    {editedPrompt.prompt_label}
                                </div>
                            )}
                        </label>
                    </div>

                    {/* Unique Label */}
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                            Unique Label
                            {isEditing ? (
                                <input
                                    type="text"
                                    value={editedPrompt.unique_label}
                                    onChange={(e) => { handleFieldChange('unique_label', e.target.value); }}
                                    className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-[#FF681F] focus:border-transparent"
                                />
                            ) : (
                                <div className="px-3 py-2 bg-gray-50 rounded-md text-sm">
                                    {editedPrompt.unique_label}
                                </div>
                            )}
                        </label>
                    </div>

                    {/* Tags */}
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                            Tags
                            {isEditing ? (
                                <input
                                    type="text"
                                    value={editedPrompt.tags?.join(', ') ?? ''}
                                    onChange={(e) => { handleTagsChange(e.target.value); }}
                                    placeholder="Enter tags separated by commas"
                                    className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-[#FF681F] focus:border-transparent"
                                />
                            ) : (
                                <div className="px-3 py-2 bg-gray-50 rounded-md text-sm">
                                    {editedPrompt.tags?.length ? (
                                        <div className="flex flex-wrap gap-1">
                                            {editedPrompt.tags.map((tag, index) => (
                                                <span
                                                    key={index}
                                                    className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded-md"
                                                >
                                                    {tag}
                                                </span>
                                            ))}
                                        </div>
                                    ) : (
                                        <span className="text-gray-500">No tags</span>
                                    )}
                                </div>
                            )}
                        </label>
                    </div>
                </div>

                {/* Model Information */}
                <div className="space-y-4">
                    <h3 className="text-sm font-medium text-gray-900">Model Configuration</h3>

                    {/* AI Model Provider */}
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                            Model Provider
                            {isEditing ? (
                                <input
                                    type="text"
                                    value={editedPrompt.ai_model_provider}
                                    onChange={(e) => { handleFieldChange('ai_model_provider', e.target.value); }}
                                    className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-[#FF681F] focus:border-transparent"
                                />
                            ) : (
                                <div className="px-3 py-2 bg-gray-50 rounded-md text-sm">
                                    {editedPrompt.ai_model_provider}
                                </div>
                            )}
                        </label>
                    </div>

                    {/* AI Model Name */}
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                            Model Name
                            {isEditing ? (
                                <input
                                    type="text"
                                    value={editedPrompt.ai_model_name}
                                    onChange={(e) => { handleFieldChange('ai_model_name', e.target.value); }}
                                    className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-[#FF681F] focus:border-transparent"
                                />
                            ) : (
                                <div className="px-3 py-2 bg-gray-50 rounded-md text-sm">
                                    {editedPrompt.ai_model_name}
                                </div>
                            )}
                        </label>
                    </div>
                </div>

                {/* Prompt Content */}
                <div className="space-y-4">
                    <h3 className="text-sm font-medium text-gray-900">Prompt Content</h3>

                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                            Prompt
                            {isEditing ? (
                                <textarea
                                    value={editedPrompt.prompt}
                                    onChange={(e) => { handleFieldChange('prompt', e.target.value); }}
                                    rows={8}
                                    className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-[#FF681F] focus:border-transparent resize-vertical"
                                />
                            ) : (
                                <div className="px-3 py-2 bg-gray-50 rounded-md text-sm whitespace-pre-wrap max-h-60 overflow-y-auto">
                                    {editedPrompt.prompt}
                                </div>
                            )}
                        </label>
                    </div>
                </div>
            </div>

            {/* Footer - Save buttons when editing */}
            {isEditing && hasChanges ? <div className="border-t border-gray-200 p-4">
                <div className="flex gap-3 justify-end">
                    <button
                        onClick={handleCancel}
                        className="px-4 py-2 text-sm border border-[#FF681F] text-[#FF681F] rounded-md hover:bg-[#FF681F] hover:text-white transition-colors"
                        type="button"
                    >
                        Cancel
                    </button>
                    <button
                        onClick={handleSave}
                        className="px-4 py-2 text-sm border border-[#FF681F] text-[#FF681F] rounded-md hover:bg-[#FF681F] hover:text-white transition-colors"
                        type="button"
                    >
                        Save
                    </button>
                    <button
                        onClick={handleSaveAsNew}
                        className="px-4 py-2 text-sm bg-[#FF681F] text-white rounded-md hover:bg-[#E55A1A] transition-colors"
                        type="button"
                    >
                        Save As New
                    </button>
                </div>
            </div> : null}
        </div>
    );
}

export default PromptDetailView;

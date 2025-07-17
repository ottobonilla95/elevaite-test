"use client";

import React, { useState, useEffect } from "react";
import { ChevronUp, ChevronDown, ChevronsLeft, ChevronsRight, ArrowLeft, PenLine } from "lucide-react";
import { type PromptResponse, type PromptUpdate, type PromptCreate } from "../../../lib/interfaces";
import PromptDetailEditingForm from "./PromptDetailEditingForm";
import PromptDetailTestingConsole from "@/components/agents/config/PromptDetailTestingConsole";
import { usePrompts } from "@/ui/contexts/PromptsContext";
import { useAgents } from "@/ui/contexts/AgentsContext";
import { PromptContextProvider } from "@/ui/contexts/PromptContext";


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
	const [activeTab, setActiveTab] = useState("tab1");
	const [parametersOpen, setParametersOpen] = useState(false);

    // Prompts context for save operations
    const { updateExistingPrompt, createNewPrompt, isEditingPrompt, setIsEditingPrompt } = usePrompts();

	const { sidebarRightOpen, setSidebarRightOpen } = useAgents();

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

	// return(
	// 	<div className="flex flex-col h-full">
	// 		<div className="prompt-details config-panel-header">
	// 			<div className="flex flex-1 items-center justify-between">
	// 				<div className="left flex items-center justify-between gap-2">
	// 					<div className="icon-container">
	// 						<svg width="22" height="22" viewBox="0 0 22 22" fill="none" xmlns="http://www.w3.org/2000/svg">
	// 							<path d="M11 20.7412C16.3799 20.7412 20.7412 16.3799 20.7412 11C20.7412 5.62008 16.3799 1.25879 11 1.25879C5.62008 1.25879 1.25879 5.62008 1.25879 11C1.25879 12.7743 1.73316 14.4378 2.56199 15.8706L1.74585 20.2542L6.1294 19.4381C7.56221 20.2668 9.22575 20.7412 11 20.7412Z" stroke="#FE854B" strokeWidth="1.46118" strokeLinecap="round" strokeLinejoin="round"/>
	// 						</svg>
	// 					</div>
	// 					<div>
	// 						<div className="font-semibold">Data Analyser</div>
	// 						<div className="font-medium text-xs" style={{ opacity: 0.65 }}>Extract Data</div>
	// 					</div>
	// 				</div>
	// 				<div className="right flex items-center justify-center flex-shrink-0 gap-3">
	// 					<button onClick={() => setIsEditingPrompt(!isEditingPrompt)}>
	// 						<PenLine size={20}/>
	// 					</button>
	// 					<button>
	// 						<svg width="4" height="18" viewBox="0 0 4 18" fill="none" xmlns="http://www.w3.org/2000/svg">
	// 							<path d="M2 10C2.55228 10 3 9.55228 3 9C3 8.44772 2.55228 8 2 8C1.44772 8 1 8.44772 1 9C1 9.55228 1.44772 10 2 10Z" stroke="black" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
	// 							<path d="M2 3C2.55228 3 3 2.55228 3 2C3 1.44772 2.55228 1 2 1C1.44772 1 1 1.44772 1 2C1 2.55228 1.44772 3 2 3Z" stroke="black" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
	// 							<path d="M2 17C2.55228 17 3 16.5523 3 16C3 15.4477 2.55228 15 2 15C1.44772 15 1 15.4477 1 16C1 16.5523 1.44772 17 2 17Z" stroke="black" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
	// 						</svg>
	// 					</button>
	// 					<button className="btn-toggle" onClick={ () => setSidebarRightOpen(!sidebarRightOpen) }>
	// 						{sidebarRightOpen ? <ChevronsRight /> : <ChevronsLeft />}
	// 					</button>
	// 				</div>
	// 			</div>
	// 		</div>
	// 		{isEditingPrompt ? (
	// 			<div className="tabs-wrapper flex flex-col grow w-full bg-white">
	// 				<div className="tabs flex my-1 text-xs text-gray-500 font-medium h-[34px]">
	// 					<div className="tabs-inner p-1 flex flex-1">
	// 						<button className={`tab rounded-sm px-2 flex-1${ 'tab1' == activeTab ? ' tab-active text-orange-500 bg-white' : '' }`} onClick={() => setActiveTab("tab1")}>
	// 							Configuration
	// 						</button>
	// 						<button className={`tab rounded-sm px-2 flex-1${ 'tab2' == activeTab ? ' tab-active text-orange-500 bg-white' : '' }`} onClick={() => setActiveTab("tab2")}>
	// 							Prompt
	// 						</button>
	// 					</div>
	// 				</div>
	// 				<div className="tab-panels flex flex-1 w-full rounded-b-xl">
	// 					{activeTab === "tab1" && (
	// 						<div className="tab-panel mt-4 flex flex-col flex-grow">
	// 							<div className="tab-content">
	// 								<PromptDetailEditingForm />
	// 							</div>
	// 						</div>
	// 					)}
	// 					{activeTab === "tab2" && (
	// 						<div className="tab-panel mt-4 flex flex-col flex-grow w-full">
	// 							<div className="tab-content flex w-full h-full">
	// 								<PromptContextProvider>
	// 									<PromptDetailTestingConsole />
	// 								</PromptContextProvider>
	// 							</div>
	// 						</div>
	// 					)}
	// 				</div>
	// 			</div>
	// 		) : (
	// 			<div>
	// 				<div className="text-sm mb-3">
	// 					Nulla faucibus tristique quis felis gravida. Faucibus turpis at quis non elementum est. In sed accumsan eu sociis aliquam vitae morbi.
	// 				</div>
	// 				<div className="grid grid-cols-2 gap-3">
	// 					<div>
	// 						<div className="font-medium text-xs mb-1">Status:</div>
	// 						<div className="badge">Deployed</div>
	// 					</div>
	// 					<div>
	// 						<div className="font-medium text-xs mb-1">Version:</div>
	// 						<div className="badge">V2</div>
	// 					</div>
	// 				</div>
	// 				<div className="mt-3">
	// 					<button className="flex justify-between items-center w-full font-medium text-sm" onClick={() => setParametersOpen(!parametersOpen)}>
	// 						Parameters:
	// 						{parametersOpen ? <ChevronUp size={18} /> : <ChevronDown size={18} />}
	// 					</button>
	// 					{parametersOpen && (
	// 						<div className="flex flex-wrap gap-2 mt-1">
	// 							<div className="badge">Max Tokens: 2,500</div>
	// 							<div className="badge">Temp: 56</div>
	// 							<div className="badge">Hosted</div>
	// 							<div className="badge">JSON</div>
	// 						</div>
	// 					)}
	// 				</div>
	// 				<div className="mt-3">
	// 					<div className="font-medium text-xs mb-1">Dataset:</div>
	// 					<div className="badge">Arlo Knowledge Base</div>
	// 				</div>
	// 				<div className="mt-3">
	// 					<div className="font-medium text-xs mb-1">Model:</div>
	// 					<div className="badge">Chat GPT-4</div>
	// 				</div>
	// 				<hr className="my-4" />
	// 				<div className="details flex flex-col gap-3">
	// 					<div className="detail flex items-center justify-between gap-2">
	// 						<div className="opacity-75 text-sm">Hallucination Risk</div>
	// 						<div className="tag-blue">Low</div>
	// 					</div>
	// 					<div className="detail flex items-center justify-between gap-2">
	// 						<div className="opacity-75 text-sm">Avg. Latency</div>
	// 						<div className="tag-blue">Normal (2.3s)</div>
	// 					</div>
	// 					<div className="detail flex items-center justify-between gap-2">
	// 						<div className="opacity-75 text-sm">Avg. Score</div>
	// 						<div className="tag-blue">8/10</div>
	// 					</div>
	// 				</div>
	// 			</div>
	// 		)}
	// 	</div>
	// )

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

"use client";

import React, { createContext, useContext, useState, useEffect, useCallback } from "react";
import { type PromptResponse, type PromptCreate, type PromptUpdate } from "../../lib/interfaces";
import { fetchAllPrompts, fetchAgentPrompts, fetchPrompt, createPrompt, updatePrompt, deletePrompt } from "../../lib/actions";

// Context interface
interface PromptsContextType {
  // State
  prompts: PromptResponse[];
  agentPrompts: PromptResponse[];
  selectedPrompt: PromptResponse | null;
  isLoading: boolean;
  error: string | null;
  isEditingPrompt: boolean;

  // Actions
  loadAllPrompts: (appName?: string) => Promise<void>;
  loadAgentPrompts: () => Promise<void>;
  selectPrompt: (promptId: string) => Promise<void>;
  clearSelectedPrompt: () => void;
  refreshPrompts: () => Promise<void>;
  createNewPrompt: (promptData: PromptCreate) => Promise<PromptResponse | null>;
  updateExistingPrompt: (promptId: string, promptData: PromptUpdate) => Promise<PromptResponse | null>;
  deleteExistingPrompt: (promptId: string) => Promise<boolean>;
  setIsEditingPrompt: (isEditing: boolean) => void;

  // Utility functions
  getPromptById: (promptId: string) => PromptResponse | undefined;
  getPromptsByLabel: (label: string) => PromptResponse[];
  searchPrompts: (query: string) => PromptResponse[];
}

// Create context
const PromptsContext = createContext<PromptsContextType | undefined>(undefined);

// Provider props
interface PromptsProviderProps {
  children: React.ReactNode;
}

// Provider component
export function PromptsProvider({ children }: PromptsProviderProps): JSX.Element {
  // State
  const [prompts, setPrompts] = useState<PromptResponse[]>([]);
  const [agentPrompts, setAgentPrompts] = useState<PromptResponse[]>([]);
  const [selectedPrompt, setSelectedPrompt] = useState<PromptResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isEditingPrompt, setIsEditingPrompt] = useState(false);

  // Load all prompts with optional app filtering
  const loadAllPrompts = useCallback(async (appName?: string): Promise<void> => {
    setIsLoading(true);
    setError(null);
    try {
      const fetchedPrompts = await fetchAllPrompts(0, 100, appName);
      setPrompts(fetchedPrompts);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "Failed to load prompts";
      setError(errorMessage);
      console.error("Error loading prompts:", err);
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Load prompts specifically for agent configuration
  const loadAgentPrompts = useCallback(async (): Promise<void> => {
    setIsLoading(true);
    setError(null);
    try {
      const fetchedPrompts = await fetchAgentPrompts();
      setAgentPrompts(fetchedPrompts);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "Failed to load agent prompts";
      setError(errorMessage);
      console.error("Error loading agent prompts:", err);
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Select a specific prompt by ID
  const selectPrompt = useCallback(async (promptId: string): Promise<void> => {
    setIsLoading(true);
    setError(null);
    try {
      const prompt = await fetchPrompt(promptId);
      setSelectedPrompt(prompt);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "Failed to load prompt";
      setError(errorMessage);
      console.error("Error selecting prompt:", err);
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Clear selected prompt
  const clearSelectedPrompt = useCallback((): void => {
    setSelectedPrompt(null);
  }, []);

  // Refresh current prompts
  const refreshPrompts = useCallback(async (): Promise<void> => {
    await Promise.all([
      loadAllPrompts(),
      loadAgentPrompts()
    ]);
  }, [loadAllPrompts, loadAgentPrompts]);

  // Create a new prompt
  const createNewPrompt = useCallback(async (promptData: PromptCreate): Promise<PromptResponse | null> => {
    setIsLoading(true);
    setError(null);
    try {
      const newPrompt = await createPrompt(promptData);
      // Refresh prompts to include the new one
      await refreshPrompts();
      return newPrompt;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "Failed to create prompt";
      setError(errorMessage);
      console.error("Error creating prompt:", err);
      return null;
    } finally {
      setIsLoading(false);
    }
  }, [refreshPrompts]);

  // Update an existing prompt
  const updateExistingPrompt = useCallback(async (promptId: string, promptData: PromptUpdate): Promise<PromptResponse | null> => {
    setIsLoading(true);
    setError(null);
    try {
      const updatedPrompt = await updatePrompt(promptId, promptData);
      // Refresh prompts to reflect changes
      await refreshPrompts();
      // Update selected prompt if it was the one being updated
      if (selectedPrompt && selectedPrompt.pid === promptId) {
        setSelectedPrompt(updatedPrompt);
      }
      return updatedPrompt;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "Failed to update prompt";
      setError(errorMessage);
      console.error("Error updating prompt:", err);
      return null;
    } finally {
      setIsLoading(false);
    }
  }, [refreshPrompts, selectedPrompt]);

  // Delete a prompt
  const deleteExistingPrompt = useCallback(async (promptId: string): Promise<boolean> => {
    setIsLoading(true);
    setError(null);
    try {
      const success = await deletePrompt(promptId);
      if (success) {
        // Refresh prompts to remove the deleted one
        await refreshPrompts();
        // Clear selected prompt if it was the one being deleted
        if (selectedPrompt && selectedPrompt.pid === promptId) {
          setSelectedPrompt(null);
        }
      }
      return success;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "Failed to delete prompt";
      setError(errorMessage);
      console.error("Error deleting prompt:", err);
      return false;
    } finally {
      setIsLoading(false);
    }
  }, [refreshPrompts, selectedPrompt]);

  // Utility: Get prompt by ID from current state
  const getPromptById = useCallback((promptId: string): PromptResponse | undefined => {
    return prompts.find(prompt => prompt.pid === promptId) ??
      agentPrompts.find(prompt => prompt.pid === promptId);
  }, [prompts, agentPrompts]);

  // Utility: Get prompts by label
  const getPromptsByLabel = useCallback((label: string): PromptResponse[] => {
    return prompts.filter(prompt =>
      prompt.prompt_label.toLowerCase().includes(label.toLowerCase())
    );
  }, [prompts]);

  // Utility: Search prompts by query
  const searchPrompts = useCallback((query: string): PromptResponse[] => {
    const lowercaseQuery = query.toLowerCase();
    return prompts.filter(prompt =>
      prompt.prompt_label.toLowerCase().includes(lowercaseQuery) ||
      prompt.prompt.toLowerCase().includes(lowercaseQuery) ||
      prompt.unique_label.toLowerCase().includes(lowercaseQuery) ||
      (prompt.tags?.some(tag => tag.toLowerCase().includes(lowercaseQuery)))
    );
  }, [prompts]);

  // Load agent prompts on mount
  useEffect(() => {
    void loadAgentPrompts();
  }, [loadAgentPrompts]);

  // Context value
  const contextValue: PromptsContextType = {
    // State
    prompts,
    agentPrompts,
    selectedPrompt,
    isLoading,
    error,
	isEditingPrompt,

    // Actions
    loadAllPrompts,
    loadAgentPrompts,
    selectPrompt,
    clearSelectedPrompt,
    refreshPrompts,
    createNewPrompt,
    updateExistingPrompt,
    deleteExistingPrompt,
	setIsEditingPrompt,

    // Utilities
    getPromptById,
    getPromptsByLabel,
    searchPrompts,
  };

  return (
    <PromptsContext.Provider value={contextValue}>
      {children}
    </PromptsContext.Provider>
  );
}

// Hook to use the context
export function usePrompts(): PromptsContextType {
  const context = useContext(PromptsContext);
  if (context === undefined) {
    throw new Error("usePrompts must be used within a PromptsProvider");
  }
  return context;
}

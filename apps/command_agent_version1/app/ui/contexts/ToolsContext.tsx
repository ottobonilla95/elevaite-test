"use client";

import React, { createContext, useContext, useEffect, useState, type ReactNode } from 'react';
import { fetchAvailableTools, fetchToolCategories } from '../../lib/toolActions';
import { type Tool, type ToolCategory } from '../../lib/interfaces';

interface ToolsContextType {
  tools: Tool[];
  categories: ToolCategory[];
  isLoading: boolean;
  error: string | null;
  refetchTools: () => Promise<void>;
  // Utility functions
  getToolsByCategory: (categoryId?: string) => Tool[];
  getToolById: (toolId: string) => Tool|undefined;
  getAvailableTools: () => Tool[];
}

const ToolsContext = createContext<ToolsContextType | undefined>(undefined);

interface ToolsProviderProps {
  children: ReactNode;
}

export function ToolsProvider({ children }: ToolsProviderProps): JSX.Element {
  const [tools, setTools] = useState<Tool[]>([]);
  const [categories, setCategories] = useState<ToolCategory[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);


  async function loadTools(): Promise<void> {
    try {
      setIsLoading(true);
      setError(null);

      // Fetch new tools system data
      const [toolsResponse, categoriesResponse] = await Promise.all([
        fetchAvailableTools(),
        fetchToolCategories()
      ]);

      setTools(toolsResponse);
      setCategories(categoriesResponse);
    } catch (err) {
      setError("Failed to load new tools from API");
    } finally {
      setIsLoading(false);
    }
  };

  async function refetchTools(): Promise<void> {
    await loadTools();
  };

  // Utility functions
  function getToolsByCategory(categoryId?: string): Tool[] {
    if (!categoryId) return tools;
    return tools.filter(tool => tool.category_id === categoryId);
  };

  function getAvailableTools(): Tool[] {
    return tools.filter(tool => tool.is_active && tool.is_available);
  };

  function getToolById(toolId: string): Tool|undefined {
    return tools.find(tool => tool.tool_id === toolId);
  }

  useEffect(() => {
    // Load both legacy and new tools on mount
    void loadTools();
  }, []);

  const value: ToolsContextType = {
    tools,
    categories,
    isLoading,
    error,
    refetchTools,
    getToolsByCategory,
    getToolById,
    getAvailableTools,
  };

  return (
    <ToolsContext.Provider value={value}>
      {children}
    </ToolsContext.Provider>
  );
};

export function useTools(): ToolsContextType {
  const context = useContext(ToolsContext);
  if (context === undefined) {
    throw new Error('useTools must be used within a ToolsProvider');
  }
  return context;
};

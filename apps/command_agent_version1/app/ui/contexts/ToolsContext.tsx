"use client";

import React, { createContext, useContext, useEffect, useState, ReactNode } from 'react';
import { fetchAvailableTools, fetchToolCategories } from '../../lib/toolActions';
import { Tool, ToolCategory } from '../../lib/interfaces';

interface ToolsContextType {
  tools: Tool[];
  categories: ToolCategory[];
  isLoading: boolean;
  error: string | null;
  refetchTools: () => Promise<void>;
  // Utility functions
  getToolsByCategory: (categoryId?: string) => Tool[];
  getAvailableTools: () => Tool[];
}

const ToolsContext = createContext<ToolsContextType | undefined>(undefined);

interface ToolsProviderProps {
  children: ReactNode;
}

export const ToolsProvider: React.FC<ToolsProviderProps> = ({ children }) => {
  const [tools, setTools] = useState<Tool[]>([]);
  const [categories, setCategories] = useState<ToolCategory[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);


  const loadTools = async () => {
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
      console.error("Failed to fetch new tools:", err);
      setError("Failed to load new tools from API");
    } finally {
      setIsLoading(false);
    }
  };

  const refetchTools = async () => {
    await loadTools();
  };

  // Utility functions
  const getToolsByCategory = (categoryId?: string): Tool[] => {
    if (!categoryId) return tools;
    return tools.filter(tool => tool.category_id === categoryId);
  };

  const getAvailableTools = (): Tool[] => {
    return tools.filter(tool => tool.is_active && tool.is_available);
  };

  useEffect(() => {
    // Load both legacy and new tools on mount
    loadTools();
  }, []);

  const value: ToolsContextType = {
    tools,
    categories,
    isLoading,
    error,
    refetchTools,
    getToolsByCategory,
    getAvailableTools,
  };

  return (
    <ToolsContext.Provider value={value}>
      {children}
    </ToolsContext.Provider>
  );
};

export const useTools = (): ToolsContextType => {
  const context = useContext(ToolsContext);
  if (context === undefined) {
    throw new Error('useTools must be used within a ToolsProvider');
  }
  return context;
};

"use client";

import React, { createContext, useContext, useEffect, useState, ReactNode } from 'react';
import { fetchAllTools } from '../../lib/actions';
import { ToolInfo } from '../../lib/interfaces';
import { getToolsFromCache, setToolsCache } from '../../lib/toolsCache';

interface ToolsContextType {
  tools: ToolInfo[];
  isLoading: boolean;
  error: string | null;
  refetchTools: () => Promise<void>;
}

const ToolsContext = createContext<ToolsContextType | undefined>(undefined);

interface ToolsProviderProps {
  children: ReactNode;
}

export const ToolsProvider: React.FC<ToolsProviderProps> = ({ children }) => {
  const [tools, setTools] = useState<ToolInfo[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadTools = async () => {
    try {
      setIsLoading(true);
      setError(null);

      // Check cache first
      const cachedTools = getToolsFromCache();
      if (cachedTools) {
        setTools(cachedTools);
        setIsLoading(false);
        return;
      }

      // Fetch from API if not in cache
      const toolsResponse = await fetchAllTools();
      setTools(toolsResponse.tools);

      // Cache the results
      setToolsCache(toolsResponse.tools);
    } catch (err) {
      console.error("Failed to fetch tools:", err);
      setError("Failed to load tools from API");
    } finally {
      setIsLoading(false);
    }
  };

  const refetchTools = async () => {
    await loadTools();
  };

  useEffect(() => {
    loadTools();
  }, []);

  const value: ToolsContextType = {
    tools,
    isLoading,
    error,
    refetchTools,
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

import { ToolInfo } from './interfaces';

// Simple in-memory cache for tools
let toolsCache: ToolInfo[] | null = null;
let cacheTimestamp: number | null = null;
const CACHE_DURATION = 5 * 60 * 1000; // 5 minutes

export function getToolsFromCache(): ToolInfo[] | null {
  if (!toolsCache || !cacheTimestamp) {
    return null;
  }
  
  const now = Date.now();
  if (now - cacheTimestamp > CACHE_DURATION) {
    // Cache expired
    toolsCache = null;
    cacheTimestamp = null;
    return null;
  }
  
  return toolsCache;
}

export function setToolsCache(tools: ToolInfo[]): void {
  toolsCache = tools;
  cacheTimestamp = Date.now();
}

export function clearToolsCache(): void {
  toolsCache = null;
  cacheTimestamp = null;
}

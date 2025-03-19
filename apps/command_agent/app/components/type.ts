"use client";

import { ReactNode } from 'react';

// Type definitions for the flow system
export type NodeCategory = 'agent' | 'component' | 'tool';
export type NodeType = 'Router' | 'RAG' | 'Q&A' | 'Summarizer' | 'Database' | 'Web Search' | 'Compute' | 'File Reader' | 'Code Execution' | 'API Connector' | 'LLM' | 'Vector Store';

export interface NodeItem {
    id: string;
    type: NodeType;
    category: NodeCategory;
    position: { x: number; y: number };
    connected: string[];
    metrics?: {
        completionTime?: number;
        successRate?: number;
        processingCount?: number;
        errorRate?: number;
    };
}

export interface SidebarItem {
    id: string;
    type: NodeType;
    description: string;
    icon: ReactNode;
}

export interface Connection {
    id: string;
    from: string;
    to: string;
    metrics?: {
        dataVolume?: number;
        latency?: number;
        successRate?: number;
    };
}

export interface Message {
    id: string;
    type: 'user' | 'agent' | 'component' | 'tool' | 'final';
    text: string;
    agent?: string;
    timestamp: Date;
}
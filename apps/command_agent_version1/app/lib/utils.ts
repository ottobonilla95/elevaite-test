import type { Tool, ChatCompletionToolParam } from "./interfaces";

/**
 * Converts a Tool object to OpenAI ChatCompletionToolParam format
 * @param tool - The tool object from the database
 * @returns OpenAI-compatible tool schema
 */
export function toolToOpenAISchema(tool: Tool): ChatCompletionToolParam {
    return {
        type: "function",
        function: {
            name: tool.name,
            description: tool.description,
            parameters: tool.parameters_schema,
        }
    };
}

// "use client";
//
// import { v4 as uuidv4 } from 'uuid';
// import { Connection, NodeItem, NodeType } from "../components/type";
// import React from "react";
//
// export const getNodeIcon = (type: NodeType, sidebarItems: any): JSX.Element => {
//     for (const category in sidebarItems) {
//         const item = sidebarItems[category].find((i: any) => i.type === type);
//         if (item && item.icon) {
//             return React.cloneElement(item.icon, { className: "w-4 h-4" });
//         }
//     }
//
//     // Default icon if not found
//     return React.createElement('div', { className: "w-4 h-4" });
// };
//
// export const formatMetricValue = (value: number, type: string): string => {
//     switch (type) {
//         case 'successRate':
//         case 'errorRate':
//             return `${value.toFixed(1)}%`;
//         case 'completionTime':
//             return `${value}ms`;
//         case 'processingCount':
//             return value.toLocaleString();
//         case 'dataVolume':
//             return `${value}KB`;
//         case 'latency':
//             return `${value}ms`;
//         default:
//             return value.toString();
//     }
// };
//
// // Create flow connections based on query type
// export const createQueryFlow = (
//     queryType: string,
//     nodes: NodeItem[],
//     setNodes: React.Dispatch<React.SetStateAction<NodeItem[]>>,
//     setConnections: React.Dispatch<React.SetStateAction<Connection[]>>
// ) => {
//     // Clear existing connections
//     setConnections([]);
//
//     const routerNode = nodes.find(node => node.type === 'Router');
//     if (!routerNode) return;
//
//     // Define which node types we need for each query type
//     const neededTypes: Record<string, NodeType[]> = {
//         product: ['Database', 'Web Search', 'RAG'],
//         calculation: ['File Reader', 'Compute'],
//         coding: ['LLM', 'Code Execution'],
//         general: ['Q&A']
//     };
//
//     const requiredTypes = neededTypes[queryType] || neededTypes.general;
//
//     // Find existing nodes of required types
//     const existingRequiredNodes = nodes.filter(
//         node => node.id !== routerNode.id && requiredTypes.includes(node.type)
//     );
//
//     // Create missing nodes
//     const newNodes: NodeItem[] = [];
//     let posY = routerNode.position.y;
//
//     requiredTypes.forEach(type => {
//         if (!existingRequiredNodes.some(node => node.type === type)) {
//             // Determine category for this type
//             let category: 'agent' | 'component' | 'tool' = 'component';
//             if (['Router', 'RAG', 'Q&A', 'Summarizer'].includes(type)) {
//                 category = 'agent';
//             } else if (['Code Execution', 'API Connector', 'LLM', 'Vector Store'].includes(type)) {
//                 category = 'tool';
//             }
//
//             // Generate random metrics
//             const metrics = {
//                 completionTime: Math.floor(Math.random() * 200) + 50,
//                 successRate: 90 + Math.random() * 9,
//                 processingCount: Math.floor(Math.random() * 1000) + 100,
//                 errorRate: Math.random() * 5
//             };
//
//             // Create new node
//             posY += 120;
//             const newNode: NodeItem = {
//                 id: `${type.toLowerCase().replace(/\s+/g, '-')}-${uuidv4().slice(0, 8)}`,
//                 type,
//                 category,
//                 position: {
//                     x: routerNode.position.x + 400,
//                     y: posY
//                 },
//                 connected: [],
//                 metrics
//             };
//
//             newNodes.push(newNode);
//         }
//     });
//
//     // Add new nodes to the nodes state
//     setNodes(prev => [...prev, ...newNodes]);
//
//     // Create connections after nodes are added
//     setTimeout(() => {
//         const allRequiredNodes = [
//             ...existingRequiredNodes,
//             ...newNodes
//         ];
//
//         const newConnections: Connection[] = [];
//
//         // Connect router to first level nodes
//         const firstLevelNodes = allRequiredNodes.filter(node =>
//             node.type === 'Database' || node.type === 'Web Search' ||
//             node.type === 'File Reader' || node.type === 'LLM' ||
//             (queryType === 'general' && node.type === 'Q&A')
//         );
//
//         firstLevelNodes.forEach(node => {
//             // Generate random metrics for the new connection
//             const connectionMetrics = {
//                 dataVolume: Math.floor(Math.random() * 500) + 50,
//                 latency: Math.floor(Math.random() * 200) + 10,
//                 successRate: 90 + Math.random() * 9.9
//             };
//
//             newConnections.push({
//                 id: `conn-${routerNode.id}-${node.id}-${uuidv4().slice(0, 6)}`,
//                 from: routerNode.id,
//                 to: node.id,
//                 metrics: connectionMetrics
//             });
//         });
//
//         // Connect first level to second level nodes as needed
//         if (queryType === 'product') {
//             const dbNode = allRequiredNodes.find(node => node.type === 'Database');
//             const webNode = allRequiredNodes.find(node => node.type === 'Web Search');
//             const ragNode = allRequiredNodes.find(node => node.type === 'RAG');
//
//             if (dbNode && ragNode) {
//                 const connectionMetrics = {
//                     dataVolume: Math.floor(Math.random() * 500) + 50,
//                     latency: Math.floor(Math.random() * 200) + 10,
//                     successRate: 90 + Math.random() * 9.9
//                 };
//
//                 newConnections.push({
//                     id: `conn-${dbNode.id}-${ragNode.id}-${uuidv4().slice(0, 6)}`,
//                     from: dbNode.id,
//                     to: ragNode.id,
//                     metrics: connectionMetrics
//                 });
//             }
//
//             if (webNode && ragNode) {
//                 const connectionMetrics = {
//                     dataVolume: Math.floor(Math.random() * 500) + 50,
//                     latency: Math.floor(Math.random() * 200) + 10,
//                     successRate: 90 + Math.random() * 9.9
//                 };
//
//                 newConnections.push({
//                     id: `conn-${webNode.id}-${ragNode.id}-${uuidv4().slice(0, 6)}`,
//                     from: webNode.id,
//                     to: ragNode.id,
//                     metrics: connectionMetrics
//                 });
//             }
//         } else if (queryType === 'calculation') {
//             const fileNode = allRequiredNodes.find(node => node.type === 'File Reader');
//             const computeNode = allRequiredNodes.find(node => node.type === 'Compute');
//
//             if (fileNode && computeNode) {
//                 const connectionMetrics = {
//                     dataVolume: Math.floor(Math.random() * 500) + 50,
//                     latency: Math.floor(Math.random() * 200) + 10,
//                     successRate: 90 + Math.random() * 9.9
//                 };
//
//                 newConnections.push({
//                     id: `conn-${fileNode.id}-${computeNode.id}-${uuidv4().slice(0, 6)}`,
//                     from: fileNode.id,
//                     to: computeNode.id,
//                     metrics: connectionMetrics
//                 });
//             }
//         } else if (queryType === 'coding') {
//             const llmNode = allRequiredNodes.find(node => node.type === 'LLM');
//             const codeNode = allRequiredNodes.find(node => node.type === 'Code Execution');
//
//             if (llmNode && codeNode) {
//                 const connectionMetrics = {
//                     dataVolume: Math.floor(Math.random() * 500) + 50,
//                     latency: Math.floor(Math.random() * 200) + 10,
//                     successRate: 90 + Math.random() * 9.9
//                 };
//
//                 newConnections.push({
//                     id: `conn-${llmNode.id}-${codeNode.id}-${uuidv4().slice(0, 6)}`,
//                     from: llmNode.id,
//                     to: codeNode.id,
//                     metrics: connectionMetrics
//                 });
//             }
//         }
//
//         setConnections(newConnections);
//
//         // Update router's connected property
//         setNodes(prevNodes =>
//             prevNodes.map(node => {
//                 if (node.id === routerNode.id) {
//                     return {
//                         ...node,
//                         connected: firstLevelNodes.map(n => n.id)
//                     };
//                 }
//                 return node;
//             })
//         );
//     }, 100);
// };
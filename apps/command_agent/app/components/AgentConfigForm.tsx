import React, { useState, useRef, useEffect } from 'react';
import { v4 as uuidv4 } from 'uuid';
import {
    Brain, BookOpen, MessageSquare, PenTool, Database,
    Search, Zap, FolderOpen, Code, Server, Sparkles, Layers
} from 'lucide-react';

// Import types
import { NodeItem, Connection, Message, NodeType, NodeCategory } from './type';

// Import components
import AnimationStyles from './AnimationStyles';
import Header from './Header';
import Sidebar from './Sidebar';
import FlowWorkspace from './FlowWorkspace';
import ChatPanel from './ChatPanel';
import NodeMetrics from './NodeMetrics';

// Import utils
import { getNodeIcon, createQueryFlow } from '../lib/utils';

const AgentConfigForm = () => {
    // State for managing nodes and connections
    const [nodes, setNodes] = useState<NodeItem[]>([
        {
            id: 'router-1',
            type: 'Router',
            category: 'agent',
            position: { x: 300, y: 150 },
            connected: [],
            metrics: {
                completionTime: 120,
                successRate: 98.5,
                processingCount: 1254,
                errorRate: 1.5
            }
        }
    ]);
    const [connections, setConnections] = useState<Connection[]>([]);

    // State for drag and drop
    const [isDragging, setIsDragging] = useState(false);
    const [draggedNode, setDraggedNode] = useState<string | null>(null);
    const [dragOffset, setDragOffset] = useState({ x: 0, y: 0 });

    // State for connection drawing
    const [isDrawingConnection, setIsDrawingConnection] = useState(false);
    const [connectionStart, setConnectionStart] = useState<string | null>(null);
    const [mousePos, setMousePos] = useState({ x: 0, y: 0 });

    // UI state
    const [sidebarOpen, setSidebarOpen] = useState(true);
    const [sidebarCategory, setSidebarCategory] = useState<'agents' | 'components' | 'tools'>('agents');
    const [showFlow, setShowFlow] = useState(true);
    const [showMetrics, setShowMetrics] = useState(true);

    // Chat state
    const [userQuery, setUserQuery] = useState('');
    const [messages, setMessages] = useState<Message[]>([]);
    const [isProcessing, setIsProcessing] = useState(false);

    // References
    const workspaceRef = useRef<HTMLDivElement>(null);
    const messagesEndRef = useRef<HTMLDivElement>(null);

    // Sidebar items organized by category
    const sidebarItems: Record<string, any[]> = {
        agents: [
            { id: 'router', type: 'Router', description: 'Routes queries to specialized agents', icon: <Brain className="w-4 h-4" /> },
            { id: 'rag', type: 'RAG', description: 'Retrieval Augmented Generation', icon: <BookOpen className="w-4 h-4" /> },
            { id: 'qa', type: 'Q&A', description: 'Question & Answer Specialist', icon: <MessageSquare className="w-4 h-4" /> },
            { id: 'summarizer', type: 'Summarizer', description: 'Creates concise summaries', icon: <PenTool className="w-4 h-4" /> },
        ],
        components: [
            { id: 'db', type: 'Database', description: 'SQL Database Connector', icon: <Database className="w-4 h-4" /> },
            { id: 'web', type: 'Web Search', description: 'Internet Search Component', icon: <Search className="w-4 h-4" /> },
            { id: 'compute', type: 'Compute', description: 'Mathematical Computation', icon: <Zap className="w-4 h-4" /> },
            { id: 'file', type: 'File Reader', description: 'Reads document files', icon: <FolderOpen className="w-4 h-4" /> },
        ],
        tools: [
            { id: 'code', type: 'Code Execution', description: 'Executes code snippets', icon: <Code className="w-4 h-4" /> },
            { id: 'api', type: 'API Connector', description: 'External API integration', icon: <Server className="w-4 h-4" /> },
            { id: 'llm', type: 'LLM', description: 'Language model processing', icon: <Sparkles className="w-4 h-4" /> },
            { id: 'vector', type: 'Vector Store', description: 'Semantic search database', icon: <Layers className="w-4 h-4" /> },
        ],
    };

    // Auto-scroll to the latest message
    useEffect(() => {
        if (messagesEndRef.current) {
            messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
        }
    }, [messages]);

    // Track mouse position for drawing connections
    useEffect(() => {
        const handleMouseMove = (e: MouseEvent) => {
            if (workspaceRef.current) {
                const rect = workspaceRef.current.getBoundingClientRect();
                setMousePos({
                    x: e.clientX - rect.left,
                    y: e.clientY - rect.top
                });
            }

            if (isDragging && draggedNode) {
                handleDragMove(e);
            }
        };

        const handleMouseUp = () => {
            if (isDragging) {
                setIsDragging(false);
                setDraggedNode(null);
            }
        };

        document.addEventListener('mousemove', handleMouseMove);
        document.addEventListener('mouseup', handleMouseUp);

        return () => {
            document.removeEventListener('mousemove', handleMouseMove);
            document.removeEventListener('mouseup', handleMouseUp);
        };
    }, [isDragging, draggedNode]);

    // Handle starting a node drag operation
    const handleDragStart = (e: React.MouseEvent, nodeId: string, fromSidebar = false) => {
        e.preventDefault();

        if (fromSidebar) {
            // Create a new node from sidebar item
            const category = sidebarCategory.slice(0, -1) as NodeCategory; // Remove 's' from plural
            const nodeType = sidebarItems[sidebarCategory].find(item => item.id === nodeId)?.type as NodeType;

            if (!nodeType) return;

            const workspaceRect = workspaceRef.current?.getBoundingClientRect();
            if (!workspaceRect) return;

            const newNodeId = `${nodeId}-${uuidv4().slice(0, 8)}`;

            // Generate specialized metrics for the new node
            const metrics = generateSpecializedMetrics(nodeType);

            const newNode: NodeItem = {
                id: newNodeId,
                type: nodeType,
                category,
                position: {
                    x: e.clientX - workspaceRect.left - 90,
                    y: e.clientY - workspaceRect.top - 30
                },
                connected: [],
                metrics
            };

            setNodes(prev => [...prev, newNode]);
            setDraggedNode(newNodeId);
        } else {
            // Drag existing node
            setDraggedNode(nodeId);
        }

        const nodeElement = e.currentTarget as HTMLElement;
        const rect = nodeElement.getBoundingClientRect();

        setDragOffset({
            x: e.clientX - rect.left,
            y: e.clientY - rect.top
        });

        setIsDragging(true);
    };

    // Generate specialized metrics based on node type
    const generateSpecializedMetrics = (nodeType: NodeType) => {
        switch (nodeType) {
            case 'RAG':
                return {
                    completionTime: Math.floor(Math.random() * 200) + 50,
                    successRate: 90 + Math.random() * 9,
                    relevance: 90 + Math.random() * 9,
                    coherence: 88 + Math.random() * 9,
                    accuracy: 86 + Math.random() * 10
                };
            case 'Database':
                return {
                    completionTime: Math.floor(Math.random() * 200) + 50,
                    successRate: 90 + Math.random() * 9,
                    queryTime: Math.floor(Math.random() * 100) + 20,
                    records: Math.floor(Math.random() * 2000) + 100,
                    cacheHit: Math.floor(Math.random() * 30) + 70
                };
            case 'Web Search':
                return {
                    completionTime: Math.floor(Math.random() * 200) + 50,
                    successRate: 90 + Math.random() * 9,
                    sources: Math.floor(Math.random() * 15) + 3,
                    freshness: Math.floor(Math.random() * 15) + 85,
                    relevance: Math.floor(Math.random() * 15) + 85
                };
            case 'LLM':
                return {
                    completionTime: Math.floor(Math.random() * 200) + 50,
                    successRate: 90 + Math.random() * 9,
                    tokens: Math.floor(Math.random() * 1000) + 300,
                    latency: Math.floor(Math.random() * 400) + 200,
                    perplexity: 2 + Math.random() * 3
                };
            case 'Q&A':
                return {
                    completionTime: Math.floor(Math.random() * 200) + 50,
                    successRate: 90 + Math.random() * 9,
                    precision: Math.floor(Math.random() * 10) + 90,
                    recall: Math.floor(Math.random() * 20) + 80,
                    f1Score: Math.floor(Math.random() * 15) + 85
                };
            case 'Code Execution':
                return {
                    completionTime: Math.floor(Math.random() * 200) + 50,
                    successRate: 90 + Math.random() * 9,
                    runtime: Math.floor(Math.random() * 100) + 20,
                    memory: Math.floor(Math.random() * 50) + 10,
                    success: Math.floor(Math.random() * 10) + 90
                };
            default:
                return {
                    completionTime: Math.floor(Math.random() * 200) + 50,
                    successRate: 90 + Math.random() * 9,
                    processingCount: Math.floor(Math.random() * 1000) + 100,
                    errorRate: Math.random() * 5
                };
        }
    };

    // Handle dragging a node
    const handleDragMove = (e: MouseEvent) => {
        if (!isDragging || !draggedNode || !workspaceRef.current) return;

        const workspaceRect = workspaceRef.current.getBoundingClientRect();

        setNodes(prevNodes =>
            prevNodes.map(node => {
                if (node.id === draggedNode) {
                    return {
                        ...node,
                        position: {
                            x: Math.max(0, e.clientX - workspaceRect.left - dragOffset.x),
                            y: Math.max(0, e.clientY - workspaceRect.top - dragOffset.y)
                        }
                    };
                }
                return node;
            })
        );
    };

    // Start drawing a connection from a node
    const startConnection = (nodeId: string) => {
        setIsDrawingConnection(true);
        setConnectionStart(nodeId);
    };

    // Complete a connection to a target node
    const completeConnection = (targetNodeId: string) => {
        if (!connectionStart || connectionStart === targetNodeId) {
            setIsDrawingConnection(false);
            setConnectionStart(null);
            return;
        }

        // Check if connection already exists
        const connectionExists = connections.some(
            conn => conn.from === connectionStart && conn.to === targetNodeId
        );

        if (!connectionExists) {
            // Generate specialized connection metrics
            const fromNode = nodes.find(n => n.id === connectionStart);
            const toNode = nodes.find(n => n.id === targetNodeId);

            let dataVolume = Math.floor(Math.random() * 500) + 50; // Default
            let latency = Math.floor(Math.random() * 200) + 10; // Default

            // Adjust based on node types
            if (fromNode && toNode) {
                // Database to RAG connections have high data volume
                if (fromNode.type === 'Database' && toNode.type === 'RAG') {
                    dataVolume = Math.floor(Math.random() * 1000) + 500;
                }

                // Web Search connections have higher latency
                if (fromNode.type === 'Web Search') {
                    latency = Math.floor(Math.random() * 300) + 100;
                }

                // LLM connections have medium to high data volume
                if (fromNode.type === 'LLM' || toNode.type === 'LLM') {
                    dataVolume = Math.floor(Math.random() * 800) + 200;
                }
            }

            const connectionMetrics = {
                dataVolume,
                latency,
                successRate: 90 + Math.random() * 9.9
            };

            const newConnection: Connection = {
                id: `conn-${connectionStart}-${targetNodeId}-${uuidv4().slice(0, 6)}`,
                from: connectionStart,
                to: targetNodeId,
                metrics: connectionMetrics
            };

            setConnections(prev => [...prev, newConnection]);

            // Update the connected property of the source node
            setNodes(prevNodes =>
                prevNodes.map(node => {
                    if (node.id === connectionStart) {
                        return {
                            ...node,
                            connected: [...node.connected, targetNodeId]
                        };
                    }
                    return node;
                })
            );
        }

        setIsDrawingConnection(false);
        setConnectionStart(null);
    };

    // Delete a connection
    const deleteConnection = (connectionId: string) => {
        const conn = connections.find(c => c.id === connectionId);
        if (!conn) return;

        setConnections(connections.filter(c => c.id !== connectionId));

        // Update the connected property of the source node
        setNodes(prevNodes =>
            prevNodes.map(node => {
                if (node.id === conn.from) {
                    return {
                        ...node,
                        connected: node.connected.filter(id => id !== conn.to)
                    };
                }
                return node;
            })
        );
    };

    // Delete a node
    const deleteNode = (nodeId: string) => {
        // Don't allow deleting the router node
        if (nodeId === 'router-1') return;

        // Remove all connections involving this node
        setConnections(connections.filter(conn => conn.from !== nodeId && conn.to !== nodeId));

        // Remove the node
        setNodes(nodes.filter(node => node.id !== nodeId));

        // Update connected arrays in other nodes
        setNodes(prevNodes =>
            prevNodes.map(node => {
                if (node.connected.includes(nodeId)) {
                    return {
                        ...node,
                        connected: node.connected.filter(id => id !== nodeId)
                    };
                }
                return node;
            })
        );
    };

    // Process a user query and animate the flow
    const handleQuerySubmit = () => {
        if (!userQuery.trim()) return;

        // Add user query to messages
        const userMessage: Message = {
            id: `msg-${uuidv4().slice(0, 8)}`,
            type: 'user',
            text: userQuery,
            timestamp: new Date()
        };

        setMessages(prev => [...prev, userMessage]);
        setIsProcessing(true);

        // Determine query type and create appropriate flow
        const query = userQuery.toLowerCase();
        let queryType = 'general';

        if (query.includes('product') || query.includes('iphone') || query.includes('how many')) {
            queryType = 'product';
        } else if (query.includes('calculate') || query.includes('sum') || query.includes('average')) {
            queryType = 'calculation';
        } else if (query.includes('code') || query.includes('function') || query.includes('programming')) {
            queryType = 'coding';
        }

        // Update metrics for all nodes with specialized values
        setNodes(prevNodes =>
            prevNodes.map(node => ({
                ...node,
                metrics: generateSpecializedMetrics(node.type)
            }))
        );

        // Create flow connections based on query type
        createQueryFlow(queryType, nodes, setNodes, setConnections);

        // Show flow view
        setShowFlow(true);

        // Simulate response messages with appropriate timing
        simulateAgentResponses(queryType);

        // Clear input
        setUserQuery('');
    };

    // Simulate agent responses for a given query type
    const simulateAgentResponses = (queryType: string) => {
        const addMessage = (type: Message['type'], text: string, agent?: string, delay = 0) => {
            setTimeout(() => {
                const newMessage: Message = {
                    id: `msg-${uuidv4().slice(0, 8)}`,
                    type,
                    text,
                    agent,
                    timestamp: new Date()
                };

                setMessages(prev => [...prev, newMessage]);

                // If this is the final message, set isProcessing to false
                if (type === 'final') {
                    setIsProcessing(false);
                }
            }, delay);
        };

        // Router response first
        addMessage(
            'agent',
            `Query classified as ${queryType} request. Routing to appropriate agents and components.`,
            'Router',
            300
        );

        if (queryType === 'product') {
            addMessage(
                'component',
                'Searching product database for relevant information.',
                'Database',
                1000
            );

            addMessage(
                'component',
                'Retrieving up-to-date information from web sources.',
                'Web Search',
                1800
            );

            addMessage(
                'agent',
                'Combining database and web information to provide comprehensive response.',
                'RAG',
                2800
            );

            addMessage(
                'final',
                'Here is the product information you requested. Our database shows 12 iPhone models released since 2020, while web searches indicate 16 models including standard, mini/Plus, Pro, and Pro Max variants of iPhone 12, 13, 14, and 15 series.',
                undefined,
                3800
            );
        } else if (queryType === 'calculation') {
            addMessage(
                'component',
                'Reading source data from available documents.',
                'File Reader',
                1000
            );

            addMessage(
                'component',
                'Performing calculation operations on the extracted data.',
                'Compute',
                2000
            );

            addMessage(
                'final',
                'Calculation complete. Based on the provided information, the result has been computed accurately.',
                undefined,
                3000
            );
        } else if (queryType === 'coding') {
            addMessage(
                'component',
                'Generating code solution based on your requirements.',
                'LLM',
                1000
            );

            addMessage(
                'component',
                'Executing and testing the generated code for correctness.',
                'Code Execution',
                2500
            );

            addMessage(
                'final',
                'Code solution generated and verified. The function works as expected and follows best practices.',
                undefined,
                3500
            );
        } else {
            // General query
            addMessage(
                'agent',
                'Analyzing your question and retrieving relevant information.',
                'Q&A',
                1000
            );

            addMessage(
                'final',
                'Here is the answer to your question. If you need more specialized processing, try asking about products, calculations, or coding tasks.',
                undefined,
                2500
            );
        }
    };

    // Handle example query click
    const handleExampleClick = (example: string) => {
        setUserQuery(example);
        setTimeout(() => handleQuerySubmit(), 100);
    };

    // Helper function to get icon for a node type
    const getNodeIconHelper = (type: NodeType): JSX.Element => {
        return getNodeIcon(type, sidebarItems);
    };

    return (
        <div className="h-screen w-screen flex flex-col overflow-hidden">
            {/* Add style for animations */}
            <AnimationStyles />

            {/* Header */}
            <Header
                sidebarOpen={sidebarOpen}
                setSidebarOpen={setSidebarOpen}
                showFlow={showFlow}
                setShowFlow={setShowFlow}
                showMetrics={showMetrics}
                setShowMetrics={setShowMetrics}
            />

            {/* Main content */}
            <div className="flex-1 flex overflow-hidden">
                {/* Sidebar */}
                <Sidebar
                    sidebarOpen={sidebarOpen}
                    sidebarCategory={sidebarCategory}
                    setSidebarCategory={setSidebarCategory}
                    sidebarItems={sidebarItems}
                    handleDragStart={handleDragStart}
                />

                {/* Main content area with flow and chat views */}
                <div className="flex-1 flex overflow-hidden">
                    {/* Flow workspace - visible when showFlow is true */}
                    {showFlow && (
                        <FlowWorkspace
                            workspaceRef={workspaceRef}
                            nodes={nodes}
                            setNodes={setNodes}
                            connections={connections}
                            setConnections={setConnections}
                            isDragging={isDragging}
                            draggedNode={draggedNode}
                            isDrawingConnection={isDrawingConnection}
                            connectionStart={connectionStart}
                            mousePos={mousePos}
                            showMetrics={showMetrics}
                            handleDragStart={handleDragStart}
                            startConnection={startConnection}
                            completeConnection={completeConnection}
                            deleteConnection={deleteConnection}
                            deleteNode={deleteNode}
                            getNodeIcon={getNodeIconHelper}
                            sidebarCategory={sidebarCategory}
                            sidebarItems={sidebarItems}
                            isProcessing={isProcessing}
                        />
                    )}

                    {/* Chat panel */}
                    <ChatPanel
                        showFlow={showFlow}
                        messages={messages}
                        userQuery={userQuery}
                        setUserQuery={setUserQuery}
                        handleQuerySubmit={handleQuerySubmit}
                        handleExampleClick={handleExampleClick}
                        isProcessing={isProcessing}
                        messagesEndRef={messagesEndRef}
                    />
                </div>
            </div>
        </div>
    );
};

export default AgentConfigForm;
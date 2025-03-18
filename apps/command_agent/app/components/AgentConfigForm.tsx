import React, { useState, useRef, useEffect } from 'react';
import { v4 as uuidv4 } from 'uuid';
import {
    Brain, BookOpen, MessageSquare, PenTool, Database,
    Search, Zap, FolderOpen, Code, Server, Sparkles,
    Layers, ChevronRight, Menu, X, ArrowRight,
    Clock, CheckCircle, AlertCircle, BarChart2
} from 'lucide-react';

// Type definitions for our flow system
type NodeCategory = 'agent' | 'component' | 'tool';
type NodeType = 'Router' | 'RAG' | 'Q&A' | 'Summarizer' | 'Database' | 'Web Search' | 'Compute' | 'File Reader' | 'Code Execution' | 'API Connector' | 'LLM' | 'Vector Store';

interface NodeItem {
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

interface SidebarItem {
    id: string;
    type: NodeType;
    description: string;
    icon: JSX.Element;
}

interface Connection {
    id: string;
    from: string;
    to: string;
    metrics?: {
        dataVolume?: number;
        latency?: number;
        successRate?: number;
    };
}

interface Message {
    id: string;
    type: 'user' | 'agent' | 'component' | 'tool' | 'final';
    text: string;
    agent?: string;
    timestamp: Date;
}

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
    const sidebarItems: Record<string, SidebarItem[]> = {
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

            // Generate random metrics for the new node
            const metrics = {
                completionTime: Math.floor(Math.random() * 200) + 50,
                successRate: 90 + Math.random() * 9,
                processingCount: Math.floor(Math.random() * 1000) + 100,
                errorRate: Math.random() * 5
            };

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
            // Generate random metrics for the new connection
            const connectionMetrics = {
                dataVolume: Math.floor(Math.random() * 500) + 50, // 50-550 KB
                latency: Math.floor(Math.random() * 200) + 10, // 10-210ms
                successRate: 90 + Math.random() * 9.9 // 90-99.9%
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

        // Update metrics for all nodes with active values
        setNodes(prevNodes =>
            prevNodes.map(node => ({
                ...node,
                metrics: {
                    completionTime: Math.floor(Math.random() * 200) + 50,
                    successRate: 90 + Math.random() * 9,
                    processingCount: Math.floor(Math.random() * 1000) + 100,
                    errorRate: Math.random() * 5
                }
            }))
        );

        // Create flow connections based on query type
        createQueryFlow(queryType);

        // Show flow view
        setShowFlow(true);

        // Simulate response messages with appropriate timing
        simulateAgentResponses(queryType);

        // Clear input
        setUserQuery('');
    };

    // Create flow connections based on query type
    const createQueryFlow = (queryType: string) => {
        // Clear existing connections
        setConnections([]);

        const routerNode = nodes.find(node => node.type === 'Router');
        if (!routerNode) return;

        // Define which node types we need for each query type
        const neededTypes: Record<string, NodeType[]> = {
            product: ['Database', 'Web Search', 'RAG'],
            calculation: ['File Reader', 'Compute'],
            coding: ['LLM', 'Code Execution'],
            general: ['Q&A']
        };

        const requiredTypes = neededTypes[queryType] || neededTypes.general;

        // Find existing nodes of required types
        const existingRequiredNodes = nodes.filter(
            node => node.id !== routerNode.id && requiredTypes.includes(node.type)
        );

        // Create missing nodes
        const newNodes: NodeItem[] = [];
        let posY = routerNode.position.y;

        requiredTypes.forEach(type => {
            if (!existingRequiredNodes.some(node => node.type === type)) {
                // Determine category for this type
                let category: NodeCategory = 'component';
                Object.entries(sidebarItems).forEach(([cat, items]) => {
                    if (items.some(item => item.type === type)) {
                        category = cat.slice(0, -1) as NodeCategory;
                    }
                });

                // Generate random metrics
                const metrics = {
                    completionTime: Math.floor(Math.random() * 200) + 50,
                    successRate: 90 + Math.random() * 9,
                    processingCount: Math.floor(Math.random() * 1000) + 100,
                    errorRate: Math.random() * 5
                };

                // Create new node
                posY += 120;
                const newNode: NodeItem = {
                    id: `${type.toLowerCase().replace(/\s+/g, '-')}-${uuidv4().slice(0, 8)}`,
                    type,
                    category,
                    position: {
                        x: routerNode.position.x + 400,
                        y: posY
                    },
                    connected: [],
                    metrics
                };

                newNodes.push(newNode);
            }
        });

        // Add new nodes to the nodes state
        setNodes(prev => [...prev, ...newNodes]);

        // Create connections after nodes are added
        setTimeout(() => {
            const allRequiredNodes = [
                ...existingRequiredNodes,
                ...newNodes
            ];

            const newConnections: Connection[] = [];

            // Connect router to first level nodes
            const firstLevelNodes = allRequiredNodes.filter(node =>
                node.type === 'Database' || node.type === 'Web Search' ||
                node.type === 'File Reader' || node.type === 'LLM' ||
                (queryType === 'general' && node.type === 'Q&A')
            );

            firstLevelNodes.forEach(node => {
                // Generate random metrics for the new connection
                const connectionMetrics = {
                    dataVolume: Math.floor(Math.random() * 500) + 50, // 50-550 KB
                    latency: Math.floor(Math.random() * 200) + 10, // 10-210ms
                    successRate: 90 + Math.random() * 9.9 // 90-99.9%
                };

                newConnections.push({
                    id: `conn-${routerNode.id}-${node.id}-${uuidv4().slice(0, 6)}`,
                    from: routerNode.id,
                    to: node.id,
                    metrics: connectionMetrics
                });
            });

            // Connect first level to second level nodes as needed
            if (queryType === 'product') {
                const dbNode = allRequiredNodes.find(node => node.type === 'Database');
                const webNode = allRequiredNodes.find(node => node.type === 'Web Search');
                const ragNode = allRequiredNodes.find(node => node.type === 'RAG');

                if (dbNode && ragNode) {
                    const connectionMetrics = {
                        dataVolume: Math.floor(Math.random() * 500) + 50,
                        latency: Math.floor(Math.random() * 200) + 10,
                        successRate: 90 + Math.random() * 9.9
                    };

                    newConnections.push({
                        id: `conn-${dbNode.id}-${ragNode.id}-${uuidv4().slice(0, 6)}`,
                        from: dbNode.id,
                        to: ragNode.id,
                        metrics: connectionMetrics
                    });
                }

                if (webNode && ragNode) {
                    const connectionMetrics = {
                        dataVolume: Math.floor(Math.random() * 500) + 50,
                        latency: Math.floor(Math.random() * 200) + 10,
                        successRate: 90 + Math.random() * 9.9
                    };

                    newConnections.push({
                        id: `conn-${webNode.id}-${ragNode.id}-${uuidv4().slice(0, 6)}`,
                        from: webNode.id,
                        to: ragNode.id,
                        metrics: connectionMetrics
                    });
                }
            } else if (queryType === 'calculation') {
                const fileNode = allRequiredNodes.find(node => node.type === 'File Reader');
                const computeNode = allRequiredNodes.find(node => node.type === 'Compute');

                if (fileNode && computeNode) {
                    const connectionMetrics = {
                        dataVolume: Math.floor(Math.random() * 500) + 50,
                        latency: Math.floor(Math.random() * 200) + 10,
                        successRate: 90 + Math.random() * 9.9
                    };

                    newConnections.push({
                        id: `conn-${fileNode.id}-${computeNode.id}-${uuidv4().slice(0, 6)}`,
                        from: fileNode.id,
                        to: computeNode.id,
                        metrics: connectionMetrics
                    });
                }
            } else if (queryType === 'coding') {
                const llmNode = allRequiredNodes.find(node => node.type === 'LLM');
                const codeNode = allRequiredNodes.find(node => node.type === 'Code Execution');

                if (llmNode && codeNode) {
                    const connectionMetrics = {
                        dataVolume: Math.floor(Math.random() * 500) + 50,
                        latency: Math.floor(Math.random() * 200) + 10,
                        successRate: 90 + Math.random() * 9.9
                    };

                    newConnections.push({
                        id: `conn-${llmNode.id}-${codeNode.id}-${uuidv4().slice(0, 6)}`,
                        from: llmNode.id,
                        to: codeNode.id,
                        metrics: connectionMetrics
                    });
                }
            }

            setConnections(newConnections);

            // Update router's connected property
            setNodes(prevNodes =>
                prevNodes.map(node => {
                    if (node.id === routerNode.id) {
                        return {
                            ...node,
                            connected: firstLevelNodes.map(n => n.id)
                        };
                    }
                    return node;
                })
            );
        }, 100);
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

    // Render connections between nodes with more minimal metrics
    const renderConnections = () => {
        return connections.map(conn => {
            const fromNode = nodes.find(n => n.id === conn.from);
            const toNode = nodes.find(n => n.id === conn.to);

            if (!fromNode || !toNode) return null;

            // Calculate center points of the nodes
            const fromX = fromNode.position.x + 90; // half of node width
            const fromY = fromNode.position.y + 40; // approximate center of node
            const toX = toNode.position.x + 90;
            const toY = toNode.position.y + 40;

            // Calculate direction and length
            const dx = toX - fromX;
            const dy = toY - fromY;
            const len = Math.sqrt(dx * dx + dy * dy);

            // Calculate the path with a simple curve (less pronounced)
            // We'll use a perpendicular offset for a cleaner look
            let path = '';
            let labelX, labelY;

            // If nodes are very close vertically, create a more horizontal curve
            if (Math.abs(dy) < 30) {
                const midX = (fromX + toX) / 2;
                const curveHeight = 30 + Math.min(Math.abs(dx) * 0.1, 50);
                const curveY = fromY - curveHeight;
                path = `M ${fromX} ${fromY} Q ${midX} ${curveY} ${toX} ${toY}`;
                labelX = midX;
                labelY = curveY;
            }
            // If nodes are very close horizontally, create a more vertical curve
            else if (Math.abs(dx) < 30) {
                const midY = (fromY + toY) / 2;
                const curveWidth = 30 + Math.min(Math.abs(dy) * 0.1, 50);
                const curveX = fromX + curveWidth;
                path = `M ${fromX} ${fromY} Q ${curveX} ${midY} ${toX} ${toY}`;
                labelX = curveX;
                labelY = midY;
            }
            // Otherwise create a nice smooth curve
            else {
                // Create vectors for direction
                const dirX = dx / len;
                const dirY = dy / len;

                // Get perpendicular direction
                const perpX = -dirY;
                const perpY = dirX;

                // Calculate control point with a moderate offset
                const offset = Math.min(len * 0.2, 80);
                const cpX = (fromX + toX) / 2 + perpX * offset;
                const cpY = (fromY + toY) / 2 + perpY * offset;

                path = `M ${fromX} ${fromY} Q ${cpX} ${cpY} ${toX} ${toY}`;
                labelX = cpX;
                labelY = cpY;
            }

            // Calculate positions for the connection delete button
            const deleteX = (fromX + toX) / 2;
            const deleteY = (fromY + toY) / 2;

            return (
                <svg
                    key={conn.id}
                    className="absolute top-0 left-0 w-full h-full pointer-events-none z-0"
                >
                    <defs>
                        <marker
                            id={`arrowhead-${conn.id}`}
                            markerWidth="10"
                            markerHeight="7"
                            refX="9"
                            refY="3.5"
                            orient="auto"
                        >
                            <polygon points="0 0, 10 3.5, 0 7" fill="rgba(99, 102, 241, 0.8)" />
                        </marker>
                    </defs>

                    <path
                        d={path}
                        fill="none"
                        stroke="rgba(99, 102, 241, 0.6)"
                        strokeWidth="2"
                        strokeDasharray="0"
                        markerEnd={`url(#arrowhead-${conn.id})`}
                        className="animate-draw-line"
                    />

                    {/* Simplified connection metrics - inline with the arrow */}
                    {showMetrics && conn.metrics && (
                        <foreignObject
                            x={labelX - 70}
                            y={labelY - 14}
                            width="140"
                            height="28"
                            pointerEvents="all"
                        >
                            <div className="bg-white/90 px-2 py-1 rounded shadow-sm border border-indigo-100 text-xs flex items-center justify-center space-x-1.5">
                                <span className="text-gray-500">{conn.metrics.dataVolume}KB</span>
                                <span className="text-gray-300">|</span>
                                <span className={`${conn.metrics.latency > 150 ? 'text-amber-500' : 'text-gray-500'}`}>{conn.metrics.latency}ms</span>
                                <span className="text-gray-300">|</span>
                                <span className={`${conn.metrics.successRate < 95 ? 'text-amber-500' : 'text-green-500'}`}>{conn.metrics.successRate.toFixed(1)}%</span>
                            </div>
                        </foreignObject>
                    )}

                    {/* Small delete button at the midpoint */}
                    <circle
                        cx={deleteX}
                        cy={deleteY + 20}
                        r="6"
                        fill="white"
                        stroke="rgba(99, 102, 241, 0.4)"
                        strokeWidth="1"
                        className="cursor-pointer shadow-sm"
                        onClick={() => deleteConnection(conn.id)}
                        pointerEvents="all"
                    />

                    <foreignObject
                        x={deleteX - 6}
                        y={deleteY + 14}
                        width="12"
                        height="12"
                        pointerEvents="all"
                    >
                        <div
                            className="w-full h-full flex items-center justify-center cursor-pointer"
                            onClick={() => deleteConnection(conn.id)}
                        >
                            <X className="w-2 h-2 text-primary/70" />
                        </div>
                    </foreignObject>
                </svg>
            );
        });
    };

    // Render the temporary connection being drawn with simpler curve
    const renderTemporaryConnection = () => {
        if (!isDrawingConnection || !connectionStart) return null;

        const fromNode = nodes.find(n => n.id === connectionStart);
        if (!fromNode) return null;

        const fromX = fromNode.position.x + 90;
        const fromY = fromNode.position.y + 40;
        const toX = mousePos.x;
        const toY = mousePos.y;

        // Calculate direction vector
        const dx = toX - fromX;
        const dy = toY - fromY;
        const len = Math.sqrt(dx * dx + dy * dy);

        // Normalize and get perpendicular direction (use moderate curve)
        const perpX = -dy / (len || 1);
        const perpY = dx / (len || 1);

        // Generate curve with moderate offset
        const offset = Math.min(len * 0.2, 60);
        const controlX = (fromX + toX) / 2 + perpX * offset;
        const controlY = (fromY + toY) / 2 + perpY * offset;

        const path = `M ${fromX} ${fromY} Q ${controlX} ${controlY} ${toX} ${toY}`;

        return (
            <svg className="absolute top-0 left-0 w-full h-full pointer-events-none z-0">
                <defs>
                    <marker
                        id="temp-arrowhead"
                        markerWidth="10"
                        markerHeight="7"
                        refX="9"
                        refY="3.5"
                        orient="auto"
                    >
                        <polygon points="0 0, 10 3.5, 0 7" fill="rgba(99, 102, 241, 0.8)" />
                    </marker>
                </defs>

                <path
                    d={path}
                    fill="none"
                    stroke="rgba(99, 102, 241, 0.5)"
                    strokeWidth="2"
                    strokeDasharray="5,3"
                    markerEnd="url(#temp-arrowhead)"
                />
            </svg>
        );
    };

    // Get the appropriate icon for a node type
    const getNodeIcon = (type: NodeType) => {
        for (const category in sidebarItems) {
            const item = sidebarItems[category].find(i => i.type === type);
            if (item && item.icon) {
                return React.cloneElement(item.icon, { className: "w-4 h-4" });
            }
        }

        // Default icon if not found
        return <Brain className="w-4 h-4" />;
    };

    // Get the appropriate metric icon
    const getMetricIcon = (metricType: string) => {
        switch (metricType) {
            case 'completionTime':
                return <Clock className="w-3 h-3" />;
            case 'successRate':
                return <CheckCircle className="w-3 h-3" />;
            case 'processingCount':
                return <BarChart2 className="w-3 h-3" />;
            case 'errorRate':
                return <AlertCircle className="w-3 h-3" />;
            default:
                return <BarChart2 className="w-3 h-3" />;
        }
    };

    // Get class names for node styling based on category
    const getNodeClasses = (category: NodeCategory) => {
        switch (category) {
            case 'agent':
                return {
                    container: 'node-agent',
                    header: 'node-header-agent'
                };
            case 'component':
                return {
                    container: 'node-component',
                    header: 'node-header-component'
                };
            case 'tool':
                return {
                    container: 'node-tool',
                    header: 'node-header-tool'
                };
            default:
                return {
                    container: '',
                    header: ''
                };
        }
    };

    // Get message bubble styling based on message type
    const getMessageClasses = (type: Message['type']) => {
        switch (type) {
            case 'user':
                return 'message-user';
            case 'agent':
                return 'message-agent';
            case 'component':
                return 'message-component';
            case 'tool':
                return 'message-tool';
            case 'final':
                return 'message-final';
            default:
                return '';
        }
    };

    // Format metric values for display
    const formatMetricValue = (value: number, type: string): string => {
        switch (type) {
            case 'successRate':
            case 'errorRate':
                return `${value.toFixed(1)}%`;
            case 'completionTime':
                return `${value}ms`;
            case 'processingCount':
                return value.toLocaleString();
            case 'dataVolume':
                return `${value}KB`;
            case 'latency':
                return `${value}ms`;
            default:
                return value.toString();
        }
    };

    const formatTime = (date: Date): string => {
        return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    };

    // Add CSS for animations and styling
    const animationStyles = `
  @keyframes draw-line {
    from {
      stroke-dasharray: 1000;
      stroke-dashoffset: 1000;
    }
    to {
      stroke-dasharray: 1000;
      stroke-dashoffset: 0;
    }
  }
  
  .animate-draw-line {
    animation: draw-line 0.8s ease-out forwards;
  }
  
  .grid-pattern {
    background-image: linear-gradient(rgba(99, 102, 241, 0.03) 1px, transparent 1px),
                      linear-gradient(90deg, rgba(99, 102, 241, 0.03) 1px, transparent 1px);
    background-size: 20px 20px;
  }
  
  .glass-panel {
    background: rgba(255, 255, 255, 0.9);
    backdrop-filter: blur(5px);
    -webkit-backdrop-filter: blur(5px);
  }
  
  .node-shadow {
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
    transition: box-shadow 0.2s ease, transform 0.2s ease;
  }
  
  .node-shadow:hover {
    box-shadow: 0 4px 12px rgba(99, 102, 241, 0.15);
    transform: translateY(-1px);
  }
`;

    // Sample example queries
    const exampleQueries = [
        "How many iPhone models were released after 2020?",
        "Calculate the average sales from our quarterly data",
        "Write a function to convert temperatures between Celsius and Fahrenheit"
    ];

    // Function to create a new or update existing node with metrics
    const createOrUpdateNode = (type: NodeType, category: NodeCategory, position: { x: number, y: number }, existingId?: string) => {
        const metrics = {
            completionTime: Math.floor(Math.random() * 200) + 50,
            successRate: 90 + Math.random() * 9,
            processingCount: Math.floor(Math.random() * 1000) + 100,
            errorRate: Math.random() * 5
        };

        if (existingId) {
            setNodes(prev => prev.map(node => {
                if (node.id === existingId) {
                    return {
                        ...node,
                        metrics
                    };
                }
                return node;
            }));
        } else {
            const newNode: NodeItem = {
                id: `${type.toLowerCase().replace(/\s+/g, '-')}-${uuidv4().slice(0, 8)}`,
                type,
                category,
                position,
                connected: [],
                metrics
            };

            setNodes(prev => [...prev, newNode]);
            return newNode.id;
        }
    };

    return (
        <div className="h-screen w-screen flex flex-col overflow-hidden">
            {/* Add style for animations */}
            <style>{animationStyles}</style>

            {/* Header */}
            <header className="glass-panel border-b border-gray-200/50 p-4 flex items-center justify-between shadow-sm">
                <div className="flex items-center space-x-4">
                    <button
                        className="p-2 rounded-md hover:bg-gray-100/50 transition-colors"
                        onClick={() => setSidebarOpen(!sidebarOpen)}
                    >
                        <Menu className="w-5 h-5" />
                    </button>
                    <h1 className="text-xl font-medium">Agent Flow Designer</h1>
                </div>

                <div className="flex space-x-2">
                    <button
                        className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${showFlow
                            ? 'bg-primary/10 text-primary'
                            : 'bg-gray-100 text-gray-700 hover:bg-gray-200/70'
                            }`}
                        onClick={() => setShowFlow(true)}
                    >
                        Flow View
                    </button>
                    <button
                        className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${!showFlow
                            ? 'bg-primary/10 text-primary'
                            : 'bg-gray-100 text-gray-700 hover:bg-gray-200/70'
                            }`}
                        onClick={() => setShowFlow(false)}
                    >
                        Chat View
                    </button>
                    {showFlow && (
                        <button
                            className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${showMetrics
                                ? 'bg-emerald-100 text-emerald-700'
                                : 'bg-gray-100 text-gray-700 hover:bg-gray-200/70'
                                }`}
                            onClick={() => setShowMetrics(!showMetrics)}
                        >
                            {showMetrics ? 'Hide Metrics' : 'Show Metrics'}
                        </button>
                    )}
                </div>
            </header>

            {/* Main content */}
            <div className="flex-1 flex overflow-hidden">
                {/* Sidebar */}
                <div
                    className={`glass-panel border-r border-gray-200/50 h-full transition-all duration-300 ease-in-out ${sidebarOpen ? 'w-64' : 'w-0 overflow-hidden'
                        }`}
                >
                    <div className="p-4 border-b border-gray-200/50">
                        <h2 className="text-lg font-medium">Agent Flow Designer</h2>
                        <p className="text-sm text-gray-500 mt-1">Drag items to workspace</p>
                    </div>

                    <div className="flex border-b border-gray-200/50">
                        {Object.keys(sidebarItems).map((cat) => (
                            <button
                                key={cat}
                                className={`flex-1 py-2.5 text-sm font-medium transition-colors ${sidebarCategory === cat
                                    ? 'text-primary border-b-2 border-primary'
                                    : 'text-gray-500 hover:text-gray-700'
                                    }`}
                                onClick={() => setSidebarCategory(cat as 'agents' | 'components' | 'tools')}
                            >
                                {cat.charAt(0).toUpperCase() + cat.slice(1)}
                            </button>
                        ))}
                    </div>

                    <div className="p-3 space-y-2 overflow-y-auto" style={{ maxHeight: 'calc(100vh - 130px)' }}>
                        {sidebarItems[sidebarCategory]?.map((item) => (
                            <div
                                key={item.id}
                                className="sidebar-item p-2.5 rounded-lg border border-gray-200/50 cursor-grab transition-transform hover:translate-x-1 active:translate-x-0 hover:shadow-md active:shadow-sm bg-white/80"
                                draggable="true"
                                onDragStart={(e) => {
                                    e.dataTransfer.setData('text/plain', item.id);
                                    e.dataTransfer.effectAllowed = 'copy';
                                }}
                                onMouseDown={(e) => handleDragStart(e, item.id, true)}
                            >
                                <div className="flex items-center">
                                    <div className="w-8 h-8 rounded-md bg-primary/10 text-primary flex items-center justify-center mr-3">
                                        {item.icon}
                                    </div>
                                    <div>
                                        <h3 className="text-sm font-medium">{item.type}</h3>
                                        <p className="text-xs text-gray-500">{item.description}</p>
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>

                {/* Main content area with flow and chat views */}
                <div className="flex-1 flex overflow-hidden">
                    {/* Flow workspace - visible when showFlow is true */}
                    {showFlow && (
                        <div
                            ref={workspaceRef}
                            className="relative flex-1 bg-gray-50/80 overflow-auto grid-pattern"
                            onDragOver={(e) => {
                                e.preventDefault();
                                e.dataTransfer.dropEffect = 'copy';
                            }}
                            onDrop={(e) => {
                                e.preventDefault();
                                const itemId = e.dataTransfer.getData('text/plain');
                                if (itemId && workspaceRef.current) {
                                    const rect = workspaceRef.current.getBoundingClientRect();
                                    const category = sidebarCategory.slice(0, -1) as NodeCategory;
                                    const itemType = sidebarItems[sidebarCategory].find(i => i.id === itemId)?.type;

                                    if (itemType) {
                                        const newNode: NodeItem = {
                                            id: `${itemId}-${uuidv4().slice(0, 8)}`,
                                            type: itemType as NodeType,
                                            category,
                                            position: {
                                                x: e.clientX - rect.left - 90,
                                                y: e.clientY - rect.top - 40
                                            },
                                            connected: [],
                                            metrics: {
                                                completionTime: Math.floor(Math.random() * 200) + 50,
                                                successRate: 90 + Math.random() * 9,
                                                processingCount: Math.floor(Math.random() * 1000) + 100,
                                                errorRate: Math.random() * 5
                                            }
                                        };

                                        setNodes(prev => [...prev, newNode]);
                                    }
                                }
                            }}
                        >
                            {/* Render nodes */}
                            {nodes.map(node => {
                                // Determine styling based on node category
                                let headerBg, borderColor, bgColor, textColor;

                                switch (node.category) {
                                    case 'agent':
                                        headerBg = 'bg-indigo-50';
                                        borderColor = 'border-indigo-200';
                                        bgColor = 'bg-indigo-100';
                                        textColor = 'text-indigo-700';
                                        break;
                                    case 'component':
                                        headerBg = 'bg-emerald-50';
                                        borderColor = 'border-emerald-200';
                                        bgColor = 'bg-emerald-100';
                                        textColor = 'text-emerald-700';
                                        break;
                                    case 'tool':
                                        headerBg = 'bg-amber-50';
                                        borderColor = 'border-amber-200';
                                        bgColor = 'bg-amber-100';
                                        textColor = 'text-amber-700';
                                        break;
                                    default:
                                        headerBg = 'bg-gray-50';
                                        borderColor = 'border-gray-200';
                                        bgColor = 'bg-gray-100';
                                        textColor = 'text-gray-700';
                                }

                                return (
                                    <div
                                        key={node.id}
                                        className={`absolute w-[180px] rounded-lg node-shadow border ${borderColor} bg-white cursor-grab ${isDragging && draggedNode === node.id ? 'shadow-lg opacity-90' : ''
                                            }`}
                                        style={{
                                            left: `${node.position.x}px`,
                                            top: `${node.position.y}px`,
                                            zIndex: isDragging && draggedNode === node.id ? 10 : 1
                                        }}
                                        onMouseDown={(e) => handleDragStart(e, node.id)}
                                    >
                                        <div className={`px-3 py-2 ${headerBg} rounded-t-lg border-b ${borderColor} flex items-center justify-between`}>
                                            <div className="flex items-center">
                                                <div className={`w-6 h-6 rounded ${bgColor} ${textColor} flex items-center justify-center mr-2`}>
                                                    {getNodeIcon(node.type)}
                                                </div>
                                                <span className="font-medium text-sm">{node.type}</span>
                                            </div>
                                            {node.id !== 'router-1' && (
                                                <button
                                                    className="w-5 h-5 rounded hover:bg-gray-200/50 flex items-center justify-center"
                                                    onClick={() => deleteNode(node.id)}
                                                >
                                                    <X className="w-3.5 h-3.5 text-gray-500" />
                                                </button>
                                            )}
                                        </div>

                                        <div className="p-3">
                                            {/* Simplified Node Metrics Panel - Inline format */}
                                            {showMetrics && node.metrics && (
                                                <div className="mb-3 py-2 px-1.5 text-xs border-b border-gray-100">
                                                    <div className="flex items-center justify-between mb-1.5">
                                                        <div className="flex items-center">
                                                            <Clock className="w-3 h-3 text-gray-400 mr-1" />
                                                            <span className="text-gray-600">Time:</span>
                                                        </div>
                                                        <span className="font-medium">{node.metrics.completionTime}ms</span>
                                                    </div>
                                                    <div className="flex items-center justify-between">
                                                        <div className="flex items-center">
                                                            <CheckCircle className="w-3 h-3 text-gray-400 mr-1" />
                                                            <span className="text-gray-600">Success:</span>
                                                        </div>
                                                        <span className={`font-medium ${node.metrics.successRate > 95 ? 'text-green-600' : 'text-amber-600'}`}>
                                                            {node.metrics.successRate.toFixed(1)}%
                                                        </span>
                                                    </div>
                                                </div>
                                            )}

                                            <div className="flex justify-between mt-2">
                                                <button
                                                    className={`text-xs px-2 py-1 rounded ${bgColor} ${textColor} hover:bg-opacity-70 transition-colors flex items-center`}
                                                    onClick={() => startConnection(node.id)}
                                                >
                                                    <ArrowRight className="w-3 h-3 mr-1" />
                                                    Connect
                                                </button>

                                                {isDrawingConnection && connectionStart && connectionStart !== node.id && (
                                                    <button
                                                        className="text-xs px-2 py-1 rounded bg-green-100 text-green-700 hover:bg-green-200 transition-colors"
                                                        onClick={() => completeConnection(node.id)}
                                                    >
                                                        Connect
                                                    </button>
                                                )}
                                            </div>
                                        </div>
                                    </div>
                                );
                            })}

                            {/* Connection lines */}
                            {renderConnections()}

                            {/* Temporary connection while drawing */}
                            {renderTemporaryConnection()}
                        </div>
                    )}

                    {/* Chat panel - always visible on mobile, only as side panel on desktop when showFlow is true */}
                    <div
                        className={`bg-white border-l border-gray-200/50 flex flex-col ${showFlow ? 'hidden md:flex md:w-[350px]' : 'w-full'
                            }`}
                    >
                        <div className="flex-1 p-4 overflow-y-auto">
                            {messages.length === 0 ? (
                                <div className="h-full flex flex-col items-center justify-center text-center p-6">
                                    <div className="mb-6 text-gray-400">
                                        <MessageSquare className="w-12 h-12 mx-auto mb-2 opacity-30" />
                                        <h3 className="text-lg font-medium text-gray-500">No messages yet</h3>
                                        <p className="text-sm text-gray-400 mt-1">Send a query to get started</p>
                                    </div>

                                    <div className="w-full space-y-3 mt-4">
                                        <p className="text-sm font-medium text-gray-600">Try one of these examples:</p>
                                        {exampleQueries.map((query, index) => (
                                            <button
                                                key={index}
                                                className="w-full text-left px-4 py-3 rounded-lg text-sm bg-gray-50 hover:bg-gray-100 transition-colors border border-gray-200/70"
                                                onClick={() => handleExampleClick(query)}
                                            >
                                                {query}
                                            </button>
                                        ))}
                                    </div>
                                </div>
                            ) : (
                                <div className="space-y-4">
                                    {messages.map((message) => {
                                        let classes = '';
                                        let badge = null;

                                        switch (message.type) {
                                            case 'user':
                                                classes = 'bg-primary/10 text-gray-800 ml-auto border-primary/20';
                                                break;
                                            case 'agent':
                                                classes = 'bg-indigo-50 border-indigo-100';
                                                badge = <span className="text-xs font-semibold text-indigo-700 mb-1 block">{message.agent} Agent</span>;
                                                break;
                                            case 'component':
                                                classes = 'bg-emerald-50 border-emerald-100';
                                                badge = <span className="text-xs font-semibold text-emerald-700 mb-1 block">{message.agent} Component</span>;
                                                break;
                                            case 'tool':
                                                classes = 'bg-amber-50 border-amber-100';
                                                badge = <span className="text-xs font-semibold text-amber-700 mb-1 block">{message.agent} Tool</span>;
                                                break;
                                            case 'final':
                                                classes = 'bg-blue-50 border-blue-100';
                                                badge = <span className="text-xs font-semibold text-blue-700 mb-1 block">Final Response</span>;
                                                break;
                                            default:
                                                classes = 'bg-gray-50 border-gray-100';
                                        }

                                        return (
                                            <div
                                                key={message.id}
                                                className={`p-3 rounded-lg max-w-[90%] border ${classes} ${message.type === 'user' ? 'ml-auto' : 'mr-auto'
                                                    }`}
                                            >
                                                {badge}
                                                <p className="text-sm whitespace-pre-wrap">{message.text}</p>
                                                <div className="text-right mt-1">
                                                    <span className="text-xs text-gray-400">
                                                        {formatTime(message.timestamp)}
                                                    </span>
                                                </div>
                                            </div>
                                        );
                                    })}
                                    <div ref={messagesEndRef} />
                                </div>
                            )}
                        </div>

                        <div className="p-4 border-t border-gray-200/50">
                            <div className="flex items-center">
                                <input
                                    type="text"
                                    className="flex-1 border border-gray-300 rounded-l-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-primary focus:border-primary"
                                    placeholder="Ask a question..."
                                    value={userQuery}
                                    onChange={(e) => setUserQuery(e.target.value)}
                                    onKeyDown={(e) => {
                                        if (e.key === 'Enter' && !e.shiftKey) {
                                            e.preventDefault();
                                            handleQuerySubmit();
                                        }
                                    }}
                                    disabled={isProcessing}
                                />
                                <button
                                    className={`bg-primary text-white px-4 py-2 rounded-r-lg hover:bg-primary/90 transition-colors ${isProcessing ? 'opacity-50 cursor-not-allowed' : ''
                                        }`}
                                    onClick={handleQuerySubmit}
                                    disabled={isProcessing}
                                >
                                    <ChevronRight className="w-5 h-5" />
                                </button>
                            </div>
                            {isProcessing && (
                                <div className="mt-2 text-xs text-gray-500 flex items-center">
                                    <div className="w-3 h-3 bg-primary/60 rounded-full animate-pulse mr-2"></div>
                                    Processing query...
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}

export default AgentConfigForm;
import React from 'react';
import { NodeItem, Connection, NodeType } from './type';
import Node from './Node';
import ConnectionLine from './ConnectionLine';
import TempConnection from './TempConnection';
import { v4 as uuidv4 } from 'uuid';

interface FlowWorkspaceProps {
    workspaceRef: React.RefObject<HTMLDivElement>;
    nodes: NodeItem[];
    setNodes: React.Dispatch<React.SetStateAction<NodeItem[]>>;
    connections: Connection[];
    setConnections: React.Dispatch<React.SetStateAction<Connection[]>>;
    isDragging: boolean;
    draggedNode: string | null;
    isDrawingConnection: boolean;
    connectionStart: string | null;
    mousePos: { x: number; y: number };
    showMetrics: boolean;
    handleDragStart: (e: React.MouseEvent, nodeId: string, fromSidebar?: boolean) => void;
    startConnection: (nodeId: string) => void;
    completeConnection: (targetNodeId: string) => void;
    deleteConnection: (connectionId: string) => void;
    deleteNode: (nodeId: string) => void;
    getNodeIcon: (type: NodeType) => JSX.Element;
    sidebarCategory: 'agents' | 'components' | 'tools';
    sidebarItems: Record<string, any[]>;
}

const FlowWorkspace: React.FC<FlowWorkspaceProps> = ({
    workspaceRef,
    nodes,
    setNodes,
    connections,
    setConnections,
    isDragging,
    draggedNode,
    isDrawingConnection,
    connectionStart,
    mousePos,
    showMetrics,
    handleDragStart,
    startConnection,
    completeConnection,
    deleteConnection,
    deleteNode,
    getNodeIcon,
    sidebarCategory,
    sidebarItems
}) => {
    return (
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
                    const category = sidebarCategory.slice(0, -1) as any;
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
            {nodes.map(node => (
                <Node
                    key={node.id}
                    node={node}
                    isDragging={isDragging}
                    draggedNode={draggedNode}
                    showMetrics={showMetrics}
                    handleDragStart={handleDragStart}
                    deleteNode={deleteNode}
                    startConnection={startConnection}
                    isDrawingConnection={isDrawingConnection}
                    connectionStart={connectionStart}
                    completeConnection={completeConnection}
                    getNodeIcon={getNodeIcon}
                />
            ))}

            {/* Connection lines */}
            {connections.map(connection => (
                <ConnectionLine
                    key={connection.id}
                    connection={connection}
                    nodes={nodes}
                    showMetrics={showMetrics}
                    deleteConnection={deleteConnection}
                />
            ))}

            {/* Temporary connection while drawing */}
            <TempConnection
                isDrawingConnection={isDrawingConnection}
                connectionStart={connectionStart}
                nodes={nodes}
                mousePos={mousePos}
            />
        </div>
    );
};

export default FlowWorkspace;
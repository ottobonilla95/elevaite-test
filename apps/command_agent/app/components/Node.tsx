import React from 'react';
import { NodeItem, NodeType } from './type';
import { X, ArrowRight } from 'lucide-react';
import NodeMetrics from './NodeMetrics';

interface NodeProps {
    node: NodeItem;
    isDragging: boolean;
    draggedNode: string | null;
    showMetrics: boolean;
    handleDragStart: (e: React.MouseEvent, nodeId: string, fromSidebar?: boolean) => void;
    deleteNode: (nodeId: string) => void;
    startConnection: (nodeId: string) => void;
    isDrawingConnection: boolean;
    connectionStart: string | null;
    completeConnection: (targetNodeId: string) => void;
    getNodeIcon: (type: NodeType) => JSX.Element;
    processingState?: 'idle' | 'active' | 'complete' | 'error';
    processingOrder?: number;
}

const Node: React.FC<NodeProps> = ({
    node,
    isDragging,
    draggedNode,
    showMetrics,
    handleDragStart,
    deleteNode,
    startConnection,
    isDrawingConnection,
    connectionStart,
    completeConnection,
    getNodeIcon,
    processingState = 'idle',
    processingOrder = 0
}) => {
    // Determine styling based on node category
    let headerBg, borderColor, bgColor, textColor;

    switch (node.category) {
        case 'agent':
            headerBg = processingState === 'active' ? 'bg-indigo-500' :
                processingState === 'complete' ? 'bg-indigo-200' : 'bg-indigo-50';
            borderColor = processingState === 'active' ? 'border-indigo-500' :
                processingState === 'complete' ? 'border-indigo-300' : 'border-indigo-200';
            bgColor = processingState === 'active' ? 'bg-indigo-400' :
                processingState === 'complete' ? 'bg-indigo-200' : 'bg-indigo-100';
            textColor = processingState === 'active' ? 'text-white' : 'text-indigo-700';
            break;
        case 'component':
            headerBg = processingState === 'active' ? 'bg-emerald-500' :
                processingState === 'complete' ? 'bg-emerald-200' : 'bg-emerald-50';
            borderColor = processingState === 'active' ? 'border-emerald-500' :
                processingState === 'complete' ? 'border-emerald-300' : 'border-emerald-200';
            bgColor = processingState === 'active' ? 'bg-emerald-400' :
                processingState === 'complete' ? 'bg-emerald-200' : 'bg-emerald-100';
            textColor = processingState === 'active' ? 'text-white' : 'text-emerald-700';
            break;
        case 'tool':
            headerBg = processingState === 'active' ? 'bg-amber-500' :
                processingState === 'complete' ? 'bg-amber-200' : 'bg-amber-50';
            borderColor = processingState === 'active' ? 'border-amber-500' :
                processingState === 'complete' ? 'border-amber-300' : 'border-amber-200';
            bgColor = processingState === 'active' ? 'bg-amber-400' :
                processingState === 'complete' ? 'bg-amber-200' : 'bg-amber-100';
            textColor = processingState === 'active' ? 'text-white' : 'text-amber-700';
            break;
        default:
            headerBg = 'bg-gray-50';
            borderColor = 'border-gray-200';
            bgColor = 'bg-gray-100';
            textColor = 'text-gray-700';
    }

    // Animation class for active nodes
    const animationClass = processingState === 'active' ? 'animate-pulse' : '';

    // Add order badge for sequential processing visualization
    const showOrderBadge = processingOrder > 0;

    return (
        <div
            className={`absolute w-[180px] rounded-lg node-shadow border ${borderColor} bg-white cursor-grab ${isDragging && draggedNode === node.id ? 'shadow-lg opacity-90' : ''
                } ${animationClass} transition-colors duration-300`}
            style={{
                left: `${node.position.x}px`,
                top: `${node.position.y}px`,
                zIndex: isDragging && draggedNode === node.id ? 10 : 1
            }}
            onMouseDown={(e) => handleDragStart(e, node.id)}
        >
            <div className={`px-3 py-2 ${headerBg} rounded-t-lg border-b ${borderColor} flex items-center justify-between transition-colors duration-300`}>
                <div className="flex items-center">
                    <div className={`w-6 h-6 rounded ${bgColor} ${textColor} flex items-center justify-center mr-2 transition-colors duration-300`}>
                        {getNodeIcon(node.type)}
                    </div>
                    <span className={`font-medium text-sm ${processingState === 'active' ? 'text-white' : ''} transition-colors duration-300`}>
                        {node.type}
                    </span>
                </div>

                {showOrderBadge && (
                    <div className="absolute -top-2 -right-2 w-5 h-5 rounded-full bg-gray-800 text-white text-xs flex items-center justify-center">
                        {processingOrder}
                    </div>
                )}

                {node.id !== 'router-1' && (
                    <button
                        className={`w-5 h-5 rounded hover:bg-gray-200/50 flex items-center justify-center ${processingState === 'active' ? 'text-white hover:bg-white/20' : 'text-gray-500'
                            }`}
                        onClick={() => deleteNode(node.id)}
                    >
                        <X className="w-3.5 h-3.5" />
                    </button>
                )}
            </div>

            <div className="p-2">
                {/* Simplified metrics panel */}
                {showMetrics && node.metrics && (
                    <NodeMetrics
                        nodeType={node.type}
                        metrics={node.metrics}
                        isActive={processingState === 'active'}
                        isComplete={processingState === 'complete'}
                    />
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
};

export default Node;
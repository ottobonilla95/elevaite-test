"use client";

import React, { useEffect, useRef } from 'react';
import { Connection, NodeItem } from './type';
import { X } from 'lucide-react';

interface ConnectionLineProps {
    connection: Connection;
    nodes: NodeItem[];
    showMetrics: boolean;
    deleteConnection: (connectionId: string) => void;
    isActive?: boolean;
    isComplete?: boolean;
}

const ConnectionLine: React.FC<ConnectionLineProps> = ({
    connection,
    nodes,
    showMetrics,
    deleteConnection,
    isActive = false,
    isComplete = false
}) => {
    const fromNode = nodes.find(n => n.id === connection.from);
    const toNode = nodes.find(n => n.id === connection.to);
    const pathRef = useRef<SVGPathElement | null>(null);
    const deleteButtonRef = useRef<SVGCircleElement | null>(null);
    const metricLabelRef = useRef<SVGTextElement | null>(null);

    if (!fromNode || !toNode) return null;

    // Node dimensions
    const nodeWidth = 180;
    const nodeHeight = 80;

    // Calculate connection points
    const { fromX, fromY, toX, toY } = calculateConnectionPoints(
        fromNode.position.x, fromNode.position.y, nodeWidth, nodeHeight,
        toNode.position.x, toNode.position.y, nodeWidth, nodeHeight
    );

    // Simple, fast path calculation for responsiveness
    const path = calculateDirectPath(fromX, fromY, toX, toY);

    // Calculate midpoint for delete button and label
    const midX = path.midX;
    const midY = path.midY;

    // Determine styles based on node category
    let strokeColor = '#4338ca'; // Default indigo
    let strokeWidth = 3;

    if (fromNode.category === 'agent') {
        strokeColor = '#4338ca'; // Indigo
    } else if (fromNode.category === 'component') {
        strokeColor = '#059669'; // Emerald
    } else if (fromNode.category === 'tool') {
        strokeColor = '#d97706'; // Amber
    }

    // Adjust for active/complete states
    if (isActive) {
        strokeColor = fromNode.category === 'agent' ? '#6366f1' :
            fromNode.category === 'component' ? '#10b981' :
                '#f59e0b';
        strokeWidth = 4;
    } else if (isComplete) {
        strokeColor = fromNode.category === 'agent' ? '#a5b4fc' :
            fromNode.category === 'component' ? '#6ee7b7' :
                '#fcd34d';
        strokeWidth = 2.5;
    }

    return (
        <svg
            key={connection.id}
            className="absolute top-0 left-0 w-full h-full pointer-events-none z-0"
        >
            <defs>
                <marker
                    id={`arrowhead-${connection.id}`}
                    markerWidth="8"
                    markerHeight="6"
                    refX="8"
                    refY="3"
                    orient="auto"
                    markerUnits="strokeWidth"
                >
                    <polygon points="0 0, 8 3, 0 6" fill={strokeColor} />
                </marker>
            </defs>

            <path
                ref={pathRef}
                d={path.pathData}
                fill="none"
                stroke={strokeColor}
                strokeWidth={strokeWidth}
                strokeDasharray="0"
                markerEnd={`url(#arrowhead-${connection.id})`}
                className={`${isActive ? 'animate-pulse' : ''} transition-colors duration-300`}
            />

            {/* Simple KB label - only shown when showMetrics is true */}
            {showMetrics && connection.metrics && (
                <text
                    ref={metricLabelRef}
                    x={midX}
                    y={midY - 12}
                    textAnchor="middle"
                    fontSize="10"
                    fontWeight="500"
                    fill="#4b5563"
                    className="pointer-events-none"
                >
                    {connection.metrics.dataVolume}K
                </text>
            )}

            {/* Delete button */}
            <circle
                ref={deleteButtonRef}
                cx={midX}
                cy={midY}
                r="7"
                fill="white"
                stroke={strokeColor}
                strokeWidth="1.5"
                className="cursor-pointer shadow-sm hover:shadow-md"
                onClick={() => deleteConnection(connection.id)}
                pointerEvents="all"
            />

            <foreignObject
                x={midX - 5}
                y={midY - 5}
                width="10"
                height="10"
                pointerEvents="all"
            >
                <div
                    className="w-full h-full flex items-center justify-center cursor-pointer"
                    onClick={() => deleteConnection(connection.id)}
                >
                    <X className="w-2.5 h-2.5 text-gray-600" />
                </div>
            </foreignObject>
        </svg>
    );
};

// Calculate the best connection points from each node
function calculateConnectionPoints(
    fromNodeX: number, fromNodeY: number, fromNodeWidth: number, fromNodeHeight: number,
    toNodeX: number, toNodeY: number, toNodeWidth: number, toNodeHeight: number
) {
    // Calculate center points
    const fromCenterX = fromNodeX + fromNodeWidth / 2;
    const fromCenterY = fromNodeY + fromNodeHeight / 2;
    const toCenterX = toNodeX + toNodeWidth / 2;
    const toCenterY = toNodeY + toNodeHeight / 2;

    // Find intersection points with node boundaries
    // This uses a simplified approach for performance
    const dx = toCenterX - fromCenterX;
    const dy = toCenterY - fromCenterY;
    const angle = Math.atan2(dy, dx);

    // Calculate exit point from source node
    const fromX = fromCenterX + Math.cos(angle) * (fromNodeWidth / 2);
    const fromY = fromCenterY + Math.sin(angle) * (fromNodeHeight / 2);

    // Calculate entry point to target node
    const toX = toCenterX - Math.cos(angle) * (toNodeWidth / 2);
    const toY = toCenterY - Math.sin(angle) * (toNodeHeight / 2);

    return { fromX, fromY, toX, toY };
}

// Calculate a direct path with a slight curve for visual appeal
// This is optimized for performance during node movement
function calculateDirectPath(fromX: number, fromY: number, toX: number, toY: number) {
    const dx = toX - fromX;
    const dy = toY - fromY;
    const distance = Math.sqrt(dx * dx + dy * dy);

    // For very direct connections, just use a straight line
    if (distance < 100) {
        return {
            pathData: `M ${fromX} ${fromY} L ${toX} ${toY}`,
            midX: (fromX + toX) / 2,
            midY: (fromY + toY) / 2
        };
    }

    // Use a simple quadratic curve for better performance
    // The control point is offset perpendicular to the line
    const midX = (fromX + toX) / 2;
    const midY = (fromY + toY) / 2;

    // Calculate a slight perpendicular offset for the control point
    const perpX = -dy / distance * Math.min(distance * 0.2, 30);
    const perpY = dx / distance * Math.min(distance * 0.2, 30);

    const cpX = midX + perpX;
    const cpY = midY + perpY;

    return {
        pathData: `M ${fromX} ${fromY} Q ${cpX} ${cpY}, ${toX} ${toY}`,
        midX: cpX,
        midY: cpY
    };
}

export default ConnectionLine;
"use client";

import React from 'react';
import { NodeItem } from './type';

interface TempConnectionProps {
    isDrawingConnection: boolean;
    connectionStart: string | null;
    nodes: NodeItem[];
    mousePos: { x: number; y: number };
}

const TempConnection: React.FC<TempConnectionProps> = ({
    isDrawingConnection,
    connectionStart,
    nodes,
    mousePos
}) => {
    if (!isDrawingConnection || !connectionStart) return null;

    const fromNode = nodes.find(n => n.id === connectionStart);
    if (!fromNode) return null;

    // Node dimensions
    const nodeWidth = 180;
    const nodeHeight = 80;

    // Calculate center of the node
    const fromCenterX = fromNode.position.x + nodeWidth / 2;
    const fromCenterY = fromNode.position.y + nodeHeight / 2;
    const toX = mousePos.x;
    const toY = mousePos.y;

    // Calculate direction vector
    const dx = toX - fromCenterX;
    const dy = toY - fromCenterY;
    const len = Math.sqrt(dx * dx + dy * dy);

    // Normalize direction vector
    const ndx = dx / len;
    const ndy = dy / len;

    // Calculate the edge point (where the line should start)
    const fromX = fromCenterX + ndx * (nodeWidth / 2);
    const fromY = fromCenterY + ndy * (nodeHeight / 2);

    // Calculate perpendicular direction for curve
    const perpX = -ndy;
    const perpY = ndx;

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
                    markerWidth="8"  // Reduced from 16
                    markerHeight="6"  // Reduced from 12
                    refX="8"         // Reduced from 16
                    refY="2"          // Reduced from 6
                    orient="auto"
                >
                    <polygon points="0 0, 10 4, 0 8" fill="#4338ca" />
                </marker>
            </defs>

            <path
                d={path}
                fill="none"
                stroke="#4338ca"
                strokeWidth="5"
                strokeDasharray="8,4"
                markerEnd="url(#temp-arrowhead)"
            />
        </svg>
    );
};

export default TempConnection;
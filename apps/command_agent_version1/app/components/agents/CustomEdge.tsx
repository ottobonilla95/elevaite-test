"use client";

import React from "react";
import { X } from "lucide-react";
import { type EdgeProps, getMarkerEnd } from "react-flow-renderer";
import "./CustomEdge.scss";

interface CustomEdgeData {
    actionType?: "Action" | "Conditional" | "Notification" | "Delay";
}

interface CustomEdgeProps extends EdgeProps {
    data?: CustomEdgeData;
}

function CustomEdge({
    id,
    sourceX,
    sourceY,
    targetX,
    targetY,
    sourcePosition,
    targetPosition,
    style = {},
    markerEnd,
    data
}: CustomEdgeProps): JSX.Element {
    // Create a curved path between source and target
    const edgePath = `M ${sourceX} ${sourceY} C ${sourceX} ${sourceY + 50} ${targetX} ${targetY - 50} ${targetX} ${targetY}`;

    // Calculate the center point of the edge for label positioning
    const centerX = (sourceX + targetX) / 2;
    const centerY = (sourceY + targetY) / 2;

    // Basic edge without a label - when no data or actionType is provided
    if (!data?.actionType) {
        return (
            <path
                id={id}
                className="react-flow__edge-path"
                d={edgePath}
                strokeWidth={2}
                markerEnd={markerEnd}
                style={{ ...style }}
            />
        );
    }

    // Get action type from data
    const actionType = data.actionType;

    // Set color based on action type
    let bgColor = "#4CAF50"; // Default green for "Action"
    if (actionType === "Conditional") {
        bgColor = "#FF9800"; // Orange for "Conditional"
    } else if (actionType === "Notification") {
        bgColor = "#9C27B0"; // Purple for "Notification"
    } else if (actionType === "Delay") {
        bgColor = "#FF5722"; // Deep Orange for "Delay"
    }

    // Function to remove only the label but keep the connection
    const removeLabelOnly = (event: React.MouseEvent) => {
        event.stopPropagation();

        // Dispatch custom event to be caught by DesignerCanvas
        const customEvent = new CustomEvent('remove-edge-label', {
            detail: { id, removeConnectionOnly: false }
        });
        document.dispatchEvent(customEvent);
    };

    return (
        <>
            <path
                id={id}
                className="react-flow__edge-path"
                d={edgePath}
                strokeWidth={2}
                markerEnd={markerEnd}
                style={{ ...style }}
            />
            <foreignObject
                width={110}
                height={28}
                x={centerX - 55}
                y={centerY - 14}
                className="edge-label-container"
                requiredExtensions="http://www.w3.org/1999/xhtml"
            >
                <div
                    className="edge-label"
                    style={{ backgroundColor: bgColor }}
                >
                    <span className="edge-label-text">
                        {actionType === "Action" ? "+ Action" : actionType}
                    </span>
                    <button
                        onClick={removeLabelOnly}
                        className="edge-label-button"
                    >
                        <X size={12} />
                    </button>
                </div>
            </foreignObject>
        </>
    );
}

export default CustomEdge;
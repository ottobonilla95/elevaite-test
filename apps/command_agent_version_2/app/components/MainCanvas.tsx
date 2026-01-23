import { Background, MiniMap, type EdgeTypes, type NodeTypes, ReactFlow, type ReactFlowInstance, type XYPosition } from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import { useCallback, useRef, type JSX } from 'react';
import { useCanvas } from '../lib/contexts/CanvasContext';
import { CanvasNodeType } from '../lib/enums';
import { getDragData } from '../lib/utilities/nodes';
import { CommandEdge } from './edges/CommandEdge';
import "./MainCanvas.scss";
import { CommandNode } from './nodes/CommandNode';




export const nodeTypes: NodeTypes = {
    [CanvasNodeType.COMMAND]: CommandNode,
}

export const edgeTypes: EdgeTypes = {
    command: CommandEdge,
}



interface MainCanvasProps {
    isMinimapVisible?: boolean;
}


export function MainCanvas(props: MainCanvasProps): JSX.Element {
    const canvasContext = useCanvas();
    const flowInstanceRef = useRef<ReactFlowInstance | null>(null);


    // Callbacks
    const onInit = useCallback(handleInit, [canvasContext]);
    const onDragOver = useCallback(handleDragOver, []);
    const onDrop = useCallback(handleDrop, []);


    // Function definitions

    function handleInit(instance: ReactFlowInstance): void {
        flowInstanceRef.current = instance;
        canvasContext.setReactFlowInstance(instance);
    }

    function handleDragOver(event: React.DragEvent): void {
        event.preventDefault();
        event.dataTransfer.dropEffect = "move";
    }

    function handleDrop(event: React.DragEvent): void {
        event.preventDefault();

        const droppedData = getDragData(event, "application/command-node");
        if (!droppedData) return;

        const clientPosition: XYPosition = { x: event.clientX, y: event.clientY };
        canvasContext.addNodeAtPosition(droppedData, clientPosition);
    }



  
    return (
        <div className="main-canvas-container">
            <ReactFlow
                onInit={onInit}
                nodes={canvasContext.nodes}
                edges={canvasContext.edges}
                nodeTypes={nodeTypes}
                edgeTypes={edgeTypes}
                defaultEdgeOptions={{ type: "command" }}
                onNodesChange={canvasContext.handleNodeChange}
                onEdgesChange={canvasContext.handleEdgesChange}
                onConnect={canvasContext.handleConnection}
                onDragOver={onDragOver}
                onDrop={onDrop}
                fitView
            >
                <Background/>
                {!props.isMinimapVisible ? undefined :
                    <MiniMap className="main-canvas-minimap" />
                }
            </ReactFlow>
        </div>
    );
}
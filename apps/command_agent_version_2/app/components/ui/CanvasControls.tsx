import { CommonButton } from "@repo/ui";
import { useReactFlow } from "@xyflow/react";
import { useState, type JSX } from "react";
import { useCanvas } from "../../lib/contexts/CanvasContext";
import { Icons } from "../icons";
import "./CanvasControls.scss";
import { ConfirmationPopup } from "./ConfirmationPopup";


interface CanvasControlsProps {
    isMinimapVisible?: boolean;
    setIsMinimapVisible?: (isVisible: boolean) => void;
}


export function CanvasControls(props: CanvasControlsProps): JSX.Element {
    const canvasContext = useCanvas();
    const flowContext = useReactFlow();
    const [isClearCanvasConfirmationOpen, setIsClearCanvasConfirmationOpen] = useState(false);


    function handleElaiClick(): void {
        console.log("Elai Clicked!");
    }

    function handleUndo(): void {
        canvasContext.undo();
    }

    function handleRedo(): void {
        canvasContext.redo();
    }

    function handleZoomIn(): void {
        void flowContext.zoomIn();
    }

    function handleZoomOut(): void {
        void flowContext.zoomOut();
    }

    function handleFitToScreen(): void {
        void flowContext.fitView();
    }

    function handleToggleMap(): void {
        if (!props.setIsMinimapVisible) return;
        props.setIsMinimapVisible(!props.isMinimapVisible);
    }

    function handleClearCanvas(): void {
        setIsClearCanvasConfirmationOpen(true);
    }

    function handleClearCanvasConfirmation(): void {
        setIsClearCanvasConfirmationOpen(false);
        canvasContext.resetCanvas();
    }

    function handleSimpleView(): void {
        canvasContext.nodeViewChange(undefined, "min");
    }

    function handleDetailedView(): void {
        canvasContext.nodeViewChange(undefined, "max");
    }


    return (
        <div className="canvas-controls-container">
            <div className="canvas-controls-contents">
                
                <CommonButton onClick={handleElaiClick} disabled title="Coming soon! — Get help from Elai to build the workflow exactly as you want it!">
                    <Icons.SVGElai/> Elai
                </CommonButton>

                <div className="separator"/>

                <div className="grouped-buttons">
                    <CommonButton onClick={handleUndo} disabled={!canvasContext.canUndo} title="Undo">
                        <Icons.SVGUndo/>
                    </CommonButton>

                    <CommonButton onClick={handleRedo} disabled={!canvasContext.canRedo} title="Redo">
                        <Icons.SVGRedo/>
                    </CommonButton>
                </div>

                <div className="separator"/>

                <div className="grouped-buttons">
                    <CommonButton onClick={handleZoomIn} title="Zoom in">
                        <Icons.SVGZoomIn/>
                    </CommonButton>

                    <CommonButton onClick={handleZoomOut} title="Zoom out">
                        <Icons.SVGZoomOut/>
                    </CommonButton>
                </div>

                <div className="separator"/>
                
                <CommonButton onClick={handleFitToScreen} title="Fit all nodes to your screen">
                    <Icons.SVGFitToScreen/>
                </CommonButton>
                
                <CommonButton
                    className={["button-toggle", props.isMinimapVisible ? "active" : undefined].filter(Boolean).join(" ")}
                    onClick={handleToggleMap} title={`${props.isMinimapVisible ? "Hide" : "Show"} the canvas minimap`}
                    disabled={!props.setIsMinimapVisible}
                >
                    <Icons.SVGMinimap/>
                </CommonButton>
                
                <CommonButton onClick={handleClearCanvas} title="Clear the workboard">
                    <Icons.SVGClearBoard/>
                </CommonButton>

                <div className="separator"/>

                <div className="paired-buttons">
                    <CommonButton
                        className={["view-toggle", canvasContext.nodeViewState === "simple" ? "active" : undefined].filter(Boolean).join(" ")}
                        onClick={handleSimpleView} disabled={canvasContext.nodeViewState === "simple"} title="Minimize all nodes"
                    >
                        <Icons.SVGSimpleView/>
                    </CommonButton>

                    <CommonButton                     
                        className={["view-toggle", canvasContext.nodeViewState === "expanded" ? "active" : undefined].filter(Boolean).join(" ")}
                        onClick={handleDetailedView} disabled={canvasContext.nodeViewState === "expanded"} title="Expand all nodes"
                    >
                        <Icons.SVGDetailedView/>
                    </CommonButton>
                </div>

            </div>


            {!isClearCanvasConfirmationOpen ? undefined :
                <ConfirmationPopup
                    title="Are you sure you want to clear the workboard?"
                    confirmLabel="Clear Workboard"
                    onConfirm={handleClearCanvasConfirmation}
                    onCancel={() => { setIsClearCanvasConfirmationOpen(false); } }
                />
            }

        </div>
    );
}
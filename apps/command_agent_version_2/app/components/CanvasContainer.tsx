"use client";
import { useState, type JSX } from "react";
import "./CanvasContainer.scss";
import { MainCanvas } from "./MainCanvas";
import { CanvasControls } from "./ui/CanvasControls";
import { ConfigPanel } from "./ui/ConfigPanel";
import { SidePanel } from "./ui/SidePanel";




export function CanvasContainer(): JSX.Element {
    const [isMinimapVisible, setIsMinimapVisible] = useState(true);
    
    return (
        <div className="main-canvas-container">
            <MainCanvas isMinimapVisible={isMinimapVisible} />
            <SidePanel/>
            <ConfigPanel/>
            <CanvasControls isMinimapVisible={isMinimapVisible} setIsMinimapVisible={setIsMinimapVisible} />
        </div>
    );
}
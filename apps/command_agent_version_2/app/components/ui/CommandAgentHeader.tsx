"use client";;
import { CommonButton } from "@repo/ui";
import { useThemes } from "@repo/ui/contexts";
import { useCanvas } from "../../lib/contexts/CanvasContext";
import { toast } from "../../lib/utilities/toast";
import { Icons } from "../icons";
import "./CommandAgentHeader.scss";
import { NavigationBar } from "./NavigationBar";


import type { JSX } from "react";


export function CommandAgentHeader(): JSX.Element {
    const themeContext = useThemes();
    const { nodes, workflowName, executionId, runPreview } = useCanvas();


    
    function handleBackClick(): void {
        console.log("Clicked back!");
    }

    async function handlePreviewClick(): Promise<void> {
        if (nodes.length === 0) {
            toast.warning("No nodes on canvas to preview.", { position: "top-center" });
            return;
        }

        await runPreview();
    }

    function handleThemeTest(): void {
        const [first, second] = themeContext.themesList;
        const currentId = localStorage.getItem("elevaite_theme") ?? first.id;
        const nextId = currentId === first.id ? second.id : first.id;
        themeContext.changeTheme(nextId);
    }


    return (
        <div className="command-agent-header-container">

            <div className="header-left">

                <div className="workflow-name">
                    <CommonButton onClick={handleBackClick}>
                        <Icons.SVGArrowBack />
                    </CommonButton>
                    <span>{workflowName}</span>
                    <div className="draft-label">Draft</div>
                </div>

            </div>

            <div className="header-center">
                <NavigationBar />
            </div>

            <div className="header-right">

                <div className="workflow-controls">
                    <CommonButton onClick={handleThemeTest} className="workflow-controls-button">
                        <Icons.SVGSearch />
                        Theme change test
                    </CommonButton>
                    <CommonButton
                        onClick={handlePreviewClick}
                        className="workflow-controls-button"
                        disabled={executionId !== null}
                    >
                        <Icons.SVGPlay />
                        {executionId !== null ? "Running..." : "Preview"}
                    </CommonButton>
                </div>

            </div>

        </div>
    );
}
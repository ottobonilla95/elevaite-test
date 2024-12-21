"use client";
import { CommonButton, ElevaiteIcons } from "@repo/ui/components";
import { useState } from "react";
import "./Sidebar.scss";
import {SessionBar} from "../SessionBar.tsx";



export function Sidebar(): JSX.Element {
    const [isExpanded, setIsExpanded] = useState(false);

    function toggleExpanded(): void {
        setIsExpanded(current => !current);
    }


    return (
        <div className={[
            "advanced-sidebar-container",
            "sidebar-area",
            isExpanded ? "is-open" : undefined,
            ].filter(Boolean).join(" ")}
        >
            <div className="advanced-sidebar-contents">
                <div className="sidebar-controls">
                    <CommonButton
                        onClick={toggleExpanded}
                        className="expand-toggle"
                        noBackground
                    >
                        <ElevaiteIcons.SVGSideArrow/>

                    </CommonButton>
                </div>
                {isExpanded ? <SessionBar/> : null}
            </div>
        </div>
    );
}
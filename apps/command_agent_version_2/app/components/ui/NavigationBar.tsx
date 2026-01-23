import { CommonButton } from "@repo/ui";
import { useState, type JSX } from "react";
import { Icons } from "../icons";
import "./NavigationBar.scss";



const navigationTabs = [
    { id: "workflow", label: "Workflow", icon: <Icons.SVGWorkflow/> },
    { id: "conversations", label: "Conversations", icon: <Icons.SVGConversations/> },
    { id: "analytics", label: "Analytics", icon: <Icons.SVGAnalytics/> },
    { id: "evaluations", label: "Evaluations", icon: <Icons.SVGEvaluations/> },
];

type behaviorOptions = "staticIcons" | "staticLabels" | "hover";

interface NavigationTab {
    id: string;
    label: string;
    icon: React.ReactElement<any>;
}

export function NavigationBar(): JSX.Element {
    const behavior: behaviorOptions = "staticIcons";
    // TODO: Handle this from context?
    const [activeTab, setActiveTab] = useState(navigationTabs[0]);



    function handleClick(tab: NavigationTab): void {
        setActiveTab(tab);
    }


    return (
        <div className="navigation-bar-container">

            {navigationTabs.map(tab =>
                <CommonButton
                    key={tab.id}
                    className={[
                        "navigation-bar-button",
                        activeTab.id === tab.id ? "active" : undefined,
                        behavior,
                    ].filter(Boolean).join(" ")}
                    overrideClass
                    onClick={() => { handleClick(tab); } }
                    title={activeTab.id === tab.id ? "" : tab.label}
                >
                    <div className="navigation-button-icon-container">{tab.icon}</div>
                    <span className="navigation-button-label">{tab.label}</span>
                </CommonButton>
            )}

        </div>
    );
}
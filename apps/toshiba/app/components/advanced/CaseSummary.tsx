import { CommonButton } from "@repo/ui/components";
import { useState } from "react";
import { ActionsBar } from "./ActionsBar";
import "./CaseSummary.scss";


enum Tabs {
    caseSummary = "Case Summary",
    transcript = "Transcript",
}




export function CaseSummary(): JSX.Element {
    const [activeTab, setActiveTab] = useState<Tabs>(Tabs.caseSummary);


    function handleTabClick(tab: Tabs): void {
        setActiveTab(tab);
    }

    function handleUpvote(): void {
        console.log("Upvoted")
    }
    function handleDownvote(): void {
        console.log("Downvoted")
    }
    function handleRefresh(): void {
        console.log("Refreshed")
    }
    function handleFlag(): void {
        console.log("Flagged")
    }
    function handleCopy(): void {
        console.log("Copied")
    }


    return (
        <div className="case-summary-container">
            <div className="case-summary-tabs">
                <CommonButton
                    className={["tab", activeTab === Tabs.caseSummary ? "active" : undefined].filter(Boolean).join(" ")}
                    onClick={() => { handleTabClick(Tabs.caseSummary); }}
                >
                    {Tabs.caseSummary}
                </CommonButton>
                <CommonButton
                    className={["tab", activeTab === Tabs.transcript ? "active" : undefined].filter(Boolean).join(" ")}
                    onClick={() => { handleTabClick(Tabs.transcript); }}
                >
                    {Tabs.transcript}
                </CommonButton>
            </div>
            <div className="case-summary-main-container">
                {activeTab === Tabs.caseSummary ? 
                    <div>Put Case Summary here.</div>
                    :
                    <div>Put Transcript here.</div>
                }
            </div>
            <ActionsBar
                onUpvote={handleUpvote}
                onDownvote={handleDownvote}
                onRefresh={handleRefresh}
                onFlag={handleFlag}
                onCopy={handleCopy}
            />
        </div>
    );
}
import { CommonButton, ElevaiteIcons } from "@repo/ui/components";
import { useState } from "react";
import "./CaseSummaryBlock.scss";
import { ActionsBar } from "./ActionsBar";

const test = `A customer reported issues with their Arlo Pro 4 camera system, specifically that the cameras frequently disconnect from the base station after the most recent firmware update (Version 3.5.2). The disconnections occur intermittently, particularly during high-traffic periods, causing significant disruptions to real-time monitoring.

Impact:
Devices Affected: 3 out of 5 cameras in the system.
Criticality: High - customer relies on real-time footage for home security.
Recent Actions: Customer attempted resetting the base station and re-pairing the cameras, but the issue persists.

Resolution Trajectory:Historical ticket data suggests that 90% of similar issues are resolved with a firmware rollback. The engineering team is reviewing compatibility concerns for a patch.

Next Steps:
Confirm successful downgrade and device functionality.
Engineering team to provide a patch for Firmware 3.5.2 within 5 business days.
Follow up with the customer to ensure satisfaction post-patch application.A customer reported issues with their Arlo Pro 4 camera system, specifically that the cameras frequently disconnect from the base station after the most recent firmware update (Version 3.5.2). The disconnections occur intermittently, particularly during high-traffic periods, causing significant disruptions to real-time monitoring.

Impact:
Devices Affected: 3 out of 5 cameras in the system.
Criticality: High - customer relies on real-time footage for home security.
Recent Actions: Customer attempted resetting the base station and re-pairing the cameras, but the issue persists.

Resolution Trajectory:Historical ticket data suggests that 90% of similar issues are resolved with a firmware rollback. The engineering team is reviewing compatibility concerns for a patch.

Next Steps:
Confirm successful downgrade and device functionality.
Engineering team to provide a patch for Firmware 3.5.2 within 5 business days.
Follow up with the customer to ensure satisfaction post-patch application.A customer reported issues with their Arlo Pro 4 camera system, specifically that the cameras frequently disconnect from the base station after the most recent firmware update (Version 3.5.2). The disconnections occur intermittently, particularly during high-traffic periods, causing significant disruptions to real-time monitoring.

Impact:
Devices Affected: 3 out of 5 cameras in the system.
Criticality: High - customer relies on real-time footage for home security.
Recent Actions: Customer attempted resetting the base station and re-pairing the cameras, but the issue persists.

Resolution Trajectory:Historical ticket data suggests that 90% of similar issues are resolved with a firmware rollback. The engineering team is reviewing compatibility concerns for a patch.

Next Steps:
Confirm successful downgrade and device functionality.
Engineering team to provide a patch for Firmware 3.5.2 within 5 business days.
Follow up with the customer to ensure satisfaction post-patch application.`;


interface CaseSummaryBlockProps {

}

export function CaseSummaryBlock(props: CaseSummaryBlockProps): JSX.Element {
    const [isExpanded, setIsExpanded] = useState(false);

    function handleToggle(): void {
        setIsExpanded(current => !current);
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
        <div className={["case-summary-block-container", isExpanded ? "expanded" : undefined].filter(Boolean).join(" ")}>
            <div className="header-container">
                <CommonButton onClick={handleToggle}><ElevaiteIcons.SVGChevron/></CommonButton>
                <span>Case Summary</span>
            </div>

            <div className="case-summary-accordion-container">
                <div className="case-summary-accordion">
                    <div className="case-summary-contents">
                        <div className="case-summary-text">
                            {test}
                        </div>
                        
                        <div className="actions-bar-wrapper">
                            <ActionsBar
                                onUpvote={handleUpvote}
                                onDownvote={handleDownvote}
                                onRefresh={handleRefresh}
                                onFlag={handleFlag}
                                onCopy={handleCopy}
                            />
                        </div>
                    </div>
                </div>
            </div>

        </div>
    );
}
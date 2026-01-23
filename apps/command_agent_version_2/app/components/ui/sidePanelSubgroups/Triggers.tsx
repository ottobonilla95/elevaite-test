import { useCanvas } from "../../../lib/contexts/CanvasContext";
import { CategoryId, TriggerNodeId } from "../../../lib/enums";
import { type SidePanelOption } from "../../../lib/interfaces";
import { getNewOption, getPayloadFromOption } from "../../../lib/utilities/nodes";
import SidePanelItem from "./SidePanelItem";
import { SubgroupWrapper } from "./SubgroupWrapper";



import type { JSX } from "react";



export default function Triggers(): JSX.Element {
    const canvasContext = useCanvas();
    const categoryId = CategoryId.TRIGGERS;
    const label = "New Trigger";

    const triggersLayout: SidePanelOption[] = [
        { id: TriggerNodeId.WEBHOOK, label: "Webhook", icon: TriggerNodeId.WEBHOOK, nodeDetails: { categoryId } },
        { id: TriggerNodeId.EVENT_LISTENER, label: "Event Listener", icon: TriggerNodeId.EVENT_LISTENER, nodeDetails: { categoryId } },
        { id: TriggerNodeId.SCHEDULER, label: "Scheduler", icon: TriggerNodeId.SCHEDULER, nodeDetails: { categoryId } },
    ];


    function handleAddTrigger(): void {
        canvasContext.addNodeAtPosition(getNewOption(label, categoryId));
    }

    function handleOptionClick(option: SidePanelOption): void {
        canvasContext.addNodeAtPosition(getPayloadFromOption(option, { categoryId }));
    }

    return (
        <div className="side-panel-subgroup-container triggers">
            <SidePanelItem
                onClick={handleAddTrigger}
                addLabel={label}
                preventDrag
            />

            <SubgroupWrapper
                layout={triggersLayout}
                onClick={handleOptionClick}
                ignoreEmpty
            />
        </div>
    );
}
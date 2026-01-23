import { useCanvas } from "../../../lib/contexts/CanvasContext";
import { AgentNodeId, CategoryId } from "../../../lib/enums";
import { type SidePanelOption } from "../../../lib/interfaces";
import { getNewOption, getPayloadFromOption } from "../../../lib/utilities/nodes";
import SidePanelItem from "./SidePanelItem";
import { SubgroupWrapper } from "./SubgroupWrapper";





import type { JSX } from "react";





export default function Agents(): JSX.Element {
    const canvasContext = useCanvas();
    const categoryId = CategoryId.AGENTS;
    const label = "New Agent";

    const agentsLayout: SidePanelOption[] = [
        { id: AgentNodeId.CONTRACT, label: "Contract Agent", icon: AgentNodeId.CONTRACT, nodeDetails: { categoryId } },
        { id: AgentNodeId.CHATBOT, label: "Chatbot Agent", icon: AgentNodeId.CHATBOT, nodeDetails: { categoryId } },
        { id: AgentNodeId.ROUTER, label: "Router Agent", icon: AgentNodeId.ROUTER, nodeDetails: { categoryId } },
        { id: AgentNodeId.ESCALATION, label: "Escalation Agent", icon: AgentNodeId.ESCALATION, nodeDetails: { categoryId } },
        { id: AgentNodeId.IMAGE, label: "Image", icon: AgentNodeId.IMAGE, nodeDetails: { categoryId } },
    ];


    function handleAddAgent(): void {
        canvasContext.addNodeAtPosition(getNewOption(label, categoryId));
    }

    function handleOptionClick(option: SidePanelOption): void {
            canvasContext.addNodeAtPosition(getPayloadFromOption(option, { categoryId }));
    }

    return (
        <div className="side-panel-subgroup-container agents">
            <SidePanelItem
                onClick={handleAddAgent}
                addLabel={label}
                preventDrag
            />

            <SubgroupWrapper
                layout={agentsLayout}
                onClick={handleOptionClick}
                ignoreEmpty
            />
        </div>
    );
}
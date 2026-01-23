import { useCanvas } from "../../../lib/contexts/CanvasContext";
import { CategoryId, ExternalAgentNodeId } from "../../../lib/enums";
import { type SidePanelOption } from "../../../lib/interfaces";
import { getNewOption, getPayloadFromOption } from "../../../lib/utilities/nodes";
import SidePanelItem from "./SidePanelItem";
import { SubgroupWrapper } from "./SubgroupWrapper";





import type { JSX } from "react";





export default function ExternalAgents(): JSX.Element {
    const canvasContext = useCanvas();
    const categoryId = CategoryId.EXTERNAL_AGENTS;
    const label = "New External Agent";

    const externalAgentsLayout: SidePanelOption[] = [
        { id: ExternalAgentNodeId.CONTRACT, label: "Contract Agent", icon: ExternalAgentNodeId.CONTRACT, nodeDetails: { categoryId } },
        { id: ExternalAgentNodeId.CHATBOT, label: "Chatbot Agent", icon: ExternalAgentNodeId.CHATBOT, nodeDetails: { categoryId } },
        { id: ExternalAgentNodeId.ROUTER, label: "Router Agent", icon: ExternalAgentNodeId.ROUTER, nodeDetails: { categoryId } },
        { id: ExternalAgentNodeId.ESCALATION, label: "Escalation Agent", icon: ExternalAgentNodeId.ESCALATION, nodeDetails: { categoryId } },
        { id: ExternalAgentNodeId.IMAGE, label: "Image", icon: ExternalAgentNodeId.IMAGE, nodeDetails: { categoryId } },
    ];


    function handleAddExternalAgent(): void {
        canvasContext.addNodeAtPosition(getNewOption(label, categoryId));
    }

    function handleOptionClick(option: SidePanelOption): void {
            canvasContext.addNodeAtPosition(getPayloadFromOption(option, { categoryId }));
    }

    return (
        <div className="side-panel-subgroup-container external-agents">
            <SidePanelItem
                onClick={handleAddExternalAgent}
                addLabel={label}
                preventDrag
            />

            <SubgroupWrapper
                layout={externalAgentsLayout}
                onClick={handleOptionClick}
                ignoreEmpty
            />
        </div>
    );
}
import { useCanvas } from "../../../lib/contexts/CanvasContext";
import { CategoryId, PromptNodeId } from "../../../lib/enums";
import { type SidePanelOption } from "../../../lib/interfaces";
import { getPayloadFromOption } from "../../../lib/utilities/nodes";
import { SubgroupWrapper } from "./SubgroupWrapper";




import type { JSX } from "react";




export default function Prompts(): JSX.Element {
    const canvasContext = useCanvas();
    const categoryId = CategoryId.PROMPTS;

    const promptsLayout: SidePanelOption[] = [
        { id: PromptNodeId.CONTRACT, label: "Contracts Prompt", icon: PromptNodeId.CONTRACT, nodeDetails: { categoryId } },
        { id: PromptNodeId.CHATBOT, label: "Chatbot Prompt", icon: PromptNodeId.CHATBOT, nodeDetails: { categoryId } },
        { id: PromptNodeId.ROUTER, label: "Router Prompt", icon: PromptNodeId.ROUTER, nodeDetails: { categoryId } },
        { id: PromptNodeId.ESCALATION, label: "Escalation Prompt", icon: PromptNodeId.ESCALATION, nodeDetails: { categoryId } },
    ];


    function handleOptionClick(option: SidePanelOption): void {
        canvasContext.addNodeAtPosition(getPayloadFromOption(option, { categoryId }));
    }

    return (
        <div className="side-panel-subgroup-container prompts">
            <SubgroupWrapper
                layout={promptsLayout}
                onClick={handleOptionClick}
            />
        </div>
    );
}
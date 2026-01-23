import { useCanvas } from "../../../lib/contexts/CanvasContext";
import { CategoryId, OutputNodeId } from "../../../lib/enums";
import { type SidePanelOption } from "../../../lib/interfaces";
import { getPayloadFromOption } from "../../../lib/utilities/nodes";
import { SubgroupWrapper } from "./SubgroupWrapper";




import type { JSX } from "react";




export default function Outputs(): JSX.Element {
    const canvasContext = useCanvas();
    const categoryId = CategoryId.OUTPUTS;

    const outputsLayout: SidePanelOption[] = [
        { id: OutputNodeId.TEXT, label: "Text", icon: OutputNodeId.TEXT, nodeDetails: { categoryId } },
        { id: OutputNodeId.AUDIO, label: "Audio", icon: OutputNodeId.AUDIO, nodeDetails: { categoryId } },
        { id: OutputNodeId.TEMPLATE, label: "Template", icon: OutputNodeId.TEMPLATE, nodeDetails: { categoryId } },
        { id: OutputNodeId.IMAGE, label: "Image", icon: OutputNodeId.IMAGE, nodeDetails: { categoryId } },
    ];


    function handleOptionClick(option: SidePanelOption): void {
        canvasContext.addNodeAtPosition(getPayloadFromOption(option, { categoryId }));
    }

    return (
        <div className="side-panel-subgroup-container outputs">
            <SubgroupWrapper
                layout={outputsLayout}
                onClick={handleOptionClick}
            />
        </div>
    );
}
import { CategoryId, InputNodeId } from "../../../lib/enums";
import { useCanvas } from "../../../lib/contexts/CanvasContext";
import { type SidePanelOption } from "../../../lib/interfaces";
import { getPayloadFromOption } from "../../../lib/utilities/nodes";
import { SubgroupWrapper } from "./SubgroupWrapper";




import type { JSX } from "react";




export default function Inputs(): JSX.Element {
    const canvasContext = useCanvas();
    const categoryId = CategoryId.INPUTS;

    const inputsLayout: SidePanelOption[] = [
        { id: InputNodeId.TEXT, label: "Text", icon: InputNodeId.TEXT, nodeDetails: { categoryId } },
        { id: InputNodeId.AUDIO, label: "Audio", icon: InputNodeId.AUDIO, nodeDetails: { categoryId } },
        { id: InputNodeId.FILE, label: "File", icon: InputNodeId.FILE, nodeDetails: { categoryId } },
        { id: InputNodeId.URL, label: "URL", icon: InputNodeId.URL, nodeDetails: { categoryId } },
        { id: InputNodeId.IMAGE, label: "Image", icon: InputNodeId.IMAGE, nodeDetails: { categoryId } },
    ];
    

    function handleOptionClick(option: SidePanelOption): void {
        canvasContext.addNodeAtPosition(getPayloadFromOption(option, { categoryId }));
    }

    return (
        <div className="side-panel-subgroup-container inputs">
            <SubgroupWrapper
                layout={inputsLayout}
                onClick={handleOptionClick}
            />
        </div>
    );
}
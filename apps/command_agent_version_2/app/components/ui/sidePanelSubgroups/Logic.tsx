import { useCanvas } from "../../../lib/contexts/CanvasContext";
import { CategoryId, LogicNodeId } from "../../../lib/enums";
import { type SidePanelOption } from "../../../lib/interfaces";
import { getPayloadFromOption } from "../../../lib/utilities/nodes";
import { SubgroupWrapper } from "./SubgroupWrapper";




import type { JSX } from "react";




export default function Logic(): JSX.Element {
    const canvasContext = useCanvas();
    const categoryId = CategoryId.LOGIC;

    const logicLayout: SidePanelOption[] = [
        { id: LogicNodeId.IF_ELSE, label: "If / Else", icon: LogicNodeId.IF_ELSE, nodeDetails: { categoryId } },
        { id: LogicNodeId.TRANSFORM, label: "Transform", icon: LogicNodeId.TRANSFORM, nodeDetails: { categoryId } },
    ];


    function handleOptionClick(option: SidePanelOption): void {
        canvasContext.addNodeAtPosition(getPayloadFromOption(option, { categoryId }));
    }

    return (
        <div className="side-panel-subgroup-container logic">
            <SubgroupWrapper
                layout={logicLayout}
                onClick={handleOptionClick}
            />
        </div>
    );
}
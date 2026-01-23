import { useCanvas } from "../../../lib/contexts/CanvasContext";
import { ActionNodeId, CategoryId } from "../../../lib/enums";
import { type SidePanelOption } from "../../../lib/interfaces";
import { getNewOption, getPayloadFromOption } from "../../../lib/utilities/nodes";
import SidePanelItem from "./SidePanelItem";
import { SubgroupWrapper } from "./SubgroupWrapper";




import type { JSX } from "react";




export default function Actions(): JSX.Element {
    const canvasContext = useCanvas();
    const categoryId = CategoryId.ACTIONS;
    const label = "New Action";

    const actionsLayout: SidePanelOption[] = [
        { id: ActionNodeId.MCP, label: "MCP", icon: ActionNodeId.MCP, nodeDetails: { categoryId } },
        { id: ActionNodeId.REST_API, label: "Rest API", icon: ActionNodeId.REST_API, nodeDetails: { categoryId } },
        { id: ActionNodeId.PYTHON_FUNCTION, label: "Python Function", icon: ActionNodeId.PYTHON_FUNCTION, nodeDetails: { categoryId } },
    ];


    function handleAddAction(): void {
        canvasContext.addNodeAtPosition(getNewOption(label, categoryId));
    }

    function handleOptionClick(option: SidePanelOption): void {
        canvasContext.addNodeAtPosition(getPayloadFromOption(option, { categoryId }));
    }

    return (
        <div className="side-panel-subgroup-container actions">
            <SidePanelItem
                onClick={handleAddAction}
                addLabel={label}
                preventDrag
            />
            
            <SubgroupWrapper
                layout={actionsLayout}
                onClick={handleOptionClick}
                ignoreEmpty
            />
        </div>
    );
}
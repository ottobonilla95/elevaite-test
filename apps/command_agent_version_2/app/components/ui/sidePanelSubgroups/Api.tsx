import { useCanvas } from "../../../lib/contexts/CanvasContext";
import { ApiNodeId, CategoryId } from "../../../lib/enums";
import { type SidePanelOption } from "../../../lib/interfaces";
import { getNewOption, getPayloadFromOption } from "../../../lib/utilities/nodes";
import SidePanelItem from "./SidePanelItem";
import { SubgroupWrapper } from "./SubgroupWrapper";


import type { JSX } from "react";


const TestApiIds = [
    ApiNodeId.TEST_0, ApiNodeId.TEST_1, ApiNodeId.TEST_2, ApiNodeId.TEST_3, ApiNodeId.TEST_4,
    ApiNodeId.TEST_5, ApiNodeId.TEST_6, ApiNodeId.TEST_7, ApiNodeId.TEST_8, ApiNodeId.TEST_9,
    ApiNodeId.TEST_10, ApiNodeId.TEST_11, ApiNodeId.TEST_12, ApiNodeId.TEST_13, ApiNodeId.TEST_14,
    ApiNodeId.TEST_15, ApiNodeId.TEST_16, ApiNodeId.TEST_17, ApiNodeId.TEST_18, ApiNodeId.TEST_19,
] as const;

function getTestApi(): SidePanelOption[] {
    return TestApiIds.map((id, i) => ({
        id,
        icon: ApiNodeId.DEFAULT,
        label: `API Name ${i.toString()}`,
        tag: "API Key",
        nodeDetails: { categoryId: CategoryId.API },
    }));
}

const apiLayout: SidePanelOption[] = getTestApi();


export default function Api(): JSX.Element {
    const canvasContext = useCanvas();
    const categoryId = CategoryId.API;
    const label = "New API";

    function handleAddApi(): void {
        canvasContext.addNodeAtPosition(getNewOption(label, categoryId));
    }

    function handleOptionClick(option: SidePanelOption): void {
        canvasContext.addNodeAtPosition(getPayloadFromOption(option, { categoryId }));
    }

    return (
        <div className="side-panel-subgroup-container api">
            <SidePanelItem
                onClick={handleAddApi}
                addLabel={label}
                preventDrag
            />

            <SubgroupWrapper
                layout={apiLayout}
                onClick={handleOptionClick}
                ignoreEmpty
            />
        </div>
    );
}
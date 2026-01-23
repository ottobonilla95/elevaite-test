import { useCanvas } from "../../../lib/contexts/CanvasContext";
import { type ConfigPanelsProps } from "../../../lib/interfaces";
import { getItemDetailWithDefault, setItemDetail, typeGuards } from "../../../lib/utilities/config";
import { DisplayText } from "../DisplayText";
import "./ConfigPanels.scss";



import type { JSX } from "react";



export function OutputTextConfig({ node }: ConfigPanelsProps): JSX.Element {
    const canvas = useCanvas();
    const text = getItemDetailWithDefault(node, "text", "", typeGuards.isString);


    function handleTextChange(newText: string): void {
        if (!canvas.selectedNodeId) return;
        
        canvas.updateNodeData(canvas.selectedNodeId, (data) => 
            setItemDetail(data, "text", newText)
        );
    }

    
    return (
        <div className="inner-config-panel-container output-text">
            <div className="description">
                Output the results of nodes as text.
            </div>
            <DisplayText
                label="Output Text"
                className="display-grow"
                value={text}
                onChange={handleTextChange}
                showDownload
                showExpand
                readOnly
            />
        </div>
    );
}
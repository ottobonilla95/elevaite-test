import { CommonButton } from "@repo/ui";
import { useCanvas } from "../../../lib/contexts/CanvasContext";
import { type InnerNodeProps } from "../../../lib/interfaces";
import { OutputTextKeys } from "../../../lib/model/innerEnums";
import { getItemDetailWithDefault, setItemDetail, typeGuards } from "../../../lib/utilities/config";
import { toast } from "../../../lib/utilities/toast";
import { Icons } from "../../icons";
import { DisplayText } from "../../ui/DisplayText";
import { ConfigButton } from "./ConfigButton";
import "./InnerNodes.scss";



import type { JSX } from "react";



export default function OutputText({ nodeId, nodeData }: InnerNodeProps): JSX.Element {
    const canvas = useCanvas();
    const text = getItemDetailWithDefault(nodeData, OutputTextKeys.TEXT, "", typeGuards.isString);

    function handleDownload(): void {
        if (!text) {
            toast.warning("Nothing to download.", { position: "top-center" });
            return;
        };
        const blob = new Blob([text], { type: "text/plain;charset=utf-8" });
        const url = URL.createObjectURL(blob);

        const link: HTMLAnchorElement = document.createElement("a");
        link.href = url;
        link.download = "Downloaded text.txt";

        document.body.appendChild(link);
        link.click();

        document.body.removeChild(link);
        URL.revokeObjectURL(url);
    }

    async function handleCopy(): Promise<void> {
        if (!text) {
            toast.warning("Nothing to copy.", { position: "top-center" });
            return;
        }
        try {
		    await navigator.clipboard.writeText(text);
            toast.success("Text copied to clipboard.", { position: "top-center" });
        } catch {
            toast.error("Failed to copy text to clipboard. Please try again.", { position: "top-center" });
        }
    }

    function handleClear(): void {
        if (!nodeId) return;
        canvas.updateNodeData(nodeId, (data) => 
            setItemDetail(data, OutputTextKeys.TEXT, "")
        );
        // toast.success("Text cleared.", { position: "top-center" });
    }

    
    return (
        <div className="inner-node-container">
            {/* <div className="actions-row">
                <CommonButton className="wide">
                    Text
                </CommonButton>
                <CommonButton onClick={handleDownload}>
                    <Icons.Node.SVGDownload/>
                </CommonButton>
                <CommonButton onClick={handleCopy}>
                    <Icons.Node.SVGDuplicate/>
                </CommonButton>
                <CommonButton className="destructive" onClick={handleClear}>
                    <Icons.Node.SVGDelete/>
                </CommonButton>
            </div> */}
            <ConfigButton>
                <DisplayText
                    className="standard-text-display"
                    value={text}
                    expandedHeader="Output text"
                    readOnly
                />
            </ConfigButton>
        </div>
    );
}

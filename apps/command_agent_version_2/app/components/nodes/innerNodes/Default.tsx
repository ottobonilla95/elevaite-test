import { type InnerNodeProps } from "../../../lib/interfaces";
import { Icons } from "../../icons";
import "../CommandNodeTray.scss";

import type { JSX } from "react";

export default function Default(_props: InnerNodeProps): JSX.Element {
    return (
        <div className="command-node-tray-container">
            <div className="tray-item">
                <Icons.Node.SVGKnowledgeBase/>
                <span>Arlo Knowledge Base</span>
                <div className="counter">3</div>
            </div>
            <div className="tray-item">
                <Icons.Node.SVGModel/>
                <span>No Model Selected</span>
            </div>
            <div className="tray-item">
                <Icons.Node.SVGTool/>
                <span>No Tools Selected</span>
            </div>
            <div className="tray-item">
                <Icons.Node.SVGPrompt/>
                <span>No Prompt Selected</span>
            </div>
        </div>
    );
}

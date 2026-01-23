import { CommonTray } from "@repo/ui";
import { type InnerNodeProps, type NodeStatusInfo, type SidePanelNodeId, type SidePanelPayload } from "../../lib/interfaces";
import { AgentNodeId, type AllNodeIds, CategoryId, InputNodeId, OutputNodeId, PromptNodeId } from "../../lib/model/uiEnums";
import { Icons } from "../icons";
import "./CommandNodeTray.scss";
import { Agent } from "./innerNodes/Agent";
import Default from "./innerNodes/Default";
import InputText from "./innerNodes/InputText";
import OutputText from "./innerNodes/OutputText";
import { Prompt } from "./innerNodes/Prompt";

import type { JSX } from "react";

interface CommandNodeTrayProps {
    isOpen: boolean;
    nodeId?: SidePanelNodeId;
    nodeData: SidePanelPayload;
    status: NodeStatusInfo;
}

type InnerNodeRenderer = (props: InnerNodeProps) => JSX.Element;

const innerNodeRegistry: Partial<Record<AllNodeIds, InnerNodeRenderer>> = {
    [AgentNodeId.CONTRACT]: Agent,
    [AgentNodeId.CHATBOT]: Agent,
    [AgentNodeId.ROUTER]: Agent,
    [AgentNodeId.ESCALATION]: Agent,
    [AgentNodeId.IMAGE]: Agent,
    [PromptNodeId.CONTRACT]: Prompt,
    [PromptNodeId.CHATBOT]: Prompt,
    [PromptNodeId.ROUTER]: Prompt,
    [PromptNodeId.ESCALATION]: Prompt,
    [InputNodeId.TEXT]: InputText,
    [OutputNodeId.TEXT]: OutputText,
};

// Fallback registry for "new" items based on category
const categoryFallbackRegistry: Partial<Record<CategoryId, InnerNodeRenderer>> = {
    [CategoryId.AGENTS]: Agent,
    [CategoryId.EXTERNAL_AGENTS]: Agent,
    [CategoryId.PROMPTS]: Prompt,
    [CategoryId.INPUTS]: InputText,
    [CategoryId.OUTPUTS]: OutputText,
};

export function CommandNodeTray(props: CommandNodeTrayProps): JSX.Element {
    const InnerNodeComponent = getInnerNode(props.nodeId, props.nodeData);
  
    
    function getInnerNode(nodeId?: SidePanelNodeId, nodeData?: SidePanelPayload): InnerNodeRenderer {
        if (!nodeId) return Default;
        
        const specificRenderer = innerNodeRegistry[nodeId as AllNodeIds];
        if (specificRenderer) return specificRenderer;
        
        const categoryId = nodeData?.nodeDetails?.categoryId;
        if (categoryId) {
            const categoryRenderer = categoryFallbackRegistry[categoryId];
            if (categoryRenderer) return categoryRenderer;
        }
        
        return Default;
    }


    return (
        <CommonTray
            isOpen={props.isOpen}
        >
            <InnerNodeComponent
                nodeId={props.nodeId}
                nodeData={props.nodeData}
                info={props.status}
            />            

            {!props.status.time && !props.status.tokens ? undefined :
                <div className="command-node-tray-details-container">
                    {!props.status.time ? undefined :
                        <div className="tray-detail-item">
                            <Icons.Node.SVGClock/>
                            <span>{`${props.status.time.toString()} sec`}</span>
                        </div>
                    }
                    {!props.status.tokens ? undefined :
                        <div className="tray-detail-item">
                            <Icons.Node.SVGToken/>
                            <span>{`${props.status.tokens.toString()} tokens`}</span>
                        </div>
                    }
                </div>
            }
        </CommonTray>
    );
}

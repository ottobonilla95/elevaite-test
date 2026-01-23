import { useEffect, useMemo, type JSX } from "react";
import { type InnerNodeProps } from "../../../lib/interfaces";
import { AgentKeys } from "../../../lib/model/innerEnums";
import { getItemDetail } from "../../../lib/utilities/config";
import { Icons } from "../../icons";
import { getModelById } from "../../ui/ModelSelection";
import { ConfigButton } from "./ConfigButton";
import "./InnerNodes.scss";

export function Agent({ nodeData }: InnerNodeProps): JSX.Element {
  const modelId = getItemDetail(nodeData, AgentKeys.MODEL);
  const tools = getItemDetail(nodeData, AgentKeys.TOOLS);

  const model = useMemo(() => {
    if (!modelId) return undefined;
    return getModelById(modelId as string);
  }, [modelId]);

  // useEffect(() => {
  //     console.log("Data:", nodeData.nodeDetails?.itemDetails);
  // }, [nodeData]);

  return (
    <div className="inner-node-container prompt">
      <ConfigButton anchor={AgentKeys.MODEL}>
        <div className="inner-node-section">
          <Icons.Node.SVGModel />
          {model ? model.label : "No model selected"}
        </div>
      </ConfigButton>
      <ConfigButton anchor={AgentKeys.TOOLS}>
        <div className="inner-node-section">
          <Icons.Node.SVGTool />
          {!tools || !Array.isArray(tools) ? (
            "No tools selected"
          ) : (
            <>
              <span>Tools</span>
              <span className="inner-tag">{tools.length}</span>
            </>
          )}
        </div>
      </ConfigButton>
    </div>
  );
}

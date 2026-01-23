import { useMemo, type JSX } from "react";
import { type InnerNodeProps } from "../../../lib/interfaces";
import { PromptKeys } from "../../../lib/model/innerEnums";
import { getItemDetail } from "../../../lib/utilities/config";
import { Icons } from "../../icons";
import { getModelById } from "../../ui/ModelSelection";
import { ConfigButton } from "./ConfigButton";
import "./InnerNodes.scss";





export function Prompt({ nodeData }: InnerNodeProps): JSX.Element {
    const modelId = getItemDetail(nodeData, PromptKeys.MODEL);
    const temperature = getItemDetail(nodeData, PromptKeys.TEMPERATURE);
    const maxTokens = getItemDetail(nodeData, PromptKeys.MAX_TOKENS);

    const model = useMemo(() => { if (!modelId) return undefined; return getModelById(modelId as string)}, [modelId])

    
    return (
        <div className="inner-node-container prompt">
            {!modelId && !temperature && !maxTokens ? 
                <ConfigButton>
                    <div className="inner-node-section warning">
                        <Icons.SVGWarning/>
                        Prompt not configured
                    </div>
                </ConfigButton>
            :
                <>
                    <ConfigButton anchor={PromptKeys.MODEL}>
                        <div className="inner-node-section">
                            {model?.icon ? model.icon
                                : <Icons.SVGWarning color="var(--ev-colors-highlight)" />
                            }
                            {model ? model.label : "Model not selected"}                            
                        </div>
                    </ConfigButton>
                    <ConfigButton anchor={PromptKeys.TEMPERATURE}>
                        <div className="inner-node-section">
                            {temperature ? <span className="inner-tag">{temperature as string}</span>
                                : <Icons.SVGWarning color="var(--ev-colors-highlight)" />
                            }
                            {temperature ? "temperature" : "temperature not set"}
                        </div>
                    </ConfigButton>
                    <ConfigButton anchor={PromptKeys.MAX_TOKENS}>
                        <div className="inner-node-section">
                            {maxTokens ? <span className="inner-tag">{maxTokens as string}</span>
                                : <Icons.SVGWarning color="var(--ev-colors-highlight)" />
                            }
                            {maxTokens ? "max tokens" : "max tokens not set"}
                        </div>
                    </ConfigButton>
                </>
            }
        </div>
    );
}
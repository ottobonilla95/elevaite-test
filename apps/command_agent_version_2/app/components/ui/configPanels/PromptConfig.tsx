import { cls, CommonButton, CommonTray } from "@repo/ui";
import { useEffect, useState, type JSX } from "react";
import { useConfigPanel } from "../../../lib/contexts/ConfigPanelContext";
import { useNodeConfig } from "../../../lib/hooks/useNodeConfig";
import { type ConfigPanelsProps } from "../../../lib/interfaces";
import { PromptKeys } from "../../../lib/model/innerEnums";
import { getItemDetail, typeGuards } from "../../../lib/utilities/config";
import { Icons } from "../../icons";
import { DisplayText } from "../DisplayText";
import { ModelSelection } from "../ModelSelection";
import { Slider } from "../Slider";
import { useFocusAnchor } from "../../../lib/hooks/useFocusAnchor";
import "./ConfigPanels.scss";




export function PromptConfig({ node: _node }: ConfigPanelsProps): JSX.Element {
    useFocusAnchor();
    const { selectedNode, updateDraftMultiple } = useConfigPanel();
    const [isParametersOpen, setIsParametersOpen] = useState(true);    
    const [text, setText] = useNodeConfig("text", "", typeGuards.isString);
    const [model, setModel] = useNodeConfig("model", "", typeGuards.isString);
    const [temperature, setTemperature] = useNodeConfig("temperature", 0.5, typeGuards.isNumber);
    const [maxTokens, setMaxTokens] = useNodeConfig("maxTokens", 4000, typeGuards.isNumber);

    
    useEffect(() => {
        if (!selectedNode) return;
        const missing: Record<string, number> = {};
        if (getItemDetail(selectedNode, "temperature") === undefined) missing.temperature = 0.5;
        if (getItemDetail(selectedNode, "maxTokens") === undefined) missing.maxTokens = 4000;
        if (Object.keys(missing).length > 0) updateDraftMultiple(missing);
    }, [selectedNode?.id]);

    
    return (
        <div className="inner-config-panel-container output-text">
            <div id={PromptKeys.TEXT}>
                <DisplayText
                    label="Prompt Instructions"
                    className="display-medium"
                    value={text}
                    onChange={setText}
                    showExpand
                    showAIAssist
                    showAddVariable
                    placeholder="Define the text transformation task. Use {{variable_name}} to reference input data."
                />
            </div>
            <CommonButton className="tray-button" noBackground onClick={() => { setIsParametersOpen(!isParametersOpen); }}>
                <div className="tray-row">
                    <div className="main-label">
                        <div className="icon"><Icons.SVGSettings/></div>
                        <span>Parameters</span>
                        <div className="info" title="Modify the details of the prompt"><Icons.SVGInfo/></div>
                    </div>
                </div>
                <div className={cls("tray-chevron", isParametersOpen && "open")}>
                    <Icons.SVGChevronDown/>
                </div>
            </CommonButton>
            <CommonTray isOpen={isParametersOpen}>
                <div id={PromptKeys.MODEL} className="tray-row">
                    <span className="label">Model</span>
                    <ModelSelection
                        value={model}
                        onChange={setModel}
                    />
                </div>
                <div id={PromptKeys.TEMPERATURE} className="tray-row">
                    <Slider
                        value={temperature}
                        onChange={setTemperature}
                        min={0}
                        max={1}
                        label="Temperature"
                        startLabel="Predictable"
                        endLabel="Creative"
                    />
                </div>
                <div id={PromptKeys.MAX_TOKENS} className="tray-row">
                    <Slider
                        value={maxTokens}
                        onChange={setMaxTokens}
                        min={0}
                        max={10000}
                        step={100}
                        decimals={0}
                        label="Max Tokens"
                        startLabel="Small Content"
                        endLabel="Large Content"
                    />
                </div>
            </CommonTray>
        </div>
    );
}
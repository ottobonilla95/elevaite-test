import { useNodeConfig } from "../../../lib/hooks/useNodeConfig";
import { type ConfigPanelsProps } from "../../../lib/interfaces";
import { InputTextKeys } from "../../../lib/model/innerEnums";
import { typeGuards } from "../../../lib/utilities/config";
import { DisplayText } from "../DisplayText";
import "./ConfigPanels.scss";



import type { JSX } from "react";



export function InputTextConfig({ node: _node }: ConfigPanelsProps): JSX.Element {
    const [text, setText] = useNodeConfig(InputTextKeys.TEXT, "", typeGuards.isString);

    
    return (
        <div className="inner-config-panel-container input-text">
            <div className="description">
                Allow users to input text.
            </div>
            <DisplayText
                label="Input Text"
                className="display-grow"
                value={text}
                onChange={setText}
                showExpand
                showDownload
                showAIAssist
                placeholder="Type text here"
            />
        </div>
    );
}
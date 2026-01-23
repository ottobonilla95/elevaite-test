import { type InnerNodeProps } from "../../../lib/interfaces";
import { InputTextKeys } from "../../../lib/model/innerEnums";
import { getItemDetailWithDefault, typeGuards } from "../../../lib/utilities/config";
import { DisplayText } from "../../ui/DisplayText";
import { ConfigButton } from "./ConfigButton";
import "./InnerNodes.scss";



import type { JSX } from "react";



export default function InputText({ nodeData }: InnerNodeProps): JSX.Element {
    const text = getItemDetailWithDefault(nodeData, InputTextKeys.TEXT, "", typeGuards.isString);

    
    return (
        <div className="inner-node-container input-text">
            <ConfigButton>
                <DisplayText
                    className="standard-text-display"
                    value={text}
                    expandedHeader="Input text"
                    readOnly
                    placeholder="Text will appear here (click to open the configuration panel)"
                />
            </ConfigButton>
        </div>
    );
}

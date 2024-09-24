import { SimpleInput, SimpleTextarea } from "@repo/ui/components";
import { useState } from "react";
import "./ExtractedBit.scss";


interface ExtractedBitProps {
    label: string;
    value: string; 
    onChange: (label: string, newValue: string) => void;
}

export function ExtractedBit(props: ExtractedBitProps): JSX.Element {
    const [manualValue, setManualValue] = useState(props.value);

    function handleChange(text :string): void {
        setManualValue(text);
        props.onChange(props.label, text);
    }

    return (
        <div className="extracted-bit-container">
            <div className="top">
                <div className="label">{props.label}</div>
                {/* <div className="date"></div> */}
            </div>
            {manualValue.length > 70 ? 
                <SimpleTextarea
                    value={manualValue}
                    onChange={handleChange}
                    useCommonStyling
                    placeholder={!props.value ? "Value not found. Insert manually" : ""}
                    rows={Math.min(Math.ceil(manualValue.length / 70), 5)}
                    // title={manualValue.length > 30 ? manualValue: ""}
                />
            :
                <SimpleInput
                    value={manualValue}
                    onChange={handleChange}
                    useCommonStyling
                    placeholder={!props.value ? "Value not found. Insert manually" : ""}
                />
            }
        </div>
    );
}
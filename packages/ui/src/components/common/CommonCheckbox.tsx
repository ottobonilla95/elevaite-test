"use client";
import { useState } from "react";
import "./CommonCheckbox.scss";
import { ElevaiteIcons } from "../icons/elevaite";



export interface CommonCheckboxProps {
    field?: string; // Use this to facilitate multi-variable setting
    label?: string;
    info?: string;
    errorMessage?: string;
    defaultTrue?: boolean;
    onChange?: (value: boolean, field?: string) => void;
}



export function CommonCheckbox(props: CommonCheckboxProps): JSX.Element {
    const [isChecked, setIsChecked] = useState(!!props.defaultTrue);

    
    function handleChange(event: React.FormEvent<HTMLInputElement>): void {
        setIsChecked(event.currentTarget.checked);
        if (props.onChange) props.onChange(event.currentTarget.checked, props.field);
    }

    
    return (
        <div className="common-checkbox-container">
            <div className="checkbox-content">
                <input
                    checked={isChecked}
                    onChange={handleChange}
                    type="checkbox"
                />
                <div className={["checkbox-icon", isChecked ? "shown" : ""].filter(Boolean).join(" ")}>
                    <ElevaiteIcons.SVGCheckmark/>
                </div>
            </div>
            {!props.label && !props.info && !props.errorMessage ? null :
                <div className="labels">
                    <span className="title">
                        {props.label}
                    </span>
                    {!props.info ? null :
                        <div className="info" title={props.info}><ElevaiteIcons.SVGInfo/></div>
                    }
                    <div className="error-message">{props.errorMessage ? props.errorMessage : ""}</div>
                </div>
            }
        </div>
    );
}


"use client";
import type { JSX } from "react";
import { useState } from "react";
import "./CommonCheckbox.scss";
import { ElevaiteIcons } from "../icons/elevaite";



export interface CommonCheckboxProps {
    field?: string; // Use this to facilitate multi-variable setting
    label?: string;
    info?: string;
    errorMessage?: string;
    defaultTrue?: boolean;
	checked?: boolean;
    disabled?: boolean;
    onChange?: (value: boolean, field?: string) => void;
}



export function CommonCheckbox(props: CommonCheckboxProps): JSX.Element {
    const [isChecked, setIsChecked] = useState(Boolean(props.defaultTrue));


    function handleChange(event: React.FormEvent<HTMLInputElement>): void {
        setIsChecked(event.currentTarget.checked);
        if (props.onChange) props.onChange(event.currentTarget.checked, props.field);
    }

	const checkedValue = props.checked !== undefined ? props.checked : isChecked;

    return (
        <div className="common-checkbox-container">
            <div className="checkbox-content">
                <input
                    checked={checkedValue}
                    onChange={handleChange}
                    type="checkbox"
                    disabled={props.disabled}
                />
                <div className={["checkbox-icon", checkedValue ? "shown" : ""].filter(Boolean).join(" ")}>
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


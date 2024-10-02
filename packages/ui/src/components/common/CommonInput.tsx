"use client";
import { useEffect, useState, KeyboardEvent } from "react";
import { ElevaiteIcons } from "../icons";
import "./CommonInput.scss";


const WARNING_MESSAGE_FIELD_IS_REQUIRED = "This field is required.";




export interface CommonInputProps {
    field?: string; // Use this to facilitate multi-variable setting
    label?: string;
    required?: boolean;
    info?: string;
    placeholder?: string;
    errorMessage?: string;
    labelIcon?: React.ReactNode;
    tooltip?: string;
    disabled?: boolean;
    noDisabledTooltip?: boolean;
    initialValue?: string;
    controlledValue?: string; // Use this to control the value externally
    className?: string;
    onChange?: (value: string, field?: string) => void;
    onKeyDown?: (key: string, field?: string) => void;
}

export function CommonInput(props: CommonInputProps): JSX.Element {
    const [value, setValue] = useState(props.initialValue ?? "");
    const [hasBeenChanged, setHasBeenChanged] = useState(false);
    const [requiredWarning, setRequiredWarning] = useState("");
    
    
    useEffect(() => {
        if (props.controlledValue === undefined || props.controlledValue === value) return;
        setValue(props.controlledValue);
    }, [props.controlledValue]);

    useEffect(() => {
        if (value.length > 0) {
            setHasBeenChanged(true);
            if (requiredWarning) setRequiredWarning("");
        }
        if (props.onChange) props.onChange(value, props.field);
    }, [value]);


    function handleBlur(): void {
        if (hasBeenChanged && props.required && !value) {
            setRequiredWarning(WARNING_MESSAGE_FIELD_IS_REQUIRED);
        } else setRequiredWarning("");
    }


    function handleChange(event: React.FormEvent<HTMLInputElement>): void {
        setValue(event.currentTarget.value);
    }

    function handleKeyDown(event: KeyboardEvent<HTMLInputElement>): void {
        if (props.onKeyDown) props.onKeyDown(event.key, props.field);
    }


    return (
        <div className={[
            "common-input-container",
            props.className,
        ].filter(Boolean).join(" ")}>
            {!props.label && !props.required && !props.info && !props.errorMessage ? null :
                <div className="labels">
                    <span className="title">
                        {props.label}
                        { !props.required ? null : 
                            <span className={["required", requiredWarning ? "unfulfilled" : undefined].filter(Boolean).join(" ")}>*</span>
                        }
                    </span>
                    {!props.info ? null :
                        <div className="info" title={props.info}><ElevaiteIcons.SVGInfo/></div>
                    }
                    <div className="error-message">{props.errorMessage ? props.errorMessage : requiredWarning}</div>
                    {!props.labelIcon ? undefined :
                        <div className="label-icon">{props.labelIcon}</div>
                    }
                </div>
            }
            <input
                onBlur={handleBlur}
                onChange={handleChange}
                onKeyDown={handleKeyDown}
                placeholder={props.placeholder}
                value={value}
                disabled={props.disabled}
                title={props.tooltip ?? (props.disabled && !props.noDisabledTooltip ? "This field is disabled." : "")}
            />
        </div>
    );
}


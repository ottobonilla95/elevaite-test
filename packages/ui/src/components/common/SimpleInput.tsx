"use client";
import { KeyboardEvent, MutableRefObject, useEffect, useRef, useState } from "react";
import "./SimpleInput.scss";



interface SimpleInputProps extends Omit<React.InputHTMLAttributes<HTMLInputElement>, "onChange" | "onKeyDown"> {
    wrapperClassName?: string;
    useCommonStyling?: boolean;
    leftIcon?: React.ReactNode;
    hideLeftIcon?: boolean;
    rightIcon?: React.ReactNode;
    hideRightIcon?: boolean;
    autoSize?: boolean;
    passedRef?: MutableRefObject<HTMLInputElement|null>;
    value: string;
    onChange?: (value: string) => void;
    onKeyDown?: (key: string, event: KeyboardEvent<HTMLInputElement>) => void;
}

export function SimpleInput({autoSize, wrapperClassName, useCommonStyling, leftIcon, hideLeftIcon, rightIcon, hideRightIcon, passedRef, value, onChange, onKeyDown, ...props}: SimpleInputProps): JSX.Element {
    const inputRef = useRef<HTMLInputElement | null>(null);
    const textMeasureRef = useRef<HTMLSpanElement | null>(null);
    const [inputWidth, setInputWidth] = useState<string | undefined>(undefined);
    
    
    useEffect(() => {
        if (autoSize && textMeasureRef.current && inputRef.current) {
            const contentWidth = textMeasureRef.current.offsetWidth;
            setInputWidth(`${contentWidth + 10}px`);
        }
    }, [value, autoSize]);


    function handleChange(event: React.FormEvent<HTMLInputElement>): void {
        if (onChange) onChange(event.currentTarget.value);
    }

    function handleKeyDown(event: KeyboardEvent<HTMLInputElement>): void {
        if (onKeyDown) onKeyDown(event.key, event);
    }


    return (
        <div className={[
            "simple-input-container",
            wrapperClassName,
            useCommonStyling ? "common-style" : undefined,
        ].filter(Boolean).join(" ")}>
            {leftIcon && !hideLeftIcon ? leftIcon : undefined}
            {autoSize && (
                <span
                    className="autosize-area"
                    ref={textMeasureRef}
                >
                    {value || props.placeholder || ""}
                </span>
            )}
            <input
                ref={(element) => {
                    inputRef.current = element;
                    if (passedRef) { passedRef.current = element; }
                }}
                value={value}
                onChange={handleChange}
                onKeyDown={handleKeyDown}
                style={autoSize && inputWidth ? { width: inputWidth } : undefined}
                {...props}
            />
            {rightIcon && !hideRightIcon ? rightIcon : undefined}
        </div>
    );
}
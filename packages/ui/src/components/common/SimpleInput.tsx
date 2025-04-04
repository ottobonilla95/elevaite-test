"use client";
import { type KeyboardEvent, type MutableRefObject, useEffect, useRef, useState } from "react";
import { CommonButton } from "./CommonButton";
import "./SimpleInput.scss";



interface SimpleInputProps extends Omit<React.InputHTMLAttributes<HTMLInputElement>, "onChange" | "onKeyDown"> {
    wrapperClassName?: string;
    useCommonStyling?: boolean;
    leftIcon?: React.ReactNode;
    hideLeftIcon?: boolean;
    rightIcon?: React.ReactNode;
    bottomRightIcon?: React.ReactNode;
    inlinePrompts?: string[];
    hideRightIcon?: boolean;
    autoSize?: boolean;
    passedRef?: MutableRefObject<HTMLInputElement|null>;
    value: string;
    onChange?: (value: string) => void;
    onKeyDown?: (key: string, event: KeyboardEvent<HTMLInputElement>) => void;
}

export function SimpleInput({autoSize, wrapperClassName, useCommonStyling, leftIcon, hideLeftIcon, rightIcon, bottomRightIcon, inlinePrompts, hideRightIcon, passedRef, value, onChange, onKeyDown, ...props}: SimpleInputProps): JSX.Element {
    const inputRef = useRef<HTMLInputElement | null>(null);
    const textMeasureRef = useRef<HTMLSpanElement | null>(null);
    const [inputWidth, setInputWidth] = useState<string | undefined>(undefined);
    
    
    useEffect(() => {
        if (autoSize && textMeasureRef.current && inputRef.current) {
            const contentWidth = textMeasureRef.current.offsetWidth;
            setInputWidth(`${(contentWidth + 10).toString()}px`);
        }
    }, [value, autoSize]);


    function handleChange(event: React.FormEvent<HTMLInputElement>): void {
        if (onChange) onChange(event.currentTarget.value);
    }

    function handleKeyDown(event: KeyboardEvent<HTMLInputElement>): void {
        if (onKeyDown) onKeyDown(event.key, event);
    }

    function handlePromptClick(prompt: string): void {
        if (onChange) onChange(prompt);
    }


    return (
        <div className={[
            "simple-input-container",
            wrapperClassName,
            useCommonStyling ? "common-style" : undefined,
        ].filter(Boolean).join(" ")}>
            <div className="simple-input-contents">
                {leftIcon && !hideLeftIcon ? leftIcon : undefined}
                {!autoSize ? undefined : (
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
            {!inlinePrompts ? undefined :
                <div className="bottom-row">
                    <div className="prompts-row">
                        {inlinePrompts.map((prompt, index) => 
                            <CommonButton
                                key={prompt + index.toString()}
                                className="prompt-button"
                                noBackground
                                onClick={() => { handlePromptClick(prompt); }}
                            >
                                {prompt}
                            </CommonButton>
                        )}
                    </div>
                    {bottomRightIcon && !hideRightIcon ? bottomRightIcon : undefined}
                </div>
            }
        </div>
    );
}
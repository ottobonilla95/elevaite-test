import { KeyboardEvent, MutableRefObject } from "react";
import "./SimpleTextarea.scss";



interface SimpleTextAreaProps extends Omit<React.TextareaHTMLAttributes<HTMLTextAreaElement>, "onChange" | "onKeyDown"> {
    wrapperClassName?: string;
    useCommonStyling?: boolean;
    leftIcon?: React.ReactNode;
    hideLeftIcon?: boolean;
    rightIcon?: React.ReactNode;
    hideRightIcon?: boolean;
    passedRef?: MutableRefObject<HTMLTextAreaElement|null>;
    value: string;
    onChange: (value: string) => void;
    onKeyDown?: (key: string) => void;
}

export function SimpleTextarea({wrapperClassName, useCommonStyling, leftIcon, hideLeftIcon, rightIcon, hideRightIcon, passedRef, value, onChange, onKeyDown, ...props}: SimpleTextAreaProps): JSX.Element {

    function handleChange(event: React.FormEvent<HTMLTextAreaElement>): void {
        onChange(event.currentTarget.value);
    }

    function handleKeyDown(event: KeyboardEvent<HTMLTextAreaElement>): void {
        if (onKeyDown) onKeyDown(event.key);
    }


    return (
        <div className={[
            "simple-textarea-container",
            wrapperClassName,
            useCommonStyling ? "common-style" : undefined,
        ].filter(Boolean).join(" ")}>
            {leftIcon && !hideLeftIcon ? leftIcon : undefined}
            <textarea
                ref={passedRef}
                value={value}
                onChange={handleChange}
                onKeyDown={handleKeyDown}
                {...props}
            />
            {rightIcon && !hideRightIcon ? rightIcon : undefined}
        </div>
    );
}
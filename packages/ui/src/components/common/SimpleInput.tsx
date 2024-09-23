import { KeyboardEvent, MutableRefObject } from "react";
import "./SimpleInput.scss";



interface SimpleInputProps extends Omit<React.InputHTMLAttributes<HTMLInputElement>, "onChange" | "onKeyDown"> {
    wrapperClassName?: string;
    useCommonStyling?: boolean;
    leftIcon?: React.ReactNode;
    hideLeftIcon?: boolean;
    rightIcon?: React.ReactNode;
    hideRightIcon?: boolean;
    passedRef?: MutableRefObject<HTMLInputElement|null>;
    value: string;
    onChange?: (value: string) => void;
    onKeyDown?: (key: string, event: KeyboardEvent<HTMLInputElement>) => void;
}

export function SimpleInput({wrapperClassName, useCommonStyling, leftIcon, hideLeftIcon, rightIcon, hideRightIcon, passedRef, value, onChange, onKeyDown, ...props}: SimpleInputProps): JSX.Element {

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
            <input
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
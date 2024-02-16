import { KeyboardEvent } from "react";
import "./SimpleInput.scss";



interface SimpleInputProps extends Omit<React.InputHTMLAttributes<HTMLInputElement>, "onChange" | "onKeyDown"> {
    wrapperClassName?: string;
    leftIcon?: React.ReactNode;
    hideLeftIcon?: boolean;
    rightIcon?: React.ReactNode;
    hideRightIcon?: boolean;
    value: string;
    onChange: (value: string) => void;
    onKeyDown?: (key: string) => void;
}

export function SimpleInput({wrapperClassName, leftIcon, hideLeftIcon, rightIcon, hideRightIcon, value, onChange, onKeyDown, ...props}: SimpleInputProps): JSX.Element {

    function handleChange(event: React.FormEvent<HTMLInputElement>): void {
        onChange(event.currentTarget.value);
    }

    function handleKeyDown(event: KeyboardEvent<HTMLInputElement>): void {
        if (onKeyDown) onKeyDown(event.key);
    }


    return (
        <div className={[
            "simple-input-container",
            wrapperClassName,
        ].filter(Boolean).join(" ")}>
            {leftIcon && !hideLeftIcon ? leftIcon : undefined}
            <input
                value={value}
                onChange={handleChange}
                onKeyDown={handleKeyDown}
                {...props}
            />
            {rightIcon && !hideRightIcon ? rightIcon : undefined}
        </div>
    );
}
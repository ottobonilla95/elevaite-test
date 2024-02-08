import "./SimpleInput.scss";



interface SimpleInputProps extends Omit<React.InputHTMLAttributes<HTMLInputElement>, "onChange"> {
    wrapperClassName?: string;
    leftIcon?: React.ReactNode;
    hideLeftIcon?: boolean;
    rightIcon?: React.ReactNode;
    hideRightIcon?: boolean;
    value: string;
    onChange: (value: string) => void;
}

export function SimpleInput({wrapperClassName, leftIcon, hideLeftIcon, rightIcon, hideRightIcon, value, onChange, ...props}: SimpleInputProps): JSX.Element {

    function handleChange(event: React.FormEvent<HTMLInputElement>): void {
        onChange(event.currentTarget.value);
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
                {...props}
            />
            {rightIcon && !hideRightIcon ? rightIcon : undefined}
        </div>
    );
}
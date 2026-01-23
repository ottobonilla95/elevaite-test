import type { JSX } from "react";
import "./CommonToggle.scss";

interface CommonToggleProps {
    checked: boolean;
    onChange: (value: boolean) => void;
    disabled?: boolean;
    label?: string;
    frontLabel?: boolean;
    className?: string;
}

export function CommonToggle({ checked, onChange, disabled, label, frontLabel, className }: CommonToggleProps): JSX.Element {
    function handleToggle(): void {
        if (!disabled) onChange(!checked);
    }

    return (
        <div className={["common-toggle", className, checked ? "checked" : "", disabled ? "disabled" : ""].filter(Boolean).join(" ")}>
            {frontLabel && label ? <span className="toggle-label">{label}</span> : null}
            <button
                className="toggle-slider"
                role="switch"
                aria-checked={checked}
                disabled={disabled}
                onClick={handleToggle}
                type="button"
            />
            {!frontLabel && label ? <span className="toggle-label">{label}</span> : null}
        </div>
    );
}

import { MutableRefObject } from "react";
import "./CommonButton.scss";


export interface CommonButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
    theme?: "light" | "dark";
    noBackground?: boolean;
    overrideClass?: boolean;
    passedRef?: MutableRefObject<HTMLButtonElement|null>;
}


export function CommonButton({className, overrideClass, noBackground, theme, passedRef, ...props}: CommonButtonProps): React.ReactElement<CommonButtonProps> {

    return (
        <button
            ref={passedRef}
            {...props}
            className={[
                "common-button",
                overrideClass ? undefined : "not-overriden",
                className,
                noBackground ? "no-background" : undefined,
                theme,
            ].filter(Boolean).join(" ")}
            type="button"
        >
            {props.children}
        </button>
    );
}
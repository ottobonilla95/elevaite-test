import "./CommonButton.scss";


export interface CommonButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
    theme?: "light" | "dark";
    noBackground?: boolean;
    overrideClass?: boolean;
}


export function CommonButton({className, overrideClass, noBackground, theme, ...props}: CommonButtonProps): React.ReactElement<CommonButtonProps> {

    return (
        <button
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